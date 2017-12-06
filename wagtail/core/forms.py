from itertools import groupby

from django import forms
from django.contrib.auth.models import Group
from django.db import transaction
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy

from wagtail.admin import widgets
from wagtail.core.models import (
    COLLECTION_PERMISSION_TYPE_CHOICES, COLLECTION_PERMISSION_TYPES, Collection, GroupCollectionManagementPermission, )


class PasswordViewRestrictionForm(forms.Form):
    password = forms.CharField(label=ugettext_lazy("Password"), widget=forms.PasswordInput)
    return_url = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        self.restriction = kwargs.pop('instance')
        super().__init__(*args, **kwargs)

    def clean_password(self):
        data = self.cleaned_data['password']
        if data != self.restriction.password:
            raise forms.ValidationError(_("The password you have entered is not correct. Please try again."))

        return data


class CollectionPermissionsForm(forms.Form):
    """
    Note 'Permissions' (plural). A single instance of this form defines the permissions
    that are assigned to an entity (i.e. group or user) for a specific collection.
    """
    collection = forms.ModelChoiceField(
        queryset=Collection.objects.all(),
        widget=widgets.AdminCollectionWidget,
    )
    permissions = forms.MultipleChoiceField(
        choices=COLLECTION_PERMISSION_TYPE_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple
    )


class BaseGroupCollectionPermissionFormSet(forms.BaseFormSet):
    permission_types = COLLECTION_PERMISSION_TYPES  # defined here for easy access from templates

    def __init__(self, data=None, files=None, instance=None, prefix='collection_permissions'):
        if instance is None:
            instance = Group()

        self.instance = instance

        initial_data = []

        for collection, collection_permissions in groupby(
            instance.collection_manage_permissions.select_related('collection').order_by('collection'),
            lambda collection_permission: collection_permission.collection
        ):
            initial_data.append({
                'collection': collection,
                'permissions': [cp.permission_type for cp in collection_permissions]
            })

        super(BaseGroupCollectionPermissionFormSet, self).__init__(
            data, files, initial=initial_data, prefix=prefix
        )
        for form in self.forms:
            form.fields['DELETE'].widget = forms.HiddenInput()

    @property
    def empty_form(self):
        empty_form = super(BaseGroupCollectionPermissionFormSet, self).empty_form
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
            # need to check for presence of 'collection' in cleaned_data,
            # because a completely blank form passes validation
            if form not in self.deleted_forms and 'collection' in form.cleaned_data
        ]
        if len(set(collections)) != len(collections):
            # collections list contains duplicates
            raise forms.ValidationError(_("You cannot have multiple permission records for the same collection."))

    @transaction.atomic
    def save(self):
        if self.instance.pk is None:
            raise Exception(
                "Cannot save a GroupCollectionPermissionFormSet for an unsaved group instance"
            )

        # get a set of (collection, permission_type) tuples for all ticked permissions
        forms_to_save = [
            form for form in self.forms
            if form not in self.deleted_forms and 'collection' in form.cleaned_data
        ]

        final_permission_records = set()
        for form in forms_to_save:
            for permission_type in form.cleaned_data['permissions']:
                final_permission_records.add((form.cleaned_data['collection'], permission_type))

        # fetch the group's existing collection permission records, and from that, build a list
        # of records to be created / deleted
        permission_ids_to_delete = []
        permission_records_to_keep = set()

        for cp in self.instance.collection_manage_permissions.all():
            if (cp.collection, cp.permission_type) in final_permission_records:
                permission_records_to_keep.add((cp.collection, cp.permission_type))
            else:
                permission_ids_to_delete.append(cp.pk)

        self.instance.collection_manage_permissions.filter(pk__in=permission_ids_to_delete).delete()

        permissions_to_add = final_permission_records - permission_records_to_keep
        GroupCollectionManagementPermission.objects.bulk_create([
            GroupCollectionManagementPermission(
                group=self.instance, collection=collection, permission_type=permission_type
            )
            for (collection, permission_type) in permissions_to_add
        ])

    def as_admin_panel(self):
        return render_to_string('wagtailcore/permissions/includes/collection_member_permissions_formset.html', {
            'formset': self
        })


GroupCollectionPermissionFormSet = forms.formset_factory(
    CollectionPermissionsForm, formset=BaseGroupCollectionPermissionFormSet, extra=0, can_delete=True
)
