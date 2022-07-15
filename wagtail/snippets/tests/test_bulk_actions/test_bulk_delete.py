from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils.text import capfirst

from wagtail.test.snippets.models import StandardSnippet
from wagtail.test.utils import WagtailTestUtils


class TestSnippetDeleteView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.snippet_model = StandardSnippet

        # create a set of test snippets
        self.test_snippets = [
            self.snippet_model.objects.create(
                text=f"Title-{i}",
            )
            for i in range(1, 6)
        ]

        self.user = self.login()
        self.url = (
            reverse(
                "wagtail_bulk_action",
                args=(
                    self.snippet_model._meta.app_label,
                    self.snippet_model._meta.model_name,
                    "delete",
                ),
            )
            + "?"
        )
        for snippet in self.test_snippets:
            self.url += f"id={snippet.pk}&"

    def test_simple(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailsnippets/bulk_actions/confirm_bulk_delete.html"
        )

    def test_bulk_delete(self):
        response = self.client.post(self.url)

        # Should redirect back to index
        self.assertEqual(response.status_code, 302)

        # Check that the users were deleted
        for snippet in self.test_snippets:
            self.assertFalse(self.snippet_model.objects.filter(pk=snippet.pk).exists())

    def test_delete_with_limited_permissions(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        html = response.content.decode()
        self.assertInHTML(
            f"<p>You don't have permission to delete these {capfirst(self.snippet_model._meta.verbose_name_plural)}</p>",
            html,
        )

        for snippet in self.test_snippets:
            self.assertInHTML(f"<li>{snippet.text}</li>", html)

        response = self.client.post(self.url)
        # User should be redirected back to the index
        self.assertEqual(response.status_code, 302)

        # Documents should not be deleted
        for snippet in self.test_snippets:
            self.assertTrue(self.snippet_model.objects.filter(pk=snippet.pk).exists())
