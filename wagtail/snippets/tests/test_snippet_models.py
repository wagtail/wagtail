from django.core import checks
from django.test import TestCase
from django.urls import reverse

from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.admin.panels import FieldPanel, get_edit_handler
from wagtail.snippets.models import SNIPPET_MODELS, register_snippet
from wagtail.test.snippets.forms import FancySnippetForm
from wagtail.test.snippets.models import (
    AlphaSnippet,
    FancySnippet,
    RegisterDecorator,
    RegisterFunction,
    StandardSnippet,
    ZuluSnippet,
)
from wagtail.test.testapp.models import AdvertWithTabbedInterface
from wagtail.test.utils import WagtailTestUtils


class TestModelOrdering(WagtailTestUtils, TestCase):
    def setUp(self):
        for i in range(1, 10):
            AdvertWithTabbedInterface.objects.create(text="advert %d" % i)
        AdvertWithTabbedInterface.objects.create(text="aaaadvert")
        self.login()

    def test_listing_respects_model_ordering(self):
        response = self.client.get(
            reverse("wagtailsnippets_tests_advertwithtabbedinterface:list")
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"][0].text, "aaaadvert")

    def test_chooser_respects_model_ordering(self):
        response = self.client.get(
            reverse("wagtailsnippetchoosers_tests_advertwithtabbedinterface:choose")
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["results"][0].text, "aaaadvert")


class TestSnippetRegistering(TestCase):
    def test_register_function(self):
        self.assertIn(RegisterFunction, SNIPPET_MODELS)

    def test_register_decorator(self):
        # Misbehaving decorators often return None
        self.assertIsNotNone(RegisterDecorator)
        self.assertIn(RegisterDecorator, SNIPPET_MODELS)


class TestSnippetOrdering(TestCase):
    def setUp(self):
        register_snippet(ZuluSnippet)
        register_snippet(AlphaSnippet)

    def test_snippets_ordering(self):
        # Ensure AlphaSnippet is before ZuluSnippet
        # Cannot check first and last position as other snippets
        # may get registered elsewhere during test
        self.assertLess(
            SNIPPET_MODELS.index(AlphaSnippet), SNIPPET_MODELS.index(ZuluSnippet)
        )


class TestSnippetEditHandlers(WagtailTestUtils, TestCase):
    def test_standard_edit_handler(self):
        edit_handler = get_edit_handler(StandardSnippet)
        form_class = edit_handler.get_form_class()
        self.assertTrue(issubclass(form_class, WagtailAdminModelForm))
        self.assertFalse(issubclass(form_class, FancySnippetForm))

    def test_fancy_edit_handler(self):
        edit_handler = get_edit_handler(FancySnippet)
        form_class = edit_handler.get_form_class()
        self.assertTrue(issubclass(form_class, WagtailAdminModelForm))
        self.assertTrue(issubclass(form_class, FancySnippetForm))


class TestPanelConfigurationChecks(WagtailTestUtils, TestCase):
    def setUp(self):
        self.warning_id = "wagtailadmin.W002"

        def get_checks_result():
            # run checks only with the 'panels' tag
            checks_result = checks.run_checks(tags=["panels"])
            return [
                warning for warning in checks_result if warning.id == self.warning_id
            ]

        self.get_checks_result = get_checks_result

    def test_model_with_single_tabbed_panel_only(self):
        StandardSnippet.content_panels = [FieldPanel("text")]

        warning = checks.Warning(
            "StandardSnippet.content_panels will have no effect on snippets editing",
            hint="""Ensure that StandardSnippet uses `panels` instead of `content_panels` \
or set up an `edit_handler` if you want a tabbed editing interface.
There are no default tabs on non-Page models so there will be no\
 Content tab for the content_panels to render in.""",
            obj=StandardSnippet,
            id="wagtailadmin.W002",
        )

        checks_results = self.get_checks_result()

        self.assertEqual([warning], checks_results)

        # clean up for future checks
        delattr(StandardSnippet, "content_panels")
