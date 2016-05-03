from __future__ import unicode_literals

import copy
from itertools import groupby

import django
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.contrib.auth.models import Group, Permission
from django.core import validators
from django.db import models, transaction
from django.forms.widgets import TextInput
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy, ungettext
from modelcluster.forms import ClusterForm, ClusterFormMetaclass
from taggit.managers import TaggableManager

from wagtail.wagtailadmin import widgets
from wagtail.wagtailcore.models import Page, Collection, GroupCollectionPermission


class URLOrAbsolutePathValidator(validators.URLValidator):
    @staticmethod
    def is_absolute_path(value):
        return value.startswith('/')

    def __call__(self, value):
        if URLOrAbsolutePathValidator.is_absolute_path(value):
            return None
        else:
            return super(URLOrAbsolutePathValidator, self).__call__(value)


class URLOrAbsolutePathField(forms.URLField):
    widget = TextInput
    default_validators = [URLOrAbsolutePathValidator()]

    def to_python(self, value):
        if not URLOrAbsolutePathValidator.is_absolute_path(value):
            value = super(URLOrAbsolutePathField, self).to_python(value)
        return value


class SearchForm(forms.Form):
    def __init__(self, *args, **kwargs):
        placeholder = kwargs.pop('placeholder', _("Search"))
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields['q'].widget.attrs = {'placeholder': placeholder}

    q = forms.CharField(label=ugettext_lazy("Search term"), widget=forms.TextInput())


class ExternalLinkChooserForm(forms.Form):
    url = URLOrAbsolutePathField(required=True, label=ugettext_lazy("URL"))


class ExternalLinkChooserWithLinkTextForm(forms.Form):
    url = URLOrAbsolutePathField(required=True, label=ugettext_lazy("URL"))
    link_text = forms.CharField(required=True)


class EmailLinkChooserForm(forms.Form):
    email_address = forms.EmailField(required=True)


class EmailLinkChooserWithLinkTextForm(forms.Form):
    email_address = forms.EmailField(required=True)
    link_text = forms.CharField(required=False)


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={'tabindex': '1'}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': ugettext_lazy("Enter password"),
                                          'tabindex': '2',
                                          }),
    )

    def __init__(self, request=None, *args, **kwargs):
        super(LoginForm, self).__init__(request=request, *args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = ugettext_lazy("Enter your %s") \
            % self.username_field.verbose_name


class PasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label=ugettext_lazy("Enter your email address to reset your password"), max_length=254)

    def clean(self):
        cleaned_data = super(PasswordResetForm, self).clean()

        # Find users of this email address
        UserModel = get_user_model()
        email = cleaned_data.get('email')
        if not email:
            raise forms.ValidationError(_("Please fill your email address."))
        active_users = UserModel._default_manager.filter(email__iexact=email, is_active=True)

        if active_users.exists():
            # Check if all users of the email address are LDAP users (and give an error if they are)
            found_non_ldap_user = False
            for user in active_users:
                if user.has_usable_password():
                    found_non_ldap_user = True
                    break

            if not found_non_ldap_user:
                # All found users are LDAP users, give error message
                raise forms.ValidationError(
                    _("Sorry, you cannot reset your password here as your user account is managed by another server.")
                )
        else:
            # No user accounts exist
            raise forms.ValidationError(_("This email address is not recognised."))

        return cleaned_data


class CopyForm(forms.Form):
    def __init__(self, *args, **kwargs):
        # CopyPage must be passed a 'page' kwarg indicating the page to be copied
        self.page = kwargs.pop('page')
        can_publish = kwargs.pop('can_publish')
        super(CopyForm, self).__init__(*args, **kwargs)

        self.fields['new_title'] = forms.CharField(initial=self.page.title, label=_("New title"))
        self.fields['new_slug'] = forms.SlugField(initial=self.page.slug, label=_("New slug"))
        self.fields['new_parent_page'] = forms.ModelChoiceField(
            initial=self.page.get_parent(),
            queryset=Page.objects.all(),
            widget=widgets.AdminPageChooser(can_choose_root=True),
            label=_("New parent page"),
            help_text=_("This copy will be a child of this given parent page.")
        )

        pages_to_copy = self.page.get_descendants(inclusive=True)
        subpage_count = pages_to_copy.count() - 1
        if subpage_count > 0:
            self.fields['copy_subpages'] = forms.BooleanField(
                required=False, initial=True, label=_("Copy subpages"),
                help_text=ungettext(
                    "This will copy %(count)s subpage.",
                    "This will copy %(count)s subpages.",
                    subpage_count) % {'count': subpage_count})

        if can_publish:
            pages_to_publish_count = pages_to_copy.live().count()
            if pages_to_publish_count > 0:
                # In the specific case that there are no subpages, customise the field label and help text
                if subpage_count == 0:
                    label = _("Publish copied page")
                    help_text = _("This page is live. Would you like to publish its copy as well?")
                else:
                    label = _("Publish copies")
                    help_text = ungettext(
                        "%(count)s of the pages being copied is live. Would you like to publish its copy?",
                        "%(count)s of the pages being copied are live. Would you like to publish their copies?",
                        pages_to_publish_count) % {'count': pages_to_publish_count}

                self.fields['publish_copies'] = forms.BooleanField(
                    required=False, initial=True, label=label, help_text=help_text
                )

    def clean(self):
        cleaned_data = super(CopyForm, self).clean()

        # Make sure the slug isn't already in use
        slug = cleaned_data.get('new_slug')

        # New parent page given in form or parent of source, if parent_page is empty
        parent_page = cleaned_data.get('new_parent_page') or self.page.get_parent()

        # Count the pages with the same slug within the context of our copy's parent page
        if slug and parent_page.get_children().filter(slug=slug).count():
            self._errors['new_slug'] = self.error_class(
                [_("This slug is already in use within the context of its parent page \"%s\"" % parent_page)]
            )
            # The slug is no longer valid, hence remove it from cleaned_data
            del cleaned_data['new_slug']

        return cleaned_data


class PageViewRestrictionForm(forms.Form):
    restriction_type = forms.ChoiceField(label="Visibility", choices=[
        ('none', ugettext_lazy("Public")),
        ('password', ugettext_lazy("Private, accessible with the following password")),
    ], widget=forms.RadioSelect)
    password = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super(PageViewRestrictionForm, self).clean()

        if cleaned_data.get('restriction_type') == 'password' and not cleaned_data.get('password'):
            self._errors["password"] = self.error_class([_('This field is required.')])
            del cleaned_data['password']

        return cleaned_data


# Form field properties to override whenever we encounter a model field
# that matches one of these types - including subclasses
FORM_FIELD_OVERRIDES = {
    models.DateField: {'widget': widgets.AdminDateInput},
    models.TimeField: {'widget': widgets.AdminTimeInput},
    models.DateTimeField: {'widget': widgets.AdminDateTimeInput},
    TaggableManager: {'widget': widgets.AdminTagWidget},
}

# Form field properties to override whenever we encounter a model field
# that matches one of these types exactly, ignoring subclasses.
# (This allows us to override the widget for models.TextField, but leave
# the RichTextField widget alone)
DIRECT_FORM_FIELD_OVERRIDES = {
    models.TextField: {'widget': widgets.AdminAutoHeightTextInput},
}


# Callback to allow us to override the default form fields provided for each model field.
def formfield_for_dbfield(db_field, **kwargs):
    # adapted from django/contrib/admin/options.py

    overrides = None

    # If we've got overrides for the formfield defined, use 'em. **kwargs
    # passed to formfield_for_dbfield override the defaults.
    if db_field.__class__ in DIRECT_FORM_FIELD_OVERRIDES:
        overrides = DIRECT_FORM_FIELD_OVERRIDES[db_field.__class__]
    else:
        for klass in db_field.__class__.mro():
            if klass in FORM_FIELD_OVERRIDES:
                overrides = FORM_FIELD_OVERRIDES[klass]
                break

    if overrides:
        kwargs = dict(copy.deepcopy(overrides), **kwargs)

    return db_field.formfield(**kwargs)


class WagtailAdminModelFormMetaclass(ClusterFormMetaclass):
    # Override the behaviour of the regular ModelForm metaclass -
    # which handles the translation of model fields to form fields -
    # to use our own formfield_for_dbfield function to do that translation.
    # This is done by sneaking a formfield_callback property into the class
    # being defined (unless the class already provides a formfield_callback
    # of its own).

    # while we're at it, we'll also set extra_form_count to 0, as we're creating
    # extra forms in JS
    extra_form_count = 0

    def __new__(cls, name, bases, attrs):
        if 'formfield_callback' not in attrs or attrs['formfield_callback'] is None:
            attrs['formfield_callback'] = formfield_for_dbfield

        new_class = super(WagtailAdminModelFormMetaclass, cls).__new__(cls, name, bases, attrs)
        return new_class

WagtailAdminModelForm = WagtailAdminModelFormMetaclass(str('WagtailAdminModelForm'), (ClusterForm,), {})

# Now, any model forms built off WagtailAdminModelForm instead of ModelForm should pick up
# the nice form fields defined in FORM_FIELD_OVERRIDES.


class WagtailAdminPageForm(WagtailAdminModelForm):

    class Meta:
        # (dealing with Treebeard's tree-related fields that really should have
        # been editable=False)
        exclude = ['content_type', 'path', 'depth', 'numchild']

    def __init__(self, data=None, files=None, parent_page=None, *args, **kwargs):
        super(WagtailAdminPageForm, self).__init__(data, files, *args, **kwargs)
        self.parent_page = parent_page

    if django.VERSION < (1, 9):
        def clean_title(self):
            return self.cleaned_data['title'].strip()

        def clean_seo_title(self):
            return self.cleaned_data['seo_title'].strip()

    def clean(self):
        cleaned_data = super(WagtailAdminPageForm, self).clean()
        if 'slug' in self.cleaned_data:
            if not Page._slug_is_available(
                cleaned_data['slug'], self.parent_page, self.instance
            ):
                self.add_error('slug', forms.ValidationError(_("This slug is already in use")))

        # Check scheduled publishing fields
        go_live_at = cleaned_data.get('go_live_at')
        expire_at = cleaned_data.get('expire_at')

        # Go live must be before expire
        if go_live_at and expire_at:
            if go_live_at > expire_at:
                msg = _('Go live date/time must be before expiry date/time')
                self.add_error('go_live_at', forms.ValidationError(msg))
                self.add_error('expire_at', forms.ValidationError(msg))

        # Expire at must be in the future
        if expire_at and expire_at < timezone.now():
            self.add_error('expire_at', forms.ValidationError(_('Expiry date/time must be in the future')))

        return cleaned_data


class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ('name',)


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
        user = kwargs.pop('user', None)

        super(BaseCollectionMemberForm, self).__init__(*args, **kwargs)

        if user is None:
            self.collections = Collection.objects.all()
        else:
            self.collections = (
                self.permission_policy.collections_user_has_permission_for(user, 'add')
            )

        if self.instance.pk:
            # editing an existing document; ensure that the list of available collections
            # includes its current collection
            self.collections = (
                self.collections | Collection.objects.filter(id=self.instance.collection_id)
            )

        if len(self.collections) == 0:
            raise Exception(
                "Cannot construct %s for a user with no collection permissions" % type(self)
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

        return super(BaseCollectionMemberForm, self).save(commit=commit)


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

        self.instance = instance

        initial_data = []

        for collection, collection_permissions in groupby(
            instance.collection_permissions.filter(
                permission__in=self.permission_queryset,
            ).order_by('collection'),
            lambda cp: cp.collection
        ):
            initial_data.append({
                'collection': collection,
                'permissions': [cp.permission for cp in collection_permissions]
            })

        super(BaseGroupCollectionMemberPermissionFormSet, self).__init__(
            data, files, initial=initial_data, prefix=prefix
        )
        for form in self.forms:
            form.fields['DELETE'].widget = forms.HiddenInput()

    @property
    def empty_form(self):
        empty_form = super(BaseGroupCollectionMemberPermissionFormSet, self).empty_form
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
            raise forms.ValidationError(
                _("You cannot have multiple permission records for the same collection.")
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
            form for form in self.forms
            if form not in self.deleted_forms and 'collection' in form.cleaned_data
        ]

        final_permission_records = set()
        for form in forms_to_save:
            for permission in form.cleaned_data['permissions']:
                final_permission_records.add((form.cleaned_data['collection'], permission))

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
            self.template,
            {'formset': self},
        )


def collection_member_permission_formset_factory(
    model, permission_types, template, default_prefix=None
):

    permission_queryset = Permission.objects.filter(
        content_type__app_label=model._meta.app_label,
        codename__in=[codename for codename, short_label, long_label in permission_types]
    )

    if default_prefix is None:
        default_prefix = '%s_permissions' % model._meta.model_name

    class CollectionMemberPermissionsForm(forms.Form):
        """
        For a given model with CollectionMember behaviour,
        defines the permissions that are assigned to an entity
        (i.e. group or user) for a specific collection
        """
        collection = forms.ModelChoiceField(
            queryset=Collection.objects.all()
        )
        permissions = forms.ModelMultipleChoiceField(
            queryset=permission_queryset,
            required=False,
            widget=forms.CheckboxSelectMultiple
        )

    GroupCollectionMemberPermissionFormSet = type(
        str('GroupCollectionMemberPermissionFormSet'),
        (BaseGroupCollectionMemberPermissionFormSet, ),
        {
            'permission_types': permission_types,
            'permission_queryset': permission_queryset,
            'default_prefix': default_prefix,
            'template': template,
        }
    )

    return forms.formset_factory(
        CollectionMemberPermissionsForm,
        formset=GroupCollectionMemberPermissionFormSet,
        extra=0,
        can_delete=True
    )
