from collections.abc import Iterable
from typing import Any, cast

import swapper
from django import forms
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.db.models import Model
from django.forms import BaseForm, Field
from django.forms.formsets import ORDERING_FIELD_NAME
from django.utils.datastructures import MultiValueDict
from modelcluster.forms import BaseChildFormSet
from ninja.schema import BaseModel
from permissionedforms import PermissionedForm
from taggit.forms import TagField, TagWidget
from taggit.models import Tag

from wagtail.admin.forms.models import WagtailAdminModelForm
from wagtail.admin.panels import Panel, get_edit_handler, get_form_for_model
from wagtail.api.conf import get_model_field
from wagtail.api.rich_text import APIRichText
from wagtail.api.v3.errors import as_validation_error
from wagtail.api.v3.registry import ContentTypeRegistration, registry
from wagtail.api.v3.schemas import create_generator
from wagtail.blocks.base import BlockField
from wagtail.blocks.field_block import FieldBlock, RichTextBlock
from wagtail.blocks.list_block import ListBlock
from wagtail.blocks.static_block import StaticBlock
from wagtail.blocks.stream_block import BaseStreamBlock
from wagtail.blocks.struct_block import BaseStructBlock

Page = swapper.load_model("wagtailcore", "Page")


# Form data key, per existing child row, listing the fields the request
# supplied for it. See PartialUpdateChildFormSet.
SUPPLIED_FIELDS_KEY = "__supplied_fields"


class PartialUpdateChildFormSet(BaseChildFormSet):
    """Leave alone the fields of an existing child row that a request didn't
    supply, rather than clearing them.

    A formset's form class is shared by all its rows, so it can't be
    narrowed to each row's own fields up front the way the top-level form
    is (see ``get_api_form_class``'s ``field_names``). Instead, each existing
    row's form drops the fields not listed under its ``SUPPLIED_FIELDS_KEY``
    entry in the form data.
    """

    def add_fields(self, form, index):
        super().add_fields(form, index)
        if index is None or not self.is_bound:
            return
        sort_order_field = getattr(self.model, "sort_order_field", None)
        if self.can_order and sort_order_field and index < self.initial_form_count():
            # The formset's initial ORDER is the row's form index, which may
            # not match its stored sort order (e.g. if that's None). Use the
            # stored one, so a row is saved whenever its sort order changes.
            sort_order = getattr(form.instance, sort_order_field)
            form.fields[ORDERING_FIELD_NAME].initial = (
                None if sort_order is None else sort_order + 1
            )
        key = form.add_prefix(SUPPLIED_FIELDS_KEY)
        if key not in self.data:
            return
        supplied = set(cast(MultiValueDict, self.data).getlist(key))
        for name in self.form.base_fields:
            if name not in supplied:
                form.fields.pop(name, None)


def get_partial_update_formset(
    formset: type[BaseChildFormSet],
) -> type[PartialUpdateChildFormSet]:
    """Combine ``PartialUpdateChildFormSet`` with a relation's own formset
    class, if it has a custom one."""
    if issubclass(formset, PartialUpdateChildFormSet):
        return formset
    return type(
        f"PartialUpdate{formset.__name__}", (PartialUpdateChildFormSet, formset), {}
    )


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
        child_model = cast(type[Model], get_model_field(model, name).related_model)
        child_schema = create_generator.get_child_relation_schema(child_model)
        filtered_formsets[name] = {
            **formset_options,
            **filter_form_options(
                child_model, formset_options, child_schema.model_fields.keys()
            ),
            "formset": get_partial_update_formset(
                formset_options.get("formset", BaseChildFormSet)
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
        # Page and snippets .get_edit_handler() is monkey-patched to the class,
        # so it isn't visible statically.
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

    form_class = get_form_for_model(
        model,
        form_class=base_form_class,
        **form_options,
    )
    use_api_block_widgets(form_class)
    return form_class


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
    setattr(page, "_meta_warnings", get_warnings(form_data))

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
    setattr(page, "_meta_warnings", get_warnings(form_data))

    return form_class(
        data=form_data,
        instance=page,
        parent_page=page.get_parent(),
        for_user=user,
    )


def build_model_form(
    model: type[Model],
    data: Any,
    user: AbstractBaseUser | AnonymousUser,
):
    """Build a bound form from a validated create-input schema.

    Uses the model's own admin form, wired up through its edit handler's
    panels (the same form the admin "create" view binds), so any custom
    ``clean()``/``clean_<field>()`` logic a project defines on that form or
    its formsets runs for real, rather than being bypassed.
    """
    form_class = get_api_form_class(model)
    payload = data.dict(exclude={"meta"})
    form_data = build_form_data(form_class, payload)
    instance = model()
    setattr(instance, "_meta_warnings", get_warnings(form_data))

    kwargs: dict[str, Any] = {"data": form_data, "instance": instance}
    if issubclass(form_class, PermissionedForm):
        kwargs["for_user"] = user

    return form_class(**kwargs)


def build_model_update_form(
    instance: Model,
    data: Any,
    user: AbstractBaseUser | AnonymousUser,
):
    """Build a bound form from a validated, partial update-input schema.

    Like :func:`build_model_form`, but binds the given, already-saved
    ``instance`` instead of constructing a new one. As with
    :func:`build_page_update_form`, this is a partial (PATCH-style) update:
    only the fields actually present in the request body (``exclude_unset``)
    are put on the form, via a form class narrowed to just those fields, so
    a field (or child relation) the request didn't mention is left as-is.
    """
    model = type(instance)
    payload = data.dict(exclude={"meta"}, exclude_unset=True)
    form_class = get_api_form_class(model, field_names=payload.keys())
    form_data = build_form_data(form_class, payload, instance=instance)
    setattr(instance, "_meta_warnings", get_warnings(form_data))

    kwargs: dict[str, Any] = {"data": form_data, "instance": instance}
    if issubclass(form_class, PermissionedForm):
        kwargs["for_user"] = user

    return form_class(**kwargs)


def get_warnings(data: MultiValueDict) -> list[Any]:
    return data.get("__meta_warnings", [])


def add_warnings(data: MultiValueDict, warnings: list[Any]) -> None:
    data.setdefault("__meta_warnings", []).extend(warnings)


class APIBlockWidget(forms.Widget):
    """Widget for a StreamField's ``BlockField`` in an API form.

    ``build_form_data`` puts the field's value into the form data already
    converted to the block's native type (see ``to_native_block_value``), so
    this reads it back as-is rather than parsing the editor's own key scheme.
    ``BlockField.clean()`` then validates it with the block's ``clean()``, as
    in the editor.
    """

    def value_from_datadict(self, data, files, name):
        return data.get(name)

    def value_omitted_from_data(self, data, files, name):
        return name not in data


def use_api_block_widgets(form_class: type[BaseForm]) -> None:
    """Give every StreamField in ``form_class``, and in its formsets' forms
    (recursively), an ``APIBlockWidget``. Only for a form class generated for
    this request, since this modifies its fields in place."""
    for field in form_class.base_fields.values():  # ty:ignore[unresolved-attribute]
        if isinstance(field, BlockField):
            field.widget = APIBlockWidget()
    for formset_class in getattr(form_class, "formsets", {}).values():
        use_api_block_widgets(formset_class.form)


def to_prep_block_value(block, value: Any, prefix: str, data: MultiValueDict) -> Any:
    """Convert ``value``, in its StreamField API JSON shape, to the block's
    JSON representation (as from ``get_prep_value``), ready for
    ``to_python``.

    For most blocks the two are the same. This rejects unknown block types,
    and converts rich text from any accepted API input format (adding any
    removals to the warnings in ``data``). A field block's value is passed
    through the block's own widget, as it would be when submitted through
    the editor, so any conversion or cleaning the widget does applies (e.g.
    Draftail's rich text converter).

    A block that contains child blocks but doesn't build on ``StreamBlock``,
    ``ListBlock`` or ``StructBlock`` (e.g. ``TypedTableBlock``) must define
    ``map_child_values(value, func)``, returning ``value`` with
    ``func(child_block, child_value, child_path)`` applied to each child
    value, so its children are converted too. Any other block that isn't a
    field block can't be written through the API, since its widget can't be
    applied.
    """
    if isinstance(block, BaseStreamBlock):
        items = []
        for i, item in enumerate(value or []):
            if not isinstance(item, dict):
                raise ValidationError(f"{prefix}: block {i} must be an object")
            child_block = block.child_blocks.get(item.get("type"))
            if child_block is None:
                raise ValidationError(
                    f"{prefix}: unrecognised block type {item.get('type')!r}"
                )
            if "value" not in item:
                raise ValidationError(f"{prefix}: block {i} has no value")
            child = {
                "type": item["type"],
                "value": to_prep_block_value(
                    child_block, item["value"], f"{prefix}-{i}-value", data
                ),
            }
            if item.get("id") is not None:
                child["id"] = item["id"]
            items.append(child)
        return items
    if isinstance(block, ListBlock):
        items = []
        for i, item in enumerate(value or []):
            item_prefix = f"{prefix}-{i}-value"
            if block._item_is_in_block_format(item):
                items.append(
                    {
                        **item,
                        "value": to_prep_block_value(
                            block.child_block, item["value"], item_prefix, data
                        ),
                    }
                )
            else:
                items.append(
                    to_prep_block_value(block.child_block, item, item_prefix, data)
                )
        return items
    if isinstance(block, BaseStructBlock):
        value = value or {}
        if not isinstance(value, dict):
            raise ValidationError(f"{prefix}: value must be an object")
        return {
            name: to_prep_block_value(
                child_block, value.get(name), f"{prefix}-{name}", data
            )
            for name, child_block in block.child_blocks.items()
        }
    if isinstance(block, FieldBlock):
        return _to_prep_field_block_value(block, value, prefix, data)
    if hasattr(block, "map_child_values"):
        return block.map_child_values(
            value,
            lambda child_block, child_value, child_path: to_prep_block_value(
                child_block, child_value, f"{prefix}-{child_path}", data
            ),
        )
    if isinstance(block, StaticBlock):
        return value
    raise ValidationError(
        f"{prefix}: {type(block).__name__} can't be written through the API"
    )


def _to_prep_field_block_value(
    block: FieldBlock, value: Any, prefix: str, data: MultiValueDict
) -> Any:
    widget = cast(forms.Field, block.field).widget  # ty:ignore[unresolved-attribute]
    if isinstance(block, RichTextBlock) and value is not None:
        try:
            value, warnings = APIRichText.convert_input(value, features=block.features)
        except ValueError as e:
            raise as_validation_error(e, loc=(prefix,)) from e
        add_warnings(data, warnings)
    try:
        if isinstance(block, RichTextBlock):
            # The editor widget takes its own format (e.g. Draftail's
            # contentstate), converted back to HTML by value_from_datadict.
            form_value = widget.format_value(value)
        else:
            form_value = block.value_for_form(block.to_python(value))
        form_data = MultiValueDict()
        if getattr(widget, "allow_multiple_selected", False):
            form_data.setlist(prefix, list(form_value or []))
        else:
            form_data[prefix] = form_value
        return block.get_prep_value(block.value_from_datadict(form_data, {}, prefix))
    except (TypeError, ValueError) as e:
        raise ValidationError(f"{prefix}: invalid value") from e


def to_native_block_value(block, value: Any, prefix: str, data: MultiValueDict) -> Any:
    """Convert ``value``, in its StreamField API JSON shape, to the block's
    native value, as ``to_python`` does for the stored value."""
    prep_value = to_prep_block_value(block, value, prefix, data)
    try:
        native_value = block.to_python(prep_value)
        # A StreamBlock converts its children lazily, so convert the whole
        # value now: a wrongly shaped value then fails here, as a validation
        # error, rather than later on.
        block.get_prep_value(native_value)
    except (TypeError, ValueError) as e:
        raise ValidationError(f"{prefix}: invalid value") from e
    return native_value


def _set_field_value(field: Field, name: str, value: Any, data: MultiValueDict) -> None:
    """Write ``value`` for a single (non-formset) form field into ``data``.

    Most widgets read a single key via plain ``.get()`` (confirmed for every
    built-in Wagtail/Django widget); the exceptions handled here are a
    ``BlockField`` (StreamField), whose value is put in already converted to
    the block's native type, for its ``APIBlockWidget``; a multi-valued field (e.g. ``ModelMultipleChoiceField`` for a
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
        data[name] = to_native_block_value(field.block, value, name, data)
    elif getattr(field.widget, "allow_multiple_selected", False):
        data.setlist(name, list(value) if value else [])
    elif hasattr(field.widget, "converter"):
        # Normally this is an envelope dict, but it can also be a plain str
        # e.g. if the field was not in the payload and thus the Pydantic field
        # default "" is used.
        if isinstance(value, dict):
            add_warnings(data, value.get("removals", []))
            value = value.get("content", "")
        # A rich text editor widget (Draftail's `to_database_format`/
        # `from_database_format` contract - core ships only Draftail, but
        # third-party editors may implement the same converter pattern).
        data[name] = field.widget.format_value(value)
    elif isinstance(field, TagField):
        # The API takes a list of tag names, but the widget expects the same
        # single edit string the admin renders. The widget's format_value()
        # builds that from tag instances via taggit's edit_string_for_tags()
        # (quoting names containing commas or spaces), which is the inverse
        # of the parse_tags() the field runs on submission.
        if isinstance(value, list):
            tag_model = getattr(field, "tag_model", Tag)
            widget = cast(TagWidget, field.widget)
            value = widget.format_value([tag_model(name=n) for n in value])
        data[name] = value
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
    edited. A relation the request mentions has its whole set replaced -
    see ``_fill_formset``. The same applies recursively to a child form
    that declares its own formsets (e.g. an InlinePanel inside an
    InlinePanel child), keyed by the relation name inside each child item.
    """
    data = MultiValueDict()
    base_fields: dict[str, Field] = form_class.base_fields  # ty:ignore[unresolved-attribute]
    for name, field in base_fields.items():
        if name in payload:
            _set_field_value(field, name, payload[name], data)

    for rel_name, formset_class in getattr(form_class, "formsets", {}).items():
        if rel_name not in payload:
            continue
        existing = (
            list(getattr(instance, rel_name).all()) if instance is not None else []
        )
        _fill_formset(data, formset_class, payload[rel_name], rel_name, existing)

    return data


def _fill_formset(
    data: MultiValueDict,
    formset_class: Any,
    items: list[dict[str, Any]],
    prefix: str,
    existing: list[Model],
) -> None:
    """Write the formset data for one child relation into ``data``.

    This replaces the relation's whole set rather than trying to diff it
    item by item: every one of the ``existing`` rows becomes an initial
    form, and each submitted item either binds to the existing row whose pk
    matches its own pk (an edit in place) or, lacking a matching pk,
    becomes a new (non-initial) form. Any existing row no *submitted*
    item's pk refers to is marked for deletion. The pk is keyed by its
    field's own name (e.g. ``id`` or ``custom_id``), as it is in the read
    schema and the formset. Without this, the submitted items would be
    added *alongside* the existing rows instead of replacing them, since an
    all-zero ``INITIAL_FORMS`` (correct when there are no ``existing``
    rows, e.g. on create) tells the formset there's nothing existing to
    reconcile against. An existing row only has the fields its item
    supplies updated; the rest keep their current values (see
    ``PartialUpdateChildFormSet``).

    If the child form declares its own formsets, each one is filled the
    same way for every row, against that row's own existing children. A
    nested relation an item doesn't mention gets an empty formset: since
    ``ChildFormSet.save()`` only adds and removes the rows its forms refer
    to, this leaves an existing row's children untouched and gives a new
    row none.
    """
    child_fields = formset_class.form.base_fields
    nested_formsets = getattr(formset_class.form, "formsets", {})
    pk_name = formset_class.model._meta.pk.name
    existing_index = {obj.pk: i for i, obj in enumerate(existing) if obj.pk is not None}

    data[f"{prefix}-INITIAL_FORMS"] = str(len(existing))
    for i, obj in enumerate(existing):
        data[f"{prefix}-{i}-{pk_name}"] = obj.pk

    matched: dict[int, tuple[int, dict[str, Any]]] = {}
    new_items: list[tuple[int, dict[str, Any]]] = []
    for position, item in enumerate(items):
        index = existing_index.get(item.get(pk_name))
        if index is not None and index not in matched:
            matched[index] = (position, item)
        else:
            new_items.append((position, item))

    # (form index, submitted position, submitted item, existing row) - None if absent
    rows: list[tuple[int, int | None, dict[str, Any] | None, Model | None]] = []
    for i, obj in enumerate(existing):
        position, item = matched.get(i, (None, None))
        if item is None:
            data[f"{prefix}-{i}-DELETE"] = "on"
        rows.append((i, position, item, obj))
    for j, (position, item) in enumerate(new_items):
        rows.append((len(existing) + j, position, item, None))

    data[f"{prefix}-TOTAL_FORMS"] = str(len(rows))
    for index, position, item, obj in rows:
        item_prefix = f"{prefix}-{index}"
        if formset_class.can_order and position is not None:
            # Existing rows keep their original form index, so set each
            # item's ORDER to its position in the submitted list instead.
            # ORDER is 1-based, like the formset's initial values - a form
            # whose ORDER matches its initial value is considered unchanged
            # and wouldn't have its sort order saved.
            data[f"{item_prefix}-{ORDERING_FIELD_NAME}"] = str(position + 1)
        if item is not None and obj is not None:
            data.setlist(
                f"{item_prefix}-{SUPPLIED_FIELDS_KEY}",
                [name for name in child_fields if name in item],
            )
        for field_name, field in child_fields.items():
            if item is not None and field_name in item:
                _set_field_value(
                    field, f"{item_prefix}-{field_name}", item[field_name], data
                )

        for rel_name, nested_formset_class in nested_formsets.items():
            nested_prefix = f"{item_prefix}-{rel_name}"
            nested_items = item.get(rel_name) if item is not None else None
            if nested_items is None:
                data[f"{nested_prefix}-INITIAL_FORMS"] = "0"
                data[f"{nested_prefix}-TOTAL_FORMS"] = "0"
                continue
            nested_existing = (
                list(getattr(obj, rel_name).all()) if obj is not None else []
            )
            _fill_formset(
                data, nested_formset_class, nested_items, nested_prefix, nested_existing
            )
