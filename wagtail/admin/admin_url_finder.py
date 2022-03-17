from django.contrib.admin.utils import quote
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse

from wagtail.hooks import search_for_hooks
from wagtail.utils.registry import ObjectTypeRegistry

"""
A mechanism for finding the admin edit URL for an arbitrary object instance, optionally applying
permission checks.

    url_finder = AdminURLFinder(request.user)
    url_finder.get_edit_url(some_page)  # => "/admin/pages/123/edit/"
    url_finder.get_edit_url(some_image)  # => "/admin/images/456/"
    url_finder.get_edit_url(some_site)  # => None (user does not have edit permission for sites)

If the user parameter is omitted, edit URLs are returned without considering permissions.

Handlers for new models can be registered via register_admin_url_finder:

    class SprocketAdminURLFinder(ModelAdminURLFinder):
        edit_url_name = 'wagtailsprockets:edit'

    register_admin_url_finder(Sprocket, SprocketAdminURLFinder)
"""


class ModelAdminURLFinder:
    """
    Handles admin edit URL lookups for an individual model
    """

    edit_url_name = None
    permission_policy = None

    def __init__(self, user=None):
        self.user = user

    def construct_edit_url(self, instance):
        """
        Return the edit URL for the given instance - regardless of whether the user can access it -
        or None if no edit URL is available.
        """
        if self.edit_url_name is None:
            raise ImproperlyConfigured(
                "%r must define edit_url_name or override construct_edit_url"
                % type(self)
            )
        return reverse(self.edit_url_name, args=(quote(instance.pk),))

    def get_edit_url(self, instance):
        """
        Return the edit URL for the given instance if one exists and the user has permission for it,
        or None otherwise.
        """
        if (
            self.user
            and self.permission_policy
            and not self.permission_policy.user_has_permission_for_instance(
                self.user, "change", instance
            )
        ):
            return None
        else:
            return self.construct_edit_url(instance)


class NullAdminURLFinder:
    """
    A dummy AdminURLFinder that always returns None
    """

    def __init__(self, user=None):
        pass

    def get_edit_url(self, instance):
        return None


finder_classes = ObjectTypeRegistry()


def register_admin_url_finder(model, handler):
    finder_classes.register(model, value=handler)


class AdminURLFinder:
    """
    The 'main' admin URL finder, which searches across all registered models
    """

    def __init__(self, user=None):
        search_for_hooks()  # ensure wagtail_hooks files have been loaded
        self.user = user
        self.finders_by_model = {}

    def get_edit_url(self, instance):
        model = type(instance)
        try:
            # do we already have a finder for this model and user?
            finder = self.finders_by_model[model]
        except KeyError:
            finder_class = finder_classes.get(instance) or NullAdminURLFinder
            finder = finder_class(self.user)
            self.finders_by_model[model] = finder

        return finder.get_edit_url(instance)
