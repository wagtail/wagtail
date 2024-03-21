from unittest import mock

from django.test import TestCase
from django.urls import reverse

from wagtail.coreutils import get_dummy_request
from wagtail.models import Page, Site
from wagtail.test.testapp.models import SimplePage
from wagtail.test.utils import WagtailTestUtils
from wagtail.views import serve


class TestLoginView(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        self.user = self.create_test_user()
        self.events_index = Page.objects.get(url_path="/home/events/")

    def test_get(self):
        response = self.client.get(reverse("wagtailcore_login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h1>Log in</h1>")
        self.assertNotContains(
            response,
            "<p>Your username and password didn't match. Please try again.</p>",
        )

    def test_post_incorrect_password(self):
        response = self.client.post(
            reverse("wagtailcore_login"),
            {
                "username": "test@email.com",
                "password": "wrongpassword",
                "next": self.events_index.url,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h1>Log in</h1>")
        self.assertContains(
            response,
            "<p>Your username and password didn't match. Please try again.</p>",
        )

    def test_post_correct_password(self):
        response = self.client.post(
            reverse("wagtailcore_login"),
            {
                "username": "test@email.com",
                "password": "password",
                "next": self.events_index.url,
            },
        )
        self.assertRedirects(response, self.events_index.url)


class TestServeView(TestCase):
    fixtures = ["test.json"]

    @mock.patch('wagtail.hooks.get_hooks')
    def test_serve_query_count(self, mocked_get_hooks):
        mocked_get_hooks.return_value = []
        request = get_dummy_request()
        Site.find_for_request(request)
        page, args, kwargs = Page.find_for_request(request, request.path)
        with mock.patch.object(page, 'serve', wraps=page.serve) as m:
            with self.assertNumQueries(0):
                serve(request, '/')
            m.assert_called_once_with(request, *args, **kwargs)

    def test_process_view_by_page(self):
        site = Site.objects.get()
        page = site.root_page.add_child(
            instance=SimplePage(
                title="Simple page", slug="simple", content="Simple"
            )
        )
        with self.modify_settings(
            MIDDLEWARE={
                "prepend": "wagtail.test.middleware.SimplePageViewInterceptorMiddleware"
            }
        ):
            response_a = self.client.get('/simple/')
            self.assertEqual(response_a.content, b'\n\n\n\n<!DOCTYPE HTML>\n<html lang="en" dir="ltr">\n    <head>\n        <title>Simple page</title>\n    </head>\n    <body>\n        \n        <h1>Simple page</h1>\n        \n    <h2>Simple page</h2>\n\n    </body>\n</html>\n')
            page.content = "Intercept me"
            page.save_revision().publish()
            response_b = self.client.get('/simple/')
            self.assertEqual(response_b.content, b'Intercepted')
