from django.contrib.auth.models import AnonymousUser, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from wagtail.documents.models import Document
from wagtail.models import Collection, GroupCollectionPermission
from wagtail.permission_policies.collections import (
    CollectionMangementPermissionPolicy,
    CollectionOwnershipPermissionPolicy,
    CollectionPermissionPolicy,
)
from wagtail.test.utils import WagtailTestUtils
from wagtail.tests.test_permission_policies import PermissionPolicyTestUtils


class PermissionPolicyTestCase(PermissionPolicyTestUtils, WagtailTestUtils, TestCase):
    def setUp(self):
        # Permissions
        document_content_type = ContentType.objects.get_for_model(Document)
        add_doc_permission = Permission.objects.get(
            content_type=document_content_type, codename="add_document"
        )
        change_doc_permission = Permission.objects.get(
            content_type=document_content_type, codename="change_document"
        )

        # Collections
        self.root_collection = Collection.get_first_root_node()
        self.reports_collection = self.root_collection.add_child(name="Reports")

        # Groups
        doc_changers_group = Group.objects.create(name="Document changers")
        GroupCollectionPermission.objects.create(
            group=doc_changers_group,
            collection=self.root_collection,
            permission=change_doc_permission,
        )

        report_changers_group = Group.objects.create(name="Report changers")
        GroupCollectionPermission.objects.create(
            group=report_changers_group,
            collection=self.reports_collection,
            permission=change_doc_permission,
        )

        report_adders_group = Group.objects.create(name="Report adders")
        GroupCollectionPermission.objects.create(
            group=report_adders_group,
            collection=self.reports_collection,
            permission=add_doc_permission,
        )

        # Users
        self.superuser = self.create_superuser(
            "superuser", "superuser@example.com", "password"
        )
        self.inactive_superuser = self.create_superuser(
            "inactivesuperuser", "inactivesuperuser@example.com", "password"
        )
        self.inactive_superuser.is_active = False
        self.inactive_superuser.save()

        # a user with change_document permission through the 'Document changers' group
        self.doc_changer = self.create_user(
            "docchanger", "docchanger@example.com", "password"
        )
        self.doc_changer.groups.add(doc_changers_group)

        # a user that has change_document permission, but is inactive
        self.inactive_doc_changer = self.create_user(
            "inactivedocchanger", "inactivedocchanger@example.com", "password"
        )
        self.inactive_doc_changer.groups.add(doc_changers_group)
        self.inactive_doc_changer.is_active = False
        self.inactive_doc_changer.save()

        # a user with change_document permission on reports via the report_changers group
        self.report_changer = self.create_user(
            "reportchanger", "reportchanger@example.com", "password"
        )
        self.report_changer.groups.add(report_changers_group)

        # a user with add_document permission on reports via the report_adders group
        self.report_adder = self.create_user(
            "reportadder", "reportadder@example.com", "password"
        )
        self.report_adder.groups.add(report_adders_group)

        # a user with no permissions
        self.useless_user = self.create_user(
            "uselessuser", "uselessuser@example.com", "password"
        )

        self.anonymous_user = AnonymousUser()

        # Documents

        # a document in the root owned by 'reportchanger'
        self.changer_doc = Document.objects.create(
            title="reportchanger's document",
            collection=self.root_collection,
            uploaded_by_user=self.report_changer,
        )

        # a document in reports owned by 'reportchanger'
        self.changer_report = Document.objects.create(
            title="reportchanger's report",
            collection=self.reports_collection,
            uploaded_by_user=self.report_changer,
        )

        # a document in reports owned by 'reportadder'
        self.adder_report = Document.objects.create(
            title="reportadder's report",
            collection=self.reports_collection,
            uploaded_by_user=self.report_adder,
        )

        # a document in reports owned by 'uselessuser'
        self.useless_report = Document.objects.create(
            title="uselessuser's report",
            collection=self.reports_collection,
            uploaded_by_user=self.useless_user,
        )

        # a document with no owner
        self.anonymous_report = Document.objects.create(
            title="anonymous report", collection=self.reports_collection
        )


class TestCollectionPermissionPolicy(PermissionPolicyTestCase):
    def setUp(self):
        super().setUp()
        self.policy = CollectionPermissionPolicy(Document)

    def test_user_has_permission(self):
        self.assertUserPermissionMatrix(
            [
                (self.superuser, True, True, True, True),
                (self.inactive_superuser, False, False, False, False),
                (self.doc_changer, False, True, False, False),
                (self.inactive_doc_changer, False, False, False, False),
                (self.report_changer, False, True, False, False),
                (self.report_adder, True, False, False, False),
                (self.useless_user, False, False, False, False),
                (self.anonymous_user, False, False, False, False),
            ]
        )

    def test_user_has_any_permission(self):
        self.assertTrue(
            self.policy.user_has_any_permission(self.superuser, ["add", "change"])
        )
        self.assertFalse(
            self.policy.user_has_any_permission(
                self.inactive_superuser, ["add", "change"]
            )
        )
        self.assertTrue(
            self.policy.user_has_any_permission(self.report_changer, ["add", "change"])
        )
        self.assertTrue(
            self.policy.user_has_any_permission(self.report_adder, ["add", "change"])
        )
        self.assertFalse(
            self.policy.user_has_any_permission(self.anonymous_user, ["add", "change"])
        )

    def test_users_with_any_permission(self):
        users_with_add_or_change_permission = self.policy.users_with_any_permission(
            ["add", "change"]
        )

        self.assertResultSetEqual(
            users_with_add_or_change_permission,
            [
                self.superuser,
                self.doc_changer,
                self.report_changer,
                self.report_adder,
            ],
        )

    def test_users_with_permission(self):
        users_with_change_permission = self.policy.users_with_permission("change")

        self.assertResultSetEqual(
            users_with_change_permission,
            [
                self.superuser,
                self.doc_changer,
                self.report_changer,
            ],
        )

        users_with_custom_permission = self.policy.users_with_permission("frobnicate")

        self.assertResultSetEqual(
            users_with_custom_permission,
            [
                self.superuser,
            ],
        )

    def test_user_has_permission_for_instance(self):
        # document in the root is only editable by users with permissions
        # on the root collection
        self.assertUserInstancePermissionMatrix(
            self.changer_doc,
            [
                (self.superuser, True, True, True),
                (self.inactive_superuser, False, False, False),
                (self.doc_changer, True, False, False),
                (self.inactive_doc_changer, False, False, False),
                (self.report_changer, False, False, False),
                (self.report_adder, False, False, False),
                (self.useless_user, False, False, False),
                (self.anonymous_user, False, False, False),
            ],
        )

        # document in 'reports' is editable by users with permissions
        # on 'reports' or the root collection
        self.assertUserInstancePermissionMatrix(
            self.useless_report,
            [
                (self.superuser, True, True, True),
                (self.inactive_superuser, False, False, False),
                (self.doc_changer, True, False, False),
                (self.inactive_doc_changer, False, False, False),
                (self.report_changer, True, False, False),
                (self.report_adder, False, False, False),
                (self.useless_user, False, False, False),
                (self.anonymous_user, False, False, False),
            ],
        )

    def test_user_has_any_permission_for_instance(self):
        self.assertTrue(
            self.policy.user_has_any_permission_for_instance(
                self.report_changer, ["change", "delete"], self.useless_report
            )
        )

        self.assertFalse(
            self.policy.user_has_any_permission_for_instance(
                self.report_changer, ["change", "delete"], self.changer_doc
            )
        )

        self.assertFalse(
            self.policy.user_has_any_permission_for_instance(
                self.anonymous_user, ["change", "delete"], self.changer_doc
            )
        )

    def test_instances_user_has_permission_for(self):
        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.superuser,
                "change",
            ),
            [
                self.changer_doc,
                self.changer_report,
                self.adder_report,
                self.useless_report,
                self.anonymous_report,
            ],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.inactive_superuser,
                "change",
            ),
            [],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.doc_changer,
                "change",
            ),
            [
                self.changer_doc,
                self.changer_report,
                self.adder_report,
                self.useless_report,
                self.anonymous_report,
            ],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.report_changer,
                "change",
            ),
            [
                self.changer_report,
                self.useless_report,
                self.adder_report,
                self.anonymous_report,
            ],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.useless_user,
                "change",
            ),
            [],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.anonymous_user,
                "change",
            ),
            [],
        )

    def test_instances_user_has_any_permission_for(self):
        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.superuser, ["change", "delete"]
            ),
            [
                self.changer_doc,
                self.changer_report,
                self.adder_report,
                self.useless_report,
                self.anonymous_report,
            ],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.inactive_superuser, ["change", "delete"]
            ),
            [],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.doc_changer, ["change", "delete"]
            ),
            [
                self.changer_doc,
                self.changer_report,
                self.adder_report,
                self.useless_report,
                self.anonymous_report,
            ],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.report_changer, ["change", "delete"]
            ),
            [
                self.changer_report,
                self.adder_report,
                self.useless_report,
                self.anonymous_report,
            ],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.useless_user, ["change", "delete"]
            ),
            [],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.anonymous_user, ["change", "delete"]
            ),
            [],
        )

    def test_users_with_permission_for_instance(self):
        self.assertResultSetEqual(
            self.policy.users_with_permission_for_instance("change", self.changer_doc),
            [self.superuser, self.doc_changer],
        )
        self.assertResultSetEqual(
            self.policy.users_with_permission_for_instance("change", self.adder_report),
            [self.superuser, self.doc_changer, self.report_changer],
        )
        self.assertResultSetEqual(
            self.policy.users_with_permission_for_instance(
                "change", self.changer_report
            ),
            [self.superuser, self.doc_changer, self.report_changer],
        )
        self.assertResultSetEqual(
            self.policy.users_with_permission_for_instance(
                "change", self.useless_report
            ),
            [self.superuser, self.doc_changer, self.report_changer],
        )
        self.assertResultSetEqual(
            self.policy.users_with_permission_for_instance(
                "change", self.anonymous_report
            ),
            [self.superuser, self.doc_changer, self.report_changer],
        )

    def test_users_with_any_permission_for_instance(self):
        self.assertResultSetEqual(
            self.policy.users_with_any_permission_for_instance(
                ["change", "delete"], self.changer_doc
            ),
            [self.superuser, self.doc_changer],
        )
        self.assertResultSetEqual(
            self.policy.users_with_any_permission_for_instance(
                ["change", "delete"], self.adder_report
            ),
            [self.superuser, self.doc_changer, self.report_changer],
        )
        self.assertResultSetEqual(
            self.policy.users_with_any_permission_for_instance(
                ["change", "delete"], self.useless_report
            ),
            [self.superuser, self.doc_changer, self.report_changer],
        )
        self.assertResultSetEqual(
            self.policy.users_with_any_permission_for_instance(
                ["delete", "frobnicate"], self.useless_report
            ),
            [self.superuser],
        )

    def test_collections_user_has_permission_for(self):
        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.superuser,
                "change",
            ),
            [self.root_collection, self.reports_collection],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.inactive_superuser,
                "change",
            ),
            [],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.doc_changer,
                "change",
            ),
            [self.root_collection, self.reports_collection],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.report_changer,
                "change",
            ),
            [self.reports_collection],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.report_adder,
                "change",
            ),
            [],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.report_adder,
                "add",
            ),
            [self.reports_collection],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.useless_user,
                "change",
            ),
            [],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.anonymous_user,
                "change",
            ),
            [],
        )

    def test_collections_user_has_any_permission_for(self):
        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.superuser, ["change", "delete"]
            ),
            [self.root_collection, self.reports_collection],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.inactive_superuser, ["change", "delete"]
            ),
            [],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.doc_changer, ["change", "delete"]
            ),
            [self.root_collection, self.reports_collection],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.report_changer, ["change", "delete"]
            ),
            [self.reports_collection],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.report_adder, ["change", "delete"]
            ),
            [],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.report_adder, ["add", "delete"]
            ),
            [self.reports_collection],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.useless_user, ["change", "delete"]
            ),
            [],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.anonymous_user, ["change", "delete"]
            ),
            [],
        )

    def test_annotate_with_permissions_with_known_access(self):
        actions = ("change", "delete", "frobnicate")
        # For these cases, the permissions are known without adding DB annotations
        cases = (
            (self.superuser, {action: True for action in actions}),
            (self.inactive_superuser, {action: False for action in actions}),
            (self.inactive_doc_changer, {action: False for action in actions}),
            (self.anonymous_user, {action: False for action in actions}),
        )
        for user, expected_permissions in cases:
            with self.assertNumQueries(1), self.subTest(user=user):
                queryset = Document.objects.all().order_by("id")
                queryset = self.policy.annotate_with_permissions(
                    queryset, user, actions
                )
                for instance in queryset:
                    self.assertEqual(
                        instance.annotated_permissions,
                        expected_permissions,
                    )

    def test_annotate_with_permissions_with_database_annotations(self):
        actions = ("change", "delete", "frobnicate")
        document_ids = (
            # root document owned by report_changer
            self.changer_doc.pk,
            # reports document owned by report_changer
            self.changer_report.pk,
            # reports document owned by report_adder
            self.adder_report.pk,
            # reports document owned by useless_user
            self.useless_report.pk,
            # reports document with no owner
            self.anonymous_report.pk,
        )

        with self.assertNumQueries(1), self.subTest(user=self.doc_changer):
            queryset = Document.objects.filter(id__in=document_ids).order_by("id")
            queryset = self.policy.annotate_with_permissions(
                queryset, self.doc_changer, actions
            )
            expected = {"change": True, "delete": True, "frobnicate": False}
            for instance in queryset:
                self.assertEqual(instance.annotated_permissions, expected)

        with self.assertNumQueries(1), self.subTest(user=self.report_changer):
            queryset = Document.objects.filter(id__in=document_ids).order_by("id")
            queryset = self.policy.annotate_with_permissions(
                queryset, self.report_changer, actions
            )
            for instance in queryset:
                expected = {"change": True, "delete": True, "frobnicate": False}
                if instance.pk == self.changer_doc.pk:
                    expected = {"change": False, "delete": False, "frobnicate": False}
                self.assertEqual(instance.annotated_permissions, expected)

        with self.assertNumQueries(1), self.subTest(user=self.report_adder):
            queryset = Document.objects.filter(id__in=document_ids).order_by("id")
            queryset = self.policy.annotate_with_permissions(
                queryset, self.report_adder, actions
            )
            expected = {"change": False, "delete": False, "frobnicate": False}
            for instance in queryset:
                self.assertEqual(instance.annotated_permissions, expected)

        with self.assertNumQueries(1), self.subTest(user=self.useless_user):
            queryset = Document.objects.filter(id__in=document_ids).order_by("id")
            queryset = self.policy.annotate_with_permissions(
                queryset, self.useless_user, actions
            )
            expected = {"change": False, "delete": False, "frobnicate": False}
            for instance in queryset:
                self.assertEqual(instance.annotated_permissions, expected)


class TestCollectionOwnershipPermissionPolicy(PermissionPolicyTestCase):
    def setUp(self):
        super().setUp()
        self.policy = CollectionOwnershipPermissionPolicy(
            Document,
            owner_field_name="uploaded_by_user",
        )

    def test_user_has_permission(self):
        self.assertUserPermissionMatrix(
            [
                (self.superuser, True, True, True, True),
                (self.inactive_superuser, False, False, False, False),
                (self.doc_changer, False, True, True, False),
                (self.inactive_doc_changer, False, False, False, False),
                (self.report_changer, False, True, True, False),
                (self.report_adder, True, True, True, False),
                (self.useless_user, False, False, False, False),
                (self.anonymous_user, False, False, False, False),
            ]
        )

    def test_user_has_any_permission(self):
        self.assertTrue(
            self.policy.user_has_any_permission(self.superuser, ["add", "change"])
        )
        self.assertFalse(
            self.policy.user_has_any_permission(
                self.inactive_superuser, ["add", "change"]
            )
        )
        self.assertTrue(
            self.policy.user_has_any_permission(self.report_changer, ["add", "delete"])
        )
        self.assertTrue(
            self.policy.user_has_any_permission(self.report_adder, ["add", "change"])
        )
        self.assertTrue(
            self.policy.user_has_any_permission(self.report_adder, ["change", "delete"])
        )
        self.assertFalse(
            self.policy.user_has_any_permission(self.anonymous_user, ["add", "change"])
        )

    def test_users_with_any_permission(self):
        users_with_add_or_change_permission = self.policy.users_with_any_permission(
            ["add", "change"]
        )

        self.assertResultSetEqual(
            users_with_add_or_change_permission,
            [
                self.superuser,
                self.doc_changer,
                self.report_changer,
                self.report_adder,
            ],
        )

    def test_users_with_permission(self):
        users_with_change_permission = self.policy.users_with_permission("change")

        self.assertResultSetEqual(
            users_with_change_permission,
            [
                self.superuser,
                self.doc_changer,
                self.report_changer,
                self.report_adder,
            ],
        )

        users_with_custom_permission = self.policy.users_with_permission("frobnicate")

        self.assertResultSetEqual(
            users_with_custom_permission,
            [
                self.superuser,
            ],
        )

    def test_user_has_permission_for_instance(self):
        # document in the root is only editable by users with permissions
        # on the root collection
        self.assertUserInstancePermissionMatrix(
            self.changer_doc,
            [
                (self.superuser, True, True, True),
                (self.inactive_superuser, False, False, False),
                (self.doc_changer, True, True, False),
                (self.inactive_doc_changer, False, False, False),
                (self.report_changer, False, False, False),
                (self.report_adder, False, False, False),
                (self.useless_user, False, False, False),
                (self.anonymous_user, False, False, False),
            ],
        )

        # document in 'reports' is editable by users with permissions
        # on 'reports' or the root collection
        self.assertUserInstancePermissionMatrix(
            self.useless_report,
            [
                (self.superuser, True, True, True),
                (self.inactive_superuser, False, False, False),
                (self.doc_changer, True, True, False),
                (self.inactive_doc_changer, False, False, False),
                (self.report_changer, True, True, False),
                (self.report_adder, False, False, False),
                (self.useless_user, False, False, False),
                (self.anonymous_user, False, False, False),
            ],
        )

        # adder_report is editable by its owner (who only has 'add' permission)
        self.assertUserInstancePermissionMatrix(
            self.adder_report,
            [
                (self.superuser, True, True, True),
                (self.inactive_superuser, False, False, False),
                (self.doc_changer, True, True, False),
                (self.inactive_doc_changer, False, False, False),
                (self.report_changer, True, True, False),
                (self.report_adder, True, True, False),
                (self.useless_user, False, False, False),
                (self.anonymous_user, False, False, False),
            ],
        )

    def test_user_has_any_permission_for_instance(self):
        self.assertTrue(
            self.policy.user_has_any_permission_for_instance(
                self.report_changer, ["change", "delete"], self.useless_report
            )
        )

        self.assertFalse(
            self.policy.user_has_any_permission_for_instance(
                self.report_changer, ["change", "delete"], self.changer_doc
            )
        )

        self.assertFalse(
            self.policy.user_has_any_permission_for_instance(
                self.report_adder, ["change", "delete"], self.changer_doc
            )
        )

        self.assertTrue(
            self.policy.user_has_any_permission_for_instance(
                self.report_adder, ["change", "delete"], self.adder_report
            )
        )

        self.assertFalse(
            self.policy.user_has_any_permission_for_instance(
                self.anonymous_user, ["change", "delete"], self.changer_doc
            )
        )

    def test_instances_user_has_permission_for(self):
        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.superuser,
                "change",
            ),
            [
                self.changer_doc,
                self.changer_report,
                self.adder_report,
                self.useless_report,
                self.anonymous_report,
            ],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.inactive_superuser,
                "change",
            ),
            [],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.doc_changer,
                "change",
            ),
            [
                self.changer_doc,
                self.changer_report,
                self.adder_report,
                self.useless_report,
                self.anonymous_report,
            ],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.report_changer,
                "change",
            ),
            [
                self.changer_report,
                self.useless_report,
                self.adder_report,
                self.anonymous_report,
            ],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.useless_user,
                "change",
            ),
            [],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.anonymous_user,
                "change",
            ),
            [],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.report_adder,
                "change",
            ),
            [
                self.adder_report,
            ],
        )

    def test_instances_user_has_any_permission_for(self):
        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.superuser, ["change", "delete"]
            ),
            [
                self.changer_doc,
                self.changer_report,
                self.adder_report,
                self.useless_report,
                self.anonymous_report,
            ],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.inactive_superuser, ["change", "delete"]
            ),
            [],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.doc_changer, ["change", "delete"]
            ),
            [
                self.changer_doc,
                self.changer_report,
                self.adder_report,
                self.useless_report,
                self.anonymous_report,
            ],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.report_changer, ["change", "delete"]
            ),
            [
                self.changer_report,
                self.adder_report,
                self.useless_report,
                self.anonymous_report,
            ],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.useless_user, ["change", "delete"]
            ),
            [],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.anonymous_user, ["change", "delete"]
            ),
            [],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.report_adder,
                ["change", "delete"],
            ),
            [
                self.adder_report,
            ],
        )

    def test_users_with_permission_for_instance(self):
        self.assertResultSetEqual(
            self.policy.users_with_permission_for_instance("change", self.changer_doc),
            [self.superuser, self.doc_changer],
        )
        self.assertResultSetEqual(
            self.policy.users_with_permission_for_instance(
                "change", self.changer_report
            ),
            [self.superuser, self.doc_changer, self.report_changer],
        )
        self.assertResultSetEqual(
            self.policy.users_with_permission_for_instance("change", self.adder_report),
            [self.superuser, self.doc_changer, self.report_changer, self.report_adder],
        )
        self.assertResultSetEqual(
            self.policy.users_with_permission_for_instance(
                "change", self.useless_report
            ),
            [self.superuser, self.doc_changer, self.report_changer],
        )
        self.assertResultSetEqual(
            self.policy.users_with_permission_for_instance(
                "change", self.anonymous_report
            ),
            [self.superuser, self.doc_changer, self.report_changer],
        )

    def test_users_with_any_permission_for_instance(self):
        self.assertResultSetEqual(
            self.policy.users_with_any_permission_for_instance(
                ["change", "delete"], self.changer_doc
            ),
            [self.superuser, self.doc_changer],
        )
        self.assertResultSetEqual(
            self.policy.users_with_any_permission_for_instance(
                ["change", "delete"], self.adder_report
            ),
            [self.superuser, self.doc_changer, self.report_changer, self.report_adder],
        )
        self.assertResultSetEqual(
            self.policy.users_with_any_permission_for_instance(
                ["change", "delete"], self.useless_report
            ),
            [self.superuser, self.doc_changer, self.report_changer],
        )
        self.assertResultSetEqual(
            self.policy.users_with_any_permission_for_instance(
                ["delete", "frobnicate"], self.useless_report
            ),
            [self.superuser, self.doc_changer, self.report_changer],
        )

    def test_collections_user_has_permission_for(self):
        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.superuser,
                "change",
            ),
            [self.root_collection, self.reports_collection],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.inactive_superuser,
                "change",
            ),
            [],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.doc_changer,
                "change",
            ),
            [self.root_collection, self.reports_collection],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.report_changer,
                "change",
            ),
            [self.reports_collection],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.report_adder,
                "change",
            ),
            [self.reports_collection],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.report_adder,
                "add",
            ),
            [self.reports_collection],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.useless_user,
                "change",
            ),
            [],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.anonymous_user,
                "change",
            ),
            [],
        )

    def test_collections_user_has_any_permission_for(self):
        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.superuser, ["change", "delete"]
            ),
            [self.root_collection, self.reports_collection],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.inactive_superuser, ["change", "delete"]
            ),
            [],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.doc_changer, ["change", "delete"]
            ),
            [self.root_collection, self.reports_collection],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.report_changer, ["change", "delete"]
            ),
            [self.reports_collection],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.report_adder, ["change", "delete"]
            ),
            [self.reports_collection],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.report_adder, ["add", "delete"]
            ),
            [self.reports_collection],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.useless_user, ["change", "delete"]
            ),
            [],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.anonymous_user, ["change", "delete"]
            ),
            [],
        )

    def test_annotate_with_permissions_with_known_access(self):
        actions = ("change", "delete", "frobnicate")
        # For these cases, the permissions are known without adding DB annotations
        cases = (
            (self.superuser, {action: True for action in actions}),
            (self.inactive_superuser, {action: False for action in actions}),
            (self.inactive_doc_changer, {action: False for action in actions}),
            (self.anonymous_user, {action: False for action in actions}),
        )
        for user, expected_permissions in cases:
            with self.assertNumQueries(1), self.subTest(user=user):
                queryset = Document.objects.all().order_by("id")
                queryset = self.policy.annotate_with_permissions(
                    queryset, user, actions
                )
                for instance in queryset:
                    self.assertEqual(
                        instance.annotated_permissions,
                        expected_permissions,
                    )

    def test_annotate_with_permissions_with_database_annotations(self):
        actions = ("change", "delete", "frobnicate")
        document_ids = (
            # root document owned by report_changer
            self.changer_doc.pk,
            # reports document owned by report_changer
            self.changer_report.pk,
            # reports document owned by report_adder
            self.adder_report.pk,
            # reports document owned by useless_user
            self.useless_report.pk,
            # reports document with no owner
            self.anonymous_report.pk,
        )

        with self.assertNumQueries(1), self.subTest(user=self.doc_changer):
            queryset = Document.objects.filter(id__in=document_ids).order_by("id")
            queryset = self.policy.annotate_with_permissions(
                queryset, self.doc_changer, actions
            )
            expected = {"change": True, "delete": True, "frobnicate": False}
            for instance in queryset:
                self.assertEqual(instance.annotated_permissions, expected)

        with self.assertNumQueries(1), self.subTest(user=self.report_changer):
            queryset = Document.objects.filter(id__in=document_ids).order_by("id")
            queryset = self.policy.annotate_with_permissions(
                queryset, self.report_changer, actions
            )
            for instance in queryset:
                expected = {"change": True, "delete": True, "frobnicate": False}
                # even though changer_report is owned by report_changer, they can't
                # change or delete it because it's in the root collection and they
                # don't have add permission on the root collection
                if instance.pk == self.changer_doc.pk:
                    expected = {"change": False, "delete": False, "frobnicate": False}
                self.assertEqual(instance.annotated_permissions, expected)

        with self.assertNumQueries(1), self.subTest(user=self.report_adder):
            queryset = Document.objects.filter(id__in=document_ids).order_by("id")
            queryset = self.policy.annotate_with_permissions(
                queryset, self.report_adder, actions
            )
            for instance in queryset:
                expected = {"change": False, "delete": False, "frobnicate": False}
                # adder_report is owned by report_adder, so they can change and delete
                if instance.pk == self.adder_report.pk:
                    expected = {"change": True, "delete": True, "frobnicate": False}
                self.assertEqual(instance.annotated_permissions, expected)

        with self.assertNumQueries(1), self.subTest(user=self.useless_user):
            queryset = Document.objects.filter(id__in=document_ids).order_by("id")
            queryset = self.policy.annotate_with_permissions(
                queryset, self.useless_user, actions
            )
            expected = {"change": False, "delete": False, "frobnicate": False}
            for instance in queryset:
                self.assertEqual(instance.annotated_permissions, expected)


class TestCollectionManagementPermission(
    PermissionPolicyTestUtils, WagtailTestUtils, TestCase
):
    def setUp(self):
        self.policy = CollectionMangementPermissionPolicy(Collection)

        # Permissions
        collection_content_type = ContentType.objects.get_for_model(Collection)
        add_collection_permission = Permission.objects.get(
            content_type=collection_content_type, codename="add_collection"
        )
        change_collection_permission = Permission.objects.get(
            content_type=collection_content_type, codename="change_collection"
        )
        delete_collection_permission = Permission.objects.get(
            content_type=collection_content_type, codename="delete_collection"
        )

        # Collections
        self.root_collection = Collection.get_first_root_node()
        self.reports_collection = self.root_collection.add_child(name="Reports")
        self.reports_2020_collection = self.reports_collection.add_child(
            name="Reports 2020"
        )

        # Users with their groups/permissions
        self.superuser = self.create_superuser(
            "superuser", "superuser@example.com", "password"
        )
        self.inactive_superuser = self.create_superuser(
            "inactivesuperuser", "inactivesuperuser@example.com", "password"
        )
        self.inactive_superuser.is_active = False
        self.inactive_superuser.save()

        # a user with change collection permission on reports via the report_changers group
        report_changers_group = Group.objects.create(name="Report changers")
        GroupCollectionPermission.objects.create(
            group=report_changers_group,
            collection=self.reports_collection,
            permission=change_collection_permission,
        )

        self.report_changer = self.create_user(
            "reportchanger", "reportchanger@example.com", "password"
        )
        self.report_changer.groups.add(report_changers_group)

        # a user with add collection permission on reports via the report_adders group
        report_adders_group = Group.objects.create(name="Report adders")
        GroupCollectionPermission.objects.create(
            group=report_adders_group,
            collection=self.reports_collection,
            permission=add_collection_permission,
        )
        self.report_adder = self.create_user(
            "reportadder", "reportadder@example.com", "password"
        )
        self.report_adder.groups.add(report_adders_group)

        # a user with delete collection permission on reports via the report_deleters group
        report_deleters_group = Group.objects.create(name="Report deleters")
        GroupCollectionPermission.objects.create(
            group=report_deleters_group,
            collection=self.reports_collection,
            permission=delete_collection_permission,
        )
        self.report_deleter = self.create_user(
            "reportdeleter", "reportdeleter@example.com", "password"
        )
        self.report_deleter.groups.add(report_deleters_group)

        # a user with no permissions
        self.useless_user = self.create_user(
            "uselessuser", "uselessuser@example.com", "password"
        )

        self.anonymous_user = AnonymousUser()

    def test_user_has_permission(self):
        self.assertUserPermissionMatrix(
            [
                (self.superuser, True, True, True, True),
                (self.inactive_superuser, False, False, False, False),
                (self.report_changer, False, True, False, False),
                (self.report_adder, True, False, False, False),
                (self.report_deleter, False, False, True, False),
                (self.useless_user, False, False, False, False),
                (self.anonymous_user, False, False, False, False),
            ]
        )

    def test_user_has_any_permission(self):
        users_with_permissions = [
            self.superuser,
            self.report_changer,
            self.report_adder,
            self.report_deleter,
        ]
        users_without_permissions = [
            self.inactive_superuser,
            self.useless_user,
            self.anonymous_user,
        ]

        for user in users_with_permissions:
            self.assertTrue(
                self.policy.user_has_any_permission(user, ["add", "change", "delete"])
            )
        for user in users_without_permissions:
            self.assertFalse(
                self.policy.user_has_any_permission(user, ["add", "change", "delete"])
            )

    def test_users_with_any_permission(self):
        users_with_add_or_change_or_delete_permission = (
            self.policy.users_with_any_permission(["add", "change", "delete"])
        )

        self.assertResultSetEqual(
            users_with_add_or_change_or_delete_permission,
            [
                self.superuser,
                self.report_changer,
                self.report_adder,
                self.report_deleter,
            ],
        )

    def test_users_with_permission(self):
        users_with_change_permission = self.policy.users_with_permission("change")

        self.assertResultSetEqual(
            users_with_change_permission,
            [
                self.superuser,
                self.report_changer,
            ],
        )

        users_with_custom_permission = self.policy.users_with_permission("frobnicate")

        self.assertResultSetEqual(
            users_with_custom_permission,
            [
                self.superuser,
            ],
        )

    def test_only_superuser_has_permission_for_root_collection(self):
        self.assertUserInstancePermissionMatrix(
            self.root_collection,
            [
                (self.superuser, True, True, True),
                (self.inactive_superuser, False, False, False),
                (self.report_changer, False, False, False),
                (self.report_adder, False, False, False),
                (self.report_deleter, False, False, False),
                (self.useless_user, False, False, False),
                (self.anonymous_user, False, False, False),
            ],
        )

    def test_user_has_permission_for_instance(self):
        # Reports collection is editable - as are its children
        self.assertUserInstancePermissionMatrix(
            self.reports_collection,
            [
                (self.superuser, True, True, True),
                (self.inactive_superuser, False, False, False),
                (self.report_changer, True, False, False),
                (self.report_deleter, False, True, False),
                (self.useless_user, False, False, False),
                (self.anonymous_user, False, False, False),
            ],
        )

        self.assertUserInstancePermissionMatrix(
            self.reports_2020_collection,
            [
                (self.superuser, True, True, True),
                (self.inactive_superuser, False, False, False),
                (self.report_changer, True, False, False),
                (self.report_deleter, False, True, False),
                (self.useless_user, False, False, False),
                (self.anonymous_user, False, False, False),
            ],
        )

    def test_user_has_any_permission_for_instance(self):
        users_with_permissions = [
            self.superuser,
            self.report_changer,
            self.report_adder,
            self.report_deleter,
        ]

        for user in users_with_permissions:
            self.assertTrue(
                self.policy.user_has_any_permission_for_instance(
                    user, ["add", "change", "delete"], self.reports_collection
                )
            )

        self.assertFalse(
            self.policy.user_has_any_permission_for_instance(
                self.report_adder, ["add", "change", "delete"], self.root_collection
            )
        )

        self.assertTrue(
            self.policy.user_has_any_permission_for_instance(
                self.superuser, ["add", "change", "delete"], self.root_collection
            )
        )

    def test_instances_user_has_permission_for(self):
        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(self.superuser, "change"),
            [
                self.root_collection,
                self.reports_collection,
                self.reports_2020_collection,
            ],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(self.report_adder, "add"),
            [self.reports_collection, self.reports_2020_collection],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(self.report_adder, "change"),
            [],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.inactive_superuser, "change"
            ),
            [],
        )

    def test_instances_user_has_any_permission_for(self):
        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.superuser, ["add", "change"]
            ),
            [
                self.root_collection,
                self.reports_collection,
                self.reports_2020_collection,
            ],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.report_adder, ["add", "change"]
            ),
            [self.reports_collection, self.reports_2020_collection],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.inactive_superuser, ["add", "change"]
            ),
            [],
        )

    def test_users_with_permission_for_instance(self):
        self.assertResultSetEqual(
            self.policy.users_with_permission_for_instance(
                "change", self.root_collection
            ),
            [self.superuser],
        )
        self.assertResultSetEqual(
            self.policy.users_with_permission_for_instance(
                "change", self.reports_collection
            ),
            [self.superuser, self.report_changer],
        )
        self.assertResultSetEqual(
            self.policy.users_with_permission_for_instance(
                "add", self.reports_collection
            ),
            [self.superuser, self.report_adder],
        )

    def test_users_with_any_permission_for_instance(self):
        self.assertResultSetEqual(
            self.policy.users_with_any_permission_for_instance(
                ["add", "change", "delete"], self.reports_2020_collection
            ),
            [
                self.superuser,
                self.report_adder,
                self.report_changer,
                self.report_deleter,
            ],
        )

    def test_collections_user_has_permission_for(self):
        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(self.superuser, "change"),
            [
                self.root_collection,
                self.reports_collection,
                self.reports_2020_collection,
            ],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(self.report_adder, "add"),
            [self.reports_collection, self.reports_2020_collection],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.report_adder, "change"
            ),
            [],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.inactive_superuser, "change"
            ),
            [],
        )

    def test_collections_user_has_any_permission_for(self):
        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.superuser, ["add", "change"]
            ),
            [
                self.root_collection,
                self.reports_collection,
                self.reports_2020_collection,
            ],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.report_adder, ["add", "change"]
            ),
            [self.reports_collection, self.reports_2020_collection],
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.inactive_superuser, ["add", "change"]
            ),
            [],
        )

    def test_annotate_with_permissions_with_known_access(self):
        actions = ("add", "change", "delete", "frobnicate")
        # For these cases, the permissions are known without adding DB annotations
        cases = (
            (self.superuser, {action: True for action in actions}),
            (self.inactive_superuser, {action: False for action in actions}),
            (self.anonymous_user, {action: False for action in actions}),
        )
        for user, expected_permissions in cases:
            with self.assertNumQueries(1), self.subTest(user=user):
                queryset = Collection.objects.all().order_by("id")
                queryset = self.policy.annotate_with_permissions(
                    queryset, user, actions
                )
                for instance in queryset:
                    self.assertEqual(
                        instance.annotated_permissions,
                        expected_permissions,
                    )

    def test_annotate_with_permissions_with_database_annotations(self):
        actions = ("add", "change", "delete", "frobnicate")
        collection_ids = (
            self.root_collection.pk,
            self.reports_collection.pk,
            self.reports_2020_collection.pk,
        )

        with self.assertNumQueries(1), self.subTest(user=self.report_changer):
            queryset = Collection.objects.filter(id__in=collection_ids).order_by("id")
            queryset = self.policy.annotate_with_permissions(
                queryset, self.report_changer, actions
            )
            expected = (
                {"add": False, "change": False, "delete": False, "frobnicate": False},
                {"add": False, "change": True, "delete": False, "frobnicate": False},
                {"add": False, "change": True, "delete": False, "frobnicate": False},
            )

            for i, instance in enumerate(list(queryset)):
                self.assertEqual(instance.annotated_permissions, expected[i])

        with self.assertNumQueries(1), self.subTest(user=self.report_adder):
            queryset = Collection.objects.filter(id__in=collection_ids).order_by("id")
            queryset = self.policy.annotate_with_permissions(
                queryset, self.report_adder, actions
            )
            expected = (
                {"add": False, "change": False, "delete": False, "frobnicate": False},
                {"add": True, "change": False, "delete": False, "frobnicate": False},
                {"add": True, "change": False, "delete": False, "frobnicate": False},
            )

            for i, instance in enumerate(list(queryset)):
                self.assertEqual(instance.annotated_permissions, expected[i])

        with self.assertNumQueries(1), self.subTest(user=self.report_deleter):
            queryset = Collection.objects.filter(id__in=collection_ids).order_by("id")
            queryset = self.policy.annotate_with_permissions(
                queryset, self.report_deleter, actions
            )
            expected = (
                {"add": False, "change": False, "delete": False, "frobnicate": False},
                {"add": False, "change": False, "delete": True, "frobnicate": False},
                {"add": False, "change": False, "delete": True, "frobnicate": False},
            )

            for i, instance in enumerate(list(queryset)):
                self.assertEqual(instance.annotated_permissions, expected[i])

        with self.assertNumQueries(1), self.subTest(user=self.useless_user):
            queryset = Collection.objects.filter(id__in=collection_ids).order_by("id")
            queryset = self.policy.annotate_with_permissions(
                queryset, self.useless_user, actions
            )
            expected = {action: False for action in actions}
            for instance in queryset:
                self.assertEqual(instance.annotated_permissions, expected)
