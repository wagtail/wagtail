from itertools import groupby

from django import forms
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Min
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from wagtail.models import (
    Collection,
    CollectionViewRestriction,
    GroupCollectionPermission,
)

from .view_restrictions import BaseViewRestrictionForm


class CollectionViewRestrictionForm(BaseViewRestrictionForm):
    class Meta:
        model = CollectionViewRestriction
        fields = ("restriction_type", "password", "groups")


class SelectWithDisabledOptions(forms.Select):
    """
    Subclass of Django's select widget that allows disabling options.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disabled_values = ()

    def create_option(self, name, value, *args, **kwargs):
        option_dict = super().create_option(name, value, *args, **kwargs)
        if value in self.disabled_values:
            option_dict["attrs"]["disabled"] = "disabled"
        return option_dict


class CollectionChoiceField(forms.ModelChoiceField):
    widget = SelectWithDisabledOptions

    def __init__(self, *args, disabled_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._indentation_start_depth = 2
        self.disabled_queryset = disabled_queryset

    def _get_disabled_queryset(self):
        return self._disabled_queryset

    def _set_disabled_queryset(self, queryset):
        self._disabled_queryset = queryset
        if queryset is None:
            self.widget.disabled_values = ()
        else:
            self.widget.disabled_values = queryset.values_list(
                self.to_field_name or "pk", flat=True
            )

    disabled_queryset = property(_get_disabled_queryset, _set_disabled_queryset)

    def _set_queryset(self, queryset):
        min_depth = self.queryset.aggregate(Min("depth"))["depth__min"]
        if min_depth is None:
            self._indentation_start_depth = 2
        else:
            self._indentation_start_depth = min_depth + 1

    def label_from_instance(self, obj):
        return obj.get_indented_name(self._indentation_start_depth, html=True)


class CollectionForm(forms.ModelForm):
    parent = CollectionChoiceField(
        label=gettext_lazy("Parent"),
        queryset=Collection.objects.all(),
        required=True,
        help_text=gettext_lazy(
            "Select hierarchical position. Note: a collection cannot become a child of itself or one of its "
            "descendants."
        ),
    )

    class Meta:
        model = Collection
        fields = ("name",)

    def clean_parent(self):
        """
        Our rules about where a user may add or move a collection are as follows:
            1. The user must have 'add' permission on the parent collection (or its ancestors)
            2. We are not moving a collection used to assign permissions for this user
            3. We are not trying to move a collection to be parented by one of their descendants

        The first 2 items are taken care in the Create and Edit views by deleting the 'parent' field
        from the edit form if the user cannot move the collection. This causes Django's form
        machinery to ignore the parent field for parent regardless of what the user submits.
        This methods enforces rule #3 when we are editing an existing collection.
        """
        parent = self.cleaned_data["parent"]
        if not self.instance._state.adding and not parent.pk == self.initial.get(
            "parent"
        ):
            old_descendants = list(
                self.instance.get_descendants(inclusive=True).values_list(
                    "pk", flat=True
                )
            )
            if parent.pk in old_descendants:
                raise ValidationError(gettext_lazy("Please select another parent"))
        return parent


class BaseCollectionMemberForm(forms.ModelForm):
    """
    Abstract form handler for editing models that belong to a collection,
    such as documents and images. These forms are (optionally) instantiated
    with a 'user' kwarg, and take care of populating the 'collection' field's
    choices with the collections the user has permission for, as well as
    hiding the field when only one collection is available.

    Subclasses must define a 'permission_policy' attribute.
    """

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

        if user is None:
            self.collections = Collection.objects.all()
        else:
            self.collections = (
                self.permission_policy.collections_user_has_permission_for(user, "add")
            )

        if self.instance.pk:
            # editing an existing document; ensure that the list of available collections
            # includes its current collection
            self.collections = self.collections | Collection.objects.filter(
                id=self.instance.collection_id
            )

        if len(self.collections) == 0:
            raise Exception(
                "Cannot construct %s for a user with no collection permissions"
                % type(self)
            )
        elif len(self.collections) == 1:
            # don't show collection field if only one collection is available
            del self.fields["collection"]
        else:
            self.fields["collection"].queryset = self.collections

    def save(self, commit=True):
        if len(self.collections) == 1:
            # populate the instance's collection field with the one available collection
            self.instance.collection = self.collections[0]

        return super().save(commit=commit)


class BaseGroupCollectionMemberPermissionFormSet(forms.BaseFormSet):
    """
    A base formset class for managing GroupCollectionPermissions for a
    model with CollectionMember behaviour. Subclasses should provide attributes:
    permission_types - a list of (codename, short_label, long_label) tuples for the permissions
        being managed here
    permission_queryset - a queryset of Permission objects for the above permissions
    default_prefix - prefix to use on form fields if one is not specified in __init__
    template = template filename
    """

    def __init__(self, data=None, files=None, instance=None, prefix=None):
        if prefix is None:
            prefix = self.default_prefix

        if instance is None:
            instance = Group()

        if instance.pk is None:
            full_collection_permissions = []
        else:
            full_collection_permissions = (
                instance.collection_permissions.filter(
                    permission__in=self.permission_queryset
                )
                .select_related("permission__content_type", "collection")
                .order_by("collection")
            )

        self.instance = instance

        initial_data = []

        for collection, collection_permissions in groupby(
            full_collection_permissions,
            lambda cp: cp.collection,
        ):
            initial_data.append(
                {
                    "collection": collection,
                    "permissions": [cp.permission for cp in collection_permissions],
                }
            )

        super().__init__(data, files, initial=initial_data, prefix=prefix)
        for form in self.forms:
            form.fields["DELETE"].widget = forms.HiddenInput()

    @property
    def empty_form(self):
        empty_form = super().empty_form
        empty_form.fields["DELETE"].widget = forms.HiddenInput()
        return empty_form

    def clean(self):
        """Checks that no two forms refer to the same collection object"""
        if any(self.errors):
            # Don't bother validating the formset unless each form is valid on its own
            return

        collections = [
            form.cleaned_data["collection"]
            for form in self.forms
            # need to check for presence of 'collection' in cleaned_data,
            # because a completely blank form passes validation
            if form not in self.deleted_forms and "collection" in form.cleaned_data
        ]
        if len(set(collections)) != len(collections):
            # collections list contains duplicates
            raise forms.ValidationError(
                _(
                    "You cannot have multiple permission records for the same collection."
                )
            )

    @transaction.atomic
    def save(self):
        if self.instance.pk is None:
            raise Exception(
                "Cannot save a GroupCollectionMemberPermissionFormSet "
                "for an unsaved group instance"
            )

        # get a set of (collection, permission) tuples for all ticked permissions
        forms_to_save = [
            form
            for form in self.forms
            if form not in self.deleted_forms and "collection" in form.cleaned_data
        ]

        final_permission_records = set()
        for form in forms_to_save:
            for permission in form.cleaned_data["permissions"]:
                final_permission_records.add(
                    (form.cleaned_data["collection"], permission)
                )

        # fetch the group's existing collection permission records for this model,
        # and from that, build a list of records to be created / deleted
        permission_ids_to_delete = []
        permission_records_to_keep = set()

        for cp in self.instance.collection_permissions.filter(
            permission__in=self.permission_queryset,
        ):
            if (cp.collection, cp.permission) in final_permission_records:
                permission_records_to_keep.add((cp.collection, cp.permission))
            else:
                permission_ids_to_delete.append(cp.id)

        self.instance.collection_permissions.filter(
            id__in=permission_ids_to_delete
        ).delete()

        permissions_to_add = final_permission_records - permission_records_to_keep
        GroupCollectionPermission.objects.bulk_create(
            [
                GroupCollectionPermission(
                    group=self.instance, collection=collection, permission=permission
                )
                for (collection, permission) in permissions_to_add
            ]
        )

    def as_admin_panel(self):
        return render_to_string(
            self.template,
            {"formset": self},
        )


def collection_member_permission_formset_factory(
    model, permission_types, template, default_prefix=None
):

    permission_queryset = Permission.objects.filter(
        content_type__app_label=model._meta.app_label,
        codename__in=[
            codename for codename, short_label, long_label in permission_types
        ],
    ).select_related("content_type")

    if default_prefix is None:
        default_prefix = "%s_permissions" % model._meta.model_name

    class PermissionMultipleChoiceField(forms.ModelMultipleChoiceField):
        """
        Allows the custom labels from ``permission_types`` to be applied to
        permission checkboxes for the ``CollectionMemberPermissionsForm`` below
        """

        def label_from_instance(self, obj):
            for codename, short_label, long_label in permission_types:
                if codename == obj.codename:
                    return long_label
            return str(obj)

    class CollectionMemberPermissionsForm(forms.Form):
        """
        For a given model with CollectionMember behaviour,
        defines the permissions that are assigned to an entity
        (i.e. group or user) for a specific collection
        """

        collection = CollectionChoiceField(
            label=_("Collection"),
            queryset=Collection.objects.all().prefetch_related("group_permissions"),
            empty_label=None,
        )
        permissions = PermissionMultipleChoiceField(
            queryset=permission_queryset,
            required=False,
            widget=forms.CheckboxSelectMultiple,
        )

    GroupCollectionMemberPermissionFormSet = type(
        str("GroupCollectionMemberPermissionFormSet"),
        (BaseGroupCollectionMemberPermissionFormSet,),
        {
            "permission_types": permission_types,
            "permission_queryset": permission_queryset,
            "default_prefix": default_prefix,
            "template": template,
        },
    )

    return forms.formset_factory(
        CollectionMemberPermissionsForm,
        formset=GroupCollectionMemberPermissionFormSet,
        extra=0,
        can_delete=True,
    )


GroupCollectionManagementPermissionFormSet = (
    collection_member_permission_formset_factory(
        Collection,
        [
            ("add_collection", _("Add"), _("Add collections")),
            ("change_collection", _("Edit"), _("Edit collections")),
            ("delete_collection", _("Delete"), _("Delete collections")),
        ],
        "wagtailadmin/permissions/includes/collection_management_permissions_form.html",
    )
)
