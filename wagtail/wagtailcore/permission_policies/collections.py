from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db.models import Q

from wagtail.wagtailcore.models import Collection, GroupCollectionPermission

from .base import BaseDjangoAuthPermissionPolicy


class CollectionPermissionPolicy(BaseDjangoAuthPermissionPolicy):
    """
    A permission policy for objects that are assigned locations in the Collection tree.
    Permissions may be defined at any node of the hierarchy, through the
    GroupCollectionPermission model, and propagate downwards. These permissions are
    applied to objects according to the standard django.contrib.auth permission model.
    """
    def _get_permission_objects_for_actions(self, actions):
        """
        Get a queryset of the Permission objects for the given actions
        """
        permission_codenames = ['%s_%s' % (action, self.model_name) for action in actions]
        return Permission.objects.filter(
            content_type=self._content_type,
            codename__in=permission_codenames
        )

    def _check_perm(self, user, actions, collection=None):
        """
        Equivalent to user.has_perm(self._get_permission_name(action)) on all listed actions,
        but using GroupCollectionPermission rather than group.permissions.
        If collection is specified, only consider GroupCollectionPermission records
        that apply to that collection.
        """
        if not user.is_active:
            return False

        if user.is_superuser:
            return True

        collection_permissions = GroupCollectionPermission.objects.filter(
            group__user=user,
            permission__in=self._get_permission_objects_for_actions(actions),
        )

        if collection:
            collection_permissions = collection_permissions.filter(
                collection__in=collection.get_ancestors(inclusive=True)
            )

        return collection_permissions.exists()

    def user_has_permission(self, user, action):
        """
        Return whether the given user has permission to perform the given action
        on some or all instances of this model
        """
        return self._check_perm(user, [action])

    def user_has_any_permission(self, user, actions):
        """
        Return whether the given user has permission to perform any of the given actions
        on some or all instances of this model
        """
        return self._check_perm(user, actions)

    def users_with_any_permission(self, actions):
        """
        Return a queryset of users who have permission to perform any of the given actions
        on some or all instances of this model
        """

        # Get the permission objects corresponding to these actions
        permissions = self._get_permission_objects_for_actions(actions)

        # Form a filter expression to apply to users, that finds the ones which:
        # - belong to a group
        # - which has a GroupCollectionPermission
        # - referencing one of the permissions we're interested in
        permission_filter_expr = Q(groups__collection_permissions__permission__in=permissions)

        # Return users that match this permission criterion or are superusers, AND are active
        filter_expr = (
            Q(is_superuser=True) | permission_filter_expr
        ) & Q(is_active=True)
        return get_user_model().objects.filter(filter_expr).distinct()

    def user_has_permission_for_instance(self, user, action, instance):
        """
        Return whether the given user has permission to perform the given action on the
        given model instance
        """
        return self._check_perm(user, [action], collection=instance.collection)

    def user_has_any_permission_for_instance(self, user, actions, instance):
        """
        Return whether the given user has permission to perform any of the given actions
        on the given model instance
        """
        return self._check_perm(user, actions, collection=instance.collection)

    def instances_user_has_any_permission_for(self, user, actions):
        """
        Return a queryset of all instances of this model for which the given user has
        permission to perform any of the given actions
        """
        if not user.is_active:
            return self.model.objects.none()
        elif user.is_superuser:
            return self.model.objects.all()
        else:
            # Get the permission objects corresponding to these actions
            permissions = self._get_permission_objects_for_actions(actions)

            # Get the collections that have a GroupCollectionPermission record
            # for any of these permissions and any of the user's groups;
            # create a list of their paths
            collection_root_paths = Collection.objects.filter(
                group_permissions__group__in=user.groups.all(),
                group_permissions__permission__in=permissions
            ).values_list('path', flat=True)

            if collection_root_paths:
                # build a filter expression that will filter our model to just those
                # instances in collections with a path that starts with one of the above
                collection_path_filter = Q(collection__path__startswith=collection_root_paths[0])
                for path in collection_root_paths[1:]:
                    collection_path_filter = collection_path_filter | Q(
                        collection__path__startswith=path
                    )
                return self.model.objects.filter(collection_path_filter)
            else:
                # no matching collections
                return self.model.objects.none()

    def users_with_any_permission_for_instance(self, actions, instance):
        """
        Return a queryset of all users who have permission to perform any of the given
        actions on the given model instance
        """
        permissions = self._get_permission_objects_for_actions(actions)
        collections = instance.collection.get_ancestors(inclusive=True)
        # Find all groups with GroupCollectionPermission records for
        # any of these permissions and collections
        groups = Group.objects.filter(
            collection_permissions__permission__in=permissions,
            collection_permissions__collection__in=collections
        )
        # Find all users who are superusers or in any of these groups, and are active
        return get_user_model().objects.filter(
            (Q(is_superuser=True) | Q(groups__in=groups)) & Q(is_active=True)
        ).distinct()
