from typing import Any

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db.models import Field, ForeignKey, Model
from modelcluster.fields import ParentalKey
from modelcluster.models import get_all_child_relations

from wagtail.fields import StreamField
from wagtail.models import Page


def _coerce_field_values(model: type[Model], values: dict[str, Any]) -> dict[str, Any]:
    """Turn a ``None`` for a non-nullable, blankable field into ``""``.

    The generated input schema (via ninja's ``create_schema``) defaults an
    optional ``blank=True, null=False`` field (e.g. ``seo_title``) to
    ``None``, since that's ninja's convention for "not required" - but the
    database column itself is ``NOT NULL``, so an omitted value needs to
    become the field's own empty value instead.
    """
    coerced = dict(values)
    for name, value in values.items():
        if value is not None:
            continue
        try:
            field = model._meta.get_field(name)
        except FieldDoesNotExist:
            continue
        if isinstance(field, Field) and not field.null:
            coerced[name] = field.get_default() if field.has_default() else ""
    return coerced


def _build_child_instances(related_model: type[Model], items: list[dict]) -> list[Any]:
    """Build (unsaved) child-relation instances from a list of plain dicts.

    ``items`` comes from the parent's ``data.dict()`` call, which (like
    pydantic's ``model_dump()``) recurses nested schema instances into plain
    dicts too - so each ``item`` here is already a dict, not a schema object.
    """
    exclude = {"sort_order"}
    for field in related_model._meta.get_fields():
        if isinstance(field, ParentalKey):
            exclude.add(field.name)

    instances = []
    messages = []
    for i, item in enumerate(items):
        instance = related_model(**_coerce_field_values(related_model, item))
        sort_order_field = getattr(related_model, "sort_order_field", None)
        if sort_order_field:
            setattr(instance, sort_order_field, i)
        try:
            instance.full_clean(exclude=exclude, validate_unique=False)
        except ValidationError as e:
            for field_name, field_messages in e.message_dict.items():
                for message in field_messages:
                    messages.append(f"Item {i}, field {field_name!r}: {message}")
        instances.append(instance)

    if messages:
        raise ValidationError(messages)

    return instances


def build_page_instance(
    model: type[Page],
    parent: Page,
    data: Any,
    user: AbstractBaseUser | AnonymousUser,
) -> Page:
    """Build an unsaved ``model`` instance from a validated create-input schema.

    Assigns simple fields directly, builds a validated ``StreamValue`` for any
    StreamField (via the block's own ``clean()``), and builds validated child
    instances for any InlinePanel-backed child relation - all without going
    through :class:`~wagtail.admin.forms.pages.WagtailAdminPageForm`, whose
    ``ClusterForm``/formset machinery expects flattened multipart form-post
    data rather than a JSON body.

    Raises :class:`~django.core.exceptions.ValidationError` (keyed by field
    name) if a StreamField's content or a child relation's fields don't
    validate. Field presence/type is already guaranteed by the pydantic input
    schema; this only covers validation the schema itself can't express.
    """
    page = model(owner=user, locale=parent.locale)
    errors: dict[str, Any] = {}

    child_relations = {field.name: field for field in get_all_child_relations(model)}
    payload = data.dict(exclude={"parent_id", "type"})
    scalar_payload = {
        name: value for name, value in payload.items() if name not in child_relations
    }
    payload.update(_coerce_field_values(model, scalar_payload))

    for name, value in payload.items():
        try:
            field = model._meta.get_field(name)
        except FieldDoesNotExist:
            field = None

        if isinstance(field, StreamField):
            try:
                cleaned = field.stream_block.clean(field.stream_block.to_python(value))
            except ValidationError as e:
                errors[name] = e
            else:
                setattr(page, name, cleaned)
        elif name in child_relations:
            related_model = child_relations[name].related_model
            try:
                setattr(page, name, _build_child_instances(related_model, value))
            except ValidationError as e:
                errors[name] = e
        elif isinstance(field, ForeignKey):
            setattr(page, f"{name}_id", value)
        else:
            setattr(page, name, value)

    if errors:
        raise ValidationError(errors)

    return page
