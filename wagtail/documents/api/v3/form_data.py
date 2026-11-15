from copy import deepcopy
from typing import Any, cast

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import AnonymousUser
from django.db.models import Model
from django.forms import ModelChoiceField, ModelForm
from django.utils.datastructures import MultiValueDict
from ninja import UploadedFile

from wagtail.api.v3.form_data import build_form_data
from wagtail.documents.forms import get_document_form


def _restore_hidden_collection_field(
    form: ModelForm,
    payload: dict[str, Any],
) -> ModelForm:
    """Restore validation when the admin form hides its sole collection choice."""
    if "collection" not in form.fields:
        collections = getattr(form, "collections")
        collection_field = cast(
            ModelChoiceField,
            deepcopy(form.base_fields["collection"]),
        )
        collection_field.queryset = collections
        form.fields["collection"] = collection_field
        if "collection" not in payload:
            form_data = cast(MultiValueDict, form.data)
            form_data["collection"] = collections[0].pk
    return form


def build_document_form(
    model: type,
    data: Any,
    file: UploadedFile,
    user: AbstractBaseUser | AnonymousUser,
) -> ModelForm:
    form_class = get_document_form(model)
    payload = data.model_dump()
    form_data = build_form_data(form_class, payload)
    instance = model(uploaded_by_user=user)
    form = form_class(
        data=form_data,
        files={"file": file},
        instance=instance,
        user=user,
    )
    submitted_payload = data.model_dump(exclude_unset=True)
    return _restore_hidden_collection_field(form, submitted_payload)


def build_document_update_form(
    instance: Model,
    data: Any,
    user: AbstractBaseUser | AnonymousUser,
) -> ModelForm:
    model = type(instance)
    payload = data.model_dump(exclude_unset=True)
    form_class = get_document_form(model, fields=payload.keys())
    form_data = build_form_data(form_class, payload, instance=instance)
    if "collection" not in payload and "collection" in form_class.base_fields:
        # Django adds ``<foreign_key>_id`` attributes dynamically.
        form_data["collection"] = instance.collection_id  # ty: ignore[unresolved-attribute]
    form = form_class(data=form_data, instance=instance, user=user)
    return _restore_hidden_collection_field(form, payload)
