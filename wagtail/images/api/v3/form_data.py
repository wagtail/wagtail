from typing import Any

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import AnonymousUser
from django.db.models import Model
from django.forms import ModelForm
from ninja import UploadedFile

from wagtail.api.v3.form_data import build_form_data
from wagtail.images.forms import get_image_form


def build_image_form(
    model: type,
    data: Any,
    file: UploadedFile,
    user: AbstractBaseUser | AnonymousUser,
) -> ModelForm:
    """Build a bound image form from a validated create-input schema and the
    uploaded file, using the admin image form (``get_image_form``) so
    ``WagtailImageField`` validation, collection-scoped choices, and
    ``BaseImageForm.save()`` metadata/index handling all apply.

    ``data.model_dump()`` uses field names (not aliases), so the wire key
    ``collection_id`` is converted back to the form field name ``collection``
    the same way snippets' ``feed_image_id`` maps to ``feed_image``.
    """
    form_class = get_image_form(model)
    payload = data.model_dump()
    form_data = build_form_data(form_class, payload)
    instance = model(uploaded_by_user=user)
    return form_class(
        data=form_data,
        files={"file": file},
        instance=instance,
        user=user,
    )


def build_image_update_form(
    instance: Model,
    data: Any,
    user: AbstractBaseUser | AnonymousUser,
) -> ModelForm:
    """Build a bound image form from a validated, partial update-input schema.

    Only the fields actually present in the request body are put on the form
    (``exclude_unset``), so a field the request didn't mention is left as-is.
    ``get_image_form`` forces the collection field in, so the instance's
    current collection is pre-filled when the request doesn't submit one -
    otherwise the required collection field would fail validation on every
    metadata-only patch.
    """
    model = type(instance)
    payload = data.model_dump(exclude_unset=True)
    form_class = get_image_form(model, fields=payload.keys())
    form_data = build_form_data(form_class, payload, instance=instance)
    if "collection" not in payload and "collection" in form_class.base_fields:
        # Django adds ``<foreign_key>_id`` attributes dynamically.
        form_data["collection"] = instance.collection_id  # ty: ignore[unresolved-attribute]
    return form_class(data=form_data, instance=instance, user=user)
