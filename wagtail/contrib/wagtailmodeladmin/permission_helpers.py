from django.contrib.auth import get_permission_codename
from wagtail.wagtailcore.models import Page


class PermissionHelper(object):
    """
    Provides permission-related helper functions to effectively control what
    what a user can and can't do to instances of a 'typical' model, where
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
    what a user can and can't do to instances of a model extending Wagtail's
    Page model. It differs wildly from ModelPermissionHelper, because
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
