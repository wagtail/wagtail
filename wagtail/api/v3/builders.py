from typing import Any, cast

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import AnonymousUser
from django.forms import BaseForm

from wagtail.admin.panels import Panel
from wagtail.api.v3.form_data import build_form_data
from wagtail.models import Page


def _get_form_class(model: type[Page]):
    # Page.get_edit_handler is monkey-patched onto the class by
    # wagtail.admin.panels.page_utils, so it isn't visible statically.
    edit_handler = cast(Panel, model.get_edit_handler())  # ty: ignore[unresolved-attribute]
    return edit_handler.get_form_class()


def _collect_form_error_messages(form: BaseForm, prefix: str = "") -> list[str]:
    """Flatten a (possibly ``ClusterForm``) form's errors into readable messages.

    Recurses into each InlinePanel-backed formset's non-form errors (e.g. a
    formset-level ``clean()``) and each child form's own field errors, since
    those aren't visited by ``form.errors`` alone.
    """
    messages = []
    for field_name, field_errors in form.errors.items():
        label = f"{prefix}{field_name}"
        messages.extend(f"{label}: {message}" for message in field_errors)

    for rel_name, formset in getattr(form, "formsets", {}).items():
        for message in formset.non_form_errors():
            messages.append(f"{prefix}{rel_name}: {message}")
        for i, child_form in enumerate(formset.forms):
            messages.extend(
                _collect_form_error_messages(
                    child_form, prefix=f"{prefix}{rel_name}[{i}]."
                )
            )

    return messages


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
    form_class = _get_form_class(model)
    payload = data.dict(exclude={"meta"})
    formset_payloads = {
        name: value for name, value in payload.items() if isinstance(value, list)
    }

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

    form_data = build_form_data(form_class, payload, formset_payloads)

    return form_class(data=form_data, instance=page, parent_page=parent, for_user=user)
