import urllib
from django.contrib.auth import get_permission_codename
from django.contrib.auth.models import Permission
from django.utils.translation import ugettext as _
from django.utils.encoding import force_text
from django.contrib.admin.utils import quote
from django.core.urlresolvers import reverse
from wagtail.wagtailcore.models import Page


class PermissionHelper(object):
    """
    Provides permission-related helper functions to help determine what a 
    user can do with a 'typical' model (where permissions are granted
    model-wide).
    """

    def __init__(self, model):
        self.model = model
        self.opts = model._meta

    def get_all_model_permissions(self):
        return Permission.objects.filter(
            content_type__app_label=self.opts.app_label,
            content_type__model=self.opts.model_name,
        )

    def has_specific_permission(self, user, codename):
        return user.has_perm("%s.%s" % (self.opts.app_label, codename))

    def has_any_permissions(self, user):
        """
        Return a boolean to indicate whether the supplied user has any
        permissions at all on the associated model
        """
        for perm in self.get_all_model_permissions():
            if self.has_specific_permission(user, perm.codename):
                return True
        return False

    def has_add_permission(self, user):
        """
        For typical models, whether or not a user can add an object depends
        on their permissions on that model
        """
        return self.has_specific_permission(
            user, get_permission_codename('add', self.opts))

    def has_edit_permission(self, user):
        """
        For typical models, whether or not a user can edit an object depends
        on their permissions on that model
        """
        return self.has_specific_permission(
            user, get_permission_codename('change', self.opts))

    def has_delete_permission(self, user):
        """
        For typical models, whether or not a user can delete an object depends
        on their permissions on that model
        """
        return self.has_specific_permission(
            user, get_permission_codename('delete', self.opts))

    def has_list_permission(self, user):
        return self.has_any_permissions(user)

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


class PagePermissionHelper(PermissionHelper):
    """
    Provides permission-related helper functions to help determine what 
    a user can do with a model extending Wagtail's Page model. It differs
    from `PermissionHelper`, because model-wide permissions aren't really
    relevant. We generally need to determine permissions on an 
    object-specific basis.
    """

    def get_valid_parent_pages(self, user):
        """
        Identifies possible parent pages for the current user by first looking
        at allowed_parent_page_models() on self.model to limit options to the
        correct type of page, then checking permissions on those individual
        pages to make sure we have permission to add a subpage to it.
        """
        # Start with empty qs
        parents_qs = Page.objects.none()

        # Add pages of the correct type
        for pt in self.model.allowed_parent_page_models():
            pt_items = Page.objects.type(pt)
            parents_qs = parents_qs | pt_items

        # Exclude pages that we can't add subpages to
        for page in parents_qs.all():
            if not page.permissions_for_user(user).can_add_subpage():
                parents_qs = parents_qs.exclude(pk=page.pk)

        return parents_qs

    def has_list_permssion(self, user):
        """
        For models extending Page, permitted actions are determined by
        permissions on individual objects. Rather than check for change
        permissions on every object individually (which would be quite
        resource intensive), we simply always allow the list view to be
        viewed, and limit further functionality when relevant.
        """
        return True

    def has_add_permission(self, user):
        """
        For models extending Page, whether or not a page of this type can be
        added somewhere in the tree essentially determines the add permission,
        rather than actual model-wide permissions
        """
        return self.get_valid_parent_pages(user).count() > 0

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

    default_button_classnames = ['button']
    add_button_classnames = ['bicolor', 'icon', 'icon-plus']
    inspect_button_classnames = []
    edit_button_classnames = []
    delete_button_classnames = ['no']

    def __init__(self, model, permission_helper, user,
                 inspect_view_enabled=False):
        self.user = user
        self.model = model
        self.opts = model._meta
        self.permission_helper = permission_helper
        self.inspect_view_enabled = inspect_view_enabled
        self.model_name = force_text(self.opts.verbose_name).lower()

    def finalise_classname(self, classnames_add=[], classnames_exclude=[]):
        combined = self.default_button_classnames + classnames_add
        finalised = [cn for cn in combined if cn not in classnames_exclude]
        return ' '.join(finalised)

    def get_action_url(self, action='index', pk=None):
        kwargs = {}
        if pk and action not in ('create', 'index'):
            kwargs.update({'object_id': pk})
        return reverse(get_url_name(self.opts, action), kwargs=kwargs)

    def show_add_button(self):
        return self.permission_helper.had_add_permission(self.user)

    def add_button(self, classnames_add=[], classnames_exclude=[]):
        classnames = self.add_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': self.get_action_url('create'),
            'label': _('Add %s') % self.model_name,
            'classname': cn,
            'title': _('Add a new %s') % self.model_name,
        }

    def inspect_button(self, pk, classnames_add=[], classnames_exclude=[]):
        classnames = self.inspect_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': self.get_action_url('inspect', pk),
            'label': _('Inspect'),
            'classname': cn,
            'title': _('View details for this %s') % self.model_name,
        }

    def edit_button(self, pk, classnames_add=[], classnames_exclude=[]):
        classnames = self.edit_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': self.get_action_url('edit', pk),
            'label': _('Edit'),
            'classname': cn,
            'title': _('Edit this %s') % self.model_name,
        }

    def delete_button(self, pk, classnames_add=[], classnames_exclude=[]):
        classnames = self.delete_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': self.get_action_url('confirm_delete', pk),
            'label': _('Delete'),
            'classname': cn,
            'title': _('Delete this %s') % self.model_name,
        }

    def get_buttons_for_obj(self, obj, exclude=[], classnames_add=[],
                            classnames_exclude=[]):
        ph = self.permission_helper
        pk = quote(getattr(obj, self.opts.pk.attname))
        btns = []
        if('inspect' not in exclude and self.inspect_view_enabled):
            btns.append(
                self.inspect_button(pk, classnames_add, classnames_exclude)
            )
        if('edit' not in exclude and ph.can_edit_object(self.user, obj)):
            btns.append(
                self.edit_button(pk, classnames_add, classnames_exclude)
            )
        if('delete' not in exclude and ph.can_delete_object(self.user, obj)):
            btns.append(
                self.delete_button(pk, classnames_add, classnames_exclude)
            )
        return btns


class PageButtonHelper(ButtonHelper):

    unpublish_button_classnames = []
    copy_button_classnmes = []

    def get_action_url(self, action='index', pk=None):
        if action not in ('create', 'index', 'inspect'):
            target_url = reverse('wagtailadmin_pages:%s' % action, args=[pk])
            next_url = urllib.quote(self.get_action_url('index'))
            return '%s?next=%s' % (target_url, next_url)
        return super(PageButtonHelper, self).get_action_url(action, pk)

    def unpublish_button(self, pk, classnames_add=[], classnames_exclude=[]):
        classnames = self.unpublish_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': self.get_action_url('unpublish', pk),
            'label': _('Unpublish'),
            'classname': cn,
            'title': _('Unpublish this %s') % self.model_name,
        }

    def copy_button(self, pk, classnames_add=[], classnames_exclude=[]):
        classnames = self.copy_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': self.get_action_url('copy', pk),
            'label': _('Copy'),
            'classname': cn,
            'title': _('Copy this %s') % self.model_name,
        }

    def get_buttons_for_obj(self, obj, exclude=[], classnames_add=[],
                            classnames_exclude=[]):
        user = self.user
        ph = self.permission_helper
        pk = quote(getattr(obj, self.opts.pk.attname))
        btns = []
        if('inspect' not in exclude and self.inspect_view_enabled):
            btns.append(
                self.inspect_button(pk, classnames_add, classnames_exclude)
            )
        if('edit' not in exclude and ph.can_edit_object(user, obj)):
            btns.append(
                self.edit_button(pk, classnames_add, classnames_exclude)
            )
        if('copy' not in exclude and ph.can_copy_object(user, obj)):
            btns.append(
                self.copy_button(pk, classnames_add, classnames_exclude)
            )
        if('unpublish' not in exclude and ph.can_unpublish_object(user, obj)):
            btns.append(
                self.unpublish_button(pk, classnames_add, classnames_exclude)
            )
        if('delete' not in exclude and ph.can_delete_object(user, obj)):
            btns.append(
                self.delete_button(pk, classnames_add, classnames_exclude)
            )
        return btns
