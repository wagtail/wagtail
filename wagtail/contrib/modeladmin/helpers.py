from __future__ import absolute_import, unicode_literals

from django.contrib.admin.utils import quote
from django.contrib.auth import get_permission_codename
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.utils.encoding import force_text
from django.utils.functional import cached_property
from django.utils.http import urlquote
from django.utils.translation import ugettext as _

from wagtail.wagtailcore.models import Page, UserPagePermissionsProxy


class AdminURLHelper(object):

    def __init__(self, model):
        self.model = model
        self.opts = model._meta

    def _get_action_url_pattern(self, action):
        if action == 'index':
            return r'^%s/%s/$' % (self.opts.app_label, self.opts.model_name)
        return r'^%s/%s/%s/$' % (self.opts.app_label, self.opts.model_name,
                                 action)

    def _get_object_specific_action_url_pattern(self, action):
        return r'^%s/%s/%s/(?P<instance_pk>[-\w]+)/$' % (
            self.opts.app_label, self.opts.model_name, action)

    def get_action_url_pattern(self, action):
        if action in ('create', 'choose_parent', 'index'):
            return self._get_action_url_pattern(action)
        return self._get_object_specific_action_url_pattern(action)

    def get_action_url_name(self, action):
        return '%s_%s_modeladmin_%s' % (
            self.opts.app_label, self.opts.model_name, action)

    def get_action_url(self, action, *args, **kwargs):
        if action in ('create', 'choose_parent', 'index'):
            return reverse(self.get_action_url_name(action))
        url_name = self.get_action_url_name(action)
        return reverse(url_name, args=args, kwargs=kwargs)

    @cached_property
    def index_url(self):
        return self.get_action_url('index')

    @cached_property
    def create_url(self):
        return self.get_action_url('create')


class PageAdminURLHelper(AdminURLHelper):

    def get_action_url(self, action, *args, **kwargs):
        if action in ('add', 'edit', 'delete', 'unpublish', 'copy'):
            url_name = 'wagtailadmin_pages:%s' % action
            target_url = reverse(url_name, args=args, kwargs=kwargs)
            return '%s?next=%s' % (target_url, urlquote(self.index_url))
        return super(PageAdminURLHelper, self).get_action_url(action, *args,
                                                              **kwargs)


class PermissionHelper(object):
    """
    Provides permission-related helper functions to help determine what a
    user can do with a 'typical' model (where permissions are granted
    model-wide), and to a specific instance of that model.
    """

    def __init__(self, model, inspect_view_enabled=False):
        self.model = model
        self.opts = model._meta
        self.inspect_view_enabled = inspect_view_enabled

    def get_all_model_permissions(self):
        """
        Return a queryset of all Permission objects pertaining to the `model`
        specified at initialisation.
        """

        return Permission.objects.filter(
            content_type__app_label=self.opts.app_label,
            content_type__model=self.opts.model_name,
        )

    def get_perm_codename(self, action):
        return get_permission_codename(action, self.opts)

    def user_has_specific_permission(self, user, perm_codename):
        """
        Combine `perm_codename` with `self.opts.app_label` to call the provided
        Django user's built-in `has_perm` method.
        """

        return user.has_perm("%s.%s" % (self.opts.app_label, perm_codename))

    def user_has_any_permissions(self, user):
        """
        Return a boolean to indicate whether `user` has any model-wide
        permissions
        """
        for perm in self.get_all_model_permissions().values('codename'):
            if self.user_has_specific_permission(user, perm['codename']):
                return True
        return False

    def user_can_list(self, user):
        """
        Return a boolean to indicate whether `user` is permitted to access the
        list view for self.model
        """
        return self.user_has_any_permissions(user)

    def user_can_create(self, user):
        """
        Return a boolean to indicate whether `user` is permitted to create new
        instances of `self.model`
        """
        perm_codename = self.get_perm_codename('add')
        return self.user_has_specific_permission(user, perm_codename)

    def user_can_inspect_obj(self, user, obj):
        """
        Return a boolean to indicate whether `user` is permitted to 'inspect'
        a specific `self.model` instance.
        """
        return self.inspect_view_enabled and self.user_has_any_permissions(
            user)

    def user_can_edit_obj(self, user, obj):
        """
        Return a boolean to indicate whether `user` is permitted to 'change'
        a specific `self.model` instance.
        """
        perm_codename = self.get_perm_codename('change')
        return self.user_has_specific_permission(user, perm_codename)

    def user_can_delete_obj(self, user, obj):
        """
        Return a boolean to indicate whether `user` is permitted to 'delete'
        a specific `self.model` instance.
        """
        perm_codename = self.get_perm_codename('delete')
        return self.user_has_specific_permission(user, perm_codename)

    def user_can_unpublish_obj(self, user, obj):
        return False

    def user_can_copy_obj(self, user, obj):
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
        # Get queryset of pages where this page type can be added
        allowed_parent_page_content_types = list(ContentType.objects.get_for_models(*self.model.allowed_parent_page_models()).values())
        allowed_parent_pages = Page.objects.filter(content_type__in=allowed_parent_page_content_types)

        # Get queryset of pages where the user has permission to add subpages
        if user.is_superuser:
            pages_where_user_can_add = Page.objects.all()
        else:
            pages_where_user_can_add = Page.objects.none()
            user_perms = UserPagePermissionsProxy(user)

            for perm in user_perms.permissions.filter(permission_type='add'):
                # user has add permission on any subpage of perm.page
                # (including perm.page itself)
                pages_where_user_can_add |= Page.objects.descendant_of(perm.page, inclusive=True)

        # Combine them
        return allowed_parent_pages & pages_where_user_can_add

    def user_can_list(self, user):
        """
        For models extending Page, permitted actions are determined by
        permissions on individual objects. Rather than check for change
        permissions on every object individually (which would be quite
        resource intensive), we simply always allow the list view to be
        viewed, and limit further functionality when relevant.
        """
        return True

    def user_can_create(self, user):
        """
        For models extending Page, whether or not a page of this type can be
        added somewhere in the tree essentially determines the add permission,
        rather than actual model-wide permissions
        """
        return self.get_valid_parent_pages(user).exists()

    def user_can_edit_obj(self, user, obj):
        perms = obj.permissions_for_user(user)
        return perms.can_edit()

    def user_can_delete_obj(self, user, obj):
        perms = obj.permissions_for_user(user)
        return perms.can_delete()

    def user_can_publish_obj(self, user, obj):
        perms = obj.permissions_for_user(user)
        return obj.live and perms.can_unpublish()

    def user_can_copy_obj(self, user, obj):
        parent_page = obj.get_parent()
        return parent_page.permissions_for_user(user).can_publish_subpage()


class ButtonHelper(object):

    default_button_classnames = ['button']
    add_button_classnames = ['bicolor', 'icon', 'icon-plus']
    inspect_button_classnames = []
    edit_button_classnames = []
    delete_button_classnames = ['no']

    def __init__(self, view, request):
        self.view = view
        self.request = request
        self.model = view.model
        self.opts = view.model._meta
        self.verbose_name = force_text(self.opts.verbose_name)
        self.verbose_name_plural = force_text(self.opts.verbose_name_plural)
        self.permission_helper = view.permission_helper
        self.url_helper = view.url_helper

    def finalise_classname(self, classnames_add=None, classnames_exclude=None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        combined = self.default_button_classnames + classnames_add
        finalised = [cn for cn in combined if cn not in classnames_exclude]
        return ' '.join(finalised)

    def add_button(self, classnames_add=None, classnames_exclude=None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        classnames = self.add_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': self.url_helper.create_url,
            'label': _('Add %s') % self.verbose_name,
            'classname': cn,
            'title': _('Add a new %s') % self.verbose_name,
        }

    def inspect_button(self, pk, classnames_add=None, classnames_exclude=None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        classnames = self.inspect_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': self.url_helper.get_action_url('inspect', quote(pk)),
            'label': _('Inspect'),
            'classname': cn,
            'title': _('Inspect this %s') % self.verbose_name,
        }

    def edit_button(self, pk, classnames_add=None, classnames_exclude=None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        classnames = self.edit_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': self.url_helper.get_action_url('edit', quote(pk)),
            'label': _('Edit'),
            'classname': cn,
            'title': _('Edit this %s') % self.verbose_name,
        }

    def delete_button(self, pk, classnames_add=None, classnames_exclude=None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        classnames = self.delete_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': self.url_helper.get_action_url('delete', quote(pk)),
            'label': _('Delete'),
            'classname': cn,
            'title': _('Delete this %s') % self.verbose_name,
        }

    def get_buttons_for_obj(self, obj, exclude=None, classnames_add=None,
                            classnames_exclude=None):
        if exclude is None:
            exclude = []
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        ph = self.permission_helper
        usr = self.request.user
        pk = quote(getattr(obj, self.opts.pk.attname))
        btns = []
        if('inspect' not in exclude and ph.user_can_inspect_obj(usr, obj)):
            btns.append(
                self.inspect_button(pk, classnames_add, classnames_exclude)
            )
        if('edit' not in exclude and ph.user_can_edit_obj(usr, obj)):
            btns.append(
                self.edit_button(pk, classnames_add, classnames_exclude)
            )
        if('delete' not in exclude and ph.user_can_delete_obj(usr, obj)):
            btns.append(
                self.delete_button(pk, classnames_add, classnames_exclude)
            )
        return btns


class PageButtonHelper(ButtonHelper):

    unpublish_button_classnames = []
    copy_button_classnames = []

    def unpublish_button(self, pk, classnames_add=None, classnames_exclude=None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        classnames = self.unpublish_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': self.url_helper.get_action_url('unpublish', quote(pk)),
            'label': _('Unpublish'),
            'classname': cn,
            'title': _('Unpublish this %s') % self.verbose_name,
        }

    def copy_button(self, pk, classnames_add=None, classnames_exclude=None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        classnames = self.copy_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': self.url_helper.get_action_url('copy', quote(pk)),
            'label': _('Copy'),
            'classname': cn,
            'title': _('Copy this %s') % self.verbose_name,
        }

    def get_buttons_for_obj(self, obj, exclude=None, classnames_add=None,
                            classnames_exclude=None):
        if exclude is None:
            exclude = []
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        ph = self.permission_helper
        usr = self.request.user
        pk = quote(getattr(obj, self.opts.pk.attname))
        btns = []
        if('inspect' not in exclude and ph.user_can_inspect_obj(usr, obj)):
            btns.append(
                self.inspect_button(pk, classnames_add, classnames_exclude)
            )
        if('edit' not in exclude and ph.user_can_edit_obj(usr, obj)):
            btns.append(
                self.edit_button(pk, classnames_add, classnames_exclude)
            )
        if('copy' not in exclude and ph.user_can_copy_obj(usr, obj)):
            btns.append(
                self.copy_button(pk, classnames_add, classnames_exclude)
            )
        if('unpublish' not in exclude and ph.user_can_unpublish_obj(usr, obj)):
            btns.append(
                self.unpublish_button(pk, classnames_add, classnames_exclude)
            )
        if('delete' not in exclude and ph.user_can_delete_obj(usr, obj)):
            btns.append(
                self.delete_button(pk, classnames_add, classnames_exclude)
            )
        return btns
