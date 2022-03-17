from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.db.models import Q

from wagtail.models import Collection, GroupCollectionPermission

from .base import BaseDjangoAuthPermissionPolicy


class CollectionPermissionLookupMixin:
    def _get_permission_objects_for_actions(self, actions):
        """
        Get a queryset of the Permission objects for the given actions
        """
        permission_codenames = [
            "%s_%s" % (action, self.model_name) for action in actions
        ]
        return Permission.objects.filter(
            content_type=self._content_type, codename__in=permission_codenames
        )

    def _check_perm(self, user, actions, collection=None):
        """
        Equivalent to user.has_perm(self._get_permission_name(action)) on all listed actions,
        but using GroupCollectionPermission rather than group.permissions.
        If collection is specified, only consider GroupCollectionPermission records
        that apply to that collection.
        """
        if not (user.is_active and user.is_authenticated):
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

    def _collections_with_perm(self, user, actions):
        """
        Return a queryset of collections on which this user has a GroupCollectionPermission
        record for any of the given actions, either on the collection itself or an ancestor
        """
        # Get the permission objects corresponding to these actions
        permissions = self._get_permission_objects_for_actions(actions)

        # Get the collections that have a GroupCollectionPermission record
        # for any of these permissions and any of the user's groups;
        # create a list of their paths
        collection_root_paths = Collection.objects.filter(
            group_permissions__group__in=user.groups.all(),
            group_permissions__permission__in=permissions,
        ).values_list("path", flat=True)

        if collection_root_paths:
            # build a filter expression that will filter our model to just those
            # instances in collections with a path that starts with one of the above
            collection_path_filter = Q(path__startswith=collection_root_paths[0])
            for path in collection_root_paths[1:]:
                collection_path_filter = collection_path_filter | Q(
                    path__startswith=path
                )

            return Collection.objects.all().filter(collection_path_filter)
        else:
            # no matching collections
            return Collection.objects.none()

    def _users_with_perm_filter(self, actions, collection=None):
        """
        Return a filter expression that will filter a user queryset to those with any
        permissions corresponding to 'actions', via either GroupCollectionPermission
        or superuser privileges.
        If collection is specified, only consider GroupCollectionPermission records
        that apply to that collection.
        """
        permissions = self._get_permission_objects_for_actions(actions)
        # Find all groups with GroupCollectionPermission records for
        # any of these permissions
        groups = Group.objects.filter(
            collection_permissions__permission__in=permissions,
        )

        if collection is not None:
            collections = collection.get_ancestors(inclusive=True)
            groups = groups.filter(collection_permissions__collection__in=collections)

        # Find all users who are superusers or in any of these groups, and are active
        return (Q(is_superuser=True) | Q(groups__in=groups)) & Q(is_active=True)

    def _users_with_perm(self, actions, collection=None):
        """
        Return a queryset of users with any permissions corresponding to 'actions',
        via either GroupCollectionPermission or superuser privileges.
        If collection is specified, only consider GroupCollectionPermission records
        that apply to that collection.
        """
        return (
            get_user_model()
            .objects.filter(
                self._users_with_perm_filter(actions, collection=collection)
            )
            .distinct()
        )

    def collections_user_has_any_permission_for(self, user, actions):
        """
        Return a queryset of all collections in which the given user has
        permission to perform any of the given actions
        """
        if user.is_active and user.is_superuser:
            # active superusers can perform any action (including unrecognised ones)
            # in any collection
            return Collection.objects.all()

        if not user.is_authenticated:
            return Collection.objects.none()

        return self._collections_with_perm(user, actions)

    def collections_user_has_permission_for(self, user, action):
        """
        Return a queryset of all collections in which the given user has
        permission to perform the given action
        """
        return self.collections_user_has_any_permission_for(user, [action])


class CollectionPermissionPolicy(
    CollectionPermissionLookupMixin, BaseDjangoAuthPermissionPolicy
):
    """
    A permission policy for objects that are assigned locations in the Collection tree.
    Permissions may be defined at any node of the hierarchy, through the
    GroupCollectionPermission model, and propagate downwards. These permissions are
    applied to objects according to the standard django.contrib.auth permission model.
    """

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
        return self._users_with_perm(actions)

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
        if not (user.is_active and user.is_authenticated):
            return self.model.objects.none()
        elif user.is_superuser:
            return self.model.objects.all()
        else:
            # filter to just the collections with this permission
            return self.model.objects.filter(
                collection__in=list(self._collections_with_perm(user, actions))
            )

    def users_with_any_permission_for_instance(self, actions, instance):
        """
        Return a queryset of all users who have permission to perform any of the given
        actions on the given model instance
        """
        return self._users_with_perm(actions, collection=instance.collection)


class CollectionOwnershipPermissionPolicy(
    CollectionPermissionLookupMixin, BaseDjangoAuthPermissionPolicy
):
    """
    A permission policy for objects that are assigned locations in the Collection tree.
    Permissions may be defined at any node of the hierarchy, through the
    GroupCollectionPermission model, and propagate downwards. These permissions are
    applied to objects according to the 'ownership' permission model
    (see permission_policies.base.OwnershipPermissionPolicy)
    """

    def __init__(self, model, auth_model=None, owner_field_name="owner"):
        super().__init__(model, auth_model=auth_model)
        self.owner_field_name = owner_field_name

        # make sure owner_field_name is a field that exists on the model
        try:
            self.model._meta.get_field(self.owner_field_name)
        except FieldDoesNotExist:
            raise ImproperlyConfigured(
                "%s has no field named '%s'. To use this model with "
                "CollectionOwnershipPermissionPolicy, you must specify a valid field name as "
                "owner_field_name." % (self.model, self.owner_field_name)
            )

    def user_has_permission(self, user, action):
        if action == "add":
            return self._check_perm(user, ["add"])
        elif action == "choose":
            return self._check_perm(user, ["choose"])
        elif action == "change" or action == "delete":
            # having 'add' permission means that there are *potentially*
            # some instances they can edit (namely: ones they own),
            # which is sufficient for returning True here
            return self._check_perm(user, ["add", "change"])
        else:
            # unrecognised actions are only allowed for active superusers
            return user.is_active and user.is_superuser

    def users_with_any_permission(self, actions):
        if "change" in actions or "delete" in actions:
            # either 'add' or 'change' permission means that there are *potentially*
            # some instances they can edit
            real_actions = ["add", "change"]
        elif "add" in actions:
            real_actions = ["add"]
        elif "choose" in actions:
            real_actions = ["choose"]
        else:
            # none of the actions passed in here are ones that we recognise, so only
            # allow them for active superusers
            return get_user_model().objects.filter(is_active=True, is_superuser=True)

        return self._users_with_perm(real_actions)

    def user_has_permission_for_instance(self, user, action, instance):
        return self.user_has_any_permission_for_instance(user, [action], instance)

    def user_has_any_permission_for_instance(self, user, actions, instance):
        if "change" in actions or "delete" in actions:
            if self._check_perm(user, ["change"], collection=instance.collection):
                return True
            elif (
                self._check_perm(user, ["add"], collection=instance.collection)
                and getattr(instance, self.owner_field_name) == user
            ):
                return True
            else:
                return False
        elif "choose" in actions:
            return self._check_perm(user, ["choose"], collection=instance.collection)
        else:
            # 'change' and 'delete' are the only actions that are well-defined
            # for specific instances. Other actions are only available to
            # active superusers.
            return user.is_active and user.is_superuser

    def instances_user_has_any_permission_for(self, user, actions):
        if user.is_active and user.is_superuser:
            # active superusers can perform any action (including unrecognised ones)
            # on any instance
            return self.model.objects.all()
        elif not user.is_authenticated:
            return self.model.objects.none()
        elif "change" in actions or "delete" in actions:
            # return instances which are:
            # - in (a descendant of) a collection for which they have 'change' permission
            # - OR in (a descendant of) a collection for which they have 'add' permission,
            #   and are owned by them

            change_perm_filter = Q(
                collection__in=list(self._collections_with_perm(user, ["change"]))
            )

            add_perm_filter = Q(
                collection__in=list(self._collections_with_perm(user, ["add"]))
            ) & Q(**{self.owner_field_name: user})

            return self.model.objects.filter(change_perm_filter | add_perm_filter)
        elif "choose" in actions:
            # Return instances which are in (a descendant of) a collection for which they
            # have 'choose' permission.
            choose_perm_filter = Q(
                collection__in=list(self._collections_with_perm(user, ["choose"]))
            )
            return self.model.objects.filter(choose_perm_filter)
        else:
            # action is either not recognised, or is the 'add' action which is
            # not meaningful for existing instances. As such, non-superusers
            # cannot perform it on any existing instances.
            return self.model.objects.none()

    def users_with_any_permission_for_instance(self, actions, instance):
        if "change" in actions or "delete" in actions:
            # form a filter expression of the users with 'change' permission
            # over this instance's collection
            filter_expr = self._users_with_perm_filter(
                ["change"], collection=instance.collection
            )

            # add on the item's owner, if they still have 'add' permission
            # (and the owner field isn't blank)
            owner = getattr(instance, self.owner_field_name)
            if owner is not None and self._check_perm(
                owner, ["add"], collection=instance.collection
            ):
                filter_expr = filter_expr | Q(pk=owner.pk)

            # return the filtered queryset
            return get_user_model().objects.filter(filter_expr).distinct()
        elif "choose" in actions:
            # Form a filter expression of the users with 'choose' permission
            # over this instance's collection.
            filter_expr = self._users_with_perm_filter(
                ["choose"], collection=instance.collection
            )
            return get_user_model().objects.filter(filter_expr).distinct()
        else:
            # action is either not recognised, or is the 'add' action which is
            # not meaningful for existing instances. As such, the action is only
            # available to superusers
            return get_user_model().objects.filter(is_active=True, is_superuser=True)

    def collections_user_has_any_permission_for(self, user, actions):
        """
        Return a queryset of all collections in which the given user has
        permission to perform any of the given actions
        """
        if user.is_active and user.is_superuser:
            # active superusers can perform any action (including unrecognised ones)
            # in any collection
            return Collection.objects.all()

        elif not user.is_authenticated:
            return Collection.objects.none()

        elif "change" in actions or "delete" in actions:
            # return collections which are covered by either 'add' or 'change' permissions
            # (since collections with 'add' permissions can *potentially* contain instances
            # they own and can therefore edit)
            return self._collections_with_perm(user, ["add", "change"])

        elif "add" in actions:
            return self._collections_with_perm(user, ["add"])

        elif "choose" in actions:
            return self._collections_with_perm(user, ["choose"])

        else:
            # action is not recognised, and so non-superusers
            # cannot perform it on any existing collections
            return Collection.objects.none()


class CollectionMangementPermissionPolicy(
    CollectionPermissionLookupMixin, BaseDjangoAuthPermissionPolicy
):
    def _descendants_with_perm(self, user, action):
        """
        Return a queryset of collections descended from a collection on which this user has
        a GroupCollectionPermission record for this action. Used for actions, like edit and
        delete where the user cannot modify the collection where they are granted permission.
        """
        # Get the permission object corresponding to this action
        permission = self._get_permission_objects_for_actions([action]).first()

        # Get the collections that have a GroupCollectionPermission record
        # for this permission and any of the user's groups;
        # create a list of their paths
        collection_roots = Collection.objects.filter(
            group_permissions__group__in=user.groups.all(),
            group_permissions__permission=permission,
        ).values("path", "depth")

        if collection_roots:
            # build a filter expression that will filter our model to just those
            # instances in collections with a path that starts with one of the above
            # but excluding the collection on which permission was granted
            collection_path_filter = Q(
                path__startswith=collection_roots[0]["path"]
            ) & Q(depth__gt=collection_roots[0]["depth"])
            for collection in collection_roots[1:]:
                collection_path_filter = collection_path_filter | (
                    Q(path__startswith=collection["path"])
                    & Q(depth__gt=collection["depth"])
                )
            return Collection.objects.all().filter(collection_path_filter)
        else:
            # no matching collections
            return Collection.objects.none()

    def user_has_permission(self, user, action):
        """
        Return whether the given user has permission to perform the given action
        on some or all instances of this model
        """
        return self.user_has_any_permission(user, [action])

    def user_has_any_permission(self, user, actions):
        """
        Return whether the given user has permission to perform any of the given actions
        on some or all instances of this model.
        """
        return self._check_perm(user, actions)

    def users_with_any_permission(self, actions):
        """
        Return a queryset of users who have permission to perform any of the given actions
        on some or all instances of this model
        """
        return self._users_with_perm(actions)

    def user_has_permission_for_instance(self, user, action, instance):
        """
        Return whether the given user has permission to perform the given action on the
        given model instance
        """
        return self._check_perm(user, [action], collection=instance)

    def user_has_any_permission_for_instance(self, user, actions, instance):
        """
        Return whether the given user has permission to perform any of the given actions
        on the given model instance
        """
        return self._check_perm(user, actions, collection=instance)

    def users_with_any_permission_for_instance(self, actions, instance):
        """
        Return a queryset of all users who have permission to perform any of the given
        actions on the given model instance
        """
        return self._users_with_perm(actions, collection=instance)

    def instances_user_has_permission_for(self, user, action):
        if user.is_active and user.is_superuser:
            # active superusers can perform any action (including unrecognised ones)
            # in any collection - except for deleting the root collection
            if action == "delete":
                return Collection.objects.exclude(depth=1).all()
            else:
                return Collection.objects.all()

        elif not user.is_authenticated:
            return Collection.objects.none()

        else:
            if action == "delete":
                return self._descendants_with_perm(user, action)
            else:
                return self._collections_with_perm(user, [action])

    def instances_user_has_any_permission_for(self, user, actions):
        return self.collections_user_has_any_permission_for(user, actions)
