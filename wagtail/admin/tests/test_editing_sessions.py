import datetime

from django.conf import settings
from django.contrib.admin.utils import quote
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from wagtail.admin.models import EditingSession
from wagtail.models import GroupPagePermission, Page, Workflow, WorkflowContentType
from wagtail.test.testapp.models import (
    Advert,
    AdvertWithCustomPrimaryKey,
    FullFeaturedSnippet,
    SimplePage,
)
from wagtail.test.utils import WagtailTestUtils

if settings.USE_TZ:
    TIMESTAMP_ANCIENT = timezone.make_aware(
        datetime.datetime(2019, 1, 1, 10, 30, 0), timezone=datetime.timezone.utc
    )
    TIMESTAMP_PAST = timezone.make_aware(
        datetime.datetime(2020, 1, 1, 10, 30, 0), timezone=datetime.timezone.utc
    )
    TIMESTAMP_1 = timezone.make_aware(
        datetime.datetime(2020, 1, 1, 11, 59, 51), timezone=datetime.timezone.utc
    )
    TIMESTAMP_2 = timezone.make_aware(
        datetime.datetime(2020, 1, 1, 11, 59, 52), timezone=datetime.timezone.utc
    )
    TIMESTAMP_3 = timezone.make_aware(
        datetime.datetime(2020, 1, 1, 11, 59, 53), timezone=datetime.timezone.utc
    )
    TIMESTAMP_4 = timezone.make_aware(
        datetime.datetime(2020, 1, 1, 11, 59, 54), timezone=datetime.timezone.utc
    )
    TIMESTAMP_NOW = timezone.make_aware(
        datetime.datetime(2020, 1, 1, 12, 0, 0), timezone=datetime.timezone.utc
    )
else:
    TIMESTAMP_ANCIENT = datetime.datetime(2019, 1, 1, 10, 30, 0)
    TIMESTAMP_PAST = datetime.datetime(2020, 1, 1, 10, 30, 0)
    TIMESTAMP_1 = datetime.datetime(2020, 1, 1, 11, 59, 51)
    TIMESTAMP_2 = datetime.datetime(2020, 1, 1, 11, 59, 52)
    TIMESTAMP_3 = datetime.datetime(2020, 1, 1, 11, 59, 53)
    TIMESTAMP_4 = datetime.datetime(2020, 1, 1, 11, 59, 54)
    TIMESTAMP_NOW = datetime.datetime(2020, 1, 1, 12, 0, 0)


class TestPingView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.create_superuser(
            "bob", password="password", first_name="Bob", last_name="Testuser"
        )
        self.other_user = self.create_user(
            "vic", password="password", first_name="Vic", last_name="Otheruser"
        )
        self.third_user = self.create_user(
            "gordon", password="password", first_name="Gordon", last_name="Thirduser"
        )

        self.login(user=self.user)
        self.root_page = Page.get_first_root_node()

        self.page = SimplePage(title="Test page", slug="test-page", content="test page")
        self.root_page.add_child(instance=self.page)

        with freeze_time(TIMESTAMP_ANCIENT):
            self.original_revision = self.page.save_revision(user=self.other_user)

        with freeze_time(TIMESTAMP_PAST):
            self.original_revision = self.page.save_revision(user=self.user)

        self.other_page = SimplePage(
            title="Other page", slug="other-page", content="other page"
        )
        self.root_page.add_child(instance=self.other_page)

        page_content_type = ContentType.objects.get_for_model(Page)

        self.session = EditingSession.objects.create(
            user=self.user,
            content_type=page_content_type,
            object_id=self.page.id,
            last_seen_at=TIMESTAMP_1,
        )
        self.other_session = EditingSession.objects.create(
            user=self.other_user,
            content_type=page_content_type,
            object_id=self.page.id,
            last_seen_at=TIMESTAMP_2,
        )
        self.old_session = EditingSession.objects.create(
            user=self.other_user,
            content_type=page_content_type,
            object_id=self.page.id,
            last_seen_at=TIMESTAMP_PAST,
        )

    def test_ping_invalid_model(self):
        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("testapp", "invalidmodel", str(self.page.id), self.session.id),
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_ping_non_page_non_snippet_model(self):
        editors = Group.objects.get(name="Editors")
        session = EditingSession.objects.create(
            user=self.user,
            content_type=ContentType.objects.get_for_model(Group),
            object_id=editors.pk,
            last_seen_at=TIMESTAMP_1,
        )
        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("auth", "group", str(editors.pk), session.id),
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_ping_non_existent_object(self):
        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", 999999, self.session.id),
            )
        )
        self.assertEqual(response.status_code, 404)

    @freeze_time(TIMESTAMP_NOW)
    def test_ping_existing_session(self):
        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", self.page.id, self.session.id),
            )
        )
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json["session_id"], self.session.id)
        self.assertEqual(
            response_json["other_sessions"],
            [
                {
                    "session_id": self.other_session.id,
                    "user": "Vic Otheruser",
                    "last_seen_at": TIMESTAMP_2.isoformat(),
                    "is_editing": False,
                    "revision_id": None,
                },
            ],
        )

        soup = self.get_soup(response_json["html"])
        rendered_sessions = soup.select("ol.w-editing-sessions__list li")
        self.assertEqual(len(rendered_sessions), 1)
        session_text = rendered_sessions[0].text
        self.assertIn("Vic Otheruser", session_text)
        self.assertIn("Currently viewing", session_text)

        self.session.refresh_from_db()
        self.assertEqual(self.session.last_seen_at, TIMESTAMP_NOW)
        self.assertFalse(self.session.is_editing)

    @freeze_time(TIMESTAMP_NOW)
    def test_ping_existing_session_with_editing_flag(self):
        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", self.page.id, self.session.id),
            ),
            {"is_editing": "1"},
        )
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json["session_id"], self.session.id)
        self.assertEqual(
            response_json["other_sessions"],
            [
                # Should not cause any changes to the other sessions list,
                # as the current session is the one that is editing
                {
                    "session_id": self.other_session.id,
                    "user": "Vic Otheruser",
                    "last_seen_at": TIMESTAMP_2.isoformat(),
                    "is_editing": False,
                    "revision_id": None,
                },
            ],
        )

        soup = self.get_soup(response_json["html"])
        rendered_sessions = soup.select("ol.w-editing-sessions__list li")
        self.assertEqual(len(rendered_sessions), 1)
        session_text = rendered_sessions[0].text
        self.assertIn("Vic Otheruser", session_text)
        self.assertIn("Currently viewing", session_text)

        self.session.refresh_from_db()
        self.assertEqual(self.session.last_seen_at, TIMESTAMP_NOW)
        self.assertTrue(self.session.is_editing)

    @freeze_time(TIMESTAMP_NOW)
    def test_ping_with_revision(self):
        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", self.page.id, self.session.id),
            ),
            {"revision_id": self.original_revision.id},
        )
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json["session_id"], self.session.id)

        # no revisions have been saved since the original revision
        self.assertEqual(
            response_json["other_sessions"],
            [
                {
                    "session_id": self.other_session.id,
                    "user": "Vic Otheruser",
                    "last_seen_at": TIMESTAMP_2.isoformat(),
                    "is_editing": False,
                    "revision_id": None,
                },
            ],
        )

        soup = self.get_soup(response_json["html"])
        rendered_sessions = soup.select("ol.w-editing-sessions__list li")
        self.assertEqual(len(rendered_sessions), 1)
        session_text = rendered_sessions[0].text
        self.assertIn("Vic Otheruser", session_text)
        self.assertIn("Currently viewing", session_text)
        self.assertNotIn("saved a new version", session_text)

        self.session.refresh_from_db()
        self.assertEqual(self.session.last_seen_at, TIMESTAMP_NOW)
        self.assertFalse(self.session.is_editing)

        with freeze_time(TIMESTAMP_3):
            new_revision = self.page.save_revision(user=self.other_user)

        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", self.page.id, self.session.id),
            ),
            {"revision_id": self.original_revision.id},
        )
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json["session_id"], self.session.id)

        # the new revision should be indicated in the response (and last_seen_at should reflect it)
        self.assertEqual(
            response_json["other_sessions"],
            [
                {
                    "session_id": self.other_session.id,
                    "user": "Vic Otheruser",
                    "last_seen_at": TIMESTAMP_3.isoformat(),
                    "is_editing": False,
                    "revision_id": new_revision.id,
                },
            ],
        )

        soup = self.get_soup(response_json["html"])
        rendered_sessions = soup.select("ol.w-editing-sessions__list li")
        self.assertEqual(len(rendered_sessions), 1)
        session_text = rendered_sessions[0].text
        self.assertIn("Vic Otheruser saved a new version", session_text)
        self.assertNotIn("Currently viewing", session_text)
        dialog_title = soup.select_one(
            'template[data-w-teleport-target-value="#title-text-w-overwrite-changes-dialog"]'
        )
        self.assertIsNotNone(dialog_title)
        self.assertIn("Vic Otheruser saved a new version", dialog_title.string)
        dialog_subtitle = soup.select_one(
            'template[data-w-teleport-target-value="#subtitle-w-overwrite-changes-dialog"]'
        )
        self.assertIsNotNone(dialog_subtitle)
        self.assertIn(
            "Proceeding will overwrite the changes made by Vic Otheruser. "
            "Refreshing the page will show you the new changes, but you will lose any of your unsaved changes.",
            dialog_subtitle.string,
        )

        self.session.refresh_from_db()
        self.assertEqual(self.session.last_seen_at, TIMESTAMP_NOW)
        self.assertFalse(self.session.is_editing)

        self.other_session.delete()

        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", self.page.id, self.session.id),
            ),
            {"revision_id": self.original_revision.id},
        )
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json["session_id"], self.session.id)

        # the new revision should still appear as an "other session" in the response,
        # even though the editing session record has been deleted
        self.assertEqual(
            response_json["other_sessions"],
            [
                {
                    "session_id": None,
                    "user": "Vic Otheruser",
                    "last_seen_at": TIMESTAMP_3.isoformat(),
                    "is_editing": False,
                    "revision_id": new_revision.id,
                },
            ],
        )

        soup = self.get_soup(response_json["html"])
        rendered_sessions = soup.select("ol.w-editing-sessions__list li")
        self.assertEqual(len(rendered_sessions), 1)
        session_text = rendered_sessions[0].text
        self.assertIn("Vic Otheruser saved a new version", session_text)
        self.assertNotIn("Currently viewing", session_text)
        dialog_title = soup.select_one(
            'template[data-w-teleport-target-value="#title-text-w-overwrite-changes-dialog"]'
        )
        self.assertIsNotNone(dialog_title)
        self.assertIn(
            "Vic Otheruser saved a new version",
            dialog_title.string,
        )
        dialog_subtitle = soup.select_one(
            'template[data-w-teleport-target-value="#subtitle-w-overwrite-changes-dialog"]'
        )
        self.assertIsNotNone(dialog_subtitle)
        self.assertIn(
            "Proceeding will overwrite the changes made by Vic Otheruser. "
            "Refreshing the page will show you the new changes, but you will lose any of your unsaved changes.",
            dialog_subtitle.string,
        )

        self.session.refresh_from_db()
        self.assertEqual(self.session.last_seen_at, TIMESTAMP_NOW)
        self.assertFalse(self.session.is_editing)

    @freeze_time(TIMESTAMP_NOW)
    def test_ping_with_multiple_revisions_since_own_revision(self):
        # Create a new revision with the other_user
        with freeze_time(TIMESTAMP_3):
            self.page.save_revision(user=self.other_user)

        # Create a new session with the third_user, and save a revision too
        third_session = EditingSession.objects.create(
            user=self.third_user,
            content_type=ContentType.objects.get_for_model(Page),
            object_id=self.page.id,
            last_seen_at=TIMESTAMP_3,
        )
        with freeze_time(TIMESTAMP_4):
            latest_revision = self.page.save_revision(user=self.third_user)

        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", self.page.id, self.session.id),
            ),
            {"revision_id": self.original_revision.id},
        )
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json["session_id"], self.session.id)

        # The revision_id should only be set for the session with the latest revision
        self.assertEqual(
            response_json["other_sessions"],
            [
                {
                    # The third_session has a newer ID, but is shown first
                    # because it has a revision_id set
                    "session_id": third_session.id,
                    "user": "Gordon Thirduser",
                    "last_seen_at": TIMESTAMP_4.isoformat(),
                    "is_editing": False,
                    "revision_id": latest_revision.id,
                },
                {
                    "session_id": self.other_session.id,
                    "user": "Vic Otheruser",
                    # The timestamp isn't updated for the other_session and it
                    # doesn't have a revision_id. This is because we don't care
                    # about the fact that this user created a new revision if
                    # it's not the latest one.
                    "last_seen_at": TIMESTAMP_2.isoformat(),
                    "is_editing": False,
                    "revision_id": None,
                },
            ],
        )

        soup = self.get_soup(response_json["html"])
        rendered_sessions = soup.select("ol.w-editing-sessions__list li")
        self.assertEqual(len(rendered_sessions), 2)
        session_text = rendered_sessions[0].text
        self.assertIn("Gordon Thirduser saved a new version", session_text)
        self.assertNotIn("Currently viewing", session_text)
        dialog_title = soup.select_one(
            'template[data-w-teleport-target-value="#title-text-w-overwrite-changes-dialog"]'
        )
        self.assertIsNotNone(dialog_title)
        self.assertIn(
            "Gordon Thirduser saved a new version",
            dialog_title.string,
        )
        dialog_subtitle = soup.select_one(
            'template[data-w-teleport-target-value="#subtitle-w-overwrite-changes-dialog"]'
        )
        self.assertIsNotNone(dialog_subtitle)
        self.assertIn(
            "Proceeding will overwrite the changes made by Gordon Thirduser. "
            "Refreshing the page will show you the new changes, but you will lose any of your unsaved changes.",
            dialog_subtitle.string,
        )
        other_session_text = rendered_sessions[1].text
        self.assertIn("Vic Otheruser", other_session_text)
        self.assertIn("Currently viewing", other_session_text)
        self.assertNotIn("saved a new version", other_session_text)

        self.session.refresh_from_db()
        self.assertEqual(self.session.last_seen_at, TIMESTAMP_NOW)
        self.assertFalse(self.session.is_editing)

    @freeze_time(TIMESTAMP_NOW)
    def test_ping_with_new_revision_that_has_no_user(self):
        # Create a new revision without any user
        with freeze_time(TIMESTAMP_3):
            latest_revision = self.page.save_revision()

        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", self.page.id, self.session.id),
            ),
            {"revision_id": self.original_revision.id},
        )
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json["session_id"], self.session.id)

        self.assertEqual(
            response_json["other_sessions"],
            [
                {
                    # Should work even if the revision has no associated user
                    "session_id": None,
                    "user": "",
                    "last_seen_at": TIMESTAMP_3.isoformat(),
                    "is_editing": False,
                    "revision_id": latest_revision.id,
                },
                {
                    "session_id": self.other_session.id,
                    "user": "Vic Otheruser",
                    "last_seen_at": TIMESTAMP_2.isoformat(),
                    "is_editing": False,
                    "revision_id": None,
                },
            ],
        )

        soup = self.get_soup(response_json["html"])
        rendered_sessions = soup.select("ol.w-editing-sessions__list li")
        self.assertEqual(len(rendered_sessions), 2)
        session_text = rendered_sessions[0].text
        self.assertIn("System saved a new version", session_text)
        self.assertNotIn("Currently viewing", session_text)
        dialog_title = soup.select_one(
            'template[data-w-teleport-target-value="#title-text-w-overwrite-changes-dialog"]'
        )
        self.assertIsNotNone(dialog_title)
        self.assertIn(
            "System saved a new version",
            dialog_title.string,
        )
        dialog_subtitle = soup.select_one(
            'template[data-w-teleport-target-value="#subtitle-w-overwrite-changes-dialog"]'
        )
        self.assertIsNotNone(dialog_subtitle)
        self.assertIn(
            "Proceeding will overwrite the changes made by System. "
            "Refreshing the page will show you the new changes, but you will lose any of your unsaved changes.",
            dialog_subtitle.string,
        )
        other_session_text = rendered_sessions[1].text
        self.assertIn("Vic Otheruser", other_session_text)
        self.assertIn("Currently viewing", other_session_text)
        self.assertNotIn("saved a new version", other_session_text)

        self.session.refresh_from_db()
        self.assertEqual(self.session.last_seen_at, TIMESTAMP_NOW)
        self.assertFalse(self.session.is_editing)

    @freeze_time(TIMESTAMP_NOW)
    def test_ping_session_ordering(self):
        fourth_user = self.create_user(
            "alyx", password="password", first_name="Alyx", last_name="Fourthuser"
        )
        fifth_user = self.create_user(
            "chell", password="password", first_name="Chell", last_name="Fifthuser"
        )

        third_session = EditingSession.objects.create(
            user=self.third_user,
            content_type=ContentType.objects.get_for_model(Page),
            object_id=self.page.id,
            last_seen_at=TIMESTAMP_2,
        )
        fourth_session = EditingSession.objects.create(
            user=fourth_user,
            content_type=ContentType.objects.get_for_model(Page),
            object_id=self.page.id,
            # newer ping but not the last one to be created
            last_seen_at=TIMESTAMP_1,
        )
        fifth_session = EditingSession.objects.create(
            user=fifth_user,
            content_type=ContentType.objects.get_for_model(Page),
            object_id=self.page.id,
            last_seen_at=TIMESTAMP_4,
            is_editing=True,
        )

        with freeze_time(TIMESTAMP_3):
            new_revision = self.page.save_revision(user=self.third_user)

        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", self.page.id, self.session.id),
            ),
            {"revision_id": self.original_revision.id},
        )
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json["session_id"], self.session.id)
        self.assertEqual(
            response_json["other_sessions"],
            [
                # The session with the new revision should be shown first
                {
                    "session_id": third_session.id,
                    "user": "Gordon Thirduser",
                    "last_seen_at": TIMESTAMP_3.isoformat(),
                    "is_editing": False,
                    "revision_id": new_revision.id,
                },
                # Then any sessions that are currently editing
                {
                    "session_id": fifth_session.id,
                    "user": "Chell Fifthuser",
                    "last_seen_at": TIMESTAMP_4.isoformat(),
                    "is_editing": True,
                    "revision_id": None,
                },
                # Then any other sessions, sorted ascending by session_id
                {
                    "session_id": self.other_session.id,
                    "user": "Vic Otheruser",
                    "last_seen_at": TIMESTAMP_2.isoformat(),
                    "is_editing": False,
                    "revision_id": None,
                },
                {
                    "session_id": fourth_session.id,
                    "user": "Alyx Fourthuser",
                    "last_seen_at": TIMESTAMP_1.isoformat(),
                    "is_editing": False,
                    "revision_id": None,
                },
            ],
        )
        self.session.refresh_from_db()
        self.assertEqual(self.session.last_seen_at, TIMESTAMP_NOW)
        self.assertFalse(self.session.is_editing)

    @freeze_time(TIMESTAMP_NOW)
    def test_ping_new_session(self):
        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", self.page.id, 999999),
            )
        )
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        new_session_id = response_json["session_id"]
        session = EditingSession.objects.get(id=new_session_id)
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.last_seen_at, TIMESTAMP_NOW)
        self.assertFalse(session.is_editing)

        self.assertEqual(
            response_json["other_sessions"],
            [
                # The user's original session is not shown as it is not
                # currently editing nor has it created the latest revision
                {
                    "session_id": self.other_session.id,
                    "user": "Vic Otheruser",
                    "last_seen_at": TIMESTAMP_2.isoformat(),
                    "is_editing": False,
                    "revision_id": None,
                },
            ],
        )

        # Should include the new URLs for the new session
        self.assertEqual(
            response_json["ping_url"],
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", self.page.id, session.id),
            ),
        )

        self.assertEqual(
            response_json["release_url"],
            reverse(
                "wagtailadmin_editing_sessions:release",
                args=(session.id,),
            ),
        )

        # content_object is a non-specific Page object
        self.assertEqual(type(session.content_object), Page)
        self.assertEqual(session.content_object.id, self.page.id)

        self.assertEqual(session.last_seen_at, TIMESTAMP_NOW)

    @freeze_time(TIMESTAMP_NOW)
    def test_ping_new_session_with_editing_flag(self):
        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", self.page.id, 999999),
            ),
            {"is_editing": "1"},
        )
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        new_session_id = response_json["session_id"]
        session = EditingSession.objects.get(id=new_session_id)
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.last_seen_at, TIMESTAMP_NOW)
        self.assertTrue(session.is_editing)

        self.assertEqual(
            response_json["other_sessions"],
            [
                # The user's original session is not shown as it is not
                # currently editing nor has it created the latest revision
                {
                    "session_id": self.other_session.id,
                    "user": "Vic Otheruser",
                    "last_seen_at": TIMESTAMP_2.isoformat(),
                    "is_editing": False,
                    "revision_id": None,
                },
            ],
        )

        # content_object is a non-specific Page object
        self.assertEqual(type(session.content_object), Page)
        self.assertEqual(session.content_object.id, self.page.id)

        self.assertEqual(session.last_seen_at, TIMESTAMP_NOW)

        # The original session should not be changed
        self.session.refresh_from_db()
        self.assertEqual(self.session.last_seen_at, TIMESTAMP_1)
        self.assertFalse(self.session.is_editing)

        # Ping with the original session
        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", self.page.id, self.session.id),
            )
        )
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json["session_id"], self.session.id)
        self.assertEqual(
            response_json["other_sessions"],
            [
                # The new session should be shown as it is currently editing
                {
                    "session_id": session.id,
                    "user": "Bob Testuser",
                    "last_seen_at": TIMESTAMP_NOW.isoformat(),
                    "is_editing": True,
                    "revision_id": None,
                },
                {
                    "session_id": self.other_session.id,
                    "user": "Vic Otheruser",
                    "last_seen_at": TIMESTAMP_2.isoformat(),
                    "is_editing": False,
                    "revision_id": None,
                },
            ],
        )

        soup = self.get_soup(response_json["html"])
        rendered_sessions = soup.select("ol.w-editing-sessions__list li")
        self.assertEqual(len(rendered_sessions), 2)
        session_text = rendered_sessions[0].text
        self.assertIn("You have unsaved changes in another window", session_text)
        self.assertNotIn("Currently viewing", session_text)
        dialog_title = soup.select_one(
            'template[data-w-teleport-target-value="#title-text-w-overwrite-changes-dialog"]'
        )
        self.assertIsNone(dialog_title)
        dialog_subtitle = soup.select_one(
            'template[data-w-teleport-target-value="#subtitle-w-overwrite-changes-dialog"]'
        )
        self.assertIsNone(dialog_subtitle)
        other_session_text = rendered_sessions[1].text
        self.assertIn("Vic Otheruser", other_session_text)
        self.assertIn("Currently viewing", other_session_text)
        self.assertNotIn("saved a new version", other_session_text)

        self.session.refresh_from_db()
        self.assertEqual(self.session.last_seen_at, TIMESTAMP_NOW)
        self.assertFalse(self.session.is_editing)

    @freeze_time(TIMESTAMP_NOW)
    def test_ping_new_session_with_revision(self):
        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", self.page.id, 999999),
            ),
            {"revision_id": self.original_revision.id},
        )
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        new_session_id = response_json["session_id"]
        session = EditingSession.objects.get(id=new_session_id)
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.last_seen_at, TIMESTAMP_NOW)
        self.assertFalse(session.is_editing)

        self.assertEqual(
            response_json["other_sessions"],
            [
                # The user's original session is not shown as it is not
                # currently editing nor has it created the latest revision
                {
                    "session_id": self.other_session.id,
                    "user": "Vic Otheruser",
                    "last_seen_at": TIMESTAMP_2.isoformat(),
                    "is_editing": False,
                    "revision_id": None,
                },
            ],
        )

        # content_object is a non-specific Page object
        self.assertEqual(type(session.content_object), Page)
        self.assertEqual(session.content_object.id, self.page.id)

        self.assertEqual(session.last_seen_at, TIMESTAMP_NOW)

        # The original session should not be changed
        self.session.refresh_from_db()
        self.assertEqual(self.session.last_seen_at, TIMESTAMP_1)
        self.assertFalse(self.session.is_editing)

        # Ping with the original session
        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", self.page.id, self.session.id),
            )
        )
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json["session_id"], self.session.id)
        self.assertEqual(
            response_json["other_sessions"],
            [
                # The new session is not shown as it is not
                # currently editing nor has it created the latest revision
                {
                    "session_id": self.other_session.id,
                    "user": "Vic Otheruser",
                    "last_seen_at": TIMESTAMP_2.isoformat(),
                    "is_editing": False,
                    "revision_id": None,
                },
            ],
        )
        self.session.refresh_from_db()
        self.assertEqual(self.session.last_seen_at, TIMESTAMP_NOW)
        self.assertFalse(self.session.is_editing)

        # Save a new revision as the current user
        with freeze_time(TIMESTAMP_4):
            new_revision = self.page.save_revision(user=self.user)

        # Ping with the previously "new" session
        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", self.page.id, new_session_id),
            ),
            {"revision_id": self.original_revision.id},
        )
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json["session_id"], new_session_id)

        self.assertEqual(
            response_json["other_sessions"],
            [
                # The new revision should be indicated in the response.
                # In this case, it's attached to the original session. This may
                # not be exactly true, i.e. the new revision might not be created
                # by the original session. However, we don't keep track of which
                # session created which revision, and we don't really need to.
                # All we need to know is that there is a new revision since the
                # one the session has in hand. As the new revision happens to
                # be created by self.user, and the only other session we have
                # of that user is the original session (self.session), we attach
                # the new revision to that session.
                {
                    "session_id": self.session.id,
                    "user": "Bob Testuser",
                    "last_seen_at": TIMESTAMP_NOW.isoformat(),
                    "is_editing": False,
                    "revision_id": new_revision.id,
                },
                {
                    "session_id": self.other_session.id,
                    "user": "Vic Otheruser",
                    "last_seen_at": TIMESTAMP_2.isoformat(),
                    "is_editing": False,
                    "revision_id": None,
                },
            ],
        )

        # Ping with the original self.session
        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", self.page.id, self.session.id),
            ),
            {"revision_id": self.original_revision.id},
        )
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json["session_id"], self.session.id)

        self.assertEqual(
            response_json["other_sessions"],
            [
                # In the eye of the original session, the new revision is
                # attached to the new session (for the same reason as the
                # previous explanation).
                {
                    "session_id": new_session_id,
                    "user": "Bob Testuser",
                    "last_seen_at": TIMESTAMP_NOW.isoformat(),
                    "is_editing": False,
                    "revision_id": new_revision.id,
                },
                {
                    "session_id": self.other_session.id,
                    "user": "Vic Otheruser",
                    "last_seen_at": TIMESTAMP_2.isoformat(),
                    "is_editing": False,
                    "revision_id": None,
                },
            ],
        )

        # Delete the new session
        session.delete()

        # Ping with the original self.session
        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", self.page.id, self.session.id),
            ),
            {"revision_id": self.original_revision.id},
        )
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json["session_id"], self.session.id)

        self.assertEqual(
            response_json["other_sessions"],
            [
                # The 'other' session of the same user is still shown
                # as it has the latest revision, even though there are no
                # other sessions to attach the revision to. The last_seen_at
                # is set to the time of the revision's creation.
                {
                    "session_id": None,
                    "user": "Bob Testuser",
                    "last_seen_at": TIMESTAMP_4.isoformat(),
                    "is_editing": False,
                    "revision_id": new_revision.id,
                },
                {
                    "session_id": self.other_session.id,
                    "user": "Vic Otheruser",
                    "last_seen_at": TIMESTAMP_2.isoformat(),
                    "is_editing": False,
                    "revision_id": None,
                },
            ],
        )

    @freeze_time(TIMESTAMP_NOW)
    def test_user_must_have_edit_permission_on_page(self):
        # make user a member of Editors
        self.user.is_superuser = False
        self.user.save()
        editors = Group.objects.get(name="Editors")
        self.user.groups.add(editors)

        # give the Editors group edit permision on other_page only
        GroupPagePermission.objects.filter(group=editors).delete()
        GroupPagePermission.objects.create(
            group=editors,
            page=self.other_page,
            permission=Permission.objects.get(codename="change_page"),
        )

        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", self.page.id, 999999),
            )
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", self.other_page.id, 999999),
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_moderator_without_explicit_edit_permission_on_page(self):
        # submit page for moderation
        workflow = self.page.get_workflow()
        workflow.start(self.page, self.other_user)

        # Revoke all page permissions from the Moderators group, so that the workflow is
        # the only thing granting them access to the page
        moderators = Group.objects.get(name="Moderators")
        moderators.page_permissions.all().delete()

        # make user a moderator
        self.user.is_superuser = False
        self.user.save()
        self.user.groups.add(moderators)

        # access to the ping endpoint should be granted
        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", self.page.id, self.session.id),
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_locked_page(self):
        self.page.locked = True
        self.page.locked_by = self.other_user
        self.page.locked_at = TIMESTAMP_PAST
        self.page.save()

        # access to the ping endpoint should be granted
        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", self.page.id, self.session.id),
            )
        )
        self.assertEqual(response.status_code, 200)

    @freeze_time(TIMESTAMP_NOW)
    def test_ping_snippet_model(self):
        snippet = Advert.objects.create(text="Test snippet")

        # make user a member of Editors
        self.user.is_superuser = False
        self.user.save()
        editors = Group.objects.get(name="Editors")
        self.user.groups.add(editors)

        editors.permissions.add(
            Permission.objects.get(codename="change_advert"),
        )

        session = EditingSession.objects.create(
            user=self.user,
            content_type=ContentType.objects.get_for_model(Advert),
            object_id=snippet.pk,
            last_seen_at=TIMESTAMP_1,
        )
        # add two sessions from other_user to test that we correctly merge them into
        # one record in the response
        EditingSession.objects.create(
            user=self.other_user,
            content_type=ContentType.objects.get_for_model(Advert),
            object_id=snippet.pk,
            last_seen_at=TIMESTAMP_2,
            is_editing=True,
        )
        other_session_2 = EditingSession.objects.create(
            user=self.other_user,
            content_type=ContentType.objects.get_for_model(Advert),
            object_id=snippet.pk,
            last_seen_at=TIMESTAMP_3,
            is_editing=False,
        )

        # session with last_seen_at too far in the past to be included in the response
        EditingSession.objects.create(
            user=self.other_user,
            content_type=ContentType.objects.get_for_model(Advert),
            object_id=snippet.pk,
            last_seen_at=TIMESTAMP_PAST,
        )
        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("tests", "advert", str(snippet.pk), session.id),
            )
        )
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json["session_id"], session.id)
        self.assertEqual(
            response_json["other_sessions"],
            [
                {
                    "session_id": other_session_2.id,
                    "user": "Vic Otheruser",
                    "last_seen_at": TIMESTAMP_3.isoformat(),
                    "is_editing": True,
                    "revision_id": None,
                },
            ],
        )
        session.refresh_from_db()
        self.assertEqual(session.last_seen_at, TIMESTAMP_NOW)
        self.assertFalse(session.is_editing)

    def test_ping_snippet_model_without_permission(self):
        snippet = Advert.objects.create(text="Test snippet")

        # make user a member of Editors
        self.user.is_superuser = False
        self.user.save()
        editors = Group.objects.get(name="Editors")
        self.user.groups.add(editors)

        session = EditingSession.objects.create(
            user=self.user,
            content_type=ContentType.objects.get_for_model(Advert),
            object_id=snippet.pk,
            last_seen_at=TIMESTAMP_1,
        )
        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("tests", "advert", str(snippet.pk), session.id),
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_moderator_without_explicit_edit_permission_on_snippet(self):
        snippet = FullFeaturedSnippet.objects.create(text="Test snippet")
        snippet.save_revision(user=self.other_user)

        # Assign default workflow to the snippet model
        snippet_content_type = ContentType.objects.get_for_model(FullFeaturedSnippet)
        workflow = Workflow.objects.get()
        WorkflowContentType.objects.create(
            content_type=snippet_content_type,
            workflow=workflow,
        )

        # submit snippet for moderation
        workflow = snippet.get_workflow()
        workflow.start(snippet, self.other_user)

        # make user a moderator. The Moderators group has no explicit permission over the
        # FullFeaturedSnippet model, and is only granted access to it via the workflow
        moderators = Group.objects.get(name="Moderators")
        self.user.is_superuser = False
        self.user.save()
        self.user.groups.add(moderators)

        session = EditingSession.objects.create(
            user=self.user,
            content_type=ContentType.objects.get_for_model(FullFeaturedSnippet),
            object_id=snippet.pk,
            last_seen_at=TIMESTAMP_1,
        )

        # access to the ping endpoint should be granted
        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("tests", "fullfeaturedsnippet", snippet.id, session.id),
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_locked_snippet(self):
        snippet = FullFeaturedSnippet.objects.create(text="Test snippet")

        snippet.locked = True
        snippet.locked_by = self.other_user
        snippet.locked_at = TIMESTAMP_PAST
        snippet.save()

        session = EditingSession.objects.create(
            user=self.user,
            content_type=ContentType.objects.get_for_model(FullFeaturedSnippet),
            object_id=snippet.pk,
            last_seen_at=TIMESTAMP_1,
        )

        # access to the ping endpoint should be granted
        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("tests", "fullfeaturedsnippet", snippet.id, session.id),
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_must_post(self):
        response = self.client.get(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", self.page.id, 999999),
            )
        )
        self.assertEqual(response.status_code, 405)
        self.assertCountEqual(
            EditingSession.objects.all(),
            [self.session, self.other_session, self.old_session],
        )

    def test_invalid_data(self):
        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", self.page.id, self.session.id),
            ),
            {"is_editing": "invalid"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Invalid data"})
        self.assertCountEqual(
            EditingSession.objects.all(),
            [self.session, self.other_session, self.old_session],
        )


class TestCleanup(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.create_superuser(
            "bob", password="password", first_name="Bob", last_name="Testuser"
        )
        self.root_page = Page.get_first_root_node()

        self.page = SimplePage(title="Test page", slug="test-page", content="test page")
        self.root_page.add_child(instance=self.page)

        page_content_type = ContentType.objects.get_for_model(Page)

        self.session = EditingSession.objects.create(
            user=self.user,
            content_type=page_content_type,
            object_id=self.page.id,
            last_seen_at=TIMESTAMP_1,
        )
        self.old_session = EditingSession.objects.create(
            user=self.user,
            content_type=page_content_type,
            object_id=self.page.id,
            last_seen_at=TIMESTAMP_PAST,
        )

    @freeze_time(TIMESTAMP_NOW)
    def test_cleanup(self):
        EditingSession.cleanup()
        self.assertTrue(EditingSession.objects.filter(id=self.session.id).exists())
        self.assertFalse(EditingSession.objects.filter(id=self.old_session.id).exists())


class TestReleaseView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.create_superuser(
            "bob", password="password", first_name="Bob", last_name="Testuser"
        )
        self.login(user=self.user)
        self.root_page = Page.get_first_root_node()

        self.page = SimplePage(title="Test page", slug="test-page", content="test page")
        self.root_page.add_child(instance=self.page)

        self.other_user = self.create_user(
            "vic", password="password", first_name="Vic", last_name="Otheruser"
        )

        page_content_type = ContentType.objects.get_for_model(Page)

        self.session = EditingSession.objects.create(
            user=self.user,
            content_type=page_content_type,
            object_id=self.page.id,
            last_seen_at=TIMESTAMP_1,
        )
        self.other_session = EditingSession.objects.create(
            user=self.other_user,
            content_type=page_content_type,
            object_id=self.page.id,
            last_seen_at=TIMESTAMP_1,
        )

    def test_release(self):
        response = self.client.post(
            reverse("wagtailadmin_editing_sessions:release", args=(self.session.id,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(EditingSession.objects.filter(id=self.session.id).exists())
        self.assertTrue(
            EditingSession.objects.filter(id=self.other_session.id).exists()
        )

    def test_must_post(self):
        response = self.client.get(
            reverse("wagtailadmin_editing_sessions:release", args=(self.session.id,))
        )
        self.assertEqual(response.status_code, 405)
        self.assertTrue(EditingSession.objects.filter(id=self.session.id).exists())
        self.assertTrue(
            EditingSession.objects.filter(id=self.other_session.id).exists()
        )

    def test_cannot_release_other_users_session(self):
        response = self.client.post(
            reverse(
                "wagtailadmin_editing_sessions:release", args=(self.other_session.id,)
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(EditingSession.objects.filter(id=self.session.id).exists())
        self.assertTrue(
            EditingSession.objects.filter(id=self.other_session.id).exists()
        )


class TestModuleInEditView(WagtailTestUtils, TestCase):
    url_name = "wagtailadmin_pages:edit"
    model = Page

    def setUp(self):
        self.user = self.create_superuser(
            "bob", password="password", first_name="Bob", last_name="Testuser"
        )
        self.login(user=self.user)
        self.content_type = ContentType.objects.get_for_model(self.model)

        self.object = self.create_object()

        self.session = EditingSession.objects.create(
            user=self.user,
            content_type=self.content_type,
            object_id=self.object.pk,
            last_seen_at=TIMESTAMP_1,
        )
        self.old_session = EditingSession.objects.create(
            user=self.user,
            content_type=self.content_type,
            object_id=self.object.pk,
            last_seen_at=TIMESTAMP_PAST,
        )

    def create_object(self):
        root_page = Page.get_first_root_node()
        page = SimplePage(title="Foo", slug="foo", content="bar")
        root_page.add_child(instance=page)
        page.save_revision()
        return page

    def get(self):
        return self.client.get(reverse(self.url_name, args=(quote(self.object.pk),)))

    def assertRevisionInput(self, soup):
        revision_input = soup.select_one('input[name="revision_id"]')
        self.assertIsNotNone(revision_input)
        self.assertEqual(revision_input.get("type"), "hidden")
        self.assertEqual(
            revision_input.get("value"),
            str(self.object.latest_revision.id),
        )

    @freeze_time(TIMESTAMP_NOW)
    def test_edit_view_with_default_interval(self):
        self.assertEqual(EditingSession.objects.all().count(), 2)
        response = self.get()
        self.assertEqual(response.status_code, 200)

        # Should perform a cleanup of the EditingSessions
        self.assertTrue(EditingSession.objects.filter(id=self.session.id).exists())
        self.assertFalse(EditingSession.objects.filter(id=self.old_session.id).exists())

        # Should create a new EditingSession for the current user
        self.assertEqual(EditingSession.objects.all().count(), 2)
        new_session = EditingSession.objects.exclude(id=self.session.id).get(
            content_type=self.content_type,
            object_id=self.object.pk,
        )
        self.assertEqual(new_session.user, self.user)

        # Should load the EditingSessionsModule with the default interval (10s)
        soup = self.get_soup(response.content)
        module = soup.select_one('form[data-controller~="w-session"]')
        self.assertIsNotNone(module)
        self.assertEqual(module.get("data-w-session-interval-value"), "10000")

        # Should show the revision_id input
        self.assertRevisionInput(module)

    @freeze_time(TIMESTAMP_NOW)
    @override_settings(WAGTAIL_EDITING_SESSION_PING_INTERVAL=30000)
    def test_edit_view_with_custom_interval(self):
        self.assertEqual(EditingSession.objects.all().count(), 2)
        response = self.get()
        self.assertEqual(response.status_code, 200)

        # Should perform a cleanup of the EditingSessions
        self.assertTrue(EditingSession.objects.filter(id=self.session.id).exists())
        self.assertFalse(EditingSession.objects.filter(id=self.old_session.id).exists())

        # Should create a new EditingSession for the current user
        self.assertEqual(EditingSession.objects.all().count(), 2)
        new_session = EditingSession.objects.exclude(id=self.session.id).get(
            content_type=self.content_type,
            object_id=self.object.pk,
        )
        self.assertEqual(new_session.user, self.user)

        # Should load the EditingSessionsModule
        soup = self.get_soup(response.content)
        module = soup.select_one('form[data-controller~="w-session"]')
        self.assertIsNotNone(module)
        self.assertEqual(
            module.get("data-w-swap-src-value"),
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=(
                    self.content_type.app_label,
                    self.content_type.model,
                    quote(self.object.pk),
                    new_session.id,
                ),
            ),
        )
        self.assertEqual(
            module.get("data-w-action-url-value"),
            reverse(
                "wagtailadmin_editing_sessions:release",
                args=(new_session.id,),
            ),
        )

        # Should use the custom interval (30s)
        self.assertEqual(module.get("data-w-session-interval-value"), "30000")
        self.assertRevisionInput(module)


class TestModuleInEditViewWithRevisableSnippet(TestModuleInEditView):
    model = FullFeaturedSnippet

    @property
    def url_name(self):
        return self.model.snippet_viewset.get_url_name("edit")

    def create_object(self):
        obj = self.model.objects.create(text="Shodan")
        obj.save_revision()
        return obj


class TestModuleInEditViewWithNonRevisableSnippet(TestModuleInEditView):
    model = AdvertWithCustomPrimaryKey

    @property
    def url_name(self):
        return self.model.snippet_viewset.get_url_name("edit")

    def create_object(self):
        return self.model.objects.create(text="GLaDOS", advert_id="m0n5t3r!/#")

    def assertRevisionInput(self, soup):
        revision_input = soup.select_one('input[name="revision_id"]')
        self.assertIsNone(revision_input)
