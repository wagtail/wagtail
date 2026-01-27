from io import StringIO

from django.contrib.admin.utils import quote
from django.contrib.auth.models import Permission
from django.core import management
from django.http import HttpRequest, HttpResponse
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from wagtail.test.testapp.models import Advert, VariousOnDeleteModel
from wagtail.test.utils import WagtailTestUtils


class TestSnippetDelete(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.test_snippet = Advert.objects.get(pk=1)
        self.user = self.login()

    def test_delete_get_with_limited_permissions(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.client.get(
            reverse(
                "wagtailsnippets_tests_advert:delete",
                args=[quote(self.test_snippet.pk)],
            )
        )
        self.assertEqual(response.status_code, 302)

    def test_delete_get(self):
        delete_url = reverse(
            "wagtailsnippets_tests_advert:delete",
            args=[quote(self.test_snippet.pk)],
        )
        response = self.client.get(delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Yes, delete")
        self.assertContains(response, delete_url)

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_delete_get_with_i18n_enabled(self):
        delete_url = reverse(
            "wagtailsnippets_tests_advert:delete",
            args=[quote(self.test_snippet.pk)],
        )
        response = self.client.get(delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Yes, delete")
        self.assertContains(response, delete_url)

    def test_delete_get_with_protected_reference(self):
        with self.captureOnCommitCallbacks(execute=True):
            VariousOnDeleteModel.objects.create(
                text="Undeletable", on_delete_protect=self.test_snippet
            )
        delete_url = reverse(
            "wagtailsnippets_tests_advert:delete",
            args=[quote(self.test_snippet.pk)],
        )
        response = self.client.get(delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This advert is referenced 1 time.")
        self.assertContains(
            response,
            "One or more references to this advert prevent it from being deleted.",
        )
        self.assertContains(
            response,
            reverse(
                "wagtailsnippets_tests_advert:usage",
                args=[quote(self.test_snippet.pk)],
            )
            + "?describe_on_delete=1",
        )
        self.assertNotContains(response, "Yes, delete")
        self.assertNotContains(response, delete_url)

    def test_delete_post_with_limited_permissions(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.client.post(
            reverse(
                "wagtailsnippets_tests_advert:delete",
                args=[quote(self.test_snippet.pk)],
            )
        )
        self.assertEqual(response.status_code, 302)

    def test_delete_post(self):
        response = self.client.post(
            reverse(
                "wagtailsnippets_tests_advert:delete",
                args=[quote(self.test_snippet.pk)],
            )
        )

        # Should be redirected to the listing page
        self.assertRedirects(response, reverse("wagtailsnippets_tests_advert:list"))

        # Check that the page is gone
        self.assertEqual(Advert.objects.filter(text="test_advert").count(), 0)

    def test_delete_post_with_protected_reference(self):
        with self.captureOnCommitCallbacks(execute=True):
            VariousOnDeleteModel.objects.create(
                text="Undeletable", on_delete_protect=self.test_snippet
            )
        delete_url = reverse(
            "wagtailsnippets_tests_advert:delete",
            args=[quote(self.test_snippet.pk)],
        )
        response = self.client.post(delete_url)

        # Should throw a PermissionDenied error and redirect to the dashboard
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("wagtailadmin_home"))

        # Check that the snippet is still here
        self.assertTrue(Advert.objects.filter(pk=self.test_snippet.pk).exists())

    def test_usage_link(self):
        output = StringIO()
        management.call_command("rebuild_references_index", stdout=output)

        response = self.client.get(
            reverse(
                "wagtailsnippets_tests_advert:delete",
                args=[quote(self.test_snippet.pk)],
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/confirm_delete.html")
        self.assertContains(response, "This advert is referenced 2 times")
        self.assertContains(
            response,
            reverse(
                "wagtailsnippets_tests_advert:usage",
                args=[quote(self.test_snippet.pk)],
            )
            + "?describe_on_delete=1",
        )

    def test_before_delete_snippet_hook_get(self):
        advert = Advert.objects.create(
            url="http://www.example.com/",
            text="Test hook",
        )

        def hook_func(request, instances):
            self.assertIsInstance(request, HttpRequest)
            self.assertQuerySetEqual(instances, ["<Advert: Test hook>"], transform=repr)
            return HttpResponse("Overridden!")

        with self.register_hook("before_delete_snippet", hook_func):
            response = self.client.get(
                reverse("wagtailsnippets_tests_advert:delete", args=[quote(advert.pk)])
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

    def test_before_delete_snippet_hook_post(self):
        advert = Advert.objects.create(
            url="http://www.example.com/",
            text="Test hook",
        )

        def hook_func(request, instances):
            self.assertIsInstance(request, HttpRequest)
            self.assertQuerySetEqual(instances, ["<Advert: Test hook>"], transform=repr)
            return HttpResponse("Overridden!")

        with self.register_hook("before_delete_snippet", hook_func):
            response = self.client.post(
                reverse(
                    "wagtailsnippets_tests_advert:delete",
                    args=[quote(advert.pk)],
                )
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # Request intercepted before advert was deleted
        self.assertTrue(Advert.objects.filter(pk=advert.pk).exists())

    def test_after_delete_snippet_hook(self):
        advert = Advert.objects.create(
            url="http://www.example.com/",
            text="Test hook",
        )

        def hook_func(request, instances):
            self.assertIsInstance(request, HttpRequest)
            self.assertQuerySetEqual(instances, ["<Advert: Test hook>"], transform=repr)
            return HttpResponse("Overridden!")

        with self.register_hook("after_delete_snippet", hook_func):
            response = self.client.post(
                reverse(
                    "wagtailsnippets_tests_advert:delete",
                    args=[quote(advert.pk)],
                )
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # Request intercepted after advert was deleted
        self.assertFalse(Advert.objects.filter(pk=advert.pk).exists())
