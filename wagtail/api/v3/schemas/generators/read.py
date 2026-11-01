import copy
from typing import Annotated, Any, Callable, Literal, TypeGuard, cast, get_type_hints

from django.core.exceptions import FieldDoesNotExist
from django.db.models import Model
from django.db.models.fields import Field
from django.db.models.fields.related import RelatedField
from django.db.models.fields.reverse_related import ForeignObjectRel
from modelcluster.fields import ParentalKey
from modelcluster.models import get_all_child_relations
from ninja import Schema
from ninja.errors import ConfigError
from ninja.orm import create_schema
from pydantic.fields import FieldInfo
from taggit.managers import TaggableManager

from wagtail.api import APIField
from wagtail.api.conf import get_model_field
from wagtail.api.rich_text import APIRichText
from wagtail.api.v3.fields import FieldSerializer
from wagtail.api.v3.schemas import BaseSchema
from wagtail.fields import RichTextField, StreamField
from wagtail.rich_text import features as feature_registry

from .blocks import (
    BlockSchemaBuilder,
    StreamFieldJsonSchema,
    register_default_block_schemas,
)

FieldSchema = tuple[Any, Any, Callable | None]
FieldSchemaFunc = Callable[["SchemaGenerator", Field], FieldSchema]


class SchemaGenerator:
    """
    Auto-generates Ninja read schemas for concrete models.

    Each generated schema combines a base schema with whatever extra fields a model
    declares through ``api_fields``, the mechanism used by the DRF-based API v2
    (see :mod:`wagtail.api.conf`). Plain, introspectable Django fields are typed
    via :func:`ninja.orm.create_schema`; everything else is handled on a
    best-effort basis - see ``build_schema`` for the exact rules.
    """

    def __init__(self):
        self.field_schemas: dict[type[Field | ForeignObjectRel], FieldSchemaFunc] = {}
        """
        Map of Django field classes to functions that return a tuple of
        (annotation, default value, resolver function) for that field type.
        """

        self._reverse_related_schema_cache: dict[type[Model], type[Schema]] = {}
        """
        Schemas already built for a given reverse-related model, so a model
        referenced by several models' api_fields only gets built once.
        """

        self._foreign_key_schema_cache: dict[type[Model], type[Schema]] = {}
        """
        Schemas already built for a given foreign key's related model, keyed
        separately from `_nested_schema_cache` since these are a distinct, much
        smaller shape (primary key(s) plus a meta.type), not a full nested schema.
        """

        self._models_being_built: list[type[Model]] = []
        """
        Models whose schemas are currently being built, outermost first, so a
        nested schema doesn't recurse back into a model it's already within.
        """

        self._foreign_key_schemas_being_built: set[type[Model]] = set()
        """
        Models whose foreign key schemas are currently being built, so a
        foreign key back to one of them (directly, or through other models)
        uses a reference schema instead of recursing forever.
        """

        self._foreign_key_reference_schema_cache: dict[type[Model], type[Schema]] = {}
        """
        Schemas already built for a foreign key's related model that only
        identify the object, see ``get_foreign_key_reference_schema``.
        """

        self._foreign_key_meta_schema_cache: dict[type[Model], type[Schema]] = {}
        """
        Meta schemas for a foreign key's related model, shared by its foreign
        key schema and its reference schema.
        """

    @staticmethod
    def _get_pk_names(model: type[Model]) -> list[str]:
        # With multi-table inheritance, the PK is a parent link (e.g. page_ptr),
        # so use the PK of the root model (e.g. Page.id) that's inherited by
        # the model, following the parent links through every level.
        while (pk := model._meta.pk).remote_field and pk.remote_field.parent_link:
            model = pk.remote_field.model
        # Use all PK fields, since a model can have a composite PK
        return [field.name for field in model._meta.pk_fields]

    @staticmethod
    def _custom_serializer_schema(api_field: APIField) -> FieldSchema:
        """Temporary API v2 compat shim for an ``APIField(serializer=...)``.

        Binds a private copy of the DRF serializer field - a deep copy, since
        DRF fields carry bind state (``field_name``, ``source_attrs``, ...) and
        the original instance is a single object shared from the model's
        ``api_fields`` tuple, still bound and used by API v2 at runtime - then
        defers to its own ``to_representation()``. This lets existing custom
        serializers (e.g. ``ImageRenditionField``) keep working as-is, rather
        than having to reimplement each one for v3.
        """

        from rest_framework.fields import Field, SkipField

        serializer = cast(Field, copy.deepcopy(api_field.serializer))
        serializer.bind(field_name=api_field.name, parent=None)
        try:
            return_type = get_type_hints(serializer.to_representation)["return"]
        except (KeyError, NameError):
            # No return type or it's only available when TYPE_CHECKING
            return_type = Any
        # allow_null / required may not reflect nullability as the field's
        # source may resolve to None regardless of those flags.
        return_type = return_type | None

        def resolve(obj: Model, context: dict) -> Any:
            try:
                value = serializer.get_attribute(obj)
            except SkipField:
                return None
            if value is None:
                return None
            return serializer.to_representation(value)

        return return_type, None, staticmethod(resolve)

    @staticmethod
    def _field_serializer_schema(api_field: APIField) -> FieldSchema:
        """Generate a schema field for an ``APIField(serializer=...)`` using a
        :class:`~wagtail.api.v3.fields.FieldSerializer`.

        A copy is bound, then ``to_representation()`` is called on the
        source-resolved value. The annotation is derived from
        ``to_representation()``'s return type hint, with ``None`` added since
        the source may resolve to ``None``.
        """

        field = cast(FieldSerializer, copy.deepcopy(api_field.serializer))
        field.bind(field_name=api_field.name)
        try:
            return_type = get_type_hints(field.to_representation)["return"]
        except (KeyError, NameError):
            # No return type or it's only available when TYPE_CHECKING
            return_type = Any
        return_type = return_type | None

        def resolve(obj: Model, context: dict) -> Any:
            value = field.get_attribute(obj)
            if value is None:
                return None
            return field.to_representation(value)

        return return_type, None, staticmethod(resolve)

    def register_field_schema(
        self,
        field_class: type[Field | ForeignObjectRel],
        func: FieldSchemaFunc,
    ) -> None:
        """Register a function to generate schema fields for ``field_class``."""
        self.field_schemas[field_class] = func

    def get_reverse_related_schema(self, model: type[Model]) -> type[Schema]:
        if model not in self._reverse_related_schema_cache:
            self._reverse_related_schema_cache[model] = self.build_schema(
                model,
                name=f"{model._meta.object_name}Schema",
                base_class=BaseSchema,
                nested=True,
            )
        return self._reverse_related_schema_cache[model]

    def get_foreign_key_schema(self, model: type[Model]) -> type[Schema]:
        """Build a nested schema for a foreign key's related model, without
        following any reverse relations (to avoid infinite recursion).

        Foreign keys within the related model's ``api_fields`` are expanded
        in the same way, except for a foreign key back to a model whose
        foreign key schema is already being built (e.g. a ``parent`` foreign
        key to the same model), which would otherwise recurse forever. That
        uses the related model's reference schema instead, see
        ``get_foreign_key_reference_schema``.

        A foreign key to a page also includes the same fields as a page's
        ``meta.parent``, i.e. the page's ID, title, specific type, and URLs.
        If the page model has no ``api_fields`` (e.g. the base ``Page``
        model), the schema is the same as ``meta.parent``.
        """
        from wagtail.api.v3.schemas.pages import (
            SimpleBasePageMetaSchema,
            SimpleBasePageSchema,
        )
        from wagtail.models import AbstractPage

        if model in self._foreign_key_schema_cache:
            return self._foreign_key_schema_cache[model]
        if model in self._foreign_key_schemas_being_built:
            return self.get_foreign_key_reference_schema(model)

        is_page = issubclass(model, AbstractPage)
        if is_page and not APIField.get_fields_for_model(model):
            return SimpleBasePageSchema

        self._foreign_key_schemas_being_built.add(model)
        try:
            name = f"{model._meta.object_name}ForeignKeySchema"
            schema = self.build_schema(
                model,
                name=f"{name}Base",
                base_class=SimpleBasePageSchema if is_page else BaseSchema,
                nested=True,
                follow_reverse_related=False,
            )
            # A page's meta.type isn't narrowed to the model, as it's the
            # page's specific type, which may be a subclass of the model
            meta_schema = (
                SimpleBasePageMetaSchema
                if is_page
                else self._get_foreign_key_meta_schema(model)
            )
            self._foreign_key_schema_cache[model] = self.extend_schema(
                schema,
                name,
                {"meta": (meta_schema, ..., None)},
            )
        finally:
            self._foreign_key_schemas_being_built.discard(model)
        return self._foreign_key_schema_cache[model]

    def get_foreign_key_reference_schema(self, model: type[Model]) -> type[Schema]:
        """Build a schema for a foreign key's related model that only
        identifies the object, with its primary key and ``meta.type``.

        For a page, this is the same as a page's ``meta.parent``, with the
        page's ID, title, specific type, and URLs.
        """
        from wagtail.api.v3.schemas.pages import SimpleBasePageSchema
        from wagtail.models import AbstractPage

        if issubclass(model, AbstractPage):
            return SimpleBasePageSchema

        if model not in self._foreign_key_reference_schema_cache:
            name = f"{model._meta.object_name}ForeignKeyReferenceSchema"
            schema = create_schema(
                model,
                name=f"{name}Base",
                fields=self._get_pk_names(model),
                base_class=BaseSchema,
            )
            self._foreign_key_reference_schema_cache[model] = self.extend_schema(
                schema,
                name,
                {"meta": (self._get_foreign_key_meta_schema(model), ..., None)},
            )
        return self._foreign_key_reference_schema_cache[model]

    def _get_foreign_key_meta_schema(self, model: type[Model]) -> type[Schema]:
        if model not in self._foreign_key_meta_schema_cache:
            self._foreign_key_meta_schema_cache[model] = self._narrowed_meta_schema(
                BaseSchema.model_fields["meta"].annotation,
                model,
                name=f"{model._meta.object_name}ForeignKeyMetaSchema",
            )
        return self._foreign_key_meta_schema_cache[model]

    def extend_schema(
        self,
        base: type[Schema],
        name: str,
        fields: dict[str, FieldSchema],
    ) -> type[Schema]:
        """Subclass ``base``, adding ``fields`` (and any ``resolve_*`` methods).

        Built via the base's own metaclass rather than ``pydantic.create_model``,
        since ninja only picks up ``resolve_<field>`` methods by scanning a
        class's namespace as the class is created.
        """
        namespace: dict[str, Any] = {"__annotations__": {}}
        for field_name, (annotation, default, resolver) in fields.items():
            namespace["__annotations__"][field_name] = annotation
            namespace[field_name] = default
            if resolver is not None:
                namespace[f"resolve_{field_name}"] = resolver

        metaclass = type(base)
        schema_class = metaclass(name, (base,), namespace)
        return cast(type[Schema], schema_class)

    def build_schema(
        self,
        model: type[Model],
        *,
        name: str,
        base_class: type[Schema],
        nested: bool,
        follow_reverse_related: bool = True,
    ) -> type[Schema]:
        """Build a schema for ``model``'s ``api_fields``, on top of ``base_class``.

        Each entry in ``api_fields`` is classified as:

        - a custom-serializer field: typed from the serializer's
          ``to_representation`` return annotation (or ``Any`` if missing or
          unresolvable), made nullable, and resolved via the serializer
          itself - see ``_custom_serializer_schema``.
        - a ``StreamField``: resolved via
          ``StreamValue.stream_block.get_api_representation``, matching how
          API v2 serializes StreamField values, and typed as ``list[Any]``
          with its blocks' shape documented in the JSON schema - see
          :class:`~wagtail.api.v3.schemas.generators.blocks.StreamFieldJsonSchema`.
        - any other concrete/forward Django field: typed via ``create_schema``.
        - a reverse relation (e.g. an ``InlinePanel``'s target): resolved as
          ``list[NestedSchema]``. Within a ``nested`` schema, only child
          relations (``ParentalKey``, e.g. an ``InlinePanel`` inside an
          ``InlinePanel`` child) are followed, and only to a model that isn't
          already being built further up - otherwise omitted - so recursion
          stops rather than cycling through the same models. If
          ``follow_reverse_related`` is False, reverse relations are always
          omitted. A child relation's ``ParentalKey`` back to the model it's
          nested in is typed with that model's reference schema, see
          ``get_foreign_key_reference_schema``.
        - anything else (a plain Python property, typically): typed as ``Any``
          and read straight off the instance.
        """
        self._models_being_built.append(model)
        try:
            return self._build_schema(
                model,
                name=name,
                base_class=base_class,
                nested=nested,
                follow_reverse_related=follow_reverse_related,
            )
        finally:
            self._models_being_built.pop()

    def _is_parent_link(
        self, field: Field | ForeignObjectRel
    ) -> TypeGuard[ParentalKey]:
        """Whether ``field`` is the ``ParentalKey`` of a child relation that
        links the model being built back to the model it's nested in (e.g. an
        ``InlinePanel`` item's ``page``).

        That object is the one being serialized, so repeating it in full for
        every item would be redundant.
        """
        if len(self._models_being_built) < 2 or not isinstance(field, ParentalKey):
            return False
        parent_model = self._models_being_built[-2]
        return field.remote_field in get_all_child_relations(parent_model)

    def _build_schema(
        self,
        model: type[Model],
        *,
        name: str,
        base_class: type[Schema],
        nested: bool,
        follow_reverse_related: bool,
    ) -> type[Schema]:
        real_names = [
            field.name
            for field in model._meta.pk_fields
            if not (field.remote_field and field.remote_field.parent_link)
        ]
        extra_fields: dict[str, FieldSchema] = {}

        meta_field = base_class.model_fields.get("meta")
        if meta_field is not None:
            extra_fields["meta"] = (
                self._narrowed_meta_schema(
                    meta_field.annotation,
                    model,
                    name=f"{model._meta.object_name}MetaSchema",
                ),
                ...,
                None,
            )

        for field in APIField.get_fields_for_model(model):
            # APIField with a custom serializer.
            if field.serializer is not None:
                if isinstance(field.serializer, FieldSerializer):
                    extra_fields[field.name] = self._field_serializer_schema(field)
                else:
                    # DRF serializer field - handle via the compat shim.
                    extra_fields[field.name] = self._custom_serializer_schema(field)
                continue

            try:
                model_field = get_model_field(model, field.name)
            except FieldDoesNotExist:
                # Not a real Django field, so treat it as a plain Python property.
                extra_fields[field.name] = (Any, None, None)
            else:
                if isinstance(model_field, ForeignObjectRel) and (
                    not follow_reverse_related
                    or (
                        nested
                        and (
                            model_field not in get_all_child_relations(model)
                            or model_field.related_model in self._models_being_built
                        )
                    )
                ):
                    continue

                if (
                    nested
                    and follow_reverse_related
                    and self._is_parent_link(model_field)
                ):
                    reference_schema = self.get_foreign_key_reference_schema(
                        model_field.related_model
                    )
                    if model_field.null:
                        reference_schema = reference_schema | None
                    extra_fields[field.name] = (reference_schema, None, None)
                    continue

                # See if field's class or its parents have a registered schema
                # generator. Use it if so, otherwise treat it as a real Django field.
                model_field = cast(Field, model_field)
                for cls in model_field.__class__.mro():
                    cls = cast(type[Field], cls)
                    if cls in self.field_schemas:
                        schema = self.field_schemas[cls](self, model_field)
                        extra_fields[field.name] = schema
                        break
                else:
                    real_names.append(field.name)

        schema = base_class
        if real_names:
            try:
                schema = create_schema(
                    model,
                    name=f"{name}Base" if extra_fields else name,
                    fields=real_names,
                    base_class=base_class,
                )
            except ConfigError:
                # A field type create_schema can't map to a Python type (rare -
                # only concrete, non-relation, non-StreamField types can hit
                # this). Fall back to treating those fields as opaque, rather
                # than failing schema generation for the whole model.
                for field_name in real_names:
                    extra_fields.setdefault(field_name, (Any, None, None))

        if extra_fields:
            schema = self.extend_schema(schema, name, extra_fields)

        return schema

    def generate_schema(
        self,
        model: type[Model],
        base_class: type[Schema],
    ) -> type[Schema]:
        """
        Build a read schema for the concrete model ``model`` using the specified
        ``base_class``.
        """
        return self.build_schema(
            model,
            name=f"{model._meta.object_name}Schema",
            base_class=base_class,
            nested=False,
        )

    @staticmethod
    def _narrowed_meta_schema(
        base_meta_schema: type[Schema], model: type[Model], *, name: str
    ) -> type[Schema]:
        """Narrow ``base_meta_schema``'s ``type`` to a ``Literal`` for ``model``.

        A shared base class's ``meta`` field (``BaseMetaSchema``/
        ``PageMetaSchema``) types ``type`` generically (``str | None``), since
        one class is reused across every model's generated schema. This
        builds a per-model subclass that only accepts its own content type
        label instead, so the OpenAPI schema (and validation) reflects the
        actual, constant value rather than an open-ended string. Used as
        ``build_schema``'s own ``meta`` field override, so the narrowing is
        baked into the same dynamic class as any other extra field rather
        than needing a second subclassing pass over the finished schema.

        ``name`` is caller-supplied since the same model may be narrowed from
        different base meta schemas, which must not share a name.
        """
        return cast(
            type[Schema],
            type(base_meta_schema)(
                name,
                (base_meta_schema,),
                {"__annotations__": {"type": Literal[model._meta.label]}},  # ty: ignore[invalid-type-form]
            ),
        )


def foreign_key_schema(generator: SchemaGenerator, field: Field) -> FieldSchema:
    field = cast(RelatedField, field)
    schema = generator.get_foreign_key_schema(field.related_model)
    if field.many_to_many or field.one_to_many:
        schema = list[schema]  # ty: ignore[invalid-type-form]
    elif field.null:
        schema = schema | None
    return cast(type, schema), None, None


def reverse_related_schema(generator: SchemaGenerator, field: Field) -> FieldSchema:
    field: ForeignObjectRel = cast(ForeignObjectRel, field)
    schema = generator.get_reverse_related_schema(field.related_model)
    if field.multiple:
        schema = list[schema]  # ty:ignore[invalid-type-form]
    else:
        # reverse OneToOneField
        schema = (schema | None) if field.null else schema
    return cast(type, schema), [], None


def streamfield_schema(generator: SchemaGenerator, field: Field) -> FieldSchema:
    field_name = field.name

    def resolve(obj: Model, context: dict) -> Any:
        value = getattr(obj, field_name)
        return value.stream_block.get_api_representation(value, context)

    annotation = Annotated[
        list[Any], StreamFieldJsonSchema(block_schema_builder, cast(StreamField, field))
    ]
    return cast(type, annotation), [], staticmethod(resolve)


def tags_schema(generator: SchemaGenerator, field: Field) -> FieldSchema:
    field_name = field.name

    def resolve(obj: Model) -> Any:
        return getattr(obj, field_name).values_list("name", flat=True)

    return list[str], [], staticmethod(resolve)


def rich_text_schema(generator: SchemaGenerator, field: Field) -> FieldSchema:
    field = cast(RichTextField, field)
    field_name = field.name
    resolved_features = (
        field.features
        if field.features is not None
        else feature_registry.get_default_features()
    )

    def resolve(obj: Model, context: dict) -> str | None:
        value = getattr(obj, field_name)
        if value is None:
            return None
        request = context.get("request")
        rich_text_format = APIRichText.resolve_format(
            request.GET.get("rich_text_format") if request else None
        )
        return APIRichText.serialize(
            value, format=rich_text_format, features=field.features
        )

    default = FieldInfo(
        default=None,
        json_schema_extra={"x-rich-text-features": resolved_features},
    )
    return cast(type, str | None), default, staticmethod(resolve)


block_schema_builder = BlockSchemaBuilder(for_input=False)
register_default_block_schemas(block_schema_builder)

read_generator = SchemaGenerator()
read_generator.register_field_schema(RelatedField, foreign_key_schema)
read_generator.register_field_schema(ForeignObjectRel, reverse_related_schema)
read_generator.register_field_schema(StreamField, streamfield_schema)
read_generator.register_field_schema(TaggableManager, tags_schema)
read_generator.register_field_schema(RichTextField, rich_text_schema)
