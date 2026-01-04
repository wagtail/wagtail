from django.contrib.auth.models import Permission
from django.test import SimpleTestCase, TestCase
from django.test.utils import override_settings
from django.urls import reverse

from wagtail.admin.menu import admin_menu
from wagtail.coreutils import get_dummy_request
from wagtail.snippets.models import SNIPPET_MODELS
from wagtail.snippets.views.snippets import get_snippet_models_for_index_view
from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.template_tests import AdminTemplateTestUtils


class TestGetSnippetModelsForIndexView(SimpleTestCase):
    def test_default_lists_all_snippets_without_menu_items(self):
        self.assertEqual(
            get_snippet_models_for_index_view(),
            [
                model
                for model in SNIPPET_MODELS
                if not model.snippet_viewset.get_menu_item_is_registered()
            ],
        )

    @override_settings(WAGTAILSNIPPETS_MENU_SHOW_ALL=True)
    def test_setting_allows_listing_of_all_snippet_models(self):
        self.assertEqual(get_snippet_models_for_index_view(), SNIPPET_MODELS)


class TestSnippetIndexView(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()

    def get(self, params=None):
        return self.client.get(reverse("wagtailsnippets:index"), params)

    def test_get_with_limited_permissions(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.get()
        self.assertEqual(response.status_code, 302)

    def test_get_with_only_view_permissions(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            ),
            Permission.objects.get(
                content_type__app_label="tests", codename="view_advert"
            ),
        )
        self.user.save()

        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/listing.html")
        soup = self.get_soup(response.content)
        link = soup.select_one("tr td a")
        self.assertEqual(link["href"], reverse("wagtailsnippets_tests_advert:list"))
        self.assertEqual(link.text.strip(), "Adverts")

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/listing.html")
        self.assertBreadcrumbsItemsRendered(
            [{"url": "", "label": "Snippets"}],
            response.content,
        )
        # Now that it uses the generic template,
        # it should not contain the locale selector
        self.assertNotContains(response, "data-locale-selector")

    def test_displays_snippet(self):
        self.assertContains(self.get(), "Adverts")

    def test_snippets_menu_item_shown_with_only_view_permission(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            ),
            Permission.objects.get(
                content_type__app_label="tests", codename="view_advert"
            ),
        )
        self.user.save()

        request = get_dummy_request()
        request.user = self.user
        menu_items = admin_menu.menu_items_for_request(request)
        snippets = [item for item in menu_items if item.name == "snippets"]
        self.assertEqual(len(snippets), 1)
        item = snippets[0]
        self.assertEqual(item.name, "snippets")
        self.assertEqual(item.label, "Snippets")
        self.assertEqual(item.icon_name, "snippet")
        self.assertEqual(item.url, reverse("wagtailsnippets:index"))
