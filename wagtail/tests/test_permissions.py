from django.contrib.auth import get_user_model
from django.db.models import Q
from unittest.mock import Mock
from django.test import TestCase

class CollectionPermissionLookupMixin:
    owner_field_name = "owner"

    def _users_with_perm_filter(self, actions, collection):
        return Q()

    def _check_perm(self, user, perms, collection):
        return False

    def users_with_any_permission_for_instance(self, actions, instance):
        known_actions = set(actions) & {"choose", "change"}
        if "delete" in actions:
            known_actions.add("change")

        filter_expr = self._users_with_perm_filter(
            known_actions, collection=instance.collection
        )

        if "change" in known_actions:
            owner = getattr(instance, self.owner_field_name)
            if owner is not None and self._check_perm(
                owner, {"add"}, collection=instance.collection
            ):
                filter_expr |= Q(pk=owner.pk)

        if known_actions:
            return get_user_model().objects.filter(filter_expr).distinct()
        else:
            return get_user_model().objects.filter(is_active=True, is_superuser=True)

class UsersWithPermissionTest(TestCase):
    def setUp(self):
        self.mixin = CollectionPermissionLookupMixin()

    def test_delete_tratado_como_change(self):
        instance = Mock()
        instance.collection = Mock()
        self.mixin._users_with_perm_filter = Mock(return_value=Q())
        actions = ["delete"]
        self.mixin.users_with_any_permission_for_instance(actions, instance)
        self.mixin._users_with_perm_filter.assert_called_with({"change"}, collection=instance.collection)

    def test_change_com_dono_com_perm_add(self):
        owner = Mock(pk=1)
        instance = Mock()
        instance.collection = Mock()
        setattr(instance, "owner", owner)
        self.mixin._check_perm = Mock(return_value=True)
        self.mixin._users_with_perm_filter = Mock(return_value=Q())
        actions = ["change"]
        self.mixin.users_with_any_permission_for_instance(actions, instance)
        self.mixin._check_perm.assert_called_with(owner, {"add"}, collection=instance.collection)

    def test_change_com_dono_sem_perm_add(self):
        owner = Mock(pk=1)
        instance = Mock()
        instance.collection = Mock()
        setattr(instance, "owner", owner)
        self.mixin._check_perm = Mock(return_value=False)
        self.mixin._users_with_perm_filter = Mock(return_value=Q())
        actions = ["change"]
        self.mixin.users_with_any_permission_for_instance(actions, instance)
        self.mixin._check_perm.assert_called_with(owner, {"add"}, collection=instance.collection)

    def test_change_sem_dono_com_perm(self):
        instance = Mock()
        instance.collection = Mock()
        setattr(instance, "owner", None)
        self.mixin._check_perm = Mock(return_value=True)
        self.mixin._users_with_perm_filter = Mock(return_value=Q())
        actions = ["change"]
        self.mixin.users_with_any_permission_for_instance(actions, instance)
        self.mixin._check_perm.assert_not_called()
    def test_change_sem_dono_sem_perm(self):
        instance = Mock()
        instance.collection = Mock()
        setattr(instance, "owner", None)
        self.mixin._check_perm = Mock(return_value=False)
        self.mixin._users_with_perm_filter = Mock(return_value=Q())
        actions = ["change"]
        self.mixin.users_with_any_permission_for_instance(actions, instance)
        self.mixin._check_perm.assert_not_called()

    def test_choose_sem_change(self):
        instance = Mock()
        instance.collection = Mock()
        self.mixin._users_with_perm_filter = Mock(return_value=Q())
        actions = ["choose"]
        self.mixin.users_with_any_permission_for_instance(actions, instance)
        self.mixin._users_with_perm_filter.assert_called_with({"choose"}, collection=instance.collection)

    def test_acao_invalida_retorna_superuser(self):
        instance = Mock()
        instance.collection = Mock()
        actions = ["add"]
        queryset = self.mixin.users_with_any_permission_for_instance(actions, instance)
        self.assertIn("is_superuser", str(queryset.query))
