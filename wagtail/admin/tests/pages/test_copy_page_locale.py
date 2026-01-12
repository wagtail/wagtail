from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from wagtail.models import Locale, Page
from wagtail.test.testapp.models import SimplePage
from wagtail.test.utils import WagtailTestUtils

class TestPageCopyLocale(WagtailTestUtils, TestCase):
    def setUp(self):
        self.root_page = Page.objects.get(id=2)
        self.user = self.login()
        
        self.en_locale = Locale.get_default()
        self.fr_locale = Locale.objects.create(language_code="fr")
        
        self.en_page = self.root_page.add_child(
            instance=SimplePage(title="English Page", slug="en-page", content="hello")
        )
        
        self.fr_home = self.root_page.add_child(
            instance=SimplePage(title="French Home", slug="fr-home", content="bonjour", locale=self.fr_locale)
        )

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_page_copy_mismatching_locale(self):
        post_data = {
            "new_title": "Copied Page",
            "new_slug": "en-page-copy",
            "new_parent_page": self.fr_home.id,
            "copy_subpages": False,
            "publish_copies": False,
        }
        response = self.client.post(
            reverse("wagtailadmin_pages:copy", args=(self.en_page.id,)),
            post_data
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "new_parent_page",
            "The parent page must have the same locale (English) as the page being copied."
        )

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_page_copy_matching_locale(self):
        en_parent = self.root_page.add_child(
            instance=SimplePage(title="English Parent", slug="en-parent", content="hello")
        )
        
        post_data = {
            "new_title": "Copied Page",
            "new_slug": "en-page-copy",
            "new_parent_page": en_parent.id,
            "copy_subpages": False,
            "publish_copies": False,
        }
        response = self.client.post(
            reverse("wagtailadmin_pages:copy", args=(self.en_page.id,)),
            post_data
        )
        
        self.assertEqual(response.status_code, 302)
        
        copy = Page.objects.get(slug="en-page-copy")
        self.assertEqual(copy.locale, self.en_page.locale)
