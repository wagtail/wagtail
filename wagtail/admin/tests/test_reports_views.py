import datetime
from io import BytesIO

from django.conf import settings
from django.conf.locale import LANG_INFO
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone, translation
from openpyxl import load_workbook

from wagtail.admin.views.mixins import ExcelDateFormatter
from wagtail.admin.views.reports import page_types_usage
from wagtail.models import (
    GroupPagePermission,
    Locale,
    ModelLogEntry,
    Page,
    PageLogEntry,
)
from wagtail.test.testapp.models import EventPage, EventPageSpeaker, SimplePage
from wagtail.test.utils import WagtailTestUtils


class TestLockedPagesView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()

    def get(self, params={}):
        return self.client.get(reverse("wagtailadmin_reports:locked_pages"), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/reports/locked_pages.html")

        # Initially there should be no locked pages
        self.assertContains(response, "No locked pages found.")

        # No user locked anything
        self.assertInHTML(
            """
            <select name="locked_by" id="id_locked_by">
                <option value="" selected>---------</option>
            </select>
            """,
            response.content.decode(),
        )

        self.page = Page.objects.first()
        self.page.locked = True
        self.page.locked_by = self.user
        self.page.locked_at = timezone.now()
        self.page.save()

        # Now the listing should contain our locked page
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/reports/locked_pages.html")
        self.assertNotContains(response, "No locked pages found.")
        self.assertContains(response, self.page.title)

        self.assertInHTML(
            f"""
            <select name="locked_by" id="id_locked_by">
                <option value="" selected>---------</option>
                <option value="{self.user.pk}">{self.user}</option>
            </select>
            """,
            response.content.decode(),
        )

        # Locked by current user shown in indicator
        self.assertContains(response, "locked-indicator indicator--is-inverse")
        self.assertContains(
            response, 'title="This page is locked, by you, to further editing"'
        )

    def test_get_with_minimal_permissions(self):
        group = Group.objects.create(name="test group")
        self.user.is_superuser = False
        self.user.save()
        self.user.groups.add(group)
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        GroupPagePermission.objects.create(
            group=group,
            page=Page.objects.first(),
            permission_type="unlock",
        )

        response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/reports/locked_pages.html")
        self.assertContains(response, "No locked pages found.")

    def test_get_with_no_permissions(self):
        self.user.is_superuser = False
        self.user.save()
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )

        response = self.get()

        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_csv_export(self):

        self.page = Page.objects.first()
        self.page.locked = True
        self.page.locked_by = self.user
        if settings.USE_TZ:
            # 12:00 UTC
            self.page.locked_at = "2013-02-01T12:00:00.000Z"
            self.page.latest_revision_created_at = "2013-01-01T12:00:00.000Z"
        else:
            # 12:00 in no specific timezone
            self.page.locked_at = "2013-02-01T12:00:00"
            self.page.latest_revision_created_at = "2013-01-01T12:00:00"
        self.page.save()

        response = self.get(params={"export": "csv"})

        # Check response
        self.assertEqual(response.status_code, 200)
        data_lines = response.getvalue().decode().split("\n")
        self.assertEqual(
            data_lines[0], "Title,Updated,Status,Type,Locked at,Locked by\r"
        )
        if settings.USE_TZ:
            self.assertEqual(
                data_lines[1],
                "Root,2013-01-01 12:00:00+00:00,live,Page,2013-02-01 12:00:00+00:00,test@email.com\r",
            )
        else:
            self.assertEqual(
                data_lines[1],
                "Root,2013-01-01 12:00:00,live,Page,2013-02-01 12:00:00,test@email.com\r",
            )

    def test_xlsx_export(self):

        self.page = Page.objects.first()
        self.page.locked = True
        self.page.locked_by = self.user
        if settings.USE_TZ:
            # 12:00 UTC
            self.page.locked_at = "2013-02-01T12:00:00.000Z"
            self.page.latest_revision_created_at = "2013-01-01T12:00:00.000Z"
        else:
            # 12:00 in no specific timezone
            self.page.locked_at = "2013-02-01T12:00:00"
            self.page.latest_revision_created_at = "2013-01-01T12:00:00"
        self.page.save()

        response = self.get(params={"export": "xlsx"})

        # Check response - the locked page info should be in it
        self.assertEqual(response.status_code, 200)
        workbook_data = response.getvalue()
        worksheet = load_workbook(filename=BytesIO(workbook_data))["Sheet1"]
        cell_array = [[cell.value for cell in row] for row in worksheet.rows]
        self.assertEqual(
            cell_array[0],
            ["Title", "Updated", "Status", "Type", "Locked at", "Locked by"],
        )
        self.assertEqual(
            cell_array[1],
            [
                "Root",
                datetime.datetime(2013, 1, 1, 12, 0),
                "live",
                "Page",
                datetime.datetime(2013, 2, 1, 12, 0),
                "test@email.com",
            ],
        )
        self.assertEqual(len(cell_array), 2)

        self.assertEqual(worksheet["B2"].number_format, ExcelDateFormatter().get())
        self.assertEqual(worksheet["E2"].number_format, ExcelDateFormatter().get())


class TestFilteredLockedPagesView(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.user = self.login()
        self.unpublished_page = Page.objects.get(
            url_path="/home/events/tentative-unpublished-event/"
        )
        self.unpublished_page.locked = True
        self.unpublished_page.locked_by = self.user
        self.unpublished_page.locked_at = timezone.now()
        self.unpublished_page.save()

    def get(self, params={}):
        return self.client.get(reverse("wagtailadmin_reports:locked_pages"), params)

    def test_filter_by_live(self):
        response = self.get(params={"live": "true"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Tentative Unpublished Event")
        self.assertContains(response, "My locked page")

        response = self.get(params={"live": "false"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tentative Unpublished Event")
        self.assertNotContains(response, "My locked page")

    def test_filter_by_user(self):
        response = self.get(params={"locked_by": self.user.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tentative Unpublished Event")
        self.assertNotContains(response, "My locked page")


class TestFilteredLogEntriesView(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.user = self.login()
        self.home_page = Page.objects.get(url_path="/home/")

        self.create_log = PageLogEntry.objects.log_action(
            self.home_page, "wagtail.create"
        )
        self.edit_log_1 = PageLogEntry.objects.log_action(
            self.home_page, "wagtail.edit"
        )
        self.edit_log_2 = PageLogEntry.objects.log_action(
            self.home_page, "wagtail.edit"
        )
        self.edit_log_3 = PageLogEntry.objects.log_action(
            self.home_page, "wagtail.edit"
        )

        self.create_comment_log = PageLogEntry.objects.log_action(
            self.home_page,
            "wagtail.comments.create",
            data={
                "comment": {
                    "contentpath": "title",
                    "text": "Foo",
                }
            },
        )
        self.edit_comment_log = PageLogEntry.objects.log_action(
            self.home_page,
            "wagtail.comments.edit",
            data={
                "comment": {
                    "contentpath": "title",
                    "text": "Edited",
                }
            },
        )
        self.create_reply_log = PageLogEntry.objects.log_action(
            self.home_page,
            "wagtail.comments.create_reply",
            data={
                "comment": {
                    "contentpath": "title",
                    "text": "Foo",
                }
            },
        )

    def get(self, params={}):
        return self.client.get(reverse("wagtailadmin_reports:site_history"), params)

    def assert_log_entries(self, response, expected):
        actual = set(response.context["object_list"])
        self.assertSetEqual(actual, set(expected))

    def test_unfiltered(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assert_log_entries(
            response,
            [
                self.create_log,
                self.edit_log_1,
                self.edit_log_2,
                self.edit_log_3,
                self.create_comment_log,
                self.edit_comment_log,
                self.create_reply_log,
            ],
        )

    def test_filter_by_action(self):
        response = self.get(params={"action": "wagtail.edit"})
        self.assertEqual(response.status_code, 200)
        self.assert_log_entries(
            response,
            [
                self.edit_log_1,
                self.edit_log_2,
                self.edit_log_3,
            ],
        )

    def test_hide_commenting_actions(self):
        response = self.get(params={"hide_commenting_actions": "on"})
        self.assertEqual(response.status_code, 200)
        self.assert_log_entries(
            response,
            [
                self.create_log,
                self.edit_log_1,
                self.edit_log_2,
                self.edit_log_3,
            ],
        )

    def test_log_entry_with_stale_content_type(self):
        stale_content_type = ContentType.objects.create(
            app_label="fake_app", model="deleted model"
        )

        ModelLogEntry.objects.create(
            object_id=123,
            content_type=stale_content_type,
            label="This instance's model was deleted, but its content type was not",
            action="wagtail.create",
            timestamp=timezone.now(),
        )

        response = self.get()
        self.assertContains(response, "Deleted model")

    def test_log_entry_with_null_content_type(self):
        ModelLogEntry.objects.create(
            object_id=123,
            content_type=None,
            label="This instance's model was deleted, and so was its content type",
            action="wagtail.create",
            timestamp=timezone.now(),
        )

        response = self.get()
        self.assertContains(response, "Unknown content type")


@override_settings(
    USE_L10N=True,
)
class TestExcelDateFormatter(TestCase):
    def test_all_locales(self):
        formatter = ExcelDateFormatter()

        for lang in LANG_INFO.keys():
            with self.subTest(lang), translation.override(lang):
                self.assertNotEqual(formatter.get(), "")

    def test_format(self):
        formatter = ExcelDateFormatter()

        with self.subTest(format="r"):
            # Format code for RFC 5322 formatted date, e.g. 'Thu, 21 Dec 2000 16:01:07'
            self.assertEqual(formatter.format("r"), "ddd, d mmm yyyy hh:mm:ss")

        with self.subTest(format="m/d/Y g:i A"):
            # Format code for e.g. '12/21/2000 4:01 PM'
            self.assertEqual(formatter.format("m/d/Y g:i A"), "mm/dd/yyyy h:mm AM/PM")


class TestAgingPagesView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()
        self.root = Page.objects.first()
        self.home = Page.objects.get(slug="home")

    def get(self, params={}):
        return self.client.get(reverse("wagtailadmin_reports:aging_pages"), params)

    def publish_home_page(self):
        self.home.save_revision().publish(user=self.user)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/reports/aging_pages.html")

    def test_displays_only_published_pages(self):
        response = self.get()
        self.assertContains(response, "No pages found.")

        self.publish_home_page()
        response = self.get()

        # Home Page should be listed
        self.assertContains(response, self.home.title)
        # Last published by user is set
        self.assertContains(response, self.user.get_username())

        self.assertNotContains(response, self.root.title)
        self.assertNotContains(response, "No pages found.")

    def test_permissions(self):
        # Publish home page
        self.publish_home_page()

        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.get()
        self.assertContains(response, "No pages found.")
        self.assertNotContains(response, self.home.title)

    def test_csv_export(self):
        self.publish_home_page()
        if settings.USE_TZ:
            self.home.last_published_at = "2013-01-01T12:00:00.000Z"
        else:
            self.home.last_published_at = "2013-01-01T12:00:00"
        self.home.save()

        response = self.get(params={"export": "csv"})
        self.assertEqual(response.status_code, 200)

        data_lines = response.getvalue().decode().split("\n")
        self.assertEqual(
            data_lines[0], "Title,Status,Last published at,Last published by,Type\r"
        )
        if settings.USE_TZ:
            self.assertEqual(
                data_lines[1],
                "Welcome to your new Wagtail site!,live + draft,2013-01-01 12:00:00+00:00,test@email.com,Page\r",
            )
        else:
            self.assertEqual(
                data_lines[1],
                "Welcome to your new Wagtail site!,live + draft,2013-01-01 12:00:00,test@email.com,Page\r",
            )

    def test_xlsx_export(self):
        self.publish_home_page()

        if settings.USE_TZ:
            self.home.last_published_at = "2013-01-01T12:00:00.000Z"
        else:
            self.home.last_published_at = "2013-01-01T12:00:00"
        self.home.save()

        response = self.get(params={"export": "xlsx"})
        self.assertEqual(response.status_code, 200)

        workbook_data = response.getvalue()
        worksheet = load_workbook(filename=BytesIO(workbook_data))["Sheet1"]
        cell_array = [[cell.value for cell in row] for row in worksheet.rows]

        self.assertEqual(
            cell_array[0],
            ["Title", "Status", "Last published at", "Last published by", "Type"],
        )
        self.assertEqual(
            cell_array[1],
            [
                "Welcome to your new Wagtail site!",
                "live + draft",
                datetime.datetime(2013, 1, 1, 12, 0),
                "test@email.com",
                "Page",
            ],
        )
        self.assertEqual(len(cell_array), 2)

        self.assertEqual(worksheet["C2"].number_format, ExcelDateFormatter().get())

    def test_report_renders_when_page_publisher_deleted(self):
        temp_user = self.create_superuser(
            "temp", email="temp@user.com", password="tempuser"
        )
        expected_deleted_string = f"user {temp_user.pk} (deleted)"

        self.home.save_revision().publish(user=temp_user)
        temp_user.delete()

        response = self.get()
        self.assertContains(response, expected_deleted_string)


class TestFilteredAgingPagesView(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.user = self.login()
        self.home_page = Page.objects.get(slug="home")
        self.aboutus_page = Page.objects.get(slug="about-us")

    def get(self, params={}):
        return self.client.get(reverse("wagtailadmin_reports:aging_pages"), params)

    def test_filter_by_live(self):
        response = self.get(params={"live": "true"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.home_page.title)
        self.assertContains(response, self.aboutus_page.title)

        response = self.get(params={"live": "false"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.home_page.title)
        self.assertNotContains(response, self.aboutus_page.title)

    def test_filter_by_content_type(self):
        response = self.get(
            params={"content_type": self.home_page.specific.content_type.pk}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.home_page.title)
        self.assertNotContains(response, self.aboutus_page.title)

    def test_filter_by_last_published_at(self):
        self.home_page.last_published_at = timezone.now()
        self.home_page.save()

        response = self.get(params={"last_published_at": "2015-01-01"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.aboutus_page.title)
        self.assertNotContains(response, self.home_page.title)


class PageTypesUsageReportViewTest(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.user = self.login()

    def get(self, params={}):
        return self.client.get(reverse("wagtailadmin_reports:page_types"), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/reports/page_types_usage.html")

    def test_displays_only_page_types(self):
        """Asserts that the correct models are included in the queryset."""
        response = self.get()
        # Assert that the response contains page models:
        self.assertContains(
            response, ContentType.objects.get_for_model(Page).name.title()
        )
        self.assertContains(
            response, ContentType.objects.get_for_model(EventPage).name.title()
        )
        # But it should not contain non-page models:
        self.assertNotContains(
            response, ContentType.objects.get_for_model(EventPageSpeaker).name.title()
        )


class PageTypesUsageReportViewQuerysetTests(WagtailTestUtils, TestCase):
    def setUp(self):
        super().setUp()
        self.view = page_types_usage.PageTypesUsageReportView()
        self.view.request = RequestFactory().get(
            reverse("wagtailadmin_reports:page_types")
        )
        self.root = Page.objects.first()
        self.home = Page.objects.get(slug="home")
        self.simple_page_a = SimplePage(title="Simple page A", content="hello")
        self.simple_page_b = SimplePage(title="Simple page B", content="hello")
        self.simple_page_c = SimplePage(title="Simple page C", content="hello")
        Page.get_first_root_node().add_child(instance=self.simple_page_a)
        Page.get_first_root_node().add_child(instance=self.simple_page_b)
        Page.get_first_root_node().add_child(instance=self.simple_page_c)

    def test_queryset_ordering(self):
        """Asserts that the queryset is ordered by page model count."""
        # Test that the queryset is correctly ordered by page model count
        queryset = self.view.get_queryset()
        # Convert queryset to list of ids to make it easier to test
        queryset_list_pks = list(queryset.values_list("pk", flat=True))
        # Get the positions of the content types in the list
        simple_page_content_type = ContentType.objects.get_for_model(SimplePage)
        simple_page_position = queryset_list_pks.index(simple_page_content_type.pk)
        page_content_type = ContentType.objects.get_for_model(Page)
        page_position = queryset_list_pks.index(page_content_type.pk)
        # Assert that the SimplePage comes before Page, since it has more entries
        self.assertTrue(simple_page_position < page_position)
        # There should be 3 SimplePages
        self.assertEqual(queryset.get(id=simple_page_content_type.pk).count, 3)
        # There should be 2 Pages (Homepage and Root)
        self.assertEqual(queryset.get(id=page_content_type.pk).count, 2)

    def test_queryset_last_edited_page(self):
        """Tests that the queryset correctly returns the last edited page."""
        # Edit the first product page
        revision = self.simple_page_a.save_revision()
        revision.publish()
        # Edit the second product page
        revision = self.simple_page_b.save_revision()
        revision.publish()
        # Edit the third product page
        revision = self.simple_page_c.save_revision()
        revision.publish()
        # Re-edit the first product page
        revision = self.simple_page_a.save_revision()
        revision.publish()
        # Get the queryset:
        queryset = self.view.decorate_paginated_queryset(self.view.get_queryset())
        # Assert that the first product page is the last edited page
        self.simple_page_a.refresh_from_db()
        self.assertEqual(queryset[0].last_edited_page.specific, self.simple_page_a)

    def test_queryset_last_edited_by(self):
        """Tests that the queryset correctly returns the last edited by user."""
        # Create some product pages:
        # Create some users:
        user_a = self.create_superuser(
            username="user_a", first_name="John", last_name="Doe"
        )
        user_b = self.create_superuser(
            username="user_b", first_name="Jane", last_name="Doe"
        )
        # Edit the first product page with user_a
        revision = self.simple_page_a.save_revision(user=user_a)
        revision.publish(user=user_a)
        # Re-edit the first product page with user_b
        revision = self.simple_page_a.save_revision(user=user_b)
        revision.publish(user=user_b)
        # Get the queryset:
        queryset = self.view.decorate_paginated_queryset(self.view.get_queryset())
        # Assert that the first product page is the last edited page
        self.simple_page_a.refresh_from_db()
        self.assertEqual(queryset[0].last_edited_page.specific, self.simple_page_a)
        # Assert that the first product page was last edited by user b
        self.assertEqual(queryset[0].last_edited_by, user_b.pk)
        self.assertEqual(queryset[0].last_edited_by_user, user_b.get_username())


@override_settings(LANGUAGE_CODE="en", WAGTAIL_I18N_ENABLED=True)
class PageTypesReportFiltersTests(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()
        self.default_locale = Locale.get_default()
        self.fr_locale, _ = Locale.objects.get_or_create(language_code="fr")

    def get(self, params={}):
        return self.client.get(reverse("wagtailadmin_reports:page_types"), params)

    def test_locale_filtering(self):
        # Create a product page in default locale
        page = Page(title="My Page")
        simple_page = SimplePage(title="Simple Page", content="hello")
        Page.get_first_root_node().add_child(instance=page)
        Page.get_first_root_node().add_child(instance=simple_page)
        # Translate pages to French
        page.copy_for_translation(self.fr_locale)
        simple_page.copy_for_translation(self.fr_locale)

        # Edit the product page in English to make sure that it's the latest
        simple_page.title = "Updated Simple Page English title"
        revision = simple_page.save_revision()
        simple_page.publish(revision)

        response = self.get()
        page_types = {
            content_type.id: content_type
            for content_type in response.context["object_list"]
        }

        page_row = page_types.get(ContentType.objects.get_for_model(Page).pk)
        simple_page_row = page_types.get(
            ContentType.objects.get_for_model(SimplePage).pk
        )

        self.assertEqual(page_row.count, 4)
        self.assertEqual(simple_page_row.count, 2)
        # The last edited page should be the French version
        self.assertEqual(page_row.last_edited_page.locale, self.fr_locale)
        # The last edited SimplePage should be the English version
        self.assertEqual(simple_page_row.last_edited_page.locale, self.default_locale)

        # Filter by French locale
        response = self.get({"page_locale": self.fr_locale.language_code})
        page_types = {
            content_type.id: content_type
            for content_type in response.context["object_list"]
        }

        page_row = page_types.get(ContentType.objects.get_for_model(Page).pk)
        simple_page_row = page_types.get(
            ContentType.objects.get_for_model(SimplePage).pk
        )

        # There should be 1 of each page (only the French locale ones)
        self.assertEqual(page_row.count, 1)
        self.assertEqual(simple_page_row.count, 1)
        # The last edited page should be the French version (even though product page was later edited in English)
        self.assertEqual(page_row.last_edited_page.locale, self.fr_locale)
        self.assertEqual(simple_page_row.last_edited_page.locale, self.fr_locale)

    @override_settings(
        WAGTAIL_CONTENT_LANGUAGES=[
            ("en", "English"),
            ("de", "German"),
            ("fr", "French"),
        ],
    )
    def test_get_locale_choices(self):
        choices = page_types_usage._get_locale_choices()

        expected_choices = [
            ("en", "English"),
            ("de", "German"),
            ("fr", "French"),
        ]

        self.assertCountEqual(choices, expected_choices)
