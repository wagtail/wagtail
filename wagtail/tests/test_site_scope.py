from django.core.cache import cache
from django.db import connection
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import translation

from wagtail.coreutils import get_dummy_request
from wagtail.models import Locale, Site, get_current_site
from wagtail.models.sites import (
    SITE_ROOT_PATHS_CACHE_KEY,
    SITE_ROOT_PATHS_CACHE_VERSION,
    STASH_SITE_ROOT_PATHS,
    WAGTAIL_STASH_SCOPE,
    find_site_scope_for_page,
    wagtail_site_stash_scope,
)
from wagtail.rich_text import expand_db_html
from wagtail.test.utils import Page, PageFixturesMixin
from wagtail.utils.stash import get as stash_get


def _run_with_site_scope(request, view, site=None):
    with wagtail_site_stash_scope(request, site=site):
        return view(request)


class TranslationCleanupMixin:
    def tearDown(self):
        translation.deactivate()


@override_settings(
    ALLOWED_HOSTS=[
        "localhost",
        "testserver",
        "events.example.com",
        "second-events.example.com",
    ]
)
class TestSiteScopeBasics(PageFixturesMixin, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.site = Site.objects.get(is_default_site=True)
        self.request = get_dummy_request(site=self.site)

    def test_get_current_site_inside_scope(self):
        captured = {}

        def view(request):
            captured["site"] = get_current_site()
            return HttpResponse("ok")

        _run_with_site_scope(self.request, view)
        self.assertEqual(captured["site"], self.site)
        self.assertIsNone(get_current_site())

    def test_explicit_site_overrides_request_hostname(self):
        events_page = Page.objects.get(url_path="/home/events/")
        events_site = Site.objects.create(
            hostname="events.example.com", root_page=events_page
        )
        captured = {}

        def view(request):
            captured["site"] = get_current_site()
            return HttpResponse("ok")

        request = get_dummy_request(site=self.site)
        _run_with_site_scope(request, view, site=events_site)
        self.assertEqual(captured["site"], events_site)

    def test_site_loader_called_once(self):
        calls = []

        def view(request):
            calls.append(get_current_site())
            calls.append(get_current_site())
            return HttpResponse("ok")

        _run_with_site_scope(self.request, view)
        self.assertEqual(calls, [self.site, self.site])

    def test_template_response_render_still_in_scope(self):
        captured = {}

        def view(request):
            response = TemplateResponse(
                request, "tests/blocks/include_block_test.html", {"test_block": "ok"}
            )
            response.render()
            captured["site"] = get_current_site()
            return response

        _run_with_site_scope(self.request, view)
        self.assertEqual(captured["site"], self.site)

    def test_site_root_paths_are_stashed(self):
        cache.delete(SITE_ROOT_PATHS_CACHE_KEY, version=SITE_ROOT_PATHS_CACHE_VERSION)

        def view(request):
            first = Site.get_site_root_paths()
            self.assertIsNotNone(
                stash_get(STASH_SITE_ROOT_PATHS, scope=WAGTAIL_STASH_SCOPE)
            )
            with CaptureQueriesContext(connection) as ctx:
                second = Site.get_site_root_paths()
            self.assertEqual(first, second)
            self.assertEqual(len(ctx), 0)
            return HttpResponse("ok")

        _run_with_site_scope(self.request, view)

    def test_explicit_site_injects_site_root_paths_into_scope(self):
        cache.delete(SITE_ROOT_PATHS_CACHE_KEY, version=SITE_ROOT_PATHS_CACHE_VERSION)
        events_page = Page.objects.get(url_path="/home/events/")
        events_site = Site.objects.create(
            hostname="events.example.com", root_page=events_page
        )
        site_root_paths = Site.get_site_root_paths()
        captured = {}

        with wagtail_site_stash_scope(
            self.request, site=events_site, site_root_paths=site_root_paths
        ):
            self.assertEqual(get_current_site(), events_site)
            self.assertEqual(
                stash_get(STASH_SITE_ROOT_PATHS, scope=WAGTAIL_STASH_SCOPE),
                site_root_paths,
            )
            with CaptureQueriesContext(connection) as ctx:
                captured["paths"] = Site.get_site_root_paths()
            captured["query_count"] = len(ctx)

        self.assertEqual(captured["paths"], site_root_paths)
        self.assertEqual(captured["query_count"], 0)

    def test_clear_site_root_paths_cache_clears_stash(self):
        def view(request):
            Site.get_site_root_paths()
            self.assertIsNotNone(
                stash_get(STASH_SITE_ROOT_PATHS, scope=WAGTAIL_STASH_SCOPE)
            )
            Site.clear_site_root_paths_cache()
            self.assertIsNone(
                stash_get(STASH_SITE_ROOT_PATHS, scope=WAGTAIL_STASH_SCOPE)
            )
            return HttpResponse("ok")

        _run_with_site_scope(self.request, view)


@override_settings(
    ALLOWED_HOSTS=[
        "localhost",
        "testserver",
        "events.example.com",
        "second-events.example.com",
    ]
)
class TestGetUrlPartsUsesStashedSite(PageFixturesMixin, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        events_page = Page.objects.get(url_path="/home/events/")
        self.events_site = Site.objects.create(
            hostname="events.example.com", root_page=events_page
        )
        self.second_events_site = Site.objects.create(
            hostname="second-events.example.com", root_page=events_page
        )
        self.christmas_page = Page.objects.get(url_path="/home/events/christmas/")
        Site.clear_site_root_paths_cache()

    def test_without_scope_matches_existing_behaviour(self):
        self.assertEqual(
            self.christmas_page.get_url_parts(),
            (self.events_site.id, "http://events.example.com", "/christmas/"),
        )
        request = get_dummy_request(site=self.second_events_site)
        self.assertEqual(
            self.christmas_page.get_url_parts(request=request),
            (
                self.second_events_site.id,
                "http://second-events.example.com",
                "/christmas/",
            ),
        )

    def test_stashed_site_used_when_request_not_passed(self):
        captured = {}

        def view(request):
            captured["parts"] = self.christmas_page.get_url_parts()
            captured["url"] = self.christmas_page.get_url()
            return HttpResponse("ok")

        request = get_dummy_request(site=self.second_events_site)
        _run_with_site_scope(request, view)
        self.assertEqual(
            captured["parts"],
            (
                self.second_events_site.id,
                "http://second-events.example.com",
                "/christmas/",
            ),
        )
        self.assertEqual(captured["url"], "/christmas/")

    def test_explicit_request_is_unchanged_when_stash_has_another_site(self):
        captured = {}

        def view(request):
            other = get_dummy_request(site=self.events_site)
            captured["parts"] = self.christmas_page.get_url_parts(request=other)
            captured["url"] = self.christmas_page.get_url(request=other)
            return HttpResponse("ok")

        _run_with_site_scope(get_dummy_request(site=self.second_events_site), view)
        self.assertEqual(
            captured["parts"],
            (self.events_site.id, "http://events.example.com", "/christmas/"),
        )
        self.assertEqual(captured["url"], "/christmas/")

    def test_multiple_page_url_resolutions_reuse_stashed_values(self):
        events_index = Page.objects.get(url_path="/home/events/")
        cache.delete(SITE_ROOT_PATHS_CACHE_KEY, version=SITE_ROOT_PATHS_CACHE_VERSION)
        request = get_dummy_request(site=self.second_events_site)

        with wagtail_site_stash_scope(request):
            self.christmas_page.get_url_parts()
            with CaptureQueriesContext(connection) as ctx:
                self.christmas_page.get_url_parts()
                events_index.get_url_parts()
                self.christmas_page.get_url()
                events_index.get_url()

        self.assertEqual(len(ctx), 0)

    def test_injected_site_scope_reuses_values_for_multiple_page_urls(self):
        events_index = Page.objects.get(url_path="/home/events/")
        cache.delete(SITE_ROOT_PATHS_CACHE_KEY, version=SITE_ROOT_PATHS_CACHE_VERSION)
        site, site_root_paths = find_site_scope_for_page(self.christmas_page)
        request = get_dummy_request(site=self.events_site)

        with wagtail_site_stash_scope(
            request, site=site, site_root_paths=site_root_paths
        ):
            with CaptureQueriesContext(connection) as ctx:
                self.christmas_page.get_url_parts()
                events_index.get_url_parts()
                self.christmas_page.get_url()
                events_index.get_url()

        self.assertEqual(len(ctx), 0)


@override_settings(
    ALLOWED_HOSTS=["localhost", "testserver", "en.example.com", "fr.example.com"],
    WAGTAIL_I18N_ENABLED=True,
    WAGTAIL_CONTENT_LANGUAGES=[
        ("en", "English"),
        ("fr", "French"),
    ],
    ROOT_URLCONF="wagtail.test.urls_multilang",
)
class TestRichTextUsesStashedSite(TranslationCleanupMixin, PageFixturesMixin, TestCase):
    fixtures = ["test.json"]

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

    def test_expand_db_html_without_request_uses_stashed_site(self):
        captured = {}

        def view(request):
            with translation.override("fr"):
                captured["html"] = expand_db_html(self.link_html)
            return HttpResponse("ok")

        _run_with_site_scope(get_dummy_request(site=self.fr_site), view)
        self.assertIn('href="/fr/events/noel/"', captured["html"])
        self.assertNotIn("en.example.com", captured["html"])

    def test_expand_db_html_without_scope_keeps_legacy_behaviour(self):
        with translation.override("fr"):
            result = expand_db_html(self.link_html)
        self.assertTrue(result.startswith("<a href="))
        self.assertIsNone(get_current_site())


@override_settings(
    ALLOWED_HOSTS=["localhost", "testserver", "en.example.com", "fr.example.com"],
    WAGTAIL_I18N_ENABLED=True,
    WAGTAIL_CONTENT_LANGUAGES=[
        ("en", "English"),
        ("fr", "French"),
    ],
    ROOT_URLCONF="wagtail.test.urls_multilang",
)
class TestPreviewSiteScope(TranslationCleanupMixin, PageFixturesMixin, TestCase):
    fixtures = ["test.json"]

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

    def test_find_site_scope_for_page_prefers_page_locale(self):
        site, site_root_paths = find_site_scope_for_page(self.fr_event_page.specific)
        self.assertEqual(site, self.fr_site)
        self.assertTrue(site_root_paths)

    def test_page_site_scope_resolves_urls_for_page_locale(self):
        site, site_root_paths = find_site_scope_for_page(self.fr_event_page.specific)
        request = get_dummy_request(site=self.en_site)
        captured = {}

        def view(request):
            with wagtail_site_stash_scope(
                request, site=site, site_root_paths=site_root_paths
            ):
                with translation.override("fr"):
                    captured["html"] = expand_db_html(self.link_html)
            return HttpResponse("ok")

        view(request)
        self.assertIn('href="/fr/events/noel/"', captured["html"])
        self.assertNotIn("en.example.com", captured["html"])
