from __future__ import absolute_import, unicode_literals

from itertools import groupby

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db import transaction
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin.widgets import AdminPageChooser
from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.models import (
    PAGE_PERMISSION_TYPE_CHOICES, PAGE_PERMISSION_TYPES, GroupPagePermission, Page,
    UserPagePermissionsProxy)
from wagtail.wagtailusers.models import UserProfile

User = get_user_model()

# The standard fields each user model is expected to have, as a minimum.
standard_fields = set(['email', 'first_name', 'last_name', 'is_superuser', 'groups'])
# Custom fields
if hasattr(settings, 'WAGTAIL_USER_CUSTOM_FIELDS'):
    custom_fields = set(settings.WAGTAIL_USER_CUSTOM_FIELDS)
else:
    custom_fields = set()


class UsernameForm(forms.ModelForm):
    """
    Intelligently sets up the username field if it is in fact a username. If the
    User model has been swapped out, and the username field is an email or
    something else, don't touch it.
    """
    def __init__(self, *args, **kwargs):
        super(UsernameForm, self).__init__(*args, **kwargs)
        if User.USERNAME_FIELD == 'username':
            field = self.fields['username']
            field.regex = r"^[\w.@+-]+$"
            field.help_text = _("Required. 30 characters or fewer. Letters, "
                                "digits and @/./+/-/_ only.")
            field.error_messages = field.error_messages.copy()
            field.error_messages.update({
                'invalid': _("This value may contain only letters, numbers "
                             "and @/./+/-/_ characters.")})

    @property
    def username_field(self):
        return self[User.USERNAME_FIELD]

    def separate_username_field(self):
        return User.USERNAME_FIELD not in standard_fields


class UserCreationForm(UsernameForm):
    required_css_class = "required"

    error_messages = {
        'duplicate_username': _("A user with that username already exists."),
        'password_mismatch': _("The two password fields didn't match."),
    }

    is_superuser = forms.BooleanField(
        label=_("Administrator"),
        required=False,
        help_text=_("Administrators have full access to manage any object or setting.")
    )

    password1 = forms.CharField(
        label=_("Password"),
        required=False,
        widget=forms.PasswordInput,
        help_text=_("Leave blank if not changing."))
    password2 = forms.CharField(
        label=_("Password confirmation"), required=False,
        widget=forms.PasswordInput,
        help_text=_("Enter the same password as above, for verification."))

    email = forms.EmailField(required=True, label=_("Email"))
    first_name = forms.CharField(required=True, label=_("First Name"))
    last_name = forms.CharField(required=True, label=_("Last Name"))

    class Meta:
        model = User
        fields = set([User.USERNAME_FIELD]) | standard_fields | custom_fields
        widgets = {
            'groups': forms.CheckboxSelectMultiple
        }

    def clean_username(self):
        username_field = User.USERNAME_FIELD
        username = self.cleaned_data[username_field]
        try:
            User._default_manager.get(**{username_field: username})
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(
            self.error_messages['duplicate_username'],
            code='duplicate_username',
        )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        # users can access django-admin iff they are a superuser
        user.is_staff = user.is_superuser

        if commit:
            user.save()
            self.save_m2m()
        return user


# Largely the same as django.contrib.auth.forms.UserCreationForm, but with enough subtle changes
# (to make password non-required) that it isn't worth inheriting...
class UserEditForm(UsernameForm):
    required_css_class = "required"

    error_messages = {
        'duplicate_username': _("A user with that username already exists."),
        'password_mismatch': _("The two password fields didn't match."),
    }

    email = forms.EmailField(required=True, label=_("Email"))
    first_name = forms.CharField(required=True, label=_("First Name"))
    last_name = forms.CharField(required=True, label=_("Last Name"))

    password1 = forms.CharField(
        label=_("Password"),
        required=False,
        widget=forms.PasswordInput,
        help_text=_("Leave blank if not changing."))
    password2 = forms.CharField(
        label=_("Password confirmation"), required=False,
        widget=forms.PasswordInput,
        help_text=_("Enter the same password as above, for verification."))

    is_superuser = forms.BooleanField(
        label=_("Administrator"),
        required=False,
        help_text=_("Administrators have full access to manage any object or setting.")
    )

    class Meta:
        model = User
        fields = set([User.USERNAME_FIELD, "is_active"]) | standard_fields | custom_fields
        widgets = {
            'groups': forms.CheckboxSelectMultiple
        }

    def clean_username(self):
        # Since User.username is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        username = self.cleaned_data["username"]
        username_field = User.USERNAME_FIELD
        try:
            User._default_manager.exclude(pk=self.instance.pk).get(**{
                username_field: username})
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(self.error_messages['duplicate_username'])

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'])
        return password2

    def save(self, commit=True):
        user = super(UserEditForm, self).save(commit=False)

        # users can access django-admin iff they are a superuser
        user.is_staff = user.is_superuser

        if self.cleaned_data["password1"]:
            user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            self.save_m2m()
        return user


class GroupForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)
        self.registered_permissions = Permission.objects.none()
        for fn in hooks.get_hooks('register_permissions'):
            self.registered_permissions = self.registered_permissions | fn()
        self.fields['permissions'].queryset = self.registered_permissions

    required_css_class = "required"

    error_messages = {
        'duplicate_name': _("A group with that name already exists."),
    }

    is_superuser = forms.BooleanField(
        label=_("Administrator"),
        required=False,
        help_text=_("Administrators have full access to manage any object or setting.")
    )

    class Meta:
        model = Group
        fields = ("name", "permissions", )

    def clean_name(self):
        # Since Group.name is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        name = self.cleaned_data["name"]
        try:
            Group._default_manager.exclude(pk=self.instance.pk).get(name=name)
        except Group.DoesNotExist:
            return name
        raise forms.ValidationError(self.error_messages['duplicate_name'])

    def save(self):
        # We go back to the object to read (in order to reapply) the
        # permissions which were set on this group, but which are not
        # accessible in the wagtail admin interface, as otherwise these would
        # be clobbered by this form.
        try:
            untouchable_permissions = self.instance.permissions.exclude(pk__in=self.registered_permissions)
            bool(untouchable_permissions)  # force this to be evaluated, as it's about to change
        except ValueError:
            # this form is not bound; we're probably creating a new group
            untouchable_permissions = []
        group = super(GroupForm, self).save()
        group.permissions.add(*untouchable_permissions)
        return group


class PagePermissionsForm(forms.Form):
    """
    Note 'Permissions' (plural). A single instance of this form defines the permissions
    that are assigned to an entity (i.e. group or user) for a specific page.
    """
    page = forms.ModelChoiceField(
        queryset=Page.objects.all(),
        widget=AdminPageChooser(show_edit_link=False, can_choose_root=True)
    )
    permission_types = forms.MultipleChoiceField(
        choices=PAGE_PERMISSION_TYPE_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple
    )


class BaseGroupPagePermissionFormSet(forms.BaseFormSet):
    permission_types = PAGE_PERMISSION_TYPES  # defined here for easy access from templates

    def __init__(self, data=None, files=None, instance=None, prefix='page_permissions'):
        if instance is None:
            instance = Group()

        self.instance = instance

        initial_data = []

        for page, page_permissions in groupby(
            instance.page_permissions.order_by('page'), lambda pp: pp.page
        ):
            initial_data.append({
                'page': page,
                'permission_types': [pp.permission_type for pp in page_permissions]
            })

        super(BaseGroupPagePermissionFormSet, self).__init__(
            data, files, initial=initial_data, prefix=prefix
        )
        for form in self.forms:
            form.fields['DELETE'].widget = forms.HiddenInput()

    @property
    def empty_form(self):
        empty_form = super(BaseGroupPagePermissionFormSet, self).empty_form
        empty_form.fields['DELETE'].widget = forms.HiddenInput()
        return empty_form

    def clean(self):
        """Checks that no two forms refer to the same page object"""
        if any(self.errors):
            # Don't bother validating the formset unless each form is valid on its own
            return

        pages = [
            form.cleaned_data['page']
            for form in self.forms
            # need to check for presence of 'page' in cleaned_data,
            # because a completely blank form passes validation
            if form not in self.deleted_forms and 'page' in form.cleaned_data
        ]
        if len(set(pages)) != len(pages):
            # pages list contains duplicates
            raise forms.ValidationError(_("You cannot have multiple permission records for the same page."))

    @transaction.atomic
    def save(self):
        if self.instance.pk is None:
            raise Exception(
                "Cannot save a GroupPagePermissionFormSet for an unsaved group instance"
            )

        # get a set of (page, permission_type) tuples for all ticked permissions
        forms_to_save = [
            form for form in self.forms
            if form not in self.deleted_forms and 'page' in form.cleaned_data
        ]

        final_permission_records = set()
        for form in forms_to_save:
            for permission_type in form.cleaned_data['permission_types']:
                final_permission_records.add((form.cleaned_data['page'], permission_type))

        # fetch the group's existing page permission records, and from that, build a list
        # of records to be created / deleted
        permission_ids_to_delete = []
        permission_records_to_keep = set()

        for pp in self.instance.page_permissions.all():
            if (pp.page, pp.permission_type) in final_permission_records:
                permission_records_to_keep.add((pp.page, pp.permission_type))
            else:
                permission_ids_to_delete.append(pp.pk)

        self.instance.page_permissions.filter(pk__in=permission_ids_to_delete).delete()

        permissions_to_add = final_permission_records - permission_records_to_keep
        GroupPagePermission.objects.bulk_create([
            GroupPagePermission(
                group=self.instance, page=page, permission_type=permission_type
            )
            for (page, permission_type) in permissions_to_add
        ])

    def as_admin_panel(self):
        return render_to_string('wagtailusers/groups/includes/page_permissions_formset.html', {
            'formset': self
        })


GroupPagePermissionFormSet = forms.formset_factory(
    PagePermissionsForm, formset=BaseGroupPagePermissionFormSet, extra=0, can_delete=True
)


class NotificationPreferencesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NotificationPreferencesForm, self).__init__(*args, **kwargs)
        user_perms = UserPagePermissionsProxy(self.instance.user)
        if not user_perms.can_publish_pages():
            del self.fields['submitted_notifications']
        if not user_perms.can_edit_pages():
            del self.fields['approved_notifications']
            del self.fields['rejected_notifications']

    class Meta:
        model = UserProfile
        fields = ("submitted_notifications", "approved_notifications", "rejected_notifications")
