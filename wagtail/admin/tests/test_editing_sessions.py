import datetime

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from wagtail.admin.models import EditingSession
from wagtail.models import GroupPagePermission, Page
from wagtail.test.testapp.models import FullFeaturedSnippet, SimplePage
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
    TIMESTAMP_NOW = timezone.make_aware(
        datetime.datetime(2020, 1, 1, 12, 0, 0), timezone=datetime.timezone.utc
    )
else:
    TIMESTAMP_ANCIENT = datetime.datetime(2019, 1, 1, 10, 30, 0)
    TIMESTAMP_PAST = datetime.datetime(2020, 1, 1, 10, 30, 0)
    TIMESTAMP_1 = datetime.datetime(2020, 1, 1, 11, 59, 51)
    TIMESTAMP_2 = datetime.datetime(2020, 1, 1, 11, 59, 52)
    TIMESTAMP_3 = datetime.datetime(2020, 1, 1, 11, 59, 53)
    TIMESTAMP_NOW = datetime.datetime(2020, 1, 1, 12, 0, 0)


class TestPingView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.create_superuser(
            "bob", password="password", first_name="Bob", last_name="Testuser"
        )
        self.other_user = self.create_user(
            "vic", password="password", first_name="Vic", last_name="Otheruser"
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
        response = self.client.get(
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
        response = self.client.get(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("auth", "group", str(editors.pk), session.id),
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_ping_non_existent_object(self):
        response = self.client.get(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", 999999, self.session.id),
            )
        )
        self.assertEqual(response.status_code, 404)

    @freeze_time(TIMESTAMP_NOW)
    def test_ping_existing_session(self):
        response = self.client.get(
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
        self.session.refresh_from_db()
        self.assertEqual(self.session.last_seen_at, TIMESTAMP_NOW)
        self.assertFalse(self.session.is_editing)

    @freeze_time(TIMESTAMP_NOW)
    def test_ping_existing_session_with_editing_flag(self):
        response = self.client.get(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", self.page.id, self.session.id),
            ),
            {"editing": "1"},
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
        self.session.refresh_from_db()
        self.assertEqual(self.session.last_seen_at, TIMESTAMP_NOW)
        self.assertTrue(self.session.is_editing)

    @freeze_time(TIMESTAMP_NOW)
    def test_ping_with_revision(self):
        response = self.client.get(
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
        self.session.refresh_from_db()
        self.assertEqual(self.session.last_seen_at, TIMESTAMP_NOW)
        self.assertFalse(self.session.is_editing)

        with freeze_time(TIMESTAMP_3):
            new_revision = self.page.save_revision(user=self.other_user)

        response = self.client.get(
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
        self.session.refresh_from_db()
        self.assertEqual(self.session.last_seen_at, TIMESTAMP_NOW)
        self.assertFalse(self.session.is_editing)

        self.other_session.delete()

        response = self.client.get(
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
        self.session.refresh_from_db()
        self.assertEqual(self.session.last_seen_at, TIMESTAMP_NOW)
        self.assertFalse(self.session.is_editing)

    @freeze_time(TIMESTAMP_NOW)
    def test_ping_new_session(self):
        response = self.client.get(
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
                {
                    "session_id": self.session.id,
                    "user": "Bob Testuser",
                    "last_seen_at": TIMESTAMP_1.isoformat(),
                    "is_editing": False,
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

        # content_object is a non-specific Page object
        self.assertEqual(type(session.content_object), Page)
        self.assertEqual(session.content_object.id, self.page.id)

        self.assertEqual(session.last_seen_at, TIMESTAMP_NOW)

    @freeze_time(TIMESTAMP_NOW)
    def test_ping_new_session_with_editing_flag(self):
        response = self.client.get(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", self.page.id, 999999),
            ),
            {"editing": "1"},
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
                {
                    "session_id": self.session.id,
                    "user": "Bob Testuser",
                    "last_seen_at": TIMESTAMP_1.isoformat(),
                    "is_editing": False,
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

        # content_object is a non-specific Page object
        self.assertEqual(type(session.content_object), Page)
        self.assertEqual(session.content_object.id, self.page.id)

        self.assertEqual(session.last_seen_at, TIMESTAMP_NOW)

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

        response = self.client.get(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", self.page.id, 999999),
            )
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.get(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("wagtailcore", "page", self.other_page.id, 999999),
            )
        )
        self.assertEqual(response.status_code, 200)

    @freeze_time(TIMESTAMP_NOW)
    def test_ping_snippet_model(self):
        snippet = FullFeaturedSnippet.objects.create(text="Test snippet")

        # make user a member of Editors
        self.user.is_superuser = False
        self.user.save()
        editors = Group.objects.get(name="Editors")
        self.user.groups.add(editors)

        editors.permissions.add(
            Permission.objects.get(codename="change_fullfeaturedsnippet"),
        )

        session = EditingSession.objects.create(
            user=self.user,
            content_type=ContentType.objects.get_for_model(FullFeaturedSnippet),
            object_id=snippet.pk,
            last_seen_at=TIMESTAMP_1,
        )
        # add two sessions from other_user to test that we correctly merge them into
        # one record in the response
        EditingSession.objects.create(
            user=self.other_user,
            content_type=ContentType.objects.get_for_model(FullFeaturedSnippet),
            object_id=snippet.pk,
            last_seen_at=TIMESTAMP_2,
            is_editing=True,
        )
        other_session_2 = EditingSession.objects.create(
            user=self.other_user,
            content_type=ContentType.objects.get_for_model(FullFeaturedSnippet),
            object_id=snippet.pk,
            last_seen_at=TIMESTAMP_3,
            is_editing=False,
        )

        # session with last_seen_at too far in the past to be included in the response
        EditingSession.objects.create(
            user=self.other_user,
            content_type=ContentType.objects.get_for_model(FullFeaturedSnippet),
            object_id=snippet.pk,
            last_seen_at=TIMESTAMP_PAST,
        )
        response = self.client.get(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("tests", "fullfeaturedsnippet", str(snippet.pk), session.id),
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
        snippet = FullFeaturedSnippet.objects.create(text="Test snippet")

        # make user a member of Editors
        self.user.is_superuser = False
        self.user.save()
        editors = Group.objects.get(name="Editors")
        self.user.groups.add(editors)

        session = EditingSession.objects.create(
            user=self.user,
            content_type=ContentType.objects.get_for_model(FullFeaturedSnippet),
            object_id=snippet.pk,
            last_seen_at=TIMESTAMP_1,
        )
        response = self.client.get(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("tests", "fullfeaturedsnippet", str(snippet.pk), session.id),
            )
        )
        self.assertEqual(response.status_code, 404)


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
