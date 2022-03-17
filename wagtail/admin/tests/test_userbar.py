from django.contrib.auth.models import AnonymousUser
from django.template import Context, Template
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse

from wagtail.models import PAGE_TEMPLATE_VAR, Page
from wagtail.test.testapp.models import BusinessChild, BusinessIndex
from wagtail.test.utils import WagtailTestUtils


class TestUserbarTag(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.create_superuser(
            username="test", email="test@email.com", password="password"
        )
        self.homepage = Page.objects.get(id=2)

    def dummy_request(self, user=None):
        request = RequestFactory().get("/")
        request.user = user or AnonymousUser()
        return request

    def test_userbar_tag(self):
        template = Template("{% load wagtailuserbar %}{% wagtailuserbar %}")
        content = template.render(
            Context(
                {
                    PAGE_TEMPLATE_VAR: self.homepage,
                    "request": self.dummy_request(self.user),
                }
            )
        )

        self.assertIn("<!-- Wagtail user bar embed code -->", content)

    def test_userbar_does_not_break_without_request(self):
        template = Template("{% load wagtailuserbar %}{% wagtailuserbar %}boom")
        content = template.render(Context({}))

        self.assertEqual("boom", content)

    def test_userbar_tag_self(self):
        """
        Ensure the userbar renders with `self` instead of `PAGE_TEMPLATE_VAR`
        """
        template = Template("{% load wagtailuserbar %}{% wagtailuserbar %}")
        content = template.render(
            Context(
                {
                    "self": self.homepage,
                    "request": self.dummy_request(self.user),
                }
            )
        )

        self.assertIn("<!-- Wagtail user bar embed code -->", content)

    def test_userbar_tag_anonymous_user(self):
        template = Template("{% load wagtailuserbar %}{% wagtailuserbar %}")
        content = template.render(
            Context(
                {
                    PAGE_TEMPLATE_VAR: self.homepage,
                    "request": self.dummy_request(),
                }
            )
        )

        # Make sure nothing was rendered
        self.assertEqual(content, "")

    def test_userbar_tag_no_page(self):
        template = Template("{% load wagtailuserbar %}{% wagtailuserbar %}")
        content = template.render(
            Context(
                {
                    "request": self.dummy_request(self.user),
                }
            )
        )

        self.assertIn("<!-- Wagtail user bar embed code -->", content)


class TestUserbarFrontend(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()
        self.homepage = Page.objects.get(id=2)

    def test_userbar_frontend(self):
        response = self.client.get(
            reverse("wagtailadmin_userbar_frontend", args=(self.homepage.id,))
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/userbar/base.html")

    def test_userbar_frontend_anonymous_user_cannot_see(self):
        # Logout
        self.client.logout()

        response = self.client.get(
            reverse("wagtailadmin_userbar_frontend", args=(self.homepage.id,))
        )

        # Check that the user received a forbidden message
        self.assertEqual(response.status_code, 403)


class TestUserbarAddLink(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        self.login()
        self.homepage = Page.objects.get(url_path="/home/")
        self.event_index = Page.objects.get(url_path="/home/events/")

        self.business_index = BusinessIndex(title="Business", live=True)
        self.homepage.add_child(instance=self.business_index)

        self.business_child = BusinessChild(title="Business Child", live=True)
        self.business_index.add_child(instance=self.business_child)

    def test_page_allowing_subpages(self):
        response = self.client.get(
            reverse("wagtailadmin_userbar_frontend", args=(self.event_index.id,))
        )

        # page allows subpages, so the 'add page' button should show
        expected_url = reverse(
            "wagtailadmin_pages:add_subpage", args=(self.event_index.id,)
        )
        needle = f"""
            <a href="{expected_url}" target="_parent" role="menuitem">
                <svg class="icon icon-plus wagtail-action-icon" aria-hidden="true">
                    <use href="#icon-plus"></use>
                </svg>
                Add a child page
            </a>
            """
        self.assertTagInHTML(needle, str(response.content))

    def test_page_disallowing_subpages(self):
        response = self.client.get(
            reverse("wagtailadmin_userbar_frontend", args=(self.business_child.id,))
        )

        # page disallows subpages, so the 'add page' button shouldn't show
        expected_url = reverse(
            "wagtailadmin_pages:add_subpage", args=(self.business_index.id,)
        )
        expected_link = (
            '<a href="%s" target="_parent">Add a child page</a>' % expected_url
        )
        self.assertNotContains(response, expected_link)


class TestUserbarModeration(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()
        self.homepage = Page.objects.get(id=2)
        self.homepage.save_revision(submitted_for_moderation=True)
        self.revision = self.homepage.get_latest_revision()

    def test_userbar_moderation(self):
        response = self.client.get(
            reverse("wagtailadmin_userbar_moderation", args=(self.revision.id,))
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/userbar/base.html")

        expected_approve_html = """
            <form action="/admin/pages/moderation/{}/approve/" target="_parent" method="post">
                <input type="hidden" name="csrfmiddlewaretoken">
                <div class="wagtail-action">
                    <input type="submit" value="Approve" class="button" />
                </div>
            </form>
        """.format(
            self.revision.id
        )
        self.assertTagInHTML(expected_approve_html, str(response.content))

        expected_reject_html = """
            <form action="/admin/pages/moderation/{}/reject/" target="_parent" method="post">
                <input type="hidden" name="csrfmiddlewaretoken">
                <div class="wagtail-action">
                    <input type="submit" value="Reject" class="button" />
                </div>
            </form>
        """.format(
            self.revision.id
        )
        self.assertTagInHTML(expected_reject_html, str(response.content))

    def test_userbar_moderation_anonymous_user_cannot_see(self):
        # Logout
        self.client.logout()

        response = self.client.get(
            reverse("wagtailadmin_userbar_moderation", args=(self.revision.id,))
        )

        # Check that the user received a forbidden message
        self.assertEqual(response.status_code, 403)
