import unittest

from django.test import TestCase
from django.urls import reverse

from wagtail.models import Page
from wagtail.models.view_restrictions import (
    get_page_view_restriction_model,
    get_page_view_restriction_model_string,
)
from wagtail.test.testapp.models import SimplePage
from wagtail.test.utils import WagtailTestUtils

ACTIVE_PAGE_VIEW_RESTRICTION_MODEL = get_page_view_restriction_model_string()

PageViewRestriction = get_page_view_restriction_model()


@unittest.skipUnless(
    ACTIVE_PAGE_VIEW_RESTRICTION_MODEL
    == "custom_pageviewrestriction.PageViewRestriction",
    "Only applicable to Custom PageViewRestriction",
)
class TestPagePrivacyWithCustomPageViewRestrictionModel(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.secret_plans_page = Page.objects.get(url_path="/home/secret-plans/")
        PageViewRestriction.objects.filter(page=self.secret_plans_page).delete()
        self.view_restriction = PageViewRestriction.objects.create(
            page=self.secret_plans_page, restriction_type=PageViewRestriction.ADMIN
        )

    def test_custom_restriction_type_with_anonymous_user(self):
        response = self.client.get("/secret-plans/")
        self.assertRedirects(response, "/_util/login/?next=/secret-plans/")

    def test_custom_restriction_type_with_unpermitted_user(self):
        self.login(username="eventeditor", password="password")
        response = self.client.get("/secret-plans/")
        self.assertEqual(response.status_code, 403)

    def test_custom_restriction_type_with_permitted_user(self):
        self.login(username="superuser", password="password")
        response = self.client.get("/secret-plans/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<title>Secret plans</title>")


@unittest.skipUnless(
    ACTIVE_PAGE_VIEW_RESTRICTION_MODEL
    == "custom_pageviewrestriction.PageViewRestriction",
    "Only applicable to Custom PageViewRestriction",
)
class TestSetPrivacyViewWithCustomPageViewRestrictionModel(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

        # Create some pages
        self.homepage = Page.objects.get(id=2)

        self.public_page = self.homepage.add_child(
            instance=SimplePage(
                title="Public page",
                content="hello",
                live=True,
            )
        )

        self.private_page = self.homepage.add_child(
            instance=SimplePage(
                title="Private page",
                content="hello",
                live=True,
            )
        )
        PageViewRestriction.objects.create(
            page=self.private_page, restriction_type=PageViewRestriction.ADMIN
        )

    def test_custom_restriction_type_in_page_privacy_options_and_form_choices(self):
        """
        This tests that the custom restriction type is available in the page privacy options and form choices
        """
        # Check `Page.private_page_options`
        self.assertIn(PageViewRestriction.ADMIN, self.public_page.private_page_options)

        # Check form choices
        response = self.client.get(
            reverse("wagtailadmin_pages:set_privacy", args=(self.public_page.id,)),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            PageViewRestriction.ADMIN,
            [
                choice[0]
                for choice in response.context["form"]
                .fields["restriction_type"]
                .choices
            ],
        )
        self.assertTrue(
            response.context["form"]
            .fields["restriction_type"]
            .valid_value(PageViewRestriction.ADMIN)
        )

    def test_get_private_custom_view_restriction(self):
        """
        This tests that the custom restriction type set correctly when a user opens the set_privacy view
        """
        url = reverse("wagtailadmin_pages:set_privacy", args=(self.private_page.id,))
        response = self.client.get(url)

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/shared/set_privacy.html")
        self.assertEqual(response.context["object"].specific, self.private_page)
        self.assertEqual(response.context["action_url"], url)

        # Check form attributes
        self.assertEqual(response.context["form"]["restriction_type"].value(), "admin")
        self.assertEqual(response.context["form"]["password"].value(), "")
        self.assertEqual(response.context["form"]["groups"].value(), [])

    def test_set_custom_view_restriction(self):
        """
        This tests that setting a custom view restriction using the set_privacy view works
        """
        post_data = {
            "restriction_type": PageViewRestriction.ADMIN,
            "password": "",
            "groups": [],
        }
        response = self.client.post(
            reverse("wagtailadmin_pages:set_privacy", args=(self.public_page.id,)),
            post_data,
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertEqual(json["step"], "set_privacy_done")
        self.assertEqual(json["is_public"], False)

        # Check that a page restriction has been created
        self.assertTrue(
            PageViewRestriction.objects.filter(page=self.public_page).exists()
        )

        restriction = PageViewRestriction.objects.get(page=self.public_page)

        # restriction_type should be 'admin'
        self.assertEqual(restriction.restriction_type, PageViewRestriction.ADMIN)

        # Be sure there is no password or group set
        self.assertEqual(restriction.password, "")
        self.assertFalse(restriction.groups.all().exists())
