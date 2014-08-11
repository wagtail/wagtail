from django.test import TestCase

from wagtail.wagtailcore.models import Page, Site
from wagtail.tests.models import SimplePage


class TestPageUrlTags(TestCase):
    fixtures = ['test.json']

    def test_pageurl_tag(self):
        response = self.client.get('/events/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                            '<a href="/events/christmas/">Christmas</a>')

    def test_slugurl_tag(self):
        response = self.client.get('/events/christmas/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                            '<a href="/events/">Back to events index</a>')


class TestIssue7(TestCase):
    """
    This tests for an issue where if a site root page was moved, all
    the page urls in that site would change to None.

    The issue was caused by the 'wagtail_site_root_paths' cache
    variable not being cleared when a site root page was moved. Which
    left all the child pages thinking that they are no longer in the
    site and return None as their url.

    Fix: d6cce69a397d08d5ee81a8cbc1977ab2c9db2682
    Discussion: https://github.com/torchbox/wagtail/issues/7
    """

    fixtures = ['test.json']

    def test_issue7(self):
        # Get homepage, root page and site
        root_page = Page.objects.get(id=1)
        homepage = Page.objects.get(url_path='/home/')
        default_site = Site.objects.get(is_default_site=True)

        # Create a new homepage under current homepage
        new_homepage = SimplePage(title="New Homepage", slug="new-homepage")
        homepage.add_child(instance=new_homepage)

        # Set new homepage as the site root page
        default_site.root_page = new_homepage
        default_site.save()

        # Warm up the cache by getting the url
        _ = homepage.url

        # Move new homepage to root
        new_homepage.move(root_page, pos='last-child')

        # Get fresh instance of new_homepage
        new_homepage = Page.objects.get(id=new_homepage.id)

        # Check url
        self.assertEqual(new_homepage.url, '/')


class TestIssue157(TestCase):
    """
    This tests for an issue where if a site root pages slug was
    changed, all the page urls in that site would change to None.

    The issue was caused by the 'wagtail_site_root_paths' cache
    variable not being cleared when a site root page was changed.
    Which left all the child pages thinking that they are no longer in
    the site and return None as their url.

    Fix: d6cce69a397d08d5ee81a8cbc1977ab2c9db2682
    Discussion: https://github.com/torchbox/wagtail/issues/157
    """

    fixtures = ['test.json']

    def test_issue157(self):
        # Get homepage
        homepage = Page.objects.get(url_path='/home/')

        # Warm up the cache by getting the url
        _ = homepage.url

        # Change homepage title and slug
        homepage.title = "New home"
        homepage.slug = "new-home"
        homepage.save()

        # Get fresh instance of homepage
        homepage = Page.objects.get(id=homepage.id)

        # Check url
        self.assertEqual(homepage.url, '/')
