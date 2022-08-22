from django import forms
from django.conf import settings
from django.forms.models import modelform_factory
from django.utils.translation import gettext_lazy as _

from wagtail.admin.forms.collections import (
    BaseCollectionMemberForm,
    CollectionChoiceField,
    collection_member_permission_formset_factory,
)
from wagtail.admin.widgets import AdminTagWidget
from wagtail.documents.models import Document
from wagtail.documents.permissions import (
    permission_policy as documents_permission_policy,
)
from wagtail.models import Collection
from wagtail.search import index as search_index


# Callback to allow us to override the default form field for the collection field
def formfield_for_dbfield(db_field, **kwargs):
    if db_field.name == "collection":
        return CollectionChoiceField(
            label=_("Collection"),
            queryset=Collection.objects.all(),
            empty_label=None,
            **kwargs,
        )

    # For all other fields, just call its formfield() method.
    return db_field.formfield(**kwargs)


class BaseDocumentForm(BaseCollectionMemberForm):
    permission_policy = documents_permission_policy

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_file = self.instance.file

    def save(self, commit=True):
        if "file" in self.changed_data:
            self.instance._set_document_file_metadata()

        super().save(commit=commit)

        if commit:
            if "file" in self.changed_data and self.original_file:
                # If providing a new document file, delete the old one.
                # NB Doing this via original_file.delete() clears the file field,
                # which definitely isn't what we want...
                self.original_file.storage.delete(self.original_file.name)
                self.original_file = None

            # Reindex the image to make sure all tags are indexed
            search_index.insert_or_update_object(self.instance)

        return self.instance

    class Meta:
        widgets = {"tags": AdminTagWidget, "file": forms.FileInput()}


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
    if "collection" not in fields:
        # force addition of the 'collection' field, because leaving it out can
        # cause dubious results when multiple collections exist (e.g adding the
        # document to the root collection where the user may not have permission) -
        # and when only one collection exists, it will get hidden anyway.
        fields = list(fields) + ["collection"]

    BaseForm = get_document_base_form()

    # If the base form specifies the 'tags' widget as a plain unconfigured AdminTagWidget,
    # substitute one that correctly passes the tag model used on the document model.
    # (If the widget has been overridden via WAGTAILDOCS_DOCUMENT_FORM_BASE, leave it
    # alone and trust that they know what they're doing)
    widgets = None
    if BaseForm._meta.widgets.get("tags") == AdminTagWidget:
        tag_model = model._meta.get_field("tags").related_model
        widgets = BaseForm._meta.widgets.copy()
        widgets["tags"] = AdminTagWidget(tag_model=tag_model)

    return modelform_factory(
        model,
        form=BaseForm,
        fields=fields,
        widgets=widgets,
        formfield_callback=formfield_for_dbfield,
    )


def get_document_multi_form(model):
    # edit form for use within the multiple uploader; consists of all fields from
    # model.admin_form_fields except file

    fields = [field for field in model.admin_form_fields if field != "file"]
    if "collection" not in fields:
        fields.append("collection")

    BaseForm = get_document_base_form()

    # If the base form specifies the 'tags' widget as a plain unconfigured AdminTagWidget,
    # substitute one that correctly passes the tag model used on the document model.
    # (If the widget has been overridden via WAGTAILDOCS_DOCUMENT_FORM_BASE, leave it
    # alone and trust that they know what they're doing)
    widgets = None
    if BaseForm._meta.widgets.get("tags") == AdminTagWidget:
        tag_model = model._meta.get_field("tags").related_model
        widgets = BaseForm._meta.widgets.copy()
        widgets["tags"] = AdminTagWidget(tag_model=tag_model)

    return modelform_factory(
        model,
        form=BaseForm,
        fields=fields,
        widgets=widgets,
        formfield_callback=formfield_for_dbfield,
    )


GroupDocumentPermissionFormSet = collection_member_permission_formset_factory(
    Document,
    [
        ("add_document", _("Add"), _("Add/edit documents you own")),
        ("change_document", _("Edit"), _("Edit any document")),
        ("choose_document", _("Choose"), _("Select documents in choosers")),
    ],
    "wagtaildocs/permissions/includes/document_permissions_formset.html",
)
