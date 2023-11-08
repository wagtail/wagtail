from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from wagtail.documents import get_document_model
from wagtail.documents.wagtail_hooks import DocumentsSummaryItem
from wagtail.models import Collection, GroupCollectionPermission, Site
from wagtail.test.utils import WagtailTestUtils


class TestDocumentsSummary(WagtailTestUtils, TestCase):
    @classmethod
    def setUpTestData(self):
        Document = get_document_model()

        # Permissions
        doc_content_type = ContentType.objects.get_for_model(Document)
        add_doc_permission = Permission.objects.get(
            content_type=doc_content_type, codename="add_document"
        )
        change_doc_permission = Permission.objects.get(
            content_type=doc_content_type, codename="change_document"
        )
        choose_doc_permission = Permission.objects.get(
            content_type=doc_content_type, codename="choose_document"
        )

        # Collections
        self.root_collection = Collection.get_first_root_node()
        self.reports_collection = self.root_collection.add_child(name="Birds")

        # Groups
        doc_changers_group = Group.objects.create(name="Document changers")
        GroupCollectionPermission.objects.create(
            group=doc_changers_group,
            collection=self.root_collection,
            permission=change_doc_permission,
        )

        report_adders_group = Group.objects.create(name="Bird adders")
        GroupCollectionPermission.objects.create(
            group=report_adders_group,
            collection=self.reports_collection,
            permission=add_doc_permission,
        )

        report_choosers_group = Group.objects.create(name="Bird choosers")
        GroupCollectionPermission.objects.create(
            group=report_choosers_group,
            collection=self.reports_collection,
            permission=choose_doc_permission,
        )

        # Users
        self.superuser = self.create_superuser(
            "superuser", "superuser@example.com", "password"
        )

        # a user with add_doc permission on reports via the report_adders group
        self.report_adder = self.create_user(
            "reportadder", "reportadder@example.com", "password"
        )
        self.report_adder.groups.add(report_adders_group)

        # a user with choose_doc permission on reports via the report_choosers group
        self.report_chooser = self.create_user(
            "reportchooser", "reportchooser@example.com", "password"
        )
        self.report_chooser.groups.add(report_choosers_group)

        # Documents

        # an doc in the root owned by 'reportadder'
        self.changer_doc = Document.objects.create(
            title="reportadder's doc",
            collection=self.root_collection,
            uploaded_by_user=self.report_adder,
        )

        # an doc in reports owned by 'reportadder'
        self.changer_report = Document.objects.create(
            title="reportadder's report",
            collection=self.reports_collection,
            uploaded_by_user=self.report_adder,
        )

        # an doc in reports owned by 'reportadder'
        self.adder_report = Document.objects.create(
            title="reportadder's report",
            collection=self.reports_collection,
            uploaded_by_user=self.report_adder,
        )

    def setUp(self):
        self.login(self.superuser)

    def get_request(self):
        return self.client.get(reverse("wagtailadmin_home")).wsgi_request

    def assertSummaryContains(self, content):
        summary = DocumentsSummaryItem(self.get_request()).render_html()
        self.assertIn(content, summary)

    def test_site_name_is_shown(self):
        self.assertEqual(Site.objects.count(), 1)
        site = Site.objects.first()
        self.assertSummaryContains(site.site_name)

    def test_user_with_permissions_is_shown_panel(self):
        self.assertTrue(DocumentsSummaryItem(self.get_request()).is_shown())

    def test_user_with_no_permissions_is_not_shown_panel(self):
        self.superuser.is_superuser = False
        self.superuser.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.superuser.save()
        self.assertFalse(DocumentsSummaryItem(self.get_request()).is_shown())

    def test_user_sees_proper_doc_count(self):
        cases = (
            (self.superuser, "<span>3</span> Documents"),
            (self.report_adder, "<span>2</span> Documents"),
            (self.report_chooser, "<span>2</span> Documents"),
        )
        for user, content in cases:
            with self.subTest(user=user):
                self.login(user)
                self.assertSummaryContains(content)
