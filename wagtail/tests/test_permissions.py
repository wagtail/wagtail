from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from wagtail.models import Collection, Locale, Page, Site, Task, Workflow
from wagtail.permission_policies import ModelPermissionPolicy
from wagtail.permission_policies.collections import CollectionManagementPermissionPolicy
from wagtail.permission_policies.pages import PagePermissionPolicy
from wagtail.permissions import (
    PolicyRegistry,
    collection_permission_policy,
    locale_permission_policy,
    page_permission_policy,
    policy_registry,
    register_permission_policy,
    site_permission_policy,
    task_permission_policy,
    workflow_permission_policy,
)
from wagtail.test.testapp.models import (
    Advert,
    RevisableChildModel,
    RevisableModel,
    SimplePage,
)


class TestPolicyRegistry(TestCase):
    def setUp(self):
        self.registry = PolicyRegistry()
        # fallback_policies is a class attribute shared by all PolicyRegistry
        # instances (including the global policy_registry), so give this
        # registry its own dict to avoid leaking state between tests.
        self.registry.fallback_policies = {}

    def test_get_fallback_policy_returns_none_if_not_created(self):
        self.assertIsNone(self.registry.get_fallback_policy(Advert))

    def test_get_by_type_with_no_policy_and_fallback_false_returns_none(self):
        self.assertIsNone(self.registry.get_by_type(Advert, fallback=False))
        self.assertIsNone(self.registry.get_fallback_policy(Advert))

    def test_get_by_type_with_no_policy_creates_fallback_policy(self):
        policy = self.registry.get_by_type(Advert)
        self.assertIsInstance(policy, ModelPermissionPolicy)
        self.assertEqual(policy.model, Advert)
        self.assertIs(self.registry.get_fallback_policy(Advert), policy)

    def test_get_by_type_returns_same_fallback_instance_on_repeated_calls(self):
        first = self.registry.get_by_type(Advert)
        second = self.registry.get_by_type(Advert)
        self.assertIs(first, second)

    def test_get_by_type_returns_registered_policy_over_fallback(self):
        policy = ModelPermissionPolicy(Advert)
        self.registry.register(Advert, policy)
        self.assertIs(self.registry.get_by_type(Advert), policy)
        # No fallback should have been created.
        self.assertIsNone(self.registry.get_fallback_policy(Advert))

    def test_get_by_type_mro_inheritance(self):
        policy = ModelPermissionPolicy(RevisableModel)
        self.registry.register(RevisableModel, policy)
        self.assertIs(self.registry.get_by_type(RevisableChildModel), policy)

    def test_get_by_type_exact_class_only_matches_exact_class(self):
        policy = ModelPermissionPolicy(RevisableModel)
        self.registry.register(RevisableModel, policy, exact_class=True)
        self.assertIs(self.registry.get_by_type(RevisableModel), policy)
        # A subclass doesn't match an exact_class registration, so a fallback
        # policy is created for it instead.
        fallback = self.registry.get_by_type(RevisableChildModel)
        self.assertIsNot(fallback, policy)
        self.assertIsInstance(fallback, ModelPermissionPolicy)

    def test_get_returns_policy_for_instance_class(self):
        policy = ModelPermissionPolicy(Advert)
        self.registry.register(Advert, policy)
        instance = Advert(text="test")
        self.assertIs(self.registry.get(instance), policy)

    def test_register_raises_if_fallback_already_created(self):
        self.registry.get_by_type(Advert)  # creates and caches a fallback policy
        policy = ModelPermissionPolicy(Advert)
        with self.assertRaisesMessage(
            ImproperlyConfigured,
            "A fallback permission policy has already been created for "
            "tests.Advert. Please ensure your custom ModelPermissionPolicy is "
            "registered earlier on, such as at the top of wagtail_hooks.py or "
            "in your AppConfig.ready().",
        ):
            self.registry.register(Advert, policy)

    def test_register_succeeds_if_no_fallback_created(self):
        policy = ModelPermissionPolicy(Advert)
        self.registry.register(Advert, policy)
        self.assertIs(self.registry.get_by_type(Advert), policy)


class TestRegisterPermissionPolicy(TestCase):
    def setUp(self):
        self.registry = PolicyRegistry()
        self.registry.fallback_policies = {}
        # register_permission_policy() delegates to the module-level global,
        # so patch it to point at an isolated registry for these tests.
        patcher = mock.patch("wagtail.permissions.policy_registry", self.registry)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_registers_default_model_permission_policy_when_none_provided(self):
        register_permission_policy(Advert)
        policy = self.registry.get_by_type(Advert)
        self.assertIsInstance(policy, ModelPermissionPolicy)
        self.assertEqual(policy.model, Advert)

    def test_registers_provided_policy(self):
        policy = ModelPermissionPolicy(Advert)
        register_permission_policy(Advert, policy)
        self.assertIs(self.registry.get_by_type(Advert), policy)

    def test_respects_exact_class_argument(self):
        policy = ModelPermissionPolicy(RevisableModel)
        register_permission_policy(RevisableModel, policy, exact_class=True)
        self.assertIs(self.registry.get_by_type(RevisableModel), policy)
        self.assertIsNot(self.registry.get_by_type(RevisableChildModel), policy)

    def test_raises_if_fallback_already_created_for_model(self):
        self.registry.get_by_type(Advert)  # creates a fallback policy
        with self.assertRaisesMessage(
            ImproperlyConfigured,
            "A fallback permission policy has already been created for "
            "tests.Advert. Please ensure your custom ModelPermissionPolicy is "
            "registered earlier on, such as at the top of wagtail_hooks.py or "
            "in your AppConfig.ready().",
        ):
            register_permission_policy(Advert)


class TestDefaultPermissionPolicies(TestCase):
    """
    The global policy_registry is pre-populated with policies for
    Wagtail's own models.
    """

    def test_page_uses_page_permission_policy(self):
        policy = policy_registry.get_by_type(Page)
        self.assertIs(policy, page_permission_policy)
        self.assertIsInstance(policy, PagePermissionPolicy)

    def test_site_uses_model_permission_policy(self):
        policy = policy_registry.get_by_type(Site)
        self.assertIs(policy, site_permission_policy)
        self.assertIsInstance(policy, ModelPermissionPolicy)

    def test_collection_uses_collection_management_permission_policy(self):
        policy = policy_registry.get_by_type(Collection)
        self.assertIs(policy, collection_permission_policy)
        self.assertIsInstance(policy, CollectionManagementPermissionPolicy)

    def test_task_uses_model_permission_policy(self):
        policy = policy_registry.get_by_type(Task)
        self.assertIs(policy, task_permission_policy)
        self.assertIsInstance(policy, ModelPermissionPolicy)

    def test_workflow_uses_model_permission_policy(self):
        policy = policy_registry.get_by_type(Workflow)
        self.assertIs(policy, workflow_permission_policy)
        self.assertIsInstance(policy, ModelPermissionPolicy)

    def test_locale_uses_model_permission_policy(self):
        policy = policy_registry.get_by_type(Locale)
        self.assertIs(policy, locale_permission_policy)
        self.assertIsInstance(policy, ModelPermissionPolicy)

    def test_page_subclass_inherits_page_permission_policy(self):
        self.assertIs(policy_registry.get_by_type(SimplePage), page_permission_policy)

    def _clear_fallback_policy(self, model):
        # fallback_policies is a class attribute shared by every PolicyRegistry
        # instance, including the global policy_registry, so any fallback
        # created for a test-only model must be cleaned up afterwards to avoid
        # leaking state into other tests.
        policy_registry.fallback_policies.pop(model, None)

    def test_unregistered_model_gets_a_fallback_model_permission_policy(self):
        self.addCleanup(self._clear_fallback_policy, Advert)
        policy = policy_registry.get_by_type(Advert)
        self.assertIsInstance(policy, ModelPermissionPolicy)
        self.assertEqual(policy.model, Advert)
        # The fallback is cached, so a second lookup returns the same instance.
        self.assertIs(policy_registry.get_by_type(Advert), policy)

    def test_registering_a_policy_for_a_model_with_existing_fallback_raises(self):
        self.addCleanup(self._clear_fallback_policy, Advert)
        # Once a fallback policy has been created for a model, the registry
        # protects against a custom policy being registered too late.
        policy_registry.get_by_type(Advert)
        with self.assertRaisesMessage(
            ImproperlyConfigured,
            "A fallback permission policy has already been created for "
            "tests.Advert. Please ensure your custom ModelPermissionPolicy is "
            "registered earlier on, such as at the top of wagtail_hooks.py or "
            "in your AppConfig.ready().",
        ):
            register_permission_policy(Advert, ModelPermissionPolicy(Advert))
