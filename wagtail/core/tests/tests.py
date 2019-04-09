from django import template
from django.core.cache import cache
from django.http import HttpRequest
from django.test import TestCase
from django.urls.exceptions import NoReverseMatch
from django.utils.safestring import SafeText

from wagtail.core.models import Page, Site
from wagtail.core.templatetags.wagtailcore_tags import richtext, slugurl
from wagtail.core.utils import resolve_model_string
from wagtail.tests.testapp.models import SimplePage


class TestPageUrlTags(TestCase):
    fixtures = ['test.json']

    def test_pageurl_tag(self):
        response = self.client.get('/events/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                            '<a href="/events/christmas/">Christmas</a>')

    def test_pageurl_fallback(self):
        tpl = template.Template('''{% load wagtailcore_tags %}<a href="{% pageurl page fallback='fallback' %}">Fallback</a>''')
        result = tpl.render(template.Context({'page': None}))
        self.assertIn('<a href="/fallback/">Fallback</a>', result)

    def test_pageurl_fallback_without_valid_fallback(self):
        tpl = template.Template('''{% load wagtailcore_tags %}<a href="{% pageurl page fallback='not-existing-endpoint' %}">Fallback</a>''')
        with self.assertRaises(NoReverseMatch):
            tpl.render(template.Context({'page': None}))

    def test_slugurl_tag(self):
        response = self.client.get('/events/christmas/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                            '<a href="/events/">Back to events index</a>')

    def test_pageurl_without_request_in_context(self):
        page = Page.objects.get(url_path='/home/events/')
        tpl = template.Template('''{% load wagtailcore_tags %}<a href="{% pageurl page %}">{{ page.title }}</a>''')

        # no 'request' object in context
        result = tpl.render(template.Context({'page': page}))
        self.assertIn('<a href="/events/">Events</a>', result)

        # 'request' object in context, but no 'site' attribute
        result = tpl.render(template.Context({'page': page, 'request': HttpRequest()}))
        self.assertIn('<a href="/events/">Events</a>', result)

    def test_bad_pageurl(self):
        tpl = template.Template('''{% load wagtailcore_tags %}<a href="{% pageurl page %}">{{ page.title }}</a>''')

        with self.assertRaisesRegex(ValueError, "pageurl tag expected a Page object, got None"):
            tpl.render(template.Context({'page': None}))

    def test_bad_slugurl(self):
        # no 'request' object in context
        result = slugurl(template.Context({}), 'bad-slug-doesnt-exist')
        self.assertEqual(result, None)

        # 'request' object in context, but no 'site' attribute
        result = slugurl(context=template.Context({'request': HttpRequest()}), slug='bad-slug-doesnt-exist')
        self.assertEqual(result, None)

    def test_slugurl_tag_returns_url_for_current_site(self):
        home_page = Page.objects.get(url_path='/home/')
        new_home_page = home_page.copy(update_attrs={'title': "New home page", 'slug': 'new-home'})
        second_site = Site.objects.create(hostname='site2.example.com', root_page=new_home_page)
        # Add a page to the new site that has a slug that is the same as one on
        # the first site, but is in a different position in the treeself.
        new_christmas_page = Page(title='Christmas', slug='christmas')
        new_home_page.add_child(instance=new_christmas_page)
        request = HttpRequest()
        request.site = second_site
        url = slugurl(context=template.Context({'request': request}), slug='christmas')
        self.assertEqual(url, '/christmas/')

    def test_slugurl_tag_returns_url_for_other_site(self):
        home_page = Page.objects.get(url_path='/home/')
        new_home_page = home_page.copy(update_attrs={'title': "New home page", 'slug': 'new-home'})
        second_site = Site.objects.create(hostname='site2.example.com', root_page=new_home_page)
        request = HttpRequest()
        request.site = second_site
        # There is no page with this slug on the current site, so this
        # should return an absolute URL for the page on the first site.
        url = slugurl(slug='christmas', context=template.Context({'request': request}))
        self.assertEqual(url, 'http://localhost/events/christmas/')

    def test_slugurl_without_request_in_context(self):
        # no 'request' object in context
        result = slugurl(template.Context({}), 'events')
        self.assertEqual(result, '/events/')

        # 'request' object in context, but no 'site' attribute
        result = slugurl(template.Context({'request': HttpRequest()}), 'events')
        self.assertEqual(result, '/events/')


class TestSiteRootPathsCache(TestCase):
    fixtures = ['test.json']

    def test_cache(self):
        """
        This tests that the cache is populated when building URLs
        """
        # Get homepage
        homepage = Page.objects.get(url_path='/home/')

        # Warm up the cache by getting the url
        _ = homepage.url  # noqa

        # Check that the cache has been set correctly
        self.assertEqual(cache.get('wagtail_site_root_paths'), [(1, '/home/', 'http://localhost')])

    def test_cache_clears_when_site_saved(self):
        """
        This tests that the cache is cleared whenever a site is saved
        """
        # Get homepage
        homepage = Page.objects.get(url_path='/home/')

        # Warm up the cache by getting the url
        _ = homepage.url  # noqa

        # Check that the cache has been set
        self.assertTrue(cache.get('wagtail_site_root_paths'))

        # Save the site
        Site.objects.get(is_default_site=True).save()

        # Check that the cache has been cleared
        self.assertFalse(cache.get('wagtail_site_root_paths'))

    def test_cache_clears_when_site_deleted(self):
        """
        This tests that the cache is cleared whenever a site is deleted
        """
        # Get homepage
        homepage = Page.objects.get(url_path='/home/')

        # Warm up the cache by getting the url
        _ = homepage.url  # noqa

        # Check that the cache has been set
        self.assertTrue(cache.get('wagtail_site_root_paths'))

        # Delete the site
        Site.objects.get(is_default_site=True).delete()

        # Check that the cache has been cleared
        self.assertFalse(cache.get('wagtail_site_root_paths'))

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
        homepage = Page.objects.get(url_path='/home/')
        default_site = Site.objects.get(is_default_site=True)

        # Create a new homepage under current homepage
        new_homepage = SimplePage(title="New Homepage", slug="new-homepage", content="hello")
        homepage.add_child(instance=new_homepage)

        # Set new homepage as the site root page
        default_site.root_page = new_homepage
        default_site.save()

        # Warm up the cache by getting the url
        _ = homepage.url  # noqa

        # Move new homepage to root
        new_homepage.move(root_page, pos='last-child')

        # Get fresh instance of new_homepage
        new_homepage = Page.objects.get(id=new_homepage.id)

        # Check url
        self.assertEqual(new_homepage.url, '/')

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
        homepage = Page.objects.get(url_path='/home/')

        # Warm up the cache by getting the url
        _ = homepage.url  # noqa

        # Change homepage title and slug
        homepage.title = "New home"
        homepage.slug = "new-home"
        homepage.save()

        # Get fresh instance of homepage
        homepage = Page.objects.get(id=homepage.id)

        # Check url
        self.assertEqual(homepage.url, '/')


class TestResolveModelString(TestCase):
    def test_resolve_from_string(self):
        model = resolve_model_string('wagtailcore.Page')

        self.assertEqual(model, Page)

    def test_resolve_from_string_with_default_app(self):
        model = resolve_model_string('Page', default_app='wagtailcore')

        self.assertEqual(model, Page)

    def test_resolve_from_string_with_different_default_app(self):
        model = resolve_model_string('wagtailcore.Page', default_app='wagtailadmin')

        self.assertEqual(model, Page)

    def test_resolve_from_class(self):
        model = resolve_model_string(Page)

        self.assertEqual(model, Page)

    def test_resolve_from_string_invalid(self):
        self.assertRaises(ValueError, resolve_model_string, 'wagtail.core.Page')

    def test_resolve_from_string_with_incorrect_default_app(self):
        self.assertRaises(LookupError, resolve_model_string, 'Page', default_app='wagtailadmin')

    def test_resolve_from_string_with_unknown_model_string(self):
        self.assertRaises(LookupError, resolve_model_string, 'wagtailadmin.Page')

    def test_resolve_from_string_with_no_default_app(self):
        self.assertRaises(ValueError, resolve_model_string, 'Page')

    def test_resolve_from_class_that_isnt_a_model(self):
        self.assertRaises(ValueError, resolve_model_string, object)

    def test_resolve_from_bad_type(self):
        self.assertRaises(ValueError, resolve_model_string, resolve_model_string)

    def test_resolve_from_none(self):
        self.assertRaises(ValueError, resolve_model_string, None)


class TestRichtextTag(TestCase):
    def test_call_with_text(self):
        result = richtext("Hello world!")
        self.assertEqual(result, '<div class="rich-text">Hello world!</div>')
        self.assertIsInstance(result, SafeText)

    def test_call_with_none(self):
        result = richtext(None)
        self.assertEqual(result, '<div class="rich-text"></div>')

    def test_call_with_invalid_value(self):
        with self.assertRaisesRegex(TypeError, "'richtext' template filter received an invalid value"):
            richtext(42)

    def test_call_with_bytes(self):
        with self.assertRaisesRegex(TypeError, "'richtext' template filter received an invalid value"):
            richtext(b"Hello world!")
