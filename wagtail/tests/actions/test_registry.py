from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from wagtail import hooks
from wagtail.actions.base import BaseAction
from wagtail.actions.registry import ActionRegistry
from wagtail.test.testapp.models import (
    Advert,
    RevisableChildModel,
    RevisableModel,
)


class DummyAction(BaseAction):
    action_name = "dummy"
    permission_policy_action = "change"

    def execute(self, skip_permission_checks=False):
        return self.instance


class UnavailableAction(BaseAction):
    action_name = "unavailable"
    permission_policy_action = "change"

    @classmethod
    def is_available_for_instance(cls, instance):
        return False

    def execute(self, skip_permission_checks=False):
        return self.instance


class TestActionRegistry(TestCase):
    def setUp(self):
        self.registry = ActionRegistry()

    def test_register_and_get(self):
        self.registry.register(RevisableModel, DummyAction)
        self.assertEqual(
            self.registry.get_action_class(RevisableModel, "dummy"),
            DummyAction,
        )
        self.assertEqual(
            self.registry.get_actions_for_model(RevisableModel),
            {"dummy": DummyAction},
        )

    def test_get_unknown_action_returns_none(self):
        self.assertIsNone(self.registry.get_action_class(RevisableModel, "nope"))

    def test_mro_inheritance(self):
        # An action registered against a base class is inherited by subclasses.
        self.registry.register(RevisableModel, DummyAction)
        self.assertEqual(
            self.registry.get_action_class(RevisableChildModel, "dummy"),
            DummyAction,
        )

    def test_mro_merging(self):
        # A subclass inherits base-class actions and adds its own.
        self.registry.register(RevisableModel, DummyAction)
        self.registry.register(RevisableChildModel, UnavailableAction)
        actions = self.registry.get_actions_for_model(RevisableChildModel)
        self.assertEqual(set(actions), {"dummy", "unavailable"})
        # The base class only has its own action.
        self.assertEqual(
            set(self.registry.get_actions_for_model(RevisableModel)),
            {"dummy"},
        )

    def test_register_rejects_non_action(self):
        class NotAnAction:
            action_name = "x"

        with self.assertRaises(TypeError):
            self.registry.register(RevisableModel, NotAnAction)

    def test_register_rejects_missing_action_name(self):
        class NamelessAction(BaseAction):
            def execute(self, skip_permission_checks=False):
                return self.instance

        with self.assertRaises(ImproperlyConfigured):
            self.registry.register(RevisableModel, NamelessAction)


class TestRegisterActionsHook(TestCase):
    def test_hook_registers_actions(self):
        registry = ActionRegistry()

        def register_dummy(reg):
            reg.register(Advert, DummyAction)

        with hooks.register_temporarily("register_actions", register_dummy):
            actions = registry.get_actions_for_model(Advert)
        self.assertEqual(actions, {"dummy": DummyAction})
