from http import HTTPStatus

from django.test import TestCase, modify_settings
from django.urls import reverse

from wagtail.contrib.redirects.models import Redirect
from wagtail.models import Page, Site


@modify_settings(ALLOWED_HOSTS={"append": "example"})
class TestRedirectsAPI(TestCase):
    @classmethod
    def setUpTestData(cls):
        example_home = Page.objects.get(slug="home").add_sibling(
            instance=Page(title="Example Homepage", slug="example-home")
        )
        example_page = example_home.add_child(
            instance=Page(title="Example Page", slug="example-page")
        )
        example_site = Site.objects.create(hostname="example", root_page=example_home)
        # Site specific redirect for /hello-world
        Redirect.objects.create(
            old_path="/hello-world",
            site=example_site,
            redirect_link="https://www.example.com/hello-world/",
        )
        # Site agnostic redirect for /hello-world (for all sites except example_site)
        Redirect.add_redirect(
            old_path="/hello-world", redirect_to="https://www.example.net/hello-world/"
        )
        # Site agnostic (temporary) redirect to a page in example_site
        Redirect.add_redirect(
            old_path="/old-example", redirect_to=example_home, is_permanent=False
        )
        # Site agnostic (temporary) with a querystring
        Redirect.add_redirect(
            old_path="/old-example?bar=foo&foo=bar",
            redirect_to=example_page,
            is_permanent=False,
        )

    def test_no_filter(self):
        """Requires html_path filter"""
        response = self.client.get(reverse("wagtailapi_v2:redirects:detail"))
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_generic_redirect(self):
        """Returns a matching (not site specific) redirect"""
        response = self.client.get(
            reverse("wagtailapi_v2:redirects:detail"),
            {"html_path": "/hello-world/"},  # Trailing slash is intentional
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Redirect to example.net
        self.assertEqual(
            response.json(),
            {"location": "https://www.example.net/hello-world/", "is_permanent": True},
        )

    def test_site_specific_redirect(self):
        """Returns a site specific redirect"""
        response = self.client.get(
            reverse("wagtailapi_v2:redirects:detail"),
            {"html_path": "/hello-world/"},  # Trailing slash is intentional
            HTTP_HOST="example",
        )
        # Redirect to example.com
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            response.json(),
            {"location": "https://www.example.com/hello-world/", "is_permanent": True},
        )

    def test_page_redirect(self):
        """Returns a redirect to a wagtail page"""
        response = self.client.get(
            reverse("wagtailapi_v2:redirects:detail"),
            {"html_path": "/old-example/"},  # Trailing slash is intentional
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Redirect to example_site homepage (example_home),
        # wagtail doesn't use the slug for site.root_page
        self.assertEqual(
            response.json(), {"location": "http://example/", "is_permanent": False}
        )

    def test_html_path_with_querystring(self):
        """Finds redirect, matching querystring"""
        response = self.client.get(
            reverse("wagtailapi_v2:redirects:detail"),
            {"html_path": "/old-example/?foo=bar&bar=foo"},  # Order shouldn't matter
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Redirect to example.net
        self.assertEqual(
            response.json(),
            {"location": "http://example/example-page/", "is_permanent": False},
        )
