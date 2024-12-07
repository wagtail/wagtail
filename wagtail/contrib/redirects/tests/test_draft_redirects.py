from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from wagtail.models import Page, Site
from wagtail.contrib.redirects.models import Redirect
from wagtail.test.utils import WagtailTestUtils

User = get_user_model()

@override_settings(WAGTAILREDIRECTS_AUTO_CREATE=True)
class TestAutoCreateRedirectsOnDraft(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.select_related("root_page").get(is_default_site=True)
        cls.user = User.objects.first()

    def setUp(self):
        self.home_page = self.site.root_page
        self.test_page = Page(
            title="Test Page",
            slug="test-page",
            content_type=self.home_page.content_type,
            live=True
        )
        self.home_page.add_child(instance=self.test_page)

    def trigger_page_slug_changed_signal(self, page):
        """Helper method to trigger slug change"""
        old_slug = page.slug
        page.slug = f"{old_slug}-changed"
        with self.captureOnCommitCallbacks(execute=True):
            page.save(log_action="wagtail.publish", user=self.user, clean=False)

    def test_redirect_created_for_published_page(self):
        """Test redirect creation for published pages"""
        old_url_path = self.test_page.url_path
        self.trigger_page_slug_changed_signal(self.test_page)

        self.assertTrue(
            Redirect.objects.filter(old_path=old_url_path).exists()
        )

    def test_redirect_not_created_for_draft_by_default(self):
        """Test no redirect creation for draft pages by default"""
        self.test_page.live = False
        self.test_page.save()

        old_url_path = self.test_page.url_path
        self.trigger_page_slug_changed_signal(self.test_page)

        self.assertFalse(
            Redirect.objects.filter(old_path=old_url_path).exists()
        )

    @override_settings(WAGTAILREDIRECTS_AUTO_CREATE_ON_DRAFT=True)
    def test_redirect_created_for_draft_when_enabled(self):
        """Test redirect creation for draft pages when enabled"""
        self.test_page.live = False
        self.test_page.save()

        old_url_path = self.test_page.url_path
        self.trigger_page_slug_changed_signal(self.test_page)

        self.assertTrue(
            Redirect.objects.filter(old_path=old_url_path).exists()
        )

    def tearDown(self):
        self.test_page.delete()
        Redirect.objects.all().delete()