from unittest import mock

from django.test import RequestFactory, TestCase
from django.urls import reverse

from wagtail.models import Page
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
    
    def test_serve_query_count(self):
        request = RequestFactory().get('/')
        
        with self.assertRaises(AssertionError):
            with self.assertNumQueries(0): 
                serve(request, '/')
        
        # we expect the serve view to set and use the request page cache
        with self.assertNumQueries(0): 
            serve(request, '/')
    
    def test_serve_calls_page_find_for_request(self):
        request = RequestFactory().get('/')
        
        with mock.patch(
            "wagtail.models.Page.find_for_request",
        ) as method:
            serve(request, '/')
        method.assert_called_once_with(request, '/')
