from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.test.snippets.models import StandardSnippet
from wagtail.test.utils import WagtailTestUtils


class TestSnippetCopyView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.snippet = StandardSnippet.objects.create(text="Test snippet")
        self.url = reverse(
            StandardSnippet.snippet_viewset.get_url_name("copy"),
            args=(self.snippet.pk,),
        )
        self.user = self.login()

    def test_without_permission(self):
        self.user.is_superuser = False
        self.user.save()
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        self.user.user_permissions.add(admin_permission)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_form_is_prefilled(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/create.html")

        # Ensure form is prefilled
        soup = self.get_soup(response.content)
        text_input = soup.select_one('input[name="text"]')
        self.assertEqual(text_input.attrs.get("value"), "Test snippet")
