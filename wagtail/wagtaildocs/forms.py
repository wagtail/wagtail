from itertools import groupby

from django import forms
from django.contrib.auth.models import Permission, Group
from django.db import transaction
from django.forms.models import modelform_factory
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin import widgets
from wagtail.wagtailcore.models import Collection, GroupCollectionPermission
from wagtail.wagtaildocs.permissions import permission_policy


class BaseDocumentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)

        super(BaseDocumentForm, self).__init__(*args, **kwargs)

        if user is None:
            self.collections = Collection.objects.all()
        else:
            self.collections = (
                permission_policy.collections_user_has_permission_for(user, 'add')
            )

        if self.instance.pk:
            # editing an existing document; ensure that the list of available collections
            # includes its current collection
            self.collections = (
                self.collections | Collection.objects.filter(id=self.instance.collection_id)
            )

        if len(self.collections) == 0:
            raise Exception(
                "Cannot construct DocumentForm for a user with no document collection permissions"
            )
        elif len(self.collections) == 1:
            # don't show collection field if only one collection is available
            del self.fields['collection']
        else:
            self.fields['collection'].queryset = self.collections

    def save(self, commit=True):
        if len(self.collections) == 1:
            # populate the instance's collection field with the one available collection
            self.instance.collection = self.collections[0]

        return super(BaseDocumentForm, self).save(commit=commit)


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
    return modelform_factory(
        model,
        fields=['title', 'tags'],
        widgets={
            'tags': widgets.AdminTagWidget,
            'file': forms.FileInput()
        })


DOCUMENT_PERMISSION_TYPES = [
    ('add_document', _("Add"), _("Add/edit documents you own")),
    ('change_document', _("Edit"), _("Edit any document")),
]
DOCUMENT_PERMISSION_QUERYSET = Permission.objects.filter(
    content_type__app_label='wagtaildocs',
    codename__in=[codename for codename, short_label, long_label in DOCUMENT_PERMISSION_TYPES]
)


class DocumentPermissionsForm(forms.Form):
    """
    Defines the document permissions that are assigned to an entity
    (i.e. group or user) for a specific collection
    """
    collection = forms.ModelChoiceField(
        queryset=Collection.objects.all()
    )
    permissions = forms.ModelMultipleChoiceField(
        queryset=DOCUMENT_PERMISSION_QUERYSET,
        required=False,
        widget=forms.CheckboxSelectMultiple
    )


class BaseGroupDocumentPermissionFormSet(forms.BaseFormSet):
    permission_types = DOCUMENT_PERMISSION_TYPES  # defined here for easy access from templates

    def __init__(self, data=None, files=None, instance=None, prefix='document_permissions'):
        if instance is None:
            instance = Group()

        self.instance = instance

        initial_data = []

        for collection, collection_permissions in groupby(
            instance.collection_permissions.filter(
                permission__in=DOCUMENT_PERMISSION_QUERYSET,
            ).order_by('collection'),
            lambda cp: cp.collection
        ):
            initial_data.append({
                'collection': collection,
                'permissions': [cp.permission for cp in collection_permissions]
            })

        super(BaseGroupDocumentPermissionFormSet, self).__init__(
            data, files, initial=initial_data, prefix=prefix
        )
        for form in self.forms:
            form.fields['DELETE'].widget = forms.HiddenInput()

    @property
    def empty_form(self):
        empty_form = super(BaseGroupDocumentPermissionFormSet, self).empty_form
        empty_form.fields['DELETE'].widget = forms.HiddenInput()
        return empty_form

    def clean(self):
        """Checks that no two forms refer to the same collection object"""
        if any(self.errors):
            # Don't bother validating the formset unless each form is valid on its own
            return

        collections = [
            form.cleaned_data['collection']
            for form in self.forms
            if form not in self.deleted_forms
        ]
        if len(set(collections)) != len(collections):
            # collections list contains duplicates
            raise forms.ValidationError(
                _("You cannot have multiple permission records for the same collection.")
            )

    @transaction.atomic
    def save(self):
        if self.instance.pk is None:
            raise Exception(
                "Cannot save a GroupDocumentPermissionFormSet for an unsaved group instance"
            )

        # get a set of (collection, permission) tuples for all ticked permissions
        forms_to_save = [form for form in self.forms if form not in self.deleted_forms]

        final_permission_records = set()
        for form in forms_to_save:
            for permission in form.cleaned_data['permissions']:
                final_permission_records.add((form.cleaned_data['collection'], permission))

        # fetch the group's existing collection permission records for documents,
        # and from that, build a list of records to be created / deleted
        permission_ids_to_delete = []
        permission_records_to_keep = set()

        for cp in self.instance.collection_permissions.filter(
            permission__in=DOCUMENT_PERMISSION_QUERYSET,
        ):
            if (cp.collection, cp.permission) in final_permission_records:
                permission_records_to_keep.add((cp.collection, cp.permission))
            else:
                permission_ids_to_delete.append(cp.id)

        self.instance.collection_permissions.filter(id__in=permission_ids_to_delete).delete()

        permissions_to_add = final_permission_records - permission_records_to_keep
        GroupCollectionPermission.objects.bulk_create([
            GroupCollectionPermission(
                group=self.instance, collection=collection, permission=permission
            )
            for (collection, permission) in permissions_to_add
        ])

    def as_admin_panel(self):
        return render_to_string(
            'wagtaildocs/permissions/includes/document_permissions_formset.html',
            {'formset': self},
        )


GroupDocumentPermissionFormSet = forms.formset_factory(
    DocumentPermissionsForm, formset=BaseGroupDocumentPermissionFormSet, extra=0, can_delete=True
)
