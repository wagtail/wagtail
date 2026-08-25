from unittest import mock

from django.contrib.admin.utils import quote
from django.contrib.auth.models import Permission
from django.http import HttpRequest, HttpResponse
from django.test import TestCase
from django.urls import reverse

from wagtail.signals import unpublished
from wagtail.test.testapp.models import DraftStateCustomPrimaryKeyModel
from wagtail.test.utils.wagtail_tests import WagtailTestUtils


class TestSnippetUnpublish(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()
        self.snippet = DraftStateCustomPrimaryKeyModel.objects.create(
            custom_id="custom/1", text="to be unpublished"
        )
        self.unpublish_url = reverse(
            "wagtailsnippets_tests_draftstatecustomprimarykeymodel:unpublish",
            args=(quote(self.snippet.pk),),
        )

    def test_unpublish_view(self):
        """
        This tests that the unpublish view responds with an unpublish confirm page
        """
        # Get unpublish page
        response = self.client.get(self.unpublish_url)

        # Check that the user received an unpublish confirm page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/confirm_unpublish.html")

    def test_unpublish_view_invalid_pk(self):
        """
        This tests that the unpublish view returns an error if the object pk is invalid
        """
        # Get unpublish page
        response = self.client.get(
            reverse(
                "wagtailsnippets_tests_draftstatecustomprimarykeymodel:unpublish",
                args=(quote(12345),),
            )
        )

        # Check that the user received a 404 response
        self.assertEqual(response.status_code, 404)

    def test_unpublish_view_get_bad_permissions(self):
        """
        This tests that the unpublish view doesn't allow users without unpublish permissions
        """
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        # Get unpublish page
        response = self.client.get(self.unpublish_url)

        # Check that the user received a 302 redirected response
        self.assertEqual(response.status_code, 302)

    def test_unpublish_view_post_bad_permissions(self):
        """
        This tests that the unpublish view doesn't allow users without unpublish permissions
        """
        # Connect a mock signal handler to unpublished signal
        mock_handler = mock.MagicMock()
        unpublished.connect(mock_handler)

        try:
            # Remove privileges from user
            self.user.is_superuser = False
            self.user.user_permissions.add(
                Permission.objects.get(
                    content_type__app_label="wagtailadmin", codename="access_admin"
                )
            )
            self.user.save()

            # Post to the unpublish view
            response = self.client.post(self.unpublish_url)

            # Should be redirected to the home page
            self.assertRedirects(response, reverse("wagtailadmin_home"))

            # Check that the object was not unpublished
            self.assertTrue(
                DraftStateCustomPrimaryKeyModel.objects.get(pk=self.snippet.pk).live
            )

            # Check that the unpublished signal was not fired
            self.assertEqual(mock_handler.call_count, 0)
        finally:
            unpublished.disconnect(mock_handler)

    def test_unpublish_view_post_with_publish_permission(self):
        """
        This posts to the unpublish view and checks that the object was unpublished,
        using a specific publish permission instead of relying on the superuser flag
        """
        # Connect a mock signal handler to unpublished signal
        mock_handler = mock.MagicMock()
        unpublished.connect(mock_handler)

        try:
            # Only add edit and publish permissions
            self.user.is_superuser = False
            edit_permission = Permission.objects.get(
                content_type__app_label="tests",
                codename="change_draftstatecustomprimarykeymodel",
            )
            publish_permission = Permission.objects.get(
                content_type__app_label="tests",
                codename="publish_draftstatecustomprimarykeymodel",
            )
            admin_permission = Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
            self.user.user_permissions.add(
                edit_permission,
                publish_permission,
                admin_permission,
            )
            self.user.save()

            # Post to the unpublish view
            response = self.client.post(self.unpublish_url)

            # Should be redirected to the listing page
            self.assertRedirects(
                response,
                reverse("wagtailsnippets_tests_draftstatecustomprimarykeymodel:list"),
            )

            # Check that the object was unpublished
            self.assertFalse(
                DraftStateCustomPrimaryKeyModel.objects.get(pk=self.snippet.pk).live
            )

            # Check that the unpublished signal was fired
            self.assertEqual(mock_handler.call_count, 1)
            mock_call = mock_handler.mock_calls[0][2]

            self.assertEqual(mock_call["sender"], DraftStateCustomPrimaryKeyModel)
            self.assertEqual(mock_call["instance"], self.snippet)
            self.assertIsInstance(
                mock_call["instance"], DraftStateCustomPrimaryKeyModel
            )
        finally:
            unpublished.disconnect(mock_handler)

    def test_unpublish_view_post(self):
        """
        This posts to the unpublish view and checks that the object was unpublished
        """
        # Connect a mock signal handler to unpublished signal
        mock_handler = mock.MagicMock()
        unpublished.connect(mock_handler)

        try:
            # Post to the unpublish view
            response = self.client.post(self.unpublish_url)

            # Should be redirected to the listing page
            self.assertRedirects(
                response,
                reverse("wagtailsnippets_tests_draftstatecustomprimarykeymodel:list"),
            )

            # Check that the object was unpublished
            self.assertFalse(
                DraftStateCustomPrimaryKeyModel.objects.get(pk=self.snippet.pk).live
            )

            # Check that the unpublished signal was fired
            self.assertEqual(mock_handler.call_count, 1)
            mock_call = mock_handler.mock_calls[0][2]

            self.assertEqual(mock_call["sender"], DraftStateCustomPrimaryKeyModel)
            self.assertEqual(mock_call["instance"], self.snippet)
            self.assertIsInstance(
                mock_call["instance"], DraftStateCustomPrimaryKeyModel
            )
        finally:
            unpublished.disconnect(mock_handler)

    def test_after_unpublish_hook(self):
        def hook_func(request, snippet):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(snippet.pk, self.snippet.pk)

            return HttpResponse("Overridden!")

        with self.register_hook("after_unpublish", hook_func):
            post_data = {}
            response = self.client.post(self.unpublish_url, post_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        self.snippet.refresh_from_db()
        self.assertEqual(self.snippet.status_string, "draft")

    def test_before_unpublish(self):
        def hook_func(request, snippet):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(snippet.pk, self.snippet.pk)

            return HttpResponse("Overridden!")

        with self.register_hook("before_unpublish", hook_func):
            post_data = {}
            response = self.client.post(self.unpublish_url, post_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # The hook response is served before unpublish is called.
        self.snippet.refresh_from_db()
        self.assertEqual(self.snippet.status_string, "live")
