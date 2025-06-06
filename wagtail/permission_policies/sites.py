from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db.models import Q

from wagtail.models import GroupSitePermission, Site

from .base import BaseDjangoAuthPermissionPolicy


class SitePermissionPolicy(BaseDjangoAuthPermissionPolicy):
    """
    A permission policy for objects that are associated with site records, such as
    wagtail.contrib.settings.models.BaseSiteSetting subclasses. Permissions may be
    assigned globally through standard django.contrib.auth permissions, or for
    individual sites through wagtail.models.GroupSitePermission records.
    """

    def _user_has_global_permission(self, user, permission_ids):
        """
        Check if the user has any of the given permissions assigned through a global
        django.contrib.auth permission, either directly or through a group.
        """
        return (
            Permission.objects.filter(
                id__in=permission_ids, group__in=user.groups.all()
            ).exists()
            or user.user_permissions.filter(id__in=permission_ids).exists()
        )

    def user_has_any_permission(self, user, actions):
        """
        Return whether the given user has permission to perform any of the given actions
        on some or all instances of this model
        """
        if not (user.is_authenticated and user.is_active):
            return False
        if user.is_superuser:
            return True

        permission_ids = list(
            self._get_permission_objects_for_actions(actions).values_list(
                "id", flat=True
            )
        )

        if self._user_has_global_permission(user, permission_ids):
            return True

        # Look for site-specific permissions associated with any of the user's groups
        if GroupSitePermission.objects.filter(
            permission_id__in=permission_ids, group__in=user.groups.all()
        ).exists():
            return True

        return False

    def users_with_any_permission(self, actions):
        """
        Return a queryset of users who have permission to perform any of the given actions
        on some or all instances of this model
        """
        permission_ids = list(
            self._get_permission_objects_for_actions(actions).values_list(
                "id", flat=True
            )
        )

        return get_user_model().objects.filter(
            (
                Q(is_superuser=True)
                # global permissions associated with the user directly
                | Q(user_permissions__in=permission_ids)
                # global permissions associated with any of the user's groups
                | Q(groups__permissions__in=permission_ids)
                # site-specific permissions associated with any of the user's groups
                | Q(groups__site_permissions__permission_id__in=permission_ids)
            )
            & Q(is_active=True)
        )

    def user_has_any_permission_for_instance(self, user, actions, instance):
        """
        Return whether the given user has permission to perform any of the given actions
        on the given model instance (which may be a Site or a model with a `site` foreign key)
        """
        if not (user.is_authenticated and user.is_active):
            return False
        if user.is_superuser:
            return True

        permission_ids = list(
            self._get_permission_objects_for_actions(actions).values_list(
                "id", flat=True
            )
        )

        if self._user_has_global_permission(user, permission_ids):
            return True

        if isinstance(instance, Site):
            site = instance
        else:
            site = instance.site

        # Look for a site-specific permission associated with any of the user's groups
        if GroupSitePermission.objects.filter(
            permission_id__in=permission_ids, group__in=user.groups.all(), site=site
        ).exists():
            return True

        return False

    def sites_user_has_any_permission_for(self, user, actions):
        """
        Return a queryset of all Site instances for which the given user has
        permission to perform any of the given actions
        """
        if not (user.is_authenticated and user.is_active):
            return Site.objects.none()
        if user.is_superuser:
            return Site.objects.all()

        permission_ids = list(
            self._get_permission_objects_for_actions(actions).values_list(
                "id", flat=True
            )
        )

        if self._user_has_global_permission(user, permission_ids):
            return Site.objects.all()

        # Look for site-specific permissions associated with any of the user's groups
        return Site.objects.filter(
            group_permissions__permission_id__in=permission_ids,
            group_permissions__group__in=user.groups.all(),
        ).distinct()

    def instances_user_has_any_permission_for(self, user, actions):
        """
        Return a queryset of all instances of this model for which the given user has
        permission to perform any of the given actions
        """
        return self.model.objects.filter(
            site__in=self.sites_user_has_any_permission_for(user, actions)
        )

    def users_with_any_permission_for_instance(self, actions, instance):
        """
        Return a queryset of all users who have permission to perform any of the given actions on
        the given model instance (which may be a Site or a model with a `site` foreign key)
        """
        permission_ids = list(
            self._get_permission_objects_for_actions(actions).values_list(
                "id", flat=True
            )
        )

        if isinstance(instance, Site):
            site = instance
        else:
            site = instance.site

        return get_user_model().objects.filter(
            (
                Q(is_superuser=True)
                # global permissions associated with the user directly
                | Q(user_permissions__in=permission_ids)
                # global permissions associated with any of the user's groups
                | Q(groups__permissions__in=permission_ids)
                # site-specific permissions associated with any of the user's groups
                | Q(
                    groups__site_permissions__permission_id__in=permission_ids,
                    groups__site_permissions__site=site,
                )
            )
            & Q(is_active=True)
        )

    # shortcuts for single actions (where BaseDjangoAuthPermissionPolicy does not
    # already implement them this way)

    def user_has_permission(self, user, action):
        return self.user_has_any_permission(user, [action])

    def sites_user_has_permission_for(self, user, action):
        return self.sites_user_has_any_permission_for(user, [action])

    def user_has_permission_for_instance(self, user, action, instance):
        return self.user_has_any_permission_for_instance(user, [action], instance)
