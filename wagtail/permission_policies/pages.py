from django.contrib.auth import get_user_model
from django.db.models import (
    CharField,
    Exists,
    ExpressionWrapper,
    F,
    OuterRef,
    PositiveIntegerField,
    Q,
    Value,
)

from wagtail.models import GroupPagePermission
from wagtail.permission_policies.base import BasePermissionPolicy


class PagePermissionPolicy(BasePermissionPolicy):
    def _base_user_has_permission(self, user):
        if not user.is_active:
            return False
        if user.is_superuser:
            return True
        return None

    def user_has_permission(self, user, action):
        base_permission = self._base_user_has_permission(user)
        if base_permission is not None:
            return base_permission
        return GroupPagePermission.objects.filter(
            group__user=user,
            permission_type=action,
        ).exists()

    def user_has_any_permission(self, user, actions):
        base_permission = self._base_user_has_permission(user)
        if base_permission is not None:
            return base_permission
        return GroupPagePermission.objects.filter(
            group__user=user,
            permission_type__in=actions,
        ).exists()

    def _base_users_with_permission_query(self, **kwargs):
        groups = GroupPagePermission.objects.filter(**kwargs).values_list(
            "group", flat=True
        )
        return (
            get_user_model()
            ._default_manager.filter(is_active=True)
            .filter(Q(is_superuser=True) | Q(groups__in=groups))
            .distinct()
        )

    def users_with_permission(self, action):
        return self._base_users_with_permission_query(permission_type=action)

    def users_with_any_permission(self, actions):
        return self._base_users_with_permission_query(permission_type__in=actions)

    def _base_user_permissions_for_instance_query(self, user, instance=None):
        if instance:
            # If we're filtering by an instance, we can use the instance's path and depth
            instance_path = Value(instance.path, CharField())
            instance_depth = Value(instance.depth, PositiveIntegerField())
        else:
            # Otherwise, we need to use the path and depth of the page being permission-checked
            instance_path = ExpressionWrapper(
                OuterRef("path"),
                output_field=CharField(),
            )
            instance_depth = ExpressionWrapper(
                OuterRef("depth"),
                output_field=PositiveIntegerField(),
            )

        return GroupPagePermission.objects.annotate(
            _instance_path=instance_path,
            _instance_depth=instance_depth,
        ).filter(
            _instance_path__startswith=F("page__path"),
            _instance_depth__gte=F("page__depth"),
            group__user=user,
        )

    def user_has_permission_for_instance(self, user, action, instance):
        base_permission = self._base_user_has_permission(user)
        if base_permission is not None:
            return base_permission
        return (
            self._base_user_permissions_for_instance_query(user, instance)
            .filter(permission_type=action)
            .exists()
        )

    def user_has_any_permission_for_instance(self, user, actions, instance):
        base_permission = self._base_user_has_permission(user)
        if base_permission is not None:
            return base_permission
        return (
            self._base_user_permissions_for_instance_query(user, instance)
            .filter(permission_type__in=actions)
            .exists()
        )

    def _base_instances_user_has_permission_for_query(self, user, **kwargs):
        return self.model._default_manager.filter(
            Exists(
                self._base_user_permissions_for_instance_query(user).filter(**kwargs)
            )
        ).distinct()

    def instances_user_has_any_permission_for(self, user, actions):
        base_permission = self._base_user_has_permission(user)
        if base_permission is False:
            return self.model._default_manager.none()
        if base_permission is True:
            return self.model._default_manager.all()
        return self._base_instances_user_has_permission_for_query(
            user, permission_type__in=actions
        )

    def instances_user_has_permission_for(self, user, action):
        base_permission = self._base_user_has_permission(user)
        if base_permission is False:
            return self.model._default_manager.none()
        if base_permission is True:
            return self.model._default_manager.all()
        return self._base_instances_user_has_permission_for_query(
            user, permission_type=action
        )

    def _base_users_with_permission_for_instance_query(self, instance, **kwargs):
        return (
            get_user_model()
            ._default_manager.filter(is_active=True)
            .filter(
                Q(is_superuser=True)
                | Exists(
                    self._base_user_permissions_for_instance_query(
                        user=OuterRef("pk"), instance=instance
                    ).filter(**kwargs)
                )
            )
            .distinct()
        )

    def users_with_any_permission_for_instance(self, actions, instance):
        return self._base_users_with_permission_for_instance_query(
            instance, permission_type__in=actions
        )

    def users_with_permission_for_instance(self, action, instance):
        return self._base_users_with_permission_for_instance_query(
            instance, permission_type=action
        )
