from django.test import TestCase
from django.urls import reverse

from wagtail.contrib.redirects.models import Redirect
from wagtail.models import Page, Site


class TestRedirectsAPI(TestCase):
    def setUp(self):
        self.example_home = Page.objects.get(slug="home").add_sibling(
            instance=Page(title="Example Homepage", slug="example-home")
        )
        self.example_page = self.example_home.add_child(
            instance=Page(title="Example Page", slug="example-page")
        )
        self.example_site = Site.objects.create(
            hostname="example", root_page=self.example_home
        )

        Redirect.objects.create(
            old_path="/hello-world",
            site=self.example_site,
            redirect_link="https://www.example.com/hello-world/",
        )

        Redirect.objects.create(
            old_path="/good-work",
            site=self.example_site,
            redirect_link="https://www.example.com/hello-world/",
        )

        Redirect.add_redirect(
            old_path="/hello-world", redirect_to="https://www.example.net/new-world/"
        )

        Redirect.add_redirect(
            old_path="/old-example", redirect_to=self.example_home, is_permanent=False
        )

        Redirect.add_redirect(
            old_path="/old-example?bar=foo&foo=bar",
            redirect_to=self.example_page,
            is_permanent=False,
        )

    def test_redirects_listing(self):
        """Returns a list of all redirects"""

        url = reverse("wagtailapi_v2:redirects:listing")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(5, len(response.json()["items"]))

        item = response.json()["items"][0]

        self.assertEqual("https://www.example.com/hello-world/", item["location"])
        self.assertEqual("/hello-world", item["old_path"])

    def test_redirect(self):
        """Returns a matching (not site specific) redirect"""

        url = reverse("wagtailapi_v2:redirects:find")

        html_path = "/hello-world"

        # Add the html_path to the URL
        url += f"?html_path={html_path}"

        response = self.client.get(url)

        # Check for a redirect status code
        self.assertEqual(response.status_code, 302)

        # Follow the redirect to get the final response
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        response_id = response.json()["id"]

        expected_dict = {
            "id": response_id,
            "meta": {
                "detail_url": f"http://localhost/api/main/redirects/{response_id}/",
                "type": "wagtailredirects.Redirect",
            },
            "old_path": "/hello-world",
            "location": "https://www.example.net/new-world/",
        }

        self.assertEqual(response.json(), expected_dict)

    def test_html_path_without_redirect(self):
        html_path = "/good-work"

        url = reverse("wagtailapi_v2:redirects:find")

        # Add the html_path to the URL
        url += f"?html_path={html_path}"

        response = self.client.get(url)

        # Check for a 404 status code
        self.assertEqual(response.status_code, 404)
