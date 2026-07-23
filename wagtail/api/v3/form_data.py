from collections.abc import Iterable
from typing import Any, cast

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.db.models import Model
from django.forms import BaseForm, Field
from django.utils.datastructures import MultiValueDict
from ninja.schema import BaseModel

from wagtail.admin.forms.models import WagtailAdminModelForm
from wagtail.admin.panels import Panel, get_edit_handler, get_form_for_model
from wagtail.api.v3.registry import ContentTypeRegistration, registry
from wagtail.api.v3.schemas import create_generator
from wagtail.blocks.base import BlockField
from wagtail.blocks.list_block import ListBlock
from wagtail.blocks.stream_block import BaseStreamBlock
from wagtail.blocks.struct_block import BaseStructBlock
from wagtail.models import Page


def filter_form_options(
    model: type[Model],
    form_options: dict[str, Any],
    writable_fields: list[str],
) -> dict[str, Any]:
    """Restrict ``form_options`` (from a ``Panel``/``InlinePanel``'s
    ``get_form_options()``) to writable APIFields: ``fields`` is narrowed to
    ``writable_fields``, minus any name that's actually a formset relation,
    and each formset in ``formsets`` is recursively narrowed the same way
    against its own child model's writable APIFields - so a child model that
    itself declares an InlinePanel is handled too.

    Reuses ``create_generator``'s cached child relation schema (built while
    generating the top-level ``create_schema``) rather than re-deriving a
    child model's writable fields from its raw ``api_fields``.
    """
    formsets = form_options.get("formsets") or {}
    fields = [name for name in writable_fields if name not in formsets]

    filtered_formsets = {}
    for name, formset_options in formsets.items():
        if name not in writable_fields:
            continue
        child_model = cast(type[Model], model._meta.get_field(name).related_model)
        child_schema = create_generator.get_child_relation_schema(child_model)
        filtered_formsets[name] = {
            **formset_options,
            **filter_form_options(
                child_model, formset_options, child_schema.model_fields.keys()
            ),
        }

    return {**form_options, "fields": fields, "formsets": filtered_formsets}


def get_api_form_class(model: type[Model], field_names: Iterable[str] | None = None):
    """
    Creates a form class for the given model, using the model's edit handler to
    preserve configuration such as required_on_save, permissions, etc., but only
    including fields that are writable APIFields.

    The form class is based on the model's ``api_base_form_class`` (if defined),
    or the edit handler's ``base_form_class``, or the model's ``base_form_class``,
    or ``WagtailAdminModelForm`` as a last resort.

    ``field_names``, if given, further restricts the form to that subset of
    writable APIFields - e.g. only the fields present in a partial update
    payload, so that a field the request didn't mention is left off the form
    entirely rather than being cleared to empty (which is what would happen
    if it were included but unbound).
    """
    try:
        # Page.get_edit_handler is monkey-patched onto the class by
        # wagtail.admin.panels.page_utils, so it isn't visible statically.
        edit_handler = cast(Panel, model.get_edit_handler())  # ty: ignore[unresolved-attribute]
    except AttributeError:
        edit_handler = get_edit_handler(model)

    # The following is similar to Panel.get_form_class(),
    form_options = edit_handler.get_form_options()
    base_form_class = (
        getattr(model, "api_base_form_class", None)
        or edit_handler.base_form_class
        or getattr(model, "base_form_class", None)
        or WagtailAdminModelForm
    )

    # but we narrow fields/formsets to only writable APIFields, adding back
    # any writable APIField that isn't exposed by a panel.
    registered_schemas = cast(ContentTypeRegistration, registry.get(model._meta.label))
    create_schema = cast(type[BaseModel], registered_schemas.create_schema)
    writable_fields = [
        name for name in create_schema.model_fields.keys() if name != "meta"
    ]
    if field_names is not None:
        field_names = set(field_names)
        writable_fields = [name for name in writable_fields if name in field_names]
    form_options.update(filter_form_options(model, form_options, writable_fields))

    return get_form_for_model(
        model,
        form_class=base_form_class,
        **form_options,
    )


def build_page_form(
    model: type[Page],
    parent: Page,
    data: Any,
    user: AbstractBaseUser | AnonymousUser,
):
    """Build a bound page form from a validated create-input schema.

    Uses the page model's own admin form (``base_form_class``, wired up
    through its edit handler's panels - the same form the admin "create page"
    view binds), so any custom ``clean()``/``clean_<field>()`` logic a
    project defines on that form or its formsets runs for real, rather than
    being bypassed.
    """
    form_class = get_api_form_class(model)
    payload = data.dict(exclude={"meta"})

    page = model(owner=user, locale=parent.locale)

    # HACK: In the admin views, slug is auto-generated client-side, and the page
    # form makes the slug field required. The page model also has a mechanism to
    # auto-generate a slug from the title if it's missing, but only if the page
    # is already in the tree (i.e. has a path) so it can check for duplicates
    # under the same parent. We can reuse that mechanism here by setting a
    # temporary cached parent object, which the model uses to determine the
    # parent for slug de-duplication, and clearing it again after the slug is
    # generated. Once the slug is obtained, we put it in the payload so the form
    # field passes validation.
    page._cached_parent_obj = parent
    if not payload.get("slug") and payload.get("title"):
        page.title = payload["title"]
        page.minimal_clean()
        payload["slug"] = page.slug
        page._cached_parent_obj = None

    form_data = build_form_data(form_class, payload)

    return form_class(data=form_data, instance=page, parent_page=parent, for_user=user)


def build_page_update_form(
    page: Page,
    data: Any,
    user: AbstractBaseUser | AnonymousUser,
):
    """Build a bound page form from a validated, partial update-input schema.

    Like :func:`build_page_form`, but binds the given, already-saved ``page``
    instead of constructing a new one - there's no parent to attach to or
    slug to auto-generate, since the page already exists in the tree.

    This is a partial (PATCH-style) update: every field in the update schema
    is optional, and only the fields actually present in the request body
    (``exclude_unset``) are put on the form at all. A field the request
    didn't mention would otherwise be bound as empty/default by the
    underlying Django form - wiping it - rather than left as-is, so the form
    class itself is narrowed to just the supplied fields (via
    ``get_api_form_class``'s ``field_names``), the same way an admin partial
    edit would only touch the fields its HTML form actually submits. This
    also covers an InlinePanel-backed child relation the request didn't
    mention: since it's never declared as a formset on the narrowed form,
    ``ClusterForm.save()`` never touches its ``_cluster_related_objects``
    entry, so ``ClusterableModel.save()``'s own unconditional
    ``.commit()`` call on that relation finds no staged changes and leaves
    its existing rows alone.

    A relation the request did mention has its whole set replaced, not
    appended to - see ``build_form_data``'s ``instance`` param.
    """
    model = type(page)
    payload = data.dict(exclude={"meta"}, exclude_unset=True)
    form_class = get_api_form_class(model, field_names=payload.keys())
    form_data = build_form_data(form_class, payload, instance=page)

    return form_class(
        data=form_data,
        instance=page,
        parent_page=page.get_parent(),
        for_user=user,
    )


def flatten_block_value(block, value: Any, prefix: str, data: MultiValueDict) -> None:
    """Write ``value`` (in its StreamField API JSON shape) into ``data``.

    Mirrors each block type's own ``value_from_datadict`` key scheme in
    reverse, so ``block.value_from_datadict(data, {}, prefix)`` reconstructs
    ``value`` when the resulting form is bound. This lets a StreamField's
    real form field (and therefore any custom ``Block.clean()`` logic) run
    against JSON input, both at the top level and inside InlinePanel
    children.
    """
    if isinstance(block, BaseStreamBlock):
        items = value or []
        data[f"{prefix}-count"] = str(len(items))
        for i, item in enumerate(items):
            data[f"{prefix}-{i}-deleted"] = ""
            data[f"{prefix}-{i}-order"] = str(i)
            data[f"{prefix}-{i}-type"] = item["type"]
            if item.get("id") is not None:
                data[f"{prefix}-{i}-id"] = item["id"]
            try:
                child_block = block.child_blocks[item["type"]]
            except KeyError:
                raise ValidationError(
                    f"{prefix}: unrecognised block type {item['type']!r}"
                ) from None
            flatten_block_value(child_block, item["value"], f"{prefix}-{i}-value", data)
    elif isinstance(block, ListBlock):
        items = value or []
        data[f"{prefix}-count"] = str(len(items))
        for i, item in enumerate(items):
            data[f"{prefix}-{i}-deleted"] = ""
            data[f"{prefix}-{i}-order"] = str(i)
            flatten_block_value(block.child_block, item, f"{prefix}-{i}-value", data)
    elif isinstance(block, BaseStructBlock):
        value = value or {}
        for name, child_block in block.child_blocks.items():
            flatten_block_value(child_block, value.get(name), f"{prefix}-{name}", data)
    else:
        # A leaf field block (CharBlock, BooleanBlock, ChooserBlock, ...):
        # its own form field's widget reads a single key via plain `.get()`,
        # confirmed for every built-in Wagtail/Django block widget.
        data[prefix] = value


def _set_field_value(field: Field, name: str, value: Any, data: MultiValueDict) -> None:
    """Write ``value`` for a single (non-formset) form field into ``data``.

    Most widgets read a single key via plain ``.get()`` (confirmed for every
    built-in Wagtail/Django widget); the exceptions handled here are a
    ``BlockField`` (StreamField), whose widget needs its own flattened key
    scheme; a multi-valued field (e.g. ``ModelMultipleChoiceField`` for a
    ``ParentalManyToManyField``), whose widget calls ``getlist`` - so it's
    set via ``setlist`` rather than plain item assignment, which would wrap
    the whole list as a single value instead of storing it as the value list
    itself; and a rich text field's widget (e.g. Draftail), whose
    ``value_from_datadict`` always runs the raw value through
    ``self.converter.to_database_format()`` - assuming it's already in the
    editor's own submission format, not our plain database-format HTML
    string. ``format_value()`` is that converter's documented inverse
    (``from_database_format``), so round-tripping our HTML through it first,
    then letting ``value_from_datadict`` convert it back, works for whichever
    rich text editor a project has configured without needing to
    special-case Draftail specifically.
    """
    if isinstance(field, BlockField):
        flatten_block_value(field.block, value, name, data)
    elif getattr(field.widget, "allow_multiple_selected", False):
        data.setlist(name, list(value) if value else [])
    elif hasattr(field.widget, "converter"):
        # A rich text editor widget (Draftail's `to_database_format`/
        # `from_database_format` contract - core ships only Draftail, but
        # third-party editors may implement the same converter pattern).
        data[name] = field.widget.format_value(value)
    else:
        data[name] = value


def build_form_data(
    form_class: type[BaseForm],
    payload: dict[str, Any],
    instance: Model | None = None,
) -> MultiValueDict:
    """Build a ``MultiValueDict`` that binds ``form_class`` (and its child
    formsets, if it's a ``ClusterForm``) as if the equivalent HTML form had
    been submitted.

    ``payload`` supplies values for the top-level form's own fields, keyed by
    field name, and, for each InlinePanel-backed relation name declared on
    the form, a list of dicts (one per child, keyed by the child form's own
    field names) - all taken directly from the parsed JSON request body.

    Only fields the form actually declares are considered: a model's
    ``api_fields`` may list more than a panel exposes, and an InlinePanel
    restricts its child form to its own panel fields, so surplus JSON keys
    are simply not looked up here (see ``InlinePanel.get_form_options``).

    ``instance``, on an update, is the page (or other model) being
    edited. This replaces the relation's whole set rather than trying to
    diff it item by item: every one of ``instance``'s current rows
    for that relation becomes an initial form, and each submitted item
    either binds to the existing row whose pk matches its own ``id`` (an
    edit in place) or, lacking a matching ``id``, becomes a new
    (non-initial) form. Any existing row no *submitted* item's ``id``
    refers to is marked for deletion. Without this, the submitted items
    would be added *alongside* the existing rows instead of replacing them,
    since an all-zero ``INITIAL_FORMS`` (correct when there's no
    ``instance``, i.e. on create) tells the formset there's
    nothing existing to reconcile against.
    """
    data = MultiValueDict()
    base_fields: dict[str, Field] = form_class.base_fields  # ty:ignore[unresolved-attribute]
    for name, field in base_fields.items():
        if name in payload:
            _set_field_value(field, name, payload[name], data)

    for rel_name, formset_class in getattr(form_class, "formsets", {}).items():
        if rel_name not in payload:
            continue
        items = payload[rel_name]
        prefix = rel_name
        child_fields = formset_class.form.base_fields

        existing = (
            list(getattr(instance, rel_name).all()) if instance is not None else []
        )
        existing_by_pk = {obj.pk: obj for obj in existing}
        matched_pks: set[Any] = set()

        data[f"{prefix}-INITIAL_FORMS"] = str(len(existing))
        for i, obj in enumerate(existing):
            data[f"{prefix}-{i}-id"] = obj.pk

        new_items = []
        for item in items:
            matched_pk = item.get("id")
            if matched_pk in existing_by_pk and matched_pk not in matched_pks:
                matched_pks.add(matched_pk)
                item_index = next(
                    i for i, obj in enumerate(existing) if obj.pk == matched_pk
                )
                item_prefix = f"{prefix}-{item_index}"
            else:
                new_items.append(item)
                continue
            for field_name, field in child_fields.items():
                if field_name in item:
                    _set_field_value(
                        field, f"{item_prefix}-{field_name}", item[field_name], data
                    )

        for i, obj in enumerate(existing):
            if obj.pk not in matched_pks:
                data[f"{prefix}-{i}-DELETE"] = "on"

        data[f"{prefix}-TOTAL_FORMS"] = str(len(existing) + len(new_items))
        for j, item in enumerate(new_items):
            item_prefix = f"{prefix}-{len(existing) + j}"
            for field_name, field in child_fields.items():
                if field_name in item:
                    _set_field_value(
                        field, f"{item_prefix}-{field_name}", item[field_name], data
                    )

    return data
