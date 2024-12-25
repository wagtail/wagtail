from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse
from freezegun import freeze_time

from wagtail.admin.staticfiles import versioned_static
from wagtail.models import Page
from wagtail.test.testapp.models import (
    DefaultStreamPage,
    EventPage,
    FormClassAdditionalFieldPage,
    SecretPage,
)
from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.template_tests import AdminTemplateTestUtils
from wagtail.test.utils.timestamps import local_datetime


class TestRevisions(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.christmas_event = EventPage.objects.get(url_path="/home/events/christmas/")
        self.christmas_event.title = "Last Christmas"
        self.christmas_event.date_from = "2013-12-25"
        self.christmas_event.body = (
            "<p>Last Christmas I gave you my heart, "
            "but the very next day you gave it away</p>"
        )
        self.last_christmas_revision = self.christmas_event.save_revision()
        self.last_christmas_revision.created_at = local_datetime(2013, 12, 25)
        self.last_christmas_revision.save()

        self.christmas_event.title = "This Christmas"
        self.christmas_event.date_from = "2014-12-25"
        self.christmas_event.body = (
            "<p>This year, to save me from tears, "
            "I'll give it to someone special</p>"
        )
        self.this_christmas_revision = self.christmas_event.save_revision()
        self.this_christmas_revision.created_at = local_datetime(2014, 12, 25)
        self.this_christmas_revision.save()

        self.login()

    def test_get_revisions_index(self):
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:revisions_index", args=(self.christmas_event.id,)
            )
        )
        history_url = reverse(
            "wagtailadmin_pages:history", args=(self.christmas_event.id,)
        )
        self.assertRedirects(response, history_url)

    def request_preview_revision(self):
        last_christmas_preview_url = reverse(
            "wagtailadmin_pages:revisions_view",
            args=(self.christmas_event.id, self.last_christmas_revision.id),
        )
        return self.client.get(last_christmas_preview_url)

    def test_preview_revision(self):
        response = self.request_preview_revision()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Last Christmas I gave you my heart")

        # Should show edit link in the userbar
        # https://github.com/wagtail/wagtail/issues/10002
        self.assertContains(response, "Edit this page")
        self.assertContains(
            response,
            reverse("wagtailadmin_pages:edit", args=(self.christmas_event.id,)),
        )

    def test_preview_revision_with_no_page_permissions_redirects_to_admin(self):
        admin_only_user = self.create_user(
            username="admin_only", email="admin_only@email.com", password="password"
        )
        admin_only_user.user_permissions.add(
            Permission.objects.get_by_natural_key(
                codename="access_admin", app_label="wagtailadmin", model="admin"
            )
        )

        self.login(user=admin_only_user)
        response = self.request_preview_revision()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("wagtailadmin_home"))

    def test_preview_revision_forbidden_without_permission(self):
        # Alter the editors group so it has no permissions for Christmas page.
        st_patricks = Page.objects.get(slug="saint-patrick")
        editors_group = Group.objects.get(name="Site-wide editors")
        editors_group.page_permissions.update(page_id=st_patricks.id)

        editor = get_user_model().objects.get(email="siteeditor@example.com")

        self.login(editor)
        response = self.request_preview_revision()

        self.assertEqual(response.status_code, 302)

    def test_revert_revision(self):
        last_christmas_preview_url = reverse(
            "wagtailadmin_pages:revisions_revert",
            args=(self.christmas_event.id, self.last_christmas_revision.id),
        )
        response = self.client.get(last_christmas_preview_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Editing Event page")
        self.assertContains(response, "You are viewing a previous version of this page")

        # Form should show the content of the revision, not the current draft
        self.assertContains(response, "Last Christmas I gave you my heart")

        # Form should use the revisions revert URL as the action
        soup = self.get_soup(response.content)
        form = soup.select_one("form[data-edit-form]")
        self.assertIsNotNone(form)
        self.assertEqual(
            form.get("action"),
            reverse(
                "wagtailadmin_pages:revisions_revert",
                args=(self.christmas_event.id, self.last_christmas_revision.id),
            ),
        )

        # Buttons should be relabelled
        self.assertContains(response, "Replace current draft")
        self.assertContains(response, "Publish this version")

    @freeze_time("2014-12-20 12:00:00")
    def test_scheduled_revision(self):
        if settings.USE_TZ:
            # 12:00 UTC
            self.christmas_event.go_live_at = "2014-12-26T12:00:00.000Z"
        else:
            # 12:00 in no specific timezone
            self.christmas_event.go_live_at = "2014-12-26T12:00:00"
        this_christmas_revision = self.christmas_event.save_revision(log_action=True)
        this_christmas_revision.publish(log_action=True)
        this_christmas_unschedule_url = reverse(
            "wagtailadmin_pages:revisions_unschedule",
            args=(self.christmas_event.id, this_christmas_revision.id),
        )
        response = self.client.get(
            reverse("wagtailadmin_pages:history", args=(self.christmas_event.id,))
        )
        self.assertEqual(response.status_code, 200)

        if settings.USE_TZ:
            # the default timezone is "Asia/Tokyo", so we expect UTC +9
            expected_date_string = "Dec. 26, 2014, 9 p.m."
        else:
            expected_date_string = "Dec. 26, 2014, noon"

        self.assertContains(
            response, f"Page scheduled for publishing at {expected_date_string}"
        )
        self.assertContains(response, this_christmas_unschedule_url)


class TestStreamRevisions(WagtailTestUtils, TestCase):
    def setUp(self):
        self.root_page = Page.objects.get(id=2)

        self.test_page = DefaultStreamPage(
            title="A DefaultStreamPage",
            slug="a-defaultstreampage",
        )
        self.root_page.add_child(instance=self.test_page)

        self.test_page.title = "An Updated DefaultStreamPage"
        self.first_revision = self.test_page.save_revision()
        self.first_revision.created_at = local_datetime(2022, 5, 10)
        self.first_revision.save()

        self.login()

    def test_revert_revision(self):
        test_page_revert_url = reverse(
            "wagtailadmin_pages:revisions_revert",
            args=(self.test_page.id, self.first_revision.id),
        )
        response = self.client.get(test_page_revert_url)
        self.assertEqual(response.status_code, 200)

        html = response.content.decode()
        blocks_js = versioned_static("wagtailadmin/js/telepath/blocks.js")
        streamfield_css = versioned_static("wagtailadmin/css/panels/streamfield.css")

        # The media files for StreamField should be included in the HTML
        self.assertTagInHTML(f'<script src="{blocks_js}"></script>', html)
        self.assertTagInHTML(
            f'<link href="{streamfield_css}" media="all" rel="stylesheet">',
            html,
            allow_extra_attrs=True,  # Django 4.1 removes the type="text/css" attribute
        )


class TestCompareRevisions(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    # Actual tests for the comparison classes can be found in test_compare.py

    base_breadcrumb_items = []
    fixtures = ["test.json"]

    def setUp(self):
        self.christmas_event = EventPage.objects.get(url_path="/home/events/christmas/")
        self.christmas_event.title = "Last Christmas"
        self.christmas_event.date_from = "2013-12-25"
        self.christmas_event.body = (
            "<p>Last Christmas I gave you my heart, "
            "but the very next day you gave it away</p>"
        )
        self.last_christmas_revision = self.christmas_event.save_revision()
        self.last_christmas_revision.created_at = local_datetime(2013, 12, 25)
        self.last_christmas_revision.save()

        self.christmas_event.title = "This Christmas"
        self.christmas_event.date_from = "2014-12-25"
        self.christmas_event.body = (
            "<p>This year, to save me from tears, "
            "I'll give it to someone special</p>"
        )
        self.this_christmas_revision = self.christmas_event.save_revision()
        self.this_christmas_revision.created_at = local_datetime(2014, 12, 25)
        self.this_christmas_revision.save()

        self.login()

    def test_compare_revisions(self):
        compare_url = reverse(
            "wagtailadmin_pages:revisions_compare",
            args=(
                self.christmas_event.id,
                self.last_christmas_revision.id,
                self.this_christmas_revision.id,
            ),
        )
        response = self.client.get(compare_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            '<span class="deletion">Last Christmas I gave you my heart, but the very next day you gave it away</span><span class="addition">This year, to save me from tears, I&#39;ll give it to someone special</span>',
            html=True,
        )

        history_url = reverse(
            "wagtailadmin_pages:history", args=(self.christmas_event.id,)
        )

        self.assertBreadcrumbsItemsRendered(
            [
                {
                    "url": reverse("wagtailadmin_explore_root")
                    if page.is_root()
                    else reverse("wagtailadmin_explore", args=(page.pk,)),
                    "label": page.get_admin_display_title(),
                }
                for page in self.christmas_event.get_ancestors(inclusive=True)
            ]
            + [
                {"url": history_url, "label": "History"},
                {"url": "", "label": "Compare", "sublabel": "This Christmas"},
            ],
            response.content,
        )

        soup = self.get_soup(response.content)
        edit_url = reverse("wagtailadmin_pages:edit", args=(self.christmas_event.id,))
        edit_button = soup.select_one(f"a.w-header-button[href='{edit_url}']")
        self.assertIsNotNone(edit_button)
        self.assertEqual(edit_button.text.strip(), "Edit")

    def test_compare_revisions_earliest(self):
        compare_url = reverse(
            "wagtailadmin_pages:revisions_compare",
            args=(self.christmas_event.id, "earliest", self.this_christmas_revision.id),
        )
        response = self.client.get(compare_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            '<span class="deletion">Last Christmas I gave you my heart, but the very next day you gave it away</span><span class="addition">This year, to save me from tears, I&#39;ll give it to someone special</span>',
            html=True,
        )

    def test_compare_revisions_latest(self):
        compare_url = reverse(
            "wagtailadmin_pages:revisions_compare",
            args=(self.christmas_event.id, self.last_christmas_revision.id, "latest"),
        )
        response = self.client.get(compare_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            '<span class="deletion">Last Christmas I gave you my heart, but the very next day you gave it away</span><span class="addition">This year, to save me from tears, I&#39;ll give it to someone special</span>',
            html=True,
        )

    def test_compare_revisions_live(self):
        # Mess with the live version, bypassing revisions
        self.christmas_event.body = (
            "<p>This year, to save me from tears, " "I'll just feed it to the dog</p>"
        )
        self.christmas_event.save(update_fields=["body"])

        compare_url = reverse(
            "wagtailadmin_pages:revisions_compare",
            args=(self.christmas_event.id, self.last_christmas_revision.id, "live"),
        )
        response = self.client.get(compare_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            '<span class="deletion">Last Christmas I gave you my heart, but the very next day you gave it away</span><span class="addition">This year, to save me from tears, I&#39;ll just feed it to the dog</span>',
            html=True,
        )


class TestCompareRevisionsWithPerUserEditHandlers(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.home = Page.objects.get(url_path="/home/")
        self.secret_page = SecretPage(
            title="Secret page",
            boring_data="InnocentCorp is the leading supplier of door hinges",
            secret_data="for flying saucers",
        )
        self.home.add_child(instance=self.secret_page)
        self.old_revision = self.secret_page.save_revision()
        self.secret_page.boring_data = (
            "InnocentCorp is the leading supplier of rubber sprockets"
        )
        self.secret_page.secret_data = "for fake moon landings"
        self.new_revision = self.secret_page.save_revision()
        self.compare_url = reverse(
            "wagtailadmin_pages:revisions_compare",
            args=(self.secret_page.id, self.old_revision.id, self.new_revision.id),
        )

    def test_comparison_as_superuser(self):
        self.login()
        response = self.client.get(self.compare_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            'InnocentCorp is the leading supplier of <span class="deletion">door hinges</span><span class="addition">rubber sprockets</span>',
            html=True,
        )
        self.assertContains(
            response,
            'for <span class="deletion">flying saucers</span><span class="addition">fake moon landings</span>',
            html=True,
        )

    def test_comparison_as_ordinary_user(self):
        user = self.create_user(username="editor", password="password")
        user.groups.add(Group.objects.get(name="Site-wide editors"))
        self.login(username="editor", password="password")

        response = self.client.get(self.compare_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            'InnocentCorp is the leading supplier of <span class="deletion">door hinges</span><span class="addition">rubber sprockets</span>',
            html=True,
        )
        self.assertNotContains(
            response,
            "moon landings",
        )


class TestCompareRevisionsWithNonModelField(WagtailTestUtils, TestCase):
    """
    Tests if form fields defined in the base_form_class will not be included.
    in revisions view as they are not actually on the model.
    Flagged in issue #3737
    Note: Actual tests for comparison classes can be found in test_compare.py
    """

    fixtures = ["test.json"]
    # FormClassAdditionalFieldPage

    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add child page of class with base_form_class override
        # non model field is 'code'
        self.test_page = FormClassAdditionalFieldPage(
            title="A Statement",
            slug="a-statement",
            location="Early Morning Cafe, Mainland, NZ",
            body="<p>hello</p>",
        )
        self.root_page.add_child(instance=self.test_page)

        # add new revision
        self.test_page.title = "Statement"
        self.test_page.location = "Victory Monument, Bangkok"
        self.test_page.body = "<p>I would like very much to go into the forrest.</p>"
        self.test_page_revision = self.test_page.save_revision()
        self.test_page_revision.created_at = local_datetime(2017, 10, 15)
        self.test_page_revision.save()

        # add another new revision
        self.test_page.title = "True Statement"
        self.test_page.location = "Victory Monument, Bangkok"
        self.test_page.body = "<p>I would like very much to go into the forest.</p>"
        self.test_page_revision_new = self.test_page.save_revision()
        self.test_page_revision_new.created_at = local_datetime(2017, 10, 16)
        self.test_page_revision_new.save()

        self.login()

    def test_base_form_class_used(self):
        """First ensure that the non-model field is appearing in edit."""
        edit_url = reverse(
            "wagtailadmin_pages:add",
            args=("tests", "formclassadditionalfieldpage", self.test_page.id),
        )
        response = self.client.get(edit_url)
        self.assertContains(
            response,
            '<input type="text" name="code" aria-describedby="panel-child-content-child-code-helptext" required id="id_code" maxlength="5" />',
            html=True,
        )

    def test_compare_revisions(self):
        """Confirm that the non-model field is not shown in revision."""
        compare_url = reverse(
            "wagtailadmin_pages:revisions_compare",
            args=(
                self.test_page.id,
                self.test_page_revision.id,
                self.test_page_revision_new.id,
            ),
        )
        response = self.client.get(compare_url)
        self.assertContains(
            response,
            '<span class="deletion">forrest.</span><span class="addition">forest.</span>',
        )
        # should not contain the field defined in the formclass used
        self.assertNotContains(response, "<h2>Code:</h2>")


class TestRevisionsUnschedule(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.christmas_event = EventPage.objects.get(url_path="/home/events/christmas/")
        self.christmas_event.title = "Last Christmas"
        self.christmas_event.date_from = "2013-12-25"
        self.christmas_event.body = (
            "<p>Last Christmas I gave you my heart, "
            "but the very next day you gave it away</p>"
        )
        self.last_christmas_revision = self.christmas_event.save_revision()
        self.last_christmas_revision.created_at = local_datetime(2013, 12, 25)
        self.last_christmas_revision.save()
        self.last_christmas_revision.publish()

        self.christmas_event.title = "This Christmas"
        self.christmas_event.date_from = "2014-12-25"
        self.christmas_event.body = (
            "<p>This year, to save me from tears, "
            "I'll give it to someone special</p>"
        )
        self.this_christmas_revision = self.christmas_event.save_revision()
        self.this_christmas_revision.created_at = local_datetime(2014, 12, 24)
        self.this_christmas_revision.save()

        self.this_christmas_revision.approved_go_live_at = local_datetime(2014, 12, 25)
        self.this_christmas_revision.save()

        self.user = self.login()

    def test_unschedule_view(self):
        """
        This tests that the unschedule view responds with a confirm page
        """
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:revisions_unschedule",
                args=(self.christmas_event.id, self.this_christmas_revision.id),
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/shared/revisions/confirm_unschedule.html"
        )

    def test_unschedule_view_invalid_page_id(self):
        """
        This tests that the unschedule view returns an error if the page id is invalid
        """
        # Get unschedule page
        response = self.client.get(
            reverse("wagtailadmin_pages:revisions_unschedule", args=(12345, 67894))
        )

        # Check that the user received a 404 response
        self.assertEqual(response.status_code, 404)

    def test_unschedule_view_invalid_revision_id(self):
        """
        This tests that the unschedule view returns an error if the page id is invalid
        """
        # Get unschedule page
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:revisions_unschedule",
                args=(self.christmas_event.id, 67894),
            )
        )

        # Check that the user received a 404 response
        self.assertEqual(response.status_code, 404)

    def test_unschedule_view_bad_permissions(self):
        """
        This tests that the unschedule view doesn't allow users without publish permissions
        """
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        # Get unschedule page
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:revisions_unschedule",
                args=(self.christmas_event.id, self.this_christmas_revision.id),
            )
        )

        # Check that the user received a 302 redirected response
        self.assertEqual(response.status_code, 302)

    def test_unschedule_view_post(self):
        """
        This posts to the unschedule view and checks that the revision was unscheduled
        """

        # Post to the unschedule page
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:revisions_unschedule",
                args=(self.christmas_event.id, self.this_christmas_revision.id),
            )
        )

        # Should be redirected to page history
        self.assertRedirects(
            response,
            reverse("wagtailadmin_pages:history", args=(self.christmas_event.id,)),
        )

        # Check that the page has no approved_schedule
        self.assertFalse(
            EventPage.objects.get(id=self.christmas_event.id).approved_schedule
        )

        # Check that the approved_go_live_at has been cleared from the revision
        self.assertIsNone(
            self.christmas_event.revisions.get(
                id=self.this_christmas_revision.id
            ).approved_go_live_at
        )

    def test_unschedule_view_post_with_next_url(self):
        """
        This tests that the redirect response follows the "next" parameter
        """

        unschedule_url = reverse(
            "wagtailadmin_pages:revisions_unschedule",
            args=(self.christmas_event.id, self.this_christmas_revision.id),
        )
        edit_url = reverse("wagtailadmin_pages:edit", args=(self.christmas_event.id,))

        # Post to the unschedule page
        response = self.client.post(f"{unschedule_url}?next={edit_url}")

        # Should be redirected to edit page
        self.assertRedirects(response, edit_url)

        # Check that the page has no approved_schedule
        self.assertFalse(
            EventPage.objects.get(id=self.christmas_event.id).approved_schedule
        )

        # Check that the approved_go_live_at has been cleared from the revision
        self.assertIsNone(
            self.christmas_event.revisions.get(
                id=self.this_christmas_revision.id
            ).approved_go_live_at
        )


class TestRevisionsUnscheduleForUnpublishedPages(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.unpublished_event = EventPage.objects.get(
            url_path="/home/events/tentative-unpublished-event/"
        )
        self.unpublished_event.title = "Unpublished Page"
        self.unpublished_event.date_from = "2014-12-25"
        self.unpublished_event.body = "<p>Some Content</p>"
        self.unpublished_revision = self.unpublished_event.save_revision()
        self.unpublished_revision.created_at = local_datetime(2014, 12, 25)
        self.unpublished_revision.save()

        self.user = self.login()

    def test_unschedule_view(self):
        """
        This tests that the unschedule view responds with a confirm page
        """
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:revisions_unschedule",
                args=(self.unpublished_event.id, self.unpublished_revision.id),
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/shared/revisions/confirm_unschedule.html"
        )

    def test_unschedule_view_post(self):
        """
        This posts to the unschedule view and checks that the revision was unscheduled
        """

        # Post to the unschedule page
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:revisions_unschedule",
                args=(self.unpublished_event.id, self.unpublished_revision.id),
            )
        )

        # Should be redirected to page history
        self.assertRedirects(
            response,
            reverse("wagtailadmin_pages:history", args=(self.unpublished_event.id,)),
        )

        # Check that the page has no approved_schedule
        self.assertFalse(
            EventPage.objects.get(id=self.unpublished_event.id).approved_schedule
        )

        # Check that the approved_go_live_at has been cleared from the revision
        self.assertIsNone(
            self.unpublished_event.revisions.get(
                id=self.unpublished_revision.id
            ).approved_go_live_at
        )
