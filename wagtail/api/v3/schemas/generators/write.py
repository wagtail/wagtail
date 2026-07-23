from collections.abc import Iterable
from typing import Any, Callable, Literal, cast

from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.db.models import Field, ForeignKey, Model
from django.db.models.fields.reverse_related import ForeignObjectRel
from modelcluster.models import get_all_child_relations
from ninja import Schema
from ninja.orm import create_schema
from ninja.orm.fields import get_schema_field
from pydantic.fields import FieldInfo
from taggit.managers import TaggableManager

from wagtail.api import APIField
from wagtail.fields import StreamField

#: (annotation, default), or None if the field has no defined writable shape.
InputFieldSchema = tuple[Any, Any] | None
InputFieldSchemaFunc = Callable[["InputSchemaGenerator", Field], InputFieldSchema]


class InputSchemaGenerator:
    """
    Auto-generates Ninja input (create/patch) schemas for concrete models.

    Mirrors :class:`wagtail.api.v3.schemas.generators.read.SchemaGenerator`,
    but describes what the API accepts for writing rather than what it
    returns for reading. A field is included if it's one of the model's own
    ``fields`` (passed to ``generate_schema``) or listed in the model's
    ``api_fields``, excluding legacy API v2 custom serializer fields (those
    are read-only computed values, not real fields).

    :param force_optional: when ``True``, every "extra" field this
        generator adds via ``api_fields`` (as opposed to a ``fields=`` name
        passed to ``generate_schema``, which has its own ``required_fields``
        control) is always optional, regardless of whatever requiredness its
        underlying Django field would otherwise imply. Used for the patch
        generator: a partial update must accept any writable field being
        left out, even one that's non-blank on the model and so would
        otherwise be required.
    """

    def __init__(self, *, force_optional: bool = False):
        self.force_optional = force_optional

        #: Map of Django field classes to functions that return an
        #: ``(annotation, default)`` tuple for that field type, or ``None``
        #: if the field type has no defined writable shape via this API.
        #: An instance attribute, not shared class state: a second
        #: generator instance (e.g. the patch generator) must be able to
        #: cache/compute its own schemas independently.
        self.field_schemas: dict[
            type[Field | ForeignObjectRel], InputFieldSchemaFunc
        ] = {}

        #: Input schemas already built for a child relation's related model
        #: (the "one" side of a ParentalKey, e.g. a carousel item), keyed by
        #: that model. Also an instance attribute for the same reason: the
        #: patch generator's child schemas need their extra fields optional
        #: too, which the create generator's cached entry wouldn't be.
        self._child_relation_schema_cache: dict[type[Model], type[Schema]] = {}

    def register_field_schema(
        self,
        field_class: type[Field | ForeignObjectRel],
        func: InputFieldSchemaFunc,
    ) -> None:
        """Register a function to generate an input schema field for ``field_class``."""
        self.field_schemas[field_class] = func

    def get_child_relation_schema(self, model: type[Model]) -> type[Schema]:
        """Build an input schema for a child relation's related model.

        Includes only the related model's own writable ``api_fields``, plus
        any that need special handling (e.g. a StreamField nested inside an
        InlinePanel-managed model).
        """
        if model not in self._child_relation_schema_cache:
            writable_field_names = {
                field.name for field in APIField.get_writable_fields_for_model(model)
            }
            if not writable_field_names:
                raise ImproperlyConfigured(
                    f"{model._meta.label} is used as a writable child relation, but "
                    f"none of its own api_fields are writable. Mark at least one "
                    f"field as APIField(name, writable=True) on {model.__name__}."
                )

            field_names = [
                field.name
                for field in model._meta.get_fields()
                if field.name in writable_field_names
                # Real fields, not e.g. reverse-relations
                and getattr(field, "concrete", False)
                # Editable fields, not e.g. pk, sort_order
                and field.editable
                # Has no registered field schema function
                and not any(cls in self.field_schemas for cls in field.__class__.mro())
            ]

            name = f"{model._meta.object_name}InputSchema"
            if field_names:
                schema = create_schema(
                    model,
                    name=f"{name}Base",
                    fields=field_names,
                    base_class=Schema,
                )
            else:
                # ninja's create_schema() treats an empty `fields` list as
                # "no restriction" and includes every model field, so build
                # an empty base schema directly instead - every writable
                # field here is a relation/StreamField/etc handled below via
                # _build_extra_fields.
                schema = type(Schema)(f"{name}Base", (Schema,), {})

            extra_fields = self._build_extra_fields(model)
            namespace: dict[str, Any] = {
                # Optional, and not itself a writable APIField: on an
                # update, matching this against an existing child row's own
                # pk (see build_form_data's existing_instance handling)
                # lets the request edit that row in place instead of
                # deleting and recreating it. Ignored on create, where
                # there's nothing existing to match against.
                "__annotations__": {"id": int | None},
                "id": None,
            }
            for field_name, (annotation, default) in extra_fields.items():
                namespace["__annotations__"][field_name] = annotation
                namespace[field_name] = default
            schema = cast(type[Schema], type(schema)(name, (schema,), namespace))

            self._child_relation_schema_cache[model] = schema
        return self._child_relation_schema_cache[model]

    def _build_extra_fields(self, model: type[Model]) -> dict[str, tuple[Any, Any]]:
        """Return ``{field_name: (annotation, default)}`` for ``api_fields`` extras.

        Custom-serializer (legacy API v2) fields are skipped since those are
        read-only computed values with no defined writable shape.
        """
        extra_fields: dict[str, tuple[Any, Any]] = {}

        for field in APIField.get_writable_fields_for_model(model):
            if field.serializer is not None:
                continue

            try:
                model_field = model._meta.get_field(field.name)
            except FieldDoesNotExist:
                # Not a real Django field (e.g. a plain Python property) -
                # there's no defined writable shape for it, so skip it.
                continue

            # See if field's class or its parents have a registered schema
            # generator. Use it if so, otherwise treat it as a real Django
            # field (a ForeignKey, or a concrete CharField/TextField/etc).
            model_field = cast(Field, model_field)
            for cls in model_field.__class__.mro():
                cls = cast(type[Field], cls)
                if cls in self.field_schemas:
                    field_schema = self.field_schemas[cls](self, model_field)
                    if field_schema is not None:
                        extra_fields[field.name] = field_schema
                    break
            else:
                extra_fields[field.name] = get_schema_field(model_field)

            if self.force_optional and field.name in extra_fields:
                extra_fields[field.name] = self._make_optional(extra_fields[field.name])

        return extra_fields

    @staticmethod
    def _narrowed_meta_schema(
        base_meta_schema: type[Schema], model: type[Model], name_suffix: str
    ) -> type[Schema]:
        """Narrow ``base_meta_schema``'s ``type`` to a ``Literal`` for ``model``.

        A shared base class's ``meta`` field types ``type`` generically
        (e.g. ``str``), since one class is reused across every model's
        generated schema. This builds a per-model subclass that only accepts
        its own content type label instead, so the OpenAPI schema (and
        validation) reflects the actual, constant value rather than an
        open-ended string.

        ``name_suffix`` (e.g. ``"Input"`` or ``"Patch"``) keeps this
        distinct from another schema generated for the same model under a
        different ``base_class`` (e.g. create vs. update): ninja/pydantic
        key OpenAPI components by class ``__name__``, so two differently
        shaped schemas sharing a name would collide and one would silently
        shadow the other in the generated docs.
        """
        return cast(
            type[Schema],
            type(base_meta_schema)(
                f"{model._meta.object_name}{name_suffix}MetaSchema",
                (base_meta_schema,),
                {"__annotations__": {"type": Literal[model._meta.label]}},  # ty: ignore[invalid-type-form]
            ),
        )

    @staticmethod
    def _make_optional(field_schema: tuple[Any, Any]) -> tuple[Any, Any]:
        """Force an ``(annotation, default)`` pair to be optional.

        Most extra fields (StreamField, tags, child relations) already default
        to an empty value from their own dedicated ``field_schemas`` function,
        so they're always optional regardless of this. This only has real work
        to do for a field whose ``default`` is a ``FieldInfo`` derived straight
        from the Django field's own requiredness (``get_schema_field``, used by
        the plain-field fallback and ``foreign_key_schema``) - e.g. a writable
        APIField on a non-blank/non-null model field, which would otherwise be
        required even for a partial (patch) update that simply doesn't mention
        it.
        """
        annotation, default = field_schema
        if isinstance(default, FieldInfo) and default.is_required():
            default = FieldInfo(
                default=None,
                alias=default.alias,
                title=default.title,
                description=default.description,
            )
            annotation = annotation | None
        return annotation, default

    def generate_schema(
        self,
        model: type[Model],
        *,
        base_class: type[Schema],
        fields: Iterable[str] = (),
        required_fields: Iterable[str] = (),
        name_suffix: str = "Input",
    ) -> type[Schema]:
        """Build an input (create) schema for the concrete model ``model``.

        ``fields`` names the model's own fields to always include (besides
        whatever ``api_fields`` adds) - e.g. a page's ``title``/``slug``.
        ``required_fields`` marks which of those ``fields`` must be provided;
        the rest are optional.

        If ``base_class`` declares a ``meta`` field (e.g. a schema holding
        control fields like ``parent_id`` and a ``type`` discriminator, kept
        under ``meta`` rather than at the top level so a model field sharing
        one of those names can't be silently shadowed by them - see
        :class:`wagtail.api.v3.schemas.pages.PageCreateBaseSchema`), it's
        narrowed to a ``Literal`` matching this specific model, the same way
        the read-side generator narrows ``meta.type`` for read schemas.

        ``name_suffix`` distinguishes this call's generated class name (and
        its narrowed meta schema's) from another call for the same model
        under a different ``base_class`` - see ``_narrowed_meta_schema``.
        Callers generating more than one schema shape per model (e.g. both
        a create and an update/patch schema) must pass distinct values.
        """
        field_names = [
            name
            for name in fields
            if name in {f.name for f in model._meta.get_fields()}
        ]
        name = f"{model._meta.object_name}{name_suffix}Schema"
        schema = create_schema(
            model,
            name=f"{name}Base",
            fields=field_names,
            optional_fields=[n for n in field_names if n not in required_fields],
            base_class=base_class,
        )

        extra_fields = self._build_extra_fields(model)
        namespace: dict[str, Any] = {"__annotations__": {}}

        meta_field = base_class.model_fields.get("meta")
        if meta_field is not None:
            namespace["__annotations__"]["meta"] = self._narrowed_meta_schema(
                meta_field.annotation, model, name_suffix
            )

        for field_name, (annotation, default) in extra_fields.items():
            namespace["__annotations__"][field_name] = annotation
            namespace[field_name] = default

        metaclass = type(schema)
        return cast(type[Schema], metaclass(name, (schema,), namespace))


def streamfield_schema(
    generator: InputSchemaGenerator, field: Field
) -> InputFieldSchema:
    return list[Any], []


def tags_schema(generator: InputSchemaGenerator, field: Field) -> InputFieldSchema:
    return list[str], []


def child_relation_schema(
    generator: InputSchemaGenerator, field: Field
) -> InputFieldSchema:
    field: ForeignObjectRel = cast(ForeignObjectRel, field)
    if field not in get_all_child_relations(field.model):
        # A reverse relation with no ParentalKey (i.e. not an InlinePanel
        # child) has no defined writable shape via this API, so it's
        # skipped rather than guessed at.
        return None

    child_schema = generator.get_child_relation_schema(field.related_model)
    return list[child_schema], []  # ty: ignore[invalid-type-form]


def foreign_key_schema(
    generator: InputSchemaGenerator, field: Field
) -> InputFieldSchema:
    field = cast(ForeignKey, field)
    return get_schema_field(field)


create_generator = InputSchemaGenerator()
create_generator.register_field_schema(StreamField, streamfield_schema)
create_generator.register_field_schema(TaggableManager, tags_schema)
create_generator.register_field_schema(ForeignObjectRel, child_relation_schema)
create_generator.register_field_schema(ForeignKey, foreign_key_schema)

#: Same field-schema handling as ``generator``, but every extra field it
#: adds is optional regardless of the underlying Django field's own
#: requiredness - for building patch (partial update) schemas, where a
#: field the request doesn't mention must be left off rather than
#: rejected as missing. A separate instance, not a shared one, so its
#: cached child-relation schemas (which also need to be all-optional) and
#: registered field-schema functions don't collide with ``generator``'s.
patch_generator = InputSchemaGenerator(force_optional=True)
patch_generator.register_field_schema(StreamField, streamfield_schema)
patch_generator.register_field_schema(TaggableManager, tags_schema)
patch_generator.register_field_schema(ForeignObjectRel, child_relation_schema)
patch_generator.register_field_schema(ForeignKey, foreign_key_schema)
