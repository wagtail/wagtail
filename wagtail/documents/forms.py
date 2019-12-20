from django import forms
from django.forms.models import modelform_factory
from django.utils.translation import ugettext_lazy as _

from wagtail.admin import widgets
from wagtail.admin.forms.collections import (
    BaseCollectionMemberForm, collection_member_permission_formset_factory)
from wagtail.documents.models import Document
from wagtail.documents.permissions import permission_policy as documents_permission_policy


class BaseDocumentForm(BaseCollectionMemberForm):
    permission_policy = documents_permission_policy


def get_document_form(model):
    fields = model.admin_form_fields
    if 'collection' not in fields:
        # force addition of the 'collection' field, because leaving it out can
        # cause dubious results when multiple collections exist (e.g adding the
        # document to the root collection where the user may not have permission) -
        # and when only one collection exists, it will get hidden anyway.
        fields = list(fields) + ['collection']

    return modelform_factory(
        model,
        form=BaseDocumentForm,
        fields=fields,
        widgets={
            'tags': widgets.AdminTagWidget,
            'file': forms.FileInput()
        })


def get_document_multi_form(model):
    fields = [field for field in model.admin_form_fields if field != 'file']
    if 'collection' not in fields:
        fields.append('collection')

    return modelform_factory(
        model,
        form=BaseDocumentForm,
        fields=fields,
        widgets={
            'tags': widgets.AdminTagWidget,
            'file': forms.FileInput()
        })


GroupDocumentPermissionFormSet = collection_member_permission_formset_factory(
    Document,
    [
        ('add_document', _("Add"), _("Add/edit documents you own")),
        ('change_document', _("Edit"), _("Edit any document")),
    ],
    'wagtaildocs/permissions/includes/document_permissions_formset.html'
)
