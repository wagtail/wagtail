from django.contrib.auth import get_user_model
from django.db.models import Q

from wagtail.models import GroupPagePermission, Page
from wagtail.permission_policies.base import BasePermissionPolicy


class PagePermissionPolicy(BasePermissionPolicy):
    perm_cache_name = "_page_perm_cache"

    def __init__(self, model=Page):
        super().__init__(model=model)

    def get_all_permissions_for_user(self, user):
        if not user.is_active or user.is_anonymous or user.is_superuser:
            return GroupPagePermission.objects.none()
        return GroupPagePermission.objects.filter(group__user=user).select_related(
            "page"
        )

    def _base_user_has_permission(self, user):
        if not user.is_active:
            return False
        if user.is_superuser:
            return True
        return None

    def user_has_permission(self, user, action):
        return self.user_has_any_permission(user, [action])

    def user_has_any_permission(self, user, actions):
        base_permission = self._base_user_has_permission(user)
        if base_permission is not None:
            return base_permission

        # User with only "add" permission can still edit their own pages
        actions = set(actions)
        if "edit" in actions:
            actions.add("add")

        permissions = {
            perm.permission_type for perm in self.get_cached_permissions_for_user(user)
        }
        return bool(actions & permissions)

    def users_with_any_permission(self, actions):
        # User with only "add" permission can still edit their own pages
        actions = set(actions)
        if "edit" in actions:
            actions.add("add")

        groups = GroupPagePermission.objects.filter(
            permission_type__in=actions
        ).values_list("group", flat=True)
        return (
            get_user_model()
            ._default_manager.filter(is_active=True)
            .filter(Q(is_superuser=True) | Q(groups__in=groups))
            .distinct()
        )

    def user_has_permission_for_instance(self, user, action, instance):
        return self.user_has_any_permission_for_instance(user, [action], instance)

    def user_has_any_permission_for_instance(self, user, actions, instance):
        base_permission = self._base_user_has_permission(user)
        if base_permission is not None:
            return base_permission

        permissions = set()
        for perm in self.get_cached_permissions_for_user(user):
            if instance.pk == perm.page_id or instance.is_descendant_of(perm.page):
                permissions.add(perm.permission_type)
                if perm.permission_type == "add" and instance.owner_id == user.pk:
                    permissions.add("edit")

        return bool(set(actions) & permissions)

    def instances_user_has_any_permission_for(self, user, actions):
        base_permission = self._base_user_has_permission(user)
        if base_permission is False:
            return self.model._default_manager.none()
        if base_permission is True:
            return self.model._default_manager.all()

        pages = self.model._default_manager.none()
        for perm in self.get_cached_permissions_for_user(user):
            if (
                perm.permission_type == "add"
                and "add" not in actions
                and "edit" in actions
            ):
                pages |= self.model._default_manager.descendant_of(
                    perm.page, inclusive=True
                ).filter(owner=user)
            elif perm.permission_type in actions:
                pages |= self.model._default_manager.descendant_of(
                    perm.page, inclusive=True
                )
        return pages

    def users_with_any_permission_for_instance(self, actions, instance):
        q = Q(is_superuser=True)

        # Find permissions for all ancestors that match any of the actions
        ancestors = instance.get_ancestors(inclusive=True)
        groups = GroupPagePermission.objects.filter(
            permission_type__in=actions, page__in=ancestors
        ).values_list("group", flat=True)

        q |= Q(groups__in=groups)

        # If "edit" is in actions but "add" is not, then we need to check for
        # cases where the user has "add" permission on an ancestor, and is the
        # owner of the instance
        if "edit" in actions and "add" not in actions:
            add_groups = GroupPagePermission.objects.filter(
                permission_type="add", page__in=ancestors
            ).values_list("group", flat=True)

            q |= Q(groups__in=add_groups) & Q(pk=instance.owner_id)

        return (
            get_user_model()
            ._default_manager.filter(is_active=True)
            .filter(q)
            .distinct()
        )
