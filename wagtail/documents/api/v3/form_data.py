from typing import Any

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import AnonymousUser
from django.db.models import Model
from django.forms import ModelForm
from ninja import UploadedFile

from wagtail.api.v3.form_data import build_form_data
from wagtail.documents.forms import get_document_form


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
    return form_class(
        data=form_data,
        files={"file": file},
        instance=instance,
        user=user,
    )


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
    return form_class(data=form_data, instance=instance, user=user)
