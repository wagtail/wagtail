from django.conf import settings
from django.contrib.admin.utils import quote
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now
from freezegun import freeze_time

from wagtail.models import ModelLogEntry
from wagtail.test.testapp.models import (
    Advert,
    DraftStateModel,
    MultiPreviewModesModel,
    RevisableModel,
)
from wagtail.test.utils import WagtailTestUtils


class TestSnippetRevisions(WagtailTestUtils, TestCase):
    @property
    def revert_url(self):
        return self.get_url(
            "revisions_revert", args=[quote(self.snippet.pk), self.initial_revision.pk]
        )

    def get(self):
        return self.client.get(self.revert_url)

    def post(self, post_data=None):
        return self.client.post(self.revert_url, post_data)

    def get_url(self, url_name, args=None):
        view_name = self.snippet.snippet_viewset.get_url_name(url_name)
        if args is None:
            args = [quote(self.snippet.pk)]
        return reverse(view_name, args=args)

    def setUp(self):
        self.user = self.login()

        with freeze_time("2022-05-10 11:00:00"):
            self.snippet = RevisableModel.objects.create(text="The original text")
            self.initial_revision = self.snippet.save_revision(user=self.user)
            ModelLogEntry.objects.create(
                content_type=ContentType.objects.get_for_model(RevisableModel),
                label="The original text",
                action="wagtail.create",
                timestamp=now(),
                object_id=self.snippet.pk,
                revision=self.initial_revision,
                content_changed=True,
            )

        self.snippet.text = "The edited text"
        self.snippet.save()
        self.edit_revision = self.snippet.save_revision(user=self.user, log_action=True)

    def test_get_revert_revision(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)

        if settings.USE_TZ:
            # the default timezone is "Asia/Tokyo", so we expect UTC +9
            expected_date_string = "May 10, 2022, 8 p.m."
        else:
            expected_date_string = "May 10, 2022, 11 a.m."

        # Message should be shown
        self.assertContains(
            response,
            f"You are viewing a previous version of this Revisable model from <b>{expected_date_string}</b> by",
            count=1,
        )

        # Form should show the content of the revision, not the current draft
        soup = self.get_soup(response.content)
        textarea = soup.select_one("textarea[name='text']")
        self.assertIsNotNone(textarea)
        self.assertEqual(textarea.text.strip(), "The original text")

        # Form action url should point to the revisions_revert view
        form_tag = f'<form action="{self.revert_url}" method="POST">'
        html = response.content.decode()
        self.assertTagInHTML(form_tag, html, count=1, allow_extra_attrs=True)

        # Buttons should be relabelled
        self.assertContains(response, "Replace current revision", count=1)

        soup = self.get_soup(response.content)
        form = soup.select_one("form[data-edit-form]")
        self.assertIsNotNone(form)

        # Autosave should be disabled
        self.assertNotIn("w-autosave", form["data-controller"].split())
        self.assertNotIn("w-autosave", form["data-action"])
        self.assertIsNone(form.attrs.get("data-w-autosave-interval-value"))

    def test_get_revert_revision_with_non_revisable_snippet(self):
        snippet = Advert.objects.create(text="foo")
        response = self.client.get(
            f"/admin/snippets/tests/advert/history/{snippet.pk}/revisions/1/revert/"
        )
        self.assertEqual(response.status_code, 404)

    def test_get_with_limited_permissions(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.get()
        self.assertEqual(response.status_code, 302)

    def test_get_with_draft_state_snippet(self):
        self.snippet = DraftStateModel.objects.create(text="Draft-enabled Foo")
        self.initial_revision = self.snippet.save_revision()
        response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/edit.html")
        soup = self.get_soup(response.content)

        # The save button should be labelled "Replace current draft"
        footer = soup.select_one("footer")
        save_button = footer.select_one(
            'button[type="submit"]:not([name="action-publish"])'
        )
        self.assertIsNotNone(save_button)
        self.assertEqual(save_button.text.strip(), "Replace current draft")
        # The publish button should exist and have name="action-publish"
        publish_button = footer.select_one(
            'button[type="submit"][name="action-publish"]'
        )
        self.assertIsNotNone(publish_button)
        self.assertEqual(publish_button.text.strip(), "Publish this version")
        self.assertEqual(
            set(publish_button.get("class")),
            {"button", "action-save", "button-longrunning"},
        )

        # Should not show the Unpublish action menu item
        unpublish_url = reverse(
            "wagtailsnippets_tests_draftstatemodel:unpublish",
            args=(quote(self.snippet.pk),),
        )
        unpublish_button = footer.select_one(f'a[href="{unpublish_url}"]')
        self.assertIsNone(unpublish_button)

    def test_get_with_previewable_snippet(self):
        self.snippet = MultiPreviewModesModel.objects.create(text="Preview-enabled foo")
        self.initial_revision = self.snippet.save_revision()

        self.snippet.text = "Preview-enabled bar"
        self.snippet.save_revision()

        response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/edit.html")

        # Message should be shown
        self.assertContains(
            response,
            "You are viewing a previous version of this",
            count=1,
        )

        # Form should show the content of the revision, not the current draft
        self.assertContains(response, "Preview-enabled foo")

        # Form action url should point to the revisions_revert view
        form_tag = f'<form action="{self.revert_url}" method="POST">'
        html = response.content.decode()
        self.assertTagInHTML(form_tag, html, count=1, allow_extra_attrs=True)

        # Buttons should be relabelled
        self.assertContains(response, "Replace current revision", count=1)

        # Should show the preview panel
        preview_url = self.get_url("preview_on_edit")
        self.assertContains(response, 'data-side-panel="preview"')
        soup = self.get_soup(response.content)
        controller = soup.select_one('[data-controller="w-preview"]')
        self.assertIsNotNone(controller)
        self.assertEqual(controller.get("data-w-preview-url-value"), preview_url)

        # Should have the preview side panel toggle button
        toggle_button = soup.find("button", {"data-side-panel-toggle": "preview"})
        self.assertIsNotNone(toggle_button)
        self.assertEqual("w-tooltip w-kbd", toggle_button["data-controller"])
        self.assertEqual("mod+p", toggle_button["data-w-kbd-key-value"])

    def test_replace_revision(self):
        get_response = self.get()
        text_from_revision = get_response.context["form"].initial["text"]

        post_response = self.post(
            post_data={
                "text": text_from_revision + " reverted",
                "revision": self.initial_revision.pk,
            }
        )
        self.assertRedirects(post_response, self.get_url("list", args=[]))

        self.snippet.refresh_from_db()
        latest_revision = self.snippet.get_latest_revision()
        log_entry = ModelLogEntry.objects.filter(revision=latest_revision).first()

        # The instance should be updated
        self.assertEqual(self.snippet.text, "The original text reverted")
        # The initial revision, edited revision, and revert revision
        self.assertEqual(self.snippet.revisions.count(), 3)
        # The latest revision should be the revert revision
        self.assertEqual(latest_revision.content["text"], "The original text reverted")

        # A new log entry with "wagtail.revert" action should be created
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.action, "wagtail.revert")

    def test_replace_with_limited_permissions(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.post(
            post_data={
                "text": "test text",
                "revision": self.initial_revision.pk,
            }
        )
        self.assertEqual(response.status_code, 302)

        self.snippet.refresh_from_db()
        self.assertNotEqual(self.snippet.text, "test text")

        # Only the initial revision and edited revision, no revert revision
        self.assertEqual(self.snippet.revisions.count(), 2)

    def test_replace_draft(self):
        self.snippet = DraftStateModel.objects.create(
            text="Draft-enabled Foo", live=False
        )
        self.initial_revision = self.snippet.save_revision()
        self.snippet.text = "Draft-enabled Foo edited"
        self.edit_revision = self.snippet.save_revision()
        get_response = self.get()
        text_from_revision = get_response.context["form"].initial["text"]

        post_response = self.post(
            post_data={
                "text": text_from_revision + " reverted",
                "revision": self.initial_revision.pk,
            }
        )
        self.assertRedirects(post_response, self.get_url("edit"))

        self.snippet.refresh_from_db()
        latest_revision = self.snippet.get_latest_revision()
        log_entry = ModelLogEntry.objects.filter(revision=latest_revision).first()
        publish_log_entries = ModelLogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(DraftStateModel),
            action="wagtail.publish",
            object_id=self.snippet.pk,
        )

        # The instance should be updated, since it is still a draft
        self.assertEqual(self.snippet.text, "Draft-enabled Foo reverted")
        # The initial revision, edited revision, and revert revision
        self.assertEqual(self.snippet.revisions.count(), 3)
        # The latest revision should be the revert revision
        self.assertEqual(latest_revision.content["text"], "Draft-enabled Foo reverted")

        # A new log entry with "wagtail.revert" action should be created
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.action, "wagtail.revert")

        # There should be no log entries for the publish action
        self.assertEqual(publish_log_entries.count(), 0)

        # The instance should still be a draft
        self.assertFalse(self.snippet.live)
        self.assertTrue(self.snippet.has_unpublished_changes)
        self.assertIsNone(self.snippet.first_published_at)
        self.assertIsNone(self.snippet.last_published_at)
        self.assertIsNone(self.snippet.live_revision)

    def test_replace_publish(self):
        self.snippet = DraftStateModel.objects.create(text="Draft-enabled Foo")
        self.initial_revision = self.snippet.save_revision()
        self.snippet.text = "Draft-enabled Foo edited"
        self.edit_revision = self.snippet.save_revision()
        get_response = self.get()
        text_from_revision = get_response.context["form"].initial["text"]

        timestamp = now()
        with freeze_time(timestamp):
            post_response = self.post(
                post_data={
                    "text": text_from_revision + " reverted",
                    "revision": self.initial_revision.pk,
                    "action-publish": "action-publish",
                }
            )

        self.assertRedirects(post_response, self.get_url("list", args=[]))

        self.snippet.refresh_from_db()
        latest_revision = self.snippet.get_latest_revision()
        log_entry = ModelLogEntry.objects.filter(revision=latest_revision).first()
        revert_log_entries = ModelLogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(DraftStateModel),
            action="wagtail.revert",
            object_id=self.snippet.pk,
        )

        # The instance should be updated
        self.assertEqual(self.snippet.text, "Draft-enabled Foo reverted")
        # The initial revision, edited revision, and revert revision
        self.assertEqual(self.snippet.revisions.count(), 3)
        # The latest revision should be the revert revision
        self.assertEqual(latest_revision.content["text"], "Draft-enabled Foo reverted")

        # The latest log entry should use the "wagtail.publish" action
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.action, "wagtail.publish")

        # There should be a log entry for the revert action
        self.assertEqual(revert_log_entries.count(), 1)

        # The instance should be live
        self.assertTrue(self.snippet.live)
        self.assertFalse(self.snippet.has_unpublished_changes)
        self.assertEqual(self.snippet.first_published_at, timestamp)
        self.assertEqual(self.snippet.last_published_at, timestamp)
        self.assertEqual(self.snippet.live_revision, self.snippet.latest_revision)
