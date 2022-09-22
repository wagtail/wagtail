from django.contrib.auth import get_permission_codename
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property

from wagtail.models import Page, UserPagePermissionsProxy


class PermissionHelper:
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

    @cached_property
    def all_permission_codenames(self):
        return list(
            self.get_all_model_permissions()
            .values_list("codename", flat=True)
            .distinct()
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
        for perm_codename in self.all_permission_codenames:
            if self.user_has_specific_permission(user, perm_codename):
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
        perm_codename = self.get_perm_codename("add")
        return self.user_has_specific_permission(user, perm_codename)

    def user_can_inspect_obj(self, user, obj):
        """
        Return a boolean to indicate whether `user` is permitted to 'inspect'
        a specific `self.model` instance.
        """
        return self.inspect_view_enabled and self.user_has_any_permissions(user)

    def user_can_edit_obj(self, user, obj):
        """
        Return a boolean to indicate whether `user` is permitted to 'change'
        a specific `self.model` instance.
        """
        perm_codename = self.get_perm_codename("change")
        return self.user_has_specific_permission(user, perm_codename)

    def user_can_delete_obj(self, user, obj):
        """
        Return a boolean to indicate whether `user` is permitted to 'delete'
        a specific `self.model` instance.
        """
        perm_codename = self.get_perm_codename("delete")
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
        allowed_parent_page_content_types = list(
            ContentType.objects.get_for_models(
                *self.model.allowed_parent_page_models()
            ).values()
        )
        allowed_parent_pages = Page.objects.filter(
            content_type__in=allowed_parent_page_content_types
        )

        # Get queryset of pages where the user has permission to add subpages
        if user.is_superuser:
            pages_where_user_can_add = Page.objects.all()
        else:
            pages_where_user_can_add = Page.objects.none()
            user_perms = UserPagePermissionsProxy(user)

            for perm in user_perms.permissions.filter(permission_type="add"):
                # user has add permission on any subpage of perm.page
                # (including perm.page itself)
                pages_where_user_can_add |= Page.objects.descendant_of(
                    perm.page, inclusive=True
                )

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
