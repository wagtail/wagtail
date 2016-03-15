from django.contrib.auth import get_permission_codename
from django.utils.translation import ugettext as _
from django.utils.encoding import force_text
from django.contrib.admin.utils import quote
from django.core.urlresolvers import reverse
from wagtail.wagtailcore.models import Page


class PermissionHelper(object):
    """
    Provides permission-related helper functions to effectively control what
    a user can and can't do to instances of a 'typical' model, where
    permissions are granted model-wide.
    """

    def __init__(self, model):
        self.model = model
        self.opts = model._meta

    def has_add_permission(self, user):
        """
        For typical models, whether or not a user can add an object depends
        on their permissions on that model
        """
        return user.has_perm("%s.%s" % (
            self.opts.app_label, get_permission_codename('add', self.opts)
        ))

    def has_edit_permission(self, user):
        """
        For typical models, whether or not a user can edit an object depends
        on their permissions on that model
        """
        return user.has_perm("%s.%s" % (
            self.opts.app_label, get_permission_codename('change', self.opts)
        ))

    def has_delete_permission(self, user):
        """
        For typical models, whether or not a user can delete an object depends
        on their permissions on that model
        """
        return user.has_perm("%s.%s" % (
            self.opts.app_label, get_permission_codename('delete', self.opts)
        ))

    def can_edit_object(self, user, obj):
        """
        Used from within templates to decide what functionality to allow
        for a specific object. For typical models, we just return the
        model-wide permission.
        """
        return self.has_edit_permission(user)

    def can_delete_object(self, user, obj):
        """
        Used from within templates to decide what functionality to allow
        for a specific object. For typical models, we just return the
        model-wide permission.
        """
        return self.has_delete_permission(user)

    def can_unpublish_object(self, user, obj):
        """
        'Unpublishing' isn't really a valid option for models not extending
        Page, so we always return False
        """
        return False

    def can_copy_object(self, user, obj):
        """
        'Copying' isn't really a valid option for models not extending
        Page, so we always return False
        """
        return False

    def allow_list_view(self, user):
        """
        For typical models, we only want to allow viewing of the list page
        if the user has permission to do something
        """
        if (
            self.has_add_permission(user) or
            self.has_edit_permission(user) or
            self.has_delete_permission(user)
        ):
            return True
        return False


class PagePermissionHelper(PermissionHelper):
    """
    Provides permission-related helper functions to effectively control what
    a user can and can't do to instances of a model extending Wagtail's Page
    model. It differs wildly from ModelPermissionHelper, because
    model-wide permissions aren't really relevant. We generally need to
    determine things on an object-specific basis.
    """

    def has_add_permission(self, user):
        """
        For models extending Page, whether or not a page of this type can be
        added somewhere in the tree essentially determines the add permission,
        rather than actual model-wide permissions
        """
        return bool(self.get_valid_parent_pages(user).count())

    def get_valid_parent_pages(self, user):
        """
        Identifies possible parent pages for the current user by first looking
        at allowed_parent_page_types() on self.model to limit options to the
        correct type of page, then checking permissions on those individual
        pages to make sure we have permission to add a subpage to it.
        """
        # Start with empty qs
        parents_qs = Page.objects.none()

        # Add pages of the correct type
        valid_parent_types = self.model.allowed_parent_page_types()
        for pt in valid_parent_types:
            pt_items = Page.objects.type(pt.model_class())
            parents_qs = parents_qs | pt_items

        # Exclude pages that we can't add subpages to
        for page in parents_qs.all():
            if not page.permissions_for_user(user).can_add_subpage():
                parents_qs = parents_qs.exclude(pk=page.pk)

        return parents_qs

    def can_edit_object(self, user, obj):
        perms = obj.permissions_for_user(user)
        return perms.can_edit()

    def can_delete_object(self, user, obj):
        perms = obj.permissions_for_user(user)
        return perms.can_delete()

    def can_unpublish_object(self, user, obj):
        perms = obj.permissions_for_user(user)
        return obj.live and perms.can_unpublish()

    def can_copy_object(self, user, obj):
        parent_page = obj.get_parent()
        return parent_page.permissions_for_user(user).can_publish_subpage()

    def allow_list_view(self, user):
        """
        For models extending Page, permitted actions are determined by
        permissions on individual objects. Rather than check for change
        permissions on every object individually (which would be quite
        resource intensive), we simply always allow the list view to be
        viewed, and limit further functionality when relevant.
        """
        return True


def get_url_pattern(model_meta, action=None):
    if not action:
        return r'^modeladmin/%s/%s/$' % (
            model_meta.app_label, model_meta.model_name)
    return r'^modeladmin/%s/%s/%s/$' % (
        model_meta.app_label, model_meta.model_name, action)


def get_object_specific_url_pattern(model_meta, action):
    return r'^modeladmin/%s/%s/%s/(?P<object_id>[-\w]+)/$' % (
        model_meta.app_label, model_meta.model_name, action)


def get_url_name(model_meta, action='index'):
    return '%s_%s_modeladmin_%s/' % (
        model_meta.app_label, model_meta.model_name, action)


class ButtonHelper(object):

    default_button_classname = 'button button-small button-secondary'

    def __init__(self, model, permission_helper, user,
                 inspect_view_enabled=False):
        self.user = user
        self.model = model
        self.opts = model._meta
        self.permission_helper = permission_helper
        self.inspect_view_enabled = inspect_view_enabled
        self.model_name = force_text(self.opts.verbose_name).lower()

    def get_action_url(self, action='create', pk=None):
        kwargs = {}
        if pk and action not in ('create', 'index'):
            kwargs.update({'object_id': pk})
        return reverse(get_url_name(self.opts, action), kwargs=kwargs)

    def add_button(self):
        return {
            'url': self.get_action_url('create'),
            'label': _('Add %s') % self.model_name,
            'classname': self.default_button_classname,
            'title': _('Add a new %s') % self.model_name,
        }

    def inspect_button(self, pk):
        return {
            'url': self.get_action_url('inspect', pk),
            'label': _('Inspect'),
            'classname': self.default_button_classname,
            'title': _('View details for this %s') % self.model_name,
        }

    def edit_button(self, pk):
        return {
            'url': self.get_action_url('edit', pk),
            'label': _('Edit'),
            'classname': self.default_button_classname,
            'title': _('Edit this %s') % self.model_name,
        }

    def delete_button(self, pk):
        return {
            'url': self.get_action_url('confirm_delete', pk),
            'label': _('Delete'),
            'classname': self.default_button_classname + ' no',
            'title': _('Delete this %s') % self.model_name,
        }

    def get_buttons_for_obj(self, obj, allow_inspect_button=True):
        user = self.user
        pk = quote(getattr(obj, self.opts.pk.attname))
        buttons = []
        if self.inspect_view_enabled and allow_inspect_button:
            buttons.append(self.inspect_button(pk))
        if self.permission_helper.can_edit_object(user, obj):
            buttons.append(self.edit_button(pk))
        if self.permission_helper.can_delete_object(user, obj):
            buttons.append(self.delete_button(pk))
        return buttons

    def get_inspect_view_buttons(self, obj):
        buttons = self.get_buttons_for_obj(obj, False)
        for button in buttons:
            button['classname'] = button['classname'].replace('button-secondary', '').replace('button-small', '')
        return buttons


class PageButtonHelper(ButtonHelper):

    def unpublish_button(self, pk):
        return {
            'url': self.get_action_url('unpublish', pk),
            'label': _('Unpublish'),
            'classname': self.default_button_classname + ' icon-cog',
            'title': _('Unpublish this %s') % self.model_name,
        }

    def copy_button(self, pk):
        return {
            'url': self.get_action_url('copy', pk),
            'label': _('Copy'),
            'classname': self.default_button_classname + ' icon-plus-inverse',
            'title': _('Copy this %s') % self.model_name,
        }

    def get_buttons_for_obj(self, obj, allow_inspect_button=True):
        user = self.user
        pk = quote(getattr(obj, self.opts.pk.attname))
        buttons = []
        if self.inspect_view_enabled and allow_inspect_button:
            buttons.append(self.inspect_button(pk))
        if self.permission_helper.can_edit_object(user, obj):
            buttons.append(self.edit_button(pk))
        if self.permission_helper.can_copy_object(user, obj):
            buttons.append(self.copy_button(pk))
        if self.permission_helper.can_unpublish_object(user, obj):
            buttons.append(self.unpublish_button(pk))
        if self.permission_helper.can_delete_object(user, obj):
            buttons.append(self.delete_button(pk))
        return buttons
