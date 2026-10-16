from django.template.response import TemplateResponse
from django.test import TestCase, override_settings
from django.utils import translation

from wagtail.coreutils import get_dummy_request
from wagtail.models import Locale, Site, get_current_site
from wagtail.models.sites import bind_site_scope_on_render, wagtail_site_stash_scope
from wagtail.test.utils import Page, PageFixturesMixin


class TestWagtailSiteStashScope(PageFixturesMixin, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.site = Site.objects.get(is_default_site=True)
        self.request = get_dummy_request(site=self.site)

    def test_opens_scope_and_binds_site(self):
        with wagtail_site_stash_scope(self.request):
            self.assertEqual(get_current_site(), self.site)

        self.assertIsNone(get_current_site())

    def test_noop_when_scope_already_open(self):
        with wagtail_site_stash_scope(self.request):
            with wagtail_site_stash_scope(self.request):
                self.assertEqual(get_current_site(), self.site)


@override_settings(
    ALLOWED_HOSTS=["localhost", "testserver", "en.example.com", "fr.example.com"],
    WAGTAIL_I18N_ENABLED=True,
    WAGTAIL_CONTENT_LANGUAGES=[
        ("en", "English"),
        ("fr", "French"),
    ],
    ROOT_URLCONF="wagtail.test.urls_multilang",
)
class TestBindSiteStashOnRender(PageFixturesMixin, TestCase):
    fixtures = ["test.json"]

    def tearDown(self):
        translation.deactivate()

    def setUp(self):
        self.en_site = Site.objects.get(is_default_site=True)
        self.en_site.hostname = "en.example.com"
        self.en_site.save()

        homepage = Page.objects.get(url_path="/home/")
        self.fr_locale = Locale.objects.create(language_code="fr")
        self.fr_homepage = homepage.copy_for_translation(self.fr_locale)
        self.fr_homepage.save_revision().publish()
        self.fr_site = Site.objects.create(
            hostname="fr.example.com",
            root_page=self.fr_homepage,
        )

        self.event_page = Page.objects.get(url_path="/home/events/christmas/")
        self.fr_event_page = self.event_page.copy_for_translation(
            self.fr_locale, copy_parents=True
        )
        self.fr_event_page.slug = "noel"
        self.fr_event_page.save(update_fields=["slug"])
        self.fr_event_page.save_revision().publish()
        Site.clear_site_root_paths_cache()

        self.link_html = f'<a id="{self.event_page.id}" linktype="page">Christmas</a>'

    def test_render_binds_site_for_richtext_filter(self):
        request = get_dummy_request(site=self.fr_site)
        response = TemplateResponse(
            request,
            "tests/richtext_filter.html",
            {"html": self.link_html},
        )
        bind_site_scope_on_render(response)
        with translation.override("fr"):
            rendered = response.render()

        self.assertIn(b'href="/fr/events/noel/"', rendered.content)
        self.assertIsNone(get_current_site())

    def test_page_serve_resolves_richtext_against_request_site(self):
        response = self.client.get(
            "/fr/events/noel/",
            HTTP_HOST="fr.example.com",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(get_current_site())
