from django import forms
from django.forms.models import modelform_factory

from wagtail.wagtailadmin import widgets


def get_document_form(model):
    return modelform_factory(
        model,
        fields=model.admin_form_fields,
        widgets={
            'tags': widgets.AdminTagWidget,
            'file': forms.FileInput()
        })
