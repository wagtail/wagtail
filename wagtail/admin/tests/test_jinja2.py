from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.template import engines
from django.test import TestCase

from wagtail.models import PAGE_TEMPLATE_VAR, Page, Site
from wagtail.test.utils import WagtailTestUtils


class TestCoreJinja(TestCase, WagtailTestUtils):
    def setUp(self):
        self.engine = engines["jinja2"]

        self.user = self.create_superuser(
            username="test", email="test@email.com", password="password"
        )
        self.homepage = Page.objects.get(id=2)

    def render(self, string, context=None, request_context=True):
        if context is None:
            context = {}

        template = self.engine.from_string(string)
        return template.render(context)

    def dummy_request(self, user=None):
        site = Site.objects.get(is_default_site=True)

        request = HttpRequest()
        request.META["HTTP_HOST"] = site.hostname
        request.META["SERVER_PORT"] = site.port
        request.user = user or AnonymousUser()
        return request

    def test_userbar(self):
        content = self.render(
            "{{ wagtailuserbar() }}",
            {
                PAGE_TEMPLATE_VAR: self.homepage,
                "request": self.dummy_request(self.user),
            },
        )
        self.assertIn("<!-- Wagtail user bar embed code -->", content)

    def test_userbar_anonymous_user(self):
        content = self.render(
            "{{ wagtailuserbar() }}",
            {PAGE_TEMPLATE_VAR: self.homepage, "request": self.dummy_request()},
        )

        # Make sure nothing was rendered
        self.assertEqual(content, "")
