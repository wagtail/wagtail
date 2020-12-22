from django import forms
from django.conf import settings
from django.forms.models import modelform_factory
from django.utils.translation import gettext_lazy as _

from wagtail.admin import widgets
from wagtail.admin.forms.collections import (
    BaseCollectionMemberForm, CollectionChoiceField, collection_member_permission_formset_factory)
from wagtail.core.models import Collection
from wagtail.documents.models import Document
from wagtail.documents.permissions import permission_policy as documents_permission_policy


# Callback to allow us to override the default form field for the collection field
def formfield_for_dbfield(db_field, **kwargs):
    if db_field.name == 'collection':
        return CollectionChoiceField(queryset=Collection.objects.all(), empty_label=None, **kwargs)

    # For all other fields, just call its formfield() method.
    return db_field.formfield(**kwargs)


class BaseDocumentForm(BaseCollectionMemberForm):
    permission_policy = documents_permission_policy

    class Meta:
        widgets = {
            'tags': widgets.AdminTagWidget,
            'file': forms.FileInput()
        }


def get_document_base_form():
    base_form_override = getattr(settings, "WAGTAILDOCS_DOCUMENT_FORM_BASE", "")
    if base_form_override:
        from django.utils.module_loading import import_string
        base_form = import_string(base_form_override)
    else:
        base_form = BaseDocumentForm
    return base_form


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
        form=get_document_base_form(),
        fields=fields,
        formfield_callback=formfield_for_dbfield,
    )


def get_document_multi_form(model):
    # edit form for use within the multiple uploader; consists of all fields from
    # model.admin_form_fields except file

    fields = [field for field in model.admin_form_fields if field != 'file']
    if 'collection' not in fields:
        fields.append('collection')

    return modelform_factory(
        model,
        form=get_document_base_form(),
        fields=fields,
        formfield_callback=formfield_for_dbfield,
    )


GroupDocumentPermissionFormSet = collection_member_permission_formset_factory(
    Document,
    [
        ('add_document', _("Add"), _("Add/edit documents you own")),
        ('change_document', _("Edit"), _("Edit any document")),
        ('choose_document', _("Choose"), _("Select documents in choosers")),
    ],
    'wagtaildocs/permissions/includes/document_permissions_formset.html'
)
