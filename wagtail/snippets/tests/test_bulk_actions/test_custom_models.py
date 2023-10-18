from django.test import TestCase
from django.urls import reverse

from wagtail.test.testapp.models import Advert, FullFeaturedSnippet
from wagtail.test.utils.wagtail_tests import WagtailTestUtils


class TestCustomModels(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()

    def create_snippets(self, model):
        return [model.objects.create(text=f"Title-{i}") for i in range(1, 6)]

    def get_action_url(self, model, snippets):
        return (
            reverse(
                "wagtail_bulk_action",
                args=(
                    model._meta.app_label,
                    model._meta.model_name,
                    "disable",
                ),
            )
            + "?"
            + "&".join(f"id={item.pk}" for item in snippets)
        )

    def get_list_url(self, model):
        return reverse(model.snippet_viewset.get_url_name("list"))

    def test_action_shown_for_custom_models(self):
        self.create_snippets(FullFeaturedSnippet)
        response = self.client.get(self.get_list_url(FullFeaturedSnippet))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Disable selected full-featured snippets")

    def test_action_confirmation_accessible_for_custom_models(self):
        snippets = self.create_snippets(FullFeaturedSnippet)
        response = self.client.get(self.get_action_url(FullFeaturedSnippet, snippets))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "wagtailadmin/bulk_actions/confirmation/base.html",
        )

    def test_action_not_shown_for_other_models(self):
        self.create_snippets(Advert)
        response = self.client.get(self.get_list_url(Advert))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Disable selected full-featured snippets")

    def test_action_confirmation_inaccessible_for_other_models(self):
        snippets = self.create_snippets(Advert)
        response = self.client.get(self.get_action_url(Advert, snippets))
        self.assertEqual(response.status_code, 404)
