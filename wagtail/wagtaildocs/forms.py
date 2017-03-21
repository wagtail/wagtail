from __future__ import absolute_import, unicode_literals

from django import forms
from django.forms.models import modelform_factory
from django.utils.lru_cache import lru_cache
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin import widgets
from wagtail.wagtailadmin.edit_handlers import (
    ObjectList, extract_panel_definitions_from_model_class)
from wagtail.wagtailadmin.forms import (
    BaseCollectionMemberForm, collection_member_permission_formset_factory)
from wagtail.wagtaildocs.models import Document
from wagtail.wagtaildocs.permissions import permission_policy as documents_permission_policy


class BaseDocumentForm(BaseCollectionMemberForm):
    permission_policy = documents_permission_policy


@lru_cache()
def get_document_edit_handler(model):
    if hasattr(model, 'edit_handler'):
        # use the edit handler specified on the document class
        edit_handler = model.edit_handler
    else:
        panels = extract_panel_definitions_from_model_class(model)
        edit_handler = ObjectList(panels, base_form_class=BaseDocumentForm)

    return edit_handler.bind_to_model(model)


def get_document_form(model):
    # TODO: Add a check that edit_handler contains panel for the collection field
    # TODO: Add a check that form is subclass of the BaseDocumentForm class
    edit_handler_class = get_document_edit_handler(model)
    return edit_handler_class.get_form_class(model)


def get_document_multi_form(model):
    return modelform_factory(
        model,
        form=BaseDocumentForm,
        fields=['title', 'collection', 'tags'],
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
