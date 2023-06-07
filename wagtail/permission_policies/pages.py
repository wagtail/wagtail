import operator
from functools import reduce

from django.contrib.auth import get_user_model
from django.db.models import (
    CharField,
    Exists,
    F,
    OuterRef,
    PositiveIntegerField,
    Q,
    Value,
)

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
        permissions = set(
            perm.permission_type for perm in self.get_cached_permissions_for_user(user)
        )
        return bool(set(actions) & permissions)

    def users_with_any_permission(self, actions):
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
        permissions = set(
            perm.permission_type
            for perm in self.get_cached_permissions_for_user(user)
            if instance.pk == perm.page_id or instance.is_descendant_of(perm.page)
        )
        return bool(set(actions) & permissions)

    def instances_user_has_any_permission_for(self, user, actions):
        base_permission = self._base_user_has_permission(user)
        if base_permission is False:
            return self.model._default_manager.none()
        if base_permission is True:
            return self.model._default_manager.all()

        or_queries = [
            Q(path__startswith=perm.page.path, depth__gte=perm.page.depth)
            for perm in self.get_cached_permissions_for_user(user)
            if perm.permission_type in actions
        ]
        if not or_queries:
            return self.model._default_manager.none()
        return self.model._default_manager.filter(reduce(operator.or_, or_queries))

    def users_with_any_permission_for_instance(self, actions, instance):
        permissions = GroupPagePermission.objects.annotate(
            _instance_path=Value(instance.path, CharField()),
            _instance_depth=Value(instance.depth, PositiveIntegerField()),
        ).filter(
            _instance_path__startswith=F("page__path"),
            _instance_depth__gte=F("page__depth"),
            group__user=OuterRef("pk"),
            permission_type__in=actions,
        )

        return (
            get_user_model()
            ._default_manager.filter(is_active=True)
            .filter(Q(is_superuser=True) | Exists(permissions))
            .distinct()
        )
