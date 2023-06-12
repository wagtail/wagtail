import json

from django import template
from django.core.cache import cache
from django.http import HttpRequest
from django.test import TestCase
from django.test.utils import override_settings
from django.urls.exceptions import NoReverseMatch
from django.utils.safestring import SafeString

from wagtail.coreutils import get_dummy_request, resolve_model_string
from wagtail.models import Locale, Page, Site, SiteRootPath
from wagtail.models.sites import (
    SITE_ROOT_PATHS_CACHE_KEY,
    SITE_ROOT_PATHS_CACHE_VERSION,
)
from wagtail.templatetags.wagtailcore_tags import richtext, slugurl
from wagtail.test.testapp.models import SimplePage


class TestPageUrlTags(TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        super().setUp()

        # Clear caches
        cache.clear()

    def test_pageurl_tag(self):
        response = self.client.get("/events/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<a href="/events/christmas/">Christmas</a>')

    def test_pageurl_with_named_url_fallback(self):
        tpl = template.Template(
            """{% load wagtailcore_tags %}<a href="{% pageurl page fallback='fallback' %}">Fallback</a>"""
        )
        with self.assertNumQueries(0):
            result = tpl.render(template.Context({"page": None}))
        self.assertIn('<a href="/fallback/">Fallback</a>', result)

    def test_pageurl_with_get_absolute_url_object_fallback(self):
        class ObjectWithURLMethod:
            def get_absolute_url(self):
                return "/object-specific-url/"

        tpl = template.Template(
            """{% load wagtailcore_tags %}<a href="{% pageurl page fallback=object_with_url_method %}">Fallback</a>"""
        )
        result = tpl.render(
            template.Context(
                {"page": None, "object_with_url_method": ObjectWithURLMethod()}
            )
        )
        self.assertIn('<a href="/object-specific-url/">Fallback</a>', result)

    def test_pageurl_with_valid_url_string_fallback(self):
        """
        `django.shortcuts.resolve_url` accepts strings containing '.' or '/' as they are.
        """
        tpl = template.Template(
            """
            {% load wagtailcore_tags %}
            <a href="{% pageurl page fallback='.' %}">Same page fallback</a>
            <a href="{% pageurl page fallback='/' %}">Homepage fallback</a>
            <a href="{% pageurl page fallback='../' %}">Up one step fallback</a>
            """
        )
        result = tpl.render(template.Context({"page": None}))
        self.assertIn('<a href=".">Same page fallback</a>', result)
        self.assertIn('<a href="/">Homepage fallback</a>', result)
        self.assertIn('<a href="../">Up one step fallback</a>', result)

    def test_pageurl_with_invalid_url_string_fallback(self):
        """
        Strings not containing '.' or '/', and not matching a named URL will error.
        """
        tpl = template.Template(
            """{% load wagtailcore_tags %}<a href="{% pageurl page fallback='not-existing-endpoint' %}">Fallback</a>"""
        )
        with self.assertRaises(NoReverseMatch):
            tpl.render(template.Context({"page": None}))

    def test_slugurl_tag(self):
        response = self.client.get("/events/christmas/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<a href="/events/">Back to events index</a>')

    def test_pageurl_without_request_in_context(self):
        page = Page.objects.get(url_path="/home/events/")
        tpl = template.Template(
            """{% load wagtailcore_tags %}<a href="{% pageurl page %}">{{ page.title }}</a>"""
        )

        # no 'request' object in context
        with self.assertNumQueries(7):
            result = tpl.render(template.Context({"page": page}))
        self.assertIn('<a href="/events/">Events</a>', result)

        # 'request' object in context, but no 'site' attribute
        result = tpl.render(
            template.Context({"page": page, "request": get_dummy_request()})
        )
        self.assertIn('<a href="/events/">Events</a>', result)

    def test_pageurl_caches(self):
        page = Page.objects.get(url_path="/home/events/")
        tpl = template.Template(
            """{% load wagtailcore_tags %}<a href="{% pageurl page %}">{{ page.title }}</a>"""
        )

        request = get_dummy_request()

        with self.assertNumQueries(8):
            result = tpl.render(template.Context({"page": page, "request": request}))
        self.assertIn('<a href="/events/">Events</a>', result)

        with self.assertNumQueries(0):
            result = tpl.render(template.Context({"page": page, "request": request}))
        self.assertIn('<a href="/events/">Events</a>', result)

    @override_settings(ALLOWED_HOSTS=["testserver", "localhost", "unknown.example.com"])
    def test_pageurl_with_unknown_site(self):
        page = Page.objects.get(url_path="/home/events/")
        tpl = template.Template(
            """{% load wagtailcore_tags %}<a href="{% pageurl page %}">{{ page.title }}</a>"""
        )

        # 'request' object in context, but site is None
        request = get_dummy_request()
        request.META["HTTP_HOST"] = "unknown.example.com"
        with self.assertNumQueries(8):
            result = tpl.render(template.Context({"page": page, "request": request}))
        self.assertIn('<a href="/events/">Events</a>', result)

    def test_bad_pageurl(self):
        tpl = template.Template(
            """{% load wagtailcore_tags %}<a href="{% pageurl page %}">{{ page.title }}</a>"""
        )

        with self.assertRaisesRegex(
            ValueError, "pageurl tag expected a Page object, got None"
        ):
            tpl.render(template.Context({"page": None}))

    def test_bad_slugurl(self):
        # no 'request' object in context
        result = slugurl(template.Context({}), "bad-slug-doesnt-exist")
        self.assertIsNone(result)

        # 'request' object in context, but no 'site' attribute
        result = slugurl(
            context=template.Context({"request": HttpRequest()}),
            slug="bad-slug-doesnt-exist",
        )
        self.assertIsNone(result)

    @override_settings(ALLOWED_HOSTS=["testserver", "localhost", "site2.example.com"])
    def test_slugurl_tag_returns_url_for_current_site(self):
        home_page = Page.objects.get(url_path="/home/")
        new_home_page = home_page.copy(
            update_attrs={"title": "New home page", "slug": "new-home"}
        )
        second_site = Site.objects.create(
            hostname="site2.example.com", root_page=new_home_page
        )
        # Add a page to the new site that has a slug that is the same as one on
        # the first site, but is in a different position in the treeself.
        new_christmas_page = Page(title="Christmas", slug="christmas")
        new_home_page.add_child(instance=new_christmas_page)
        request = get_dummy_request(site=second_site)
        url = slugurl(context=template.Context({"request": request}), slug="christmas")
        self.assertEqual(url, "/christmas/")

    @override_settings(ALLOWED_HOSTS=["testserver", "localhost", "site2.example.com"])
    def test_slugurl_tag_returns_url_for_other_site(self):
        home_page = Page.objects.get(url_path="/home/")
        new_home_page = home_page.copy(
            update_attrs={"title": "New home page", "slug": "new-home"}
        )
        second_site = Site.objects.create(
            hostname="site2.example.com", root_page=new_home_page
        )
        request = get_dummy_request(site=second_site)
        # There is no page with this slug on the current site, so this
        # should return an absolute URL for the page on the first site.
        url = slugurl(slug="christmas", context=template.Context({"request": request}))
        self.assertEqual(url, "http://localhost/events/christmas/")

    def test_slugurl_without_request_in_context(self):
        # no 'request' object in context
        result = slugurl(template.Context({}), "events")
        self.assertEqual(result, "/events/")

        # 'request' object in context, but no 'site' attribute
        with self.assertNumQueries(3):
            result = slugurl(
                template.Context({"request": get_dummy_request()}), "events"
            )
        self.assertEqual(result, "/events/")

    @override_settings(ALLOWED_HOSTS=["testserver", "localhost", "unknown.example.com"])
    def test_slugurl_with_null_site_in_request(self):
        # 'request' object in context, but site is None
        request = get_dummy_request()
        request.META["HTTP_HOST"] = "unknown.example.com"
        result = slugurl(template.Context({"request": request}), "events")
        self.assertEqual(result, "/events/")

    def test_fullpageurl(self):
        tpl = template.Template(
            """{% load wagtailcore_tags %}<a href="{% fullpageurl page %}">Events</a>"""
        )
        page = Page.objects.get(url_path="/home/events/")
        with self.assertNumQueries(7):
            result = tpl.render(template.Context({"page": page}))
        self.assertIn('<a href="http://localhost/events/">Events</a>', result)

    def test_fullpageurl_with_named_url_fallback(self):
        tpl = template.Template(
            """{% load wagtailcore_tags %}<a href="{% fullpageurl page fallback='fallback' %}">Fallback</a>"""
        )
        with self.assertNumQueries(0):
            result = tpl.render(template.Context({"page": None}))
        self.assertIn('<a href="/fallback/">Fallback</a>', result)

    def test_fullpageurl_with_absolute_fallback(self):
        tpl = template.Template(
            """{% load wagtailcore_tags %}<a href="{% fullpageurl page fallback='fallback' %}">Fallback</a>"""
        )
        with self.assertNumQueries(0):
            result = tpl.render(
                template.Context({"page": None, "request": get_dummy_request()})
            )
        self.assertIn('<a href="http://localhost/fallback/">Fallback</a>', result)

    def test_fullpageurl_with_invalid_page(self):
        tpl = template.Template(
            """{% load wagtailcore_tags %}<a href="{% fullpageurl page %}">Events</a>"""
        )
        with self.assertRaises(ValueError):
            tpl.render(template.Context({"page": 123}))

    def test_pageurl_with_invalid_page(self):
        tpl = template.Template(
            """{% load wagtailcore_tags %}<a href="{% pageurl page %}">Events</a>"""
        )
        with self.assertRaises(ValueError):
            tpl.render(template.Context({"page": 123}))


class TestWagtailSiteTag(TestCase):
    fixtures = ["test.json"]

    def test_wagtail_site_tag(self):
        request = get_dummy_request(site=Site.objects.first())

        tpl = template.Template(
            """{% load wagtailcore_tags %}{% wagtail_site as current_site %}{{ current_site.hostname }}"""
        )
        result = tpl.render(template.Context({"request": request}))
        self.assertEqual("localhost", result)

    def test_wagtail_site_tag_with_missing_request_context(self):
        tpl = template.Template(
            """{% load wagtailcore_tags %}{% wagtail_site as current_site %}{{ current_site.hostname }}"""
        )
        result = tpl.render(template.Context({}))
        # should fail silently
        self.assertEqual("", result)


class TestSiteRootPathsCache(TestCase):
    fixtures = ["test.json"]

    def get_cached_site_root_paths(self):
        return cache.get(
            SITE_ROOT_PATHS_CACHE_KEY, version=SITE_ROOT_PATHS_CACHE_VERSION
        )

    def test_cache(self):
        """
        This tests that the cache is populated when building URLs
        """
        # Get homepage
        homepage = Page.objects.get(url_path="/home/")

        # Warm up the cache by getting the url
        _ = homepage.url

        # Check that the cache has been set correctly
        self.assertEqual(
            self.get_cached_site_root_paths(),
            [
                SiteRootPath(
                    site_id=1,
                    root_path="/home/",
                    root_url="http://localhost",
                    language_code="en",
                )
            ],
        )

    def test_cache_backend_uses_json_serialization(self):
        """
        This tests that, even if the cache backend uses JSON serialization,
        get_site_root_paths() returns a list of SiteRootPath objects.
        """
        result = Site.get_site_root_paths()

        self.assertEqual(
            result,
            [
                SiteRootPath(
                    site_id=1,
                    root_path="/home/",
                    root_url="http://localhost",
                    language_code="en",
                )
            ],
        )

        # Go through JSON (de)serialisation to check that the result is
        # still a list of named tuples.
        cache.set(
            SITE_ROOT_PATHS_CACHE_KEY,
            json.loads(json.dumps(result)),
            version=SITE_ROOT_PATHS_CACHE_VERSION,
        )

        result = Site.get_site_root_paths()
        self.assertIsInstance(result[0], SiteRootPath)

    def test_cache_clears_when_site_saved(self):
        """
        This tests that the cache is cleared whenever a site is saved
        """
        # Get homepage
        homepage = Page.objects.get(url_path="/home/")

        # Warm up the cache by getting the url
        _ = homepage.url

        # Check that the cache has been set
        self.assertEqual(
            self.get_cached_site_root_paths(),
            [
                SiteRootPath(
                    site_id=1,
                    root_path="/home/",
                    root_url="http://localhost",
                    language_code="en",
                )
            ],
        )

        # Save the site
        Site.objects.get(is_default_site=True).save()

        # Check that the cache has been cleared
        self.assertIsNone(self.get_cached_site_root_paths())

    def test_cache_clears_when_site_deleted(self):
        """
        This tests that the cache is cleared whenever a site is deleted
        """
        # Get homepage
        homepage = Page.objects.get(url_path="/home/")

        # Warm up the cache by getting the url
        _ = homepage.url

        # Check that the cache has been set
        self.assertEqual(
            self.get_cached_site_root_paths(),
            [
                SiteRootPath(
                    site_id=1,
                    root_path="/home/",
                    root_url="http://localhost",
                    language_code="en",
                )
            ],
        )

        # Delete the site
        Site.objects.get(is_default_site=True).delete()

        # Check that the cache has been cleared
        self.assertIsNone(self.get_cached_site_root_paths())

    def test_cache_clears_when_site_root_moves(self):
        """
        This tests for an issue where if a site root page was moved, all
        the page urls in that site would change to None.

        The issue was caused by the 'wagtail_site_root_paths' cache
        variable not being cleared when a site root page was moved. Which
        left all the child pages thinking that they are no longer in the
        site and return None as their url.

        Fix: d6cce69a397d08d5ee81a8cbc1977ab2c9db2682
        Discussion: https://github.com/wagtail/wagtail/issues/7
        """
        # Get homepage, root page and site
        root_page = Page.objects.get(id=1)
        homepage = Page.objects.get(url_path="/home/")
        default_site = Site.objects.get(is_default_site=True)

        # Create a new homepage under current homepage
        new_homepage = SimplePage(
            title="New Homepage", slug="new-homepage", content="hello"
        )
        homepage.add_child(instance=new_homepage)

        # Set new homepage as the site root page
        default_site.root_page = new_homepage
        default_site.save()

        # Warm up the cache by getting the url
        _ = homepage.url

        # Move new homepage to root
        new_homepage.move(root_page, pos="last-child")

        # Get fresh instance of new_homepage
        new_homepage = Page.objects.get(id=new_homepage.id)

        # Check url
        self.assertEqual(new_homepage.url, "/")

    def test_cache_clears_when_site_root_slug_changes(self):
        """
        This tests for an issue where if a site root pages slug was
        changed, all the page urls in that site would change to None.

        The issue was caused by the 'wagtail_site_root_paths' cache
        variable not being cleared when a site root page was changed.
        Which left all the child pages thinking that they are no longer in
        the site and return None as their url.

        Fix: d6cce69a397d08d5ee81a8cbc1977ab2c9db2682
        Discussion: https://github.com/wagtail/wagtail/issues/157
        """
        # Get homepage
        homepage = Page.objects.get(url_path="/home/")

        # Warm up the cache by getting the url
        _ = homepage.url

        # Change homepage title and slug
        homepage.title = "New home"
        homepage.slug = "new-home"
        homepage.save()

        # Get fresh instance of homepage
        homepage = Page.objects.get(id=homepage.id)

        # Check url
        self.assertEqual(homepage.url, "/")

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_cache_clears_when_site_root_is_translated_as_alias(self):
        # Get homepage
        homepage = Page.objects.get(url_path="/home/")

        # Warm up the cache by getting the url
        _ = homepage.url

        # Translate the homepage
        translated_homepage = homepage.copy_for_translation(
            Locale.objects.create(language_code="fr"), alias=True
        )

        # Check url
        self.assertEqual(translated_homepage.url, "/")


class TestResolveModelString(TestCase):
    def test_resolve_from_string(self):
        model = resolve_model_string("wagtailcore.Page")

        self.assertEqual(model, Page)

    def test_resolve_from_string_with_default_app(self):
        model = resolve_model_string("Page", default_app="wagtailcore")

        self.assertEqual(model, Page)

    def test_resolve_from_string_with_different_default_app(self):
        model = resolve_model_string("wagtailcore.Page", default_app="wagtailadmin")

        self.assertEqual(model, Page)

    def test_resolve_from_class(self):
        model = resolve_model_string(Page)

        self.assertEqual(model, Page)

    def test_resolve_from_string_invalid(self):
        self.assertRaises(ValueError, resolve_model_string, "wagtail.core.Page")

    def test_resolve_from_string_with_incorrect_default_app(self):
        self.assertRaises(
            LookupError, resolve_model_string, "Page", default_app="wagtailadmin"
        )

    def test_resolve_from_string_with_unknown_model_string(self):
        self.assertRaises(LookupError, resolve_model_string, "wagtailadmin.Page")

    def test_resolve_from_string_with_no_default_app(self):
        self.assertRaises(ValueError, resolve_model_string, "Page")

    def test_resolve_from_class_that_isnt_a_model(self):
        self.assertRaises(ValueError, resolve_model_string, object)

    def test_resolve_from_bad_type(self):
        self.assertRaises(ValueError, resolve_model_string, resolve_model_string)

    def test_resolve_from_none(self):
        self.assertRaises(ValueError, resolve_model_string, None)


class TestRichtextTag(TestCase):
    def test_call_with_text(self):
        result = richtext("Hello world!")
        self.assertEqual(result, "Hello world!")
        self.assertIsInstance(result, SafeString)

    def test_call_with_none(self):
        result = richtext(None)
        self.assertEqual(result, "")

    def test_call_with_invalid_value(self):
        with self.assertRaisesRegex(
            TypeError, "'richtext' template filter received an invalid value"
        ):
            richtext(42)

    def test_call_with_bytes(self):
        with self.assertRaisesRegex(
            TypeError, "'richtext' template filter received an invalid value"
        ):
            richtext(b"Hello world!")
