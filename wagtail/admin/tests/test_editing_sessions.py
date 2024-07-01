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
    TIMESTAMP_PAST = timezone.make_aware(
        datetime.datetime(2020, 1, 1, 11, 30, 0), timezone=datetime.timezone.utc
    )
    TIMESTAMP_RECENT = timezone.make_aware(
        datetime.datetime(2020, 1, 1, 11, 59, 59), timezone=datetime.timezone.utc
    )
    TIMESTAMP_NOW = timezone.make_aware(
        datetime.datetime(2020, 1, 1, 12, 0, 0), timezone=datetime.timezone.utc
    )
else:
    TIMESTAMP_PAST = datetime.datetime(2020, 1, 1, 11, 30, 0)
    TIMESTAMP_RECENT = datetime.datetime(2020, 1, 1, 11, 59, 59)
    TIMESTAMP_NOW = datetime.datetime(2020, 1, 1, 12, 0, 0)


class TestPingView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.create_superuser(
            "bob", password="password", first_name="Bob", last_name="Testuser"
        )
        self.login(user=self.user)
        self.root_page = Page.get_first_root_node()

        self.page = SimplePage(title="Test page", slug="test-page", content="test page")
        self.root_page.add_child(instance=self.page)
        self.other_page = SimplePage(
            title="Other page", slug="other-page", content="other page"
        )
        self.root_page.add_child(instance=self.other_page)

        self.other_user = self.create_user(
            "vic", password="password", first_name="Vic", last_name="Otheruser"
        )

        page_content_type = ContentType.objects.get_for_model(Page)

        self.session = EditingSession.objects.create(
            user=self.user,
            content_type=page_content_type,
            object_id=self.page.id,
            last_seen_at=TIMESTAMP_RECENT,
        )
        self.other_session = EditingSession.objects.create(
            user=self.other_user,
            content_type=page_content_type,
            object_id=self.page.id,
            last_seen_at=TIMESTAMP_RECENT,
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
            last_seen_at=TIMESTAMP_RECENT,
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
        self.assertCountEqual(
            response_json["other_sessions"],
            [
                {
                    "session_id": self.other_session.id,
                    "user": "Vic Otheruser",
                    "last_seen_at": TIMESTAMP_RECENT.isoformat(),
                },
            ],
        )
        self.session.refresh_from_db()
        self.assertEqual(self.session.last_seen_at, TIMESTAMP_NOW)

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

        self.assertCountEqual(
            response_json["other_sessions"],
            [
                {
                    "session_id": self.session.id,
                    "user": "Bob Testuser",
                    "last_seen_at": TIMESTAMP_RECENT.isoformat(),
                },
                {
                    "session_id": self.other_session.id,
                    "user": "Vic Otheruser",
                    "last_seen_at": TIMESTAMP_RECENT.isoformat(),
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
            last_seen_at=TIMESTAMP_RECENT,
        )
        other_session = EditingSession.objects.create(
            user=self.other_user,
            content_type=ContentType.objects.get_for_model(FullFeaturedSnippet),
            object_id=snippet.pk,
            last_seen_at=TIMESTAMP_RECENT,
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
        self.assertCountEqual(
            response_json["other_sessions"],
            [
                {
                    "session_id": other_session.id,
                    "user": "Vic Otheruser",
                    "last_seen_at": TIMESTAMP_RECENT.isoformat(),
                },
            ],
        )
        session.refresh_from_db()
        self.assertEqual(session.last_seen_at, TIMESTAMP_NOW)

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
            last_seen_at=TIMESTAMP_RECENT,
        )
        response = self.client.get(
            reverse(
                "wagtailadmin_editing_sessions:ping",
                args=("tests", "fullfeaturedsnippet", str(snippet.pk), session.id),
            )
        )
        self.assertEqual(response.status_code, 404)
