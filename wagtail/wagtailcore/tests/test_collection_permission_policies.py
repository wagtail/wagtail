from __future__ import absolute_import, unicode_literals

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from wagtail.wagtailcore.models import Collection, GroupCollectionPermission
from wagtail.wagtailcore.permission_policies.collections import (
    CollectionOwnershipPermissionPolicy, CollectionPermissionPolicy)
from wagtail.wagtailcore.tests.test_permission_policies import PermissionPolicyTestUtils
from wagtail.wagtaildocs.models import Document


class PermissionPolicyTestCase(PermissionPolicyTestUtils, TestCase):
    def setUp(self):
        # Permissions
        document_content_type = ContentType.objects.get_for_model(Document)
        add_doc_permission = Permission.objects.get(
            content_type=document_content_type, codename='add_document'
        )
        change_doc_permission = Permission.objects.get(
            content_type=document_content_type, codename='change_document'
        )

        # Collections
        self.root_collection = Collection.get_first_root_node()
        self.reports_collection = self.root_collection.add_child(name="Reports")

        # Groups
        doc_changers_group = Group.objects.create(name="Document changers")
        GroupCollectionPermission.objects.create(
            group=doc_changers_group,
            collection=self.root_collection,
            permission=change_doc_permission
        )

        report_changers_group = Group.objects.create(name="Report changers")
        GroupCollectionPermission.objects.create(
            group=report_changers_group,
            collection=self.reports_collection,
            permission=change_doc_permission
        )

        report_adders_group = Group.objects.create(name="Report adders")
        GroupCollectionPermission.objects.create(
            group=report_adders_group,
            collection=self.reports_collection,
            permission=add_doc_permission
        )

        # Users
        User = get_user_model()

        self.superuser = User.objects.create_superuser(
            'superuser', 'superuser@example.com', 'password'
        )
        self.inactive_superuser = User.objects.create_superuser(
            'inactivesuperuser', 'inactivesuperuser@example.com', 'password', is_active=False
        )

        # a user with change_document permission through the 'Document changers' group
        self.doc_changer = User.objects.create_user(
            'docchanger', 'docchanger@example.com', 'password'
        )
        self.doc_changer.groups.add(doc_changers_group)

        # a user that has change_document permission, but is inactive
        self.inactive_doc_changer = User.objects.create_user(
            'inactivedocchanger', 'inactivedocchanger@example.com', 'password', is_active=False
        )
        self.inactive_doc_changer.groups.add(doc_changers_group)

        # a user with change_document permission on reports via the report_changers group
        self.report_changer = User.objects.create_user(
            'reportchanger', 'reportchanger@example.com', 'password'
        )
        self.report_changer.groups.add(report_changers_group)

        # a user with add_document permission on reports via the report_adders group
        self.report_adder = User.objects.create_user(
            'reportadder', 'reportadder@example.com', 'password'
        )
        self.report_adder.groups.add(report_adders_group)

        # a user with no permissions
        self.useless_user = User.objects.create_user(
            'uselessuser', 'uselessuser@example.com', 'password'
        )

        self.anonymous_user = AnonymousUser()

        # Documents

        # a document in the root owned by 'reportchanger'
        self.changer_doc = Document.objects.create(
            title="reportchanger's document", collection=self.root_collection,
            uploaded_by_user=self.report_changer
        )

        # a document in reports owned by 'reportchanger'
        self.changer_report = Document.objects.create(
            title="reportchanger's report", collection=self.reports_collection,
            uploaded_by_user=self.report_changer
        )

        # a document in reports owned by 'reportadder'
        self.adder_report = Document.objects.create(
            title="reportadder's report", collection=self.reports_collection,
            uploaded_by_user=self.report_adder
        )

        # a document in reports owned by 'uselessuser'
        self.useless_report = Document.objects.create(
            title="uselessuser's report", collection=self.reports_collection,
            uploaded_by_user=self.useless_user
        )

        # a document with no owner
        self.anonymous_report = Document.objects.create(
            title="anonymous report", collection=self.reports_collection
        )


class TestCollectionPermissionPolicy(PermissionPolicyTestCase):
    def setUp(self):
        super(TestCollectionPermissionPolicy, self).setUp()
        self.policy = CollectionPermissionPolicy(Document)

    def test_user_has_permission(self):
        self.assertUserPermissionMatrix([
            (self.superuser, True, True, True, True),
            (self.inactive_superuser, False, False, False, False),
            (self.doc_changer, False, True, False, False),
            (self.inactive_doc_changer, False, False, False, False),
            (self.report_changer, False, True, False, False),
            (self.report_adder, True, False, False, False),
            (self.useless_user, False, False, False, False),
            (self.anonymous_user, False, False, False, False),
        ])

    def test_user_has_any_permission(self):
        self.assertTrue(
            self.policy.user_has_any_permission(self.superuser, ['add', 'change'])
        )
        self.assertFalse(
            self.policy.user_has_any_permission(self.inactive_superuser, ['add', 'change'])
        )
        self.assertTrue(
            self.policy.user_has_any_permission(self.report_changer, ['add', 'change'])
        )
        self.assertTrue(
            self.policy.user_has_any_permission(self.report_adder, ['add', 'change'])
        )
        self.assertFalse(
            self.policy.user_has_any_permission(self.anonymous_user, ['add', 'change'])
        )

    def test_users_with_any_permission(self):
        users_with_add_or_change_permission = self.policy.users_with_any_permission(
            ['add', 'change']
        )

        self.assertResultSetEqual(users_with_add_or_change_permission, [
            self.superuser,
            self.doc_changer,
            self.report_changer,
            self.report_adder,
        ])

    def test_users_with_permission(self):
        users_with_change_permission = self.policy.users_with_permission('change')

        self.assertResultSetEqual(users_with_change_permission, [
            self.superuser,
            self.doc_changer,
            self.report_changer,
        ])

        users_with_custom_permission = self.policy.users_with_permission('frobnicate')

        self.assertResultSetEqual(users_with_custom_permission, [
            self.superuser,
        ])

    def test_user_has_permission_for_instance(self):
        # document in the root is only editable by users with permissions
        # on the root collection
        self.assertUserInstancePermissionMatrix(self.changer_doc, [
            (self.superuser, True, True, True),
            (self.inactive_superuser, False, False, False),
            (self.doc_changer, True, False, False),
            (self.inactive_doc_changer, False, False, False),
            (self.report_changer, False, False, False),
            (self.report_adder, False, False, False),
            (self.useless_user, False, False, False),
            (self.anonymous_user, False, False, False),
        ])

        # document in 'reports' is editable by users with permissions
        # on 'reports' or the root collection
        self.assertUserInstancePermissionMatrix(self.useless_report, [
            (self.superuser, True, True, True),
            (self.inactive_superuser, False, False, False),
            (self.doc_changer, True, False, False),
            (self.inactive_doc_changer, False, False, False),
            (self.report_changer, True, False, False),
            (self.report_adder, False, False, False),
            (self.useless_user, False, False, False),
            (self.anonymous_user, False, False, False),
        ])

    def test_user_has_any_permission_for_instance(self):
        self.assertTrue(
            self.policy.user_has_any_permission_for_instance(
                self.report_changer, ['change', 'delete'], self.useless_report
            )
        )

        self.assertFalse(
            self.policy.user_has_any_permission_for_instance(
                self.report_changer, ['change', 'delete'], self.changer_doc
            )
        )

        self.assertFalse(
            self.policy.user_has_any_permission_for_instance(
                self.anonymous_user, ['change', 'delete'], self.changer_doc
            )
        )

    def test_instances_user_has_permission_for(self):
        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.superuser, 'change',
            ),
            [
                self.changer_doc, self.changer_report, self.adder_report,
                self.useless_report, self.anonymous_report
            ]
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.inactive_superuser, 'change',
            ),
            []
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.doc_changer, 'change',
            ),
            [
                self.changer_doc, self.changer_report, self.adder_report,
                self.useless_report, self.anonymous_report
            ]
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.report_changer, 'change',
            ),
            [
                self.changer_report, self.useless_report, self.adder_report,
                self.anonymous_report
            ]
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.useless_user, 'change',
            ),
            []
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.anonymous_user, 'change',
            ),
            []
        )

    def test_instances_user_has_any_permission_for(self):
        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.superuser, ['change', 'delete']
            ),
            [
                self.changer_doc, self.changer_report, self.adder_report,
                self.useless_report, self.anonymous_report
            ]
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.inactive_superuser, ['change', 'delete']
            ),
            []
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.doc_changer, ['change', 'delete']
            ),
            [
                self.changer_doc, self.changer_report, self.adder_report,
                self.useless_report, self.anonymous_report
            ]
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.report_changer, ['change', 'delete']
            ),
            [
                self.changer_report, self.adder_report,
                self.useless_report, self.anonymous_report
            ]
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.useless_user, ['change', 'delete']
            ),
            []
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.anonymous_user, ['change', 'delete']
            ),
            []
        )

    def test_users_with_permission_for_instance(self):
        self.assertResultSetEqual(
            self.policy.users_with_permission_for_instance('change', self.changer_doc),
            [
                self.superuser, self.doc_changer
            ]
        )
        self.assertResultSetEqual(
            self.policy.users_with_permission_for_instance('change', self.adder_report),
            [
                self.superuser, self.doc_changer, self.report_changer
            ]
        )
        self.assertResultSetEqual(
            self.policy.users_with_permission_for_instance('change', self.changer_report),
            [
                self.superuser, self.doc_changer, self.report_changer
            ]
        )
        self.assertResultSetEqual(
            self.policy.users_with_permission_for_instance('change', self.useless_report),
            [
                self.superuser, self.doc_changer, self.report_changer
            ]
        )
        self.assertResultSetEqual(
            self.policy.users_with_permission_for_instance('change', self.anonymous_report),
            [
                self.superuser, self.doc_changer, self.report_changer
            ]
        )

    def test_users_with_any_permission_for_instance(self):
        self.assertResultSetEqual(
            self.policy.users_with_any_permission_for_instance(
                ['change', 'delete'], self.changer_doc
            ),
            [
                self.superuser, self.doc_changer
            ]
        )
        self.assertResultSetEqual(
            self.policy.users_with_any_permission_for_instance(
                ['change', 'delete'], self.adder_report
            ),
            [
                self.superuser, self.doc_changer, self.report_changer
            ]
        )
        self.assertResultSetEqual(
            self.policy.users_with_any_permission_for_instance(
                ['change', 'delete'], self.useless_report
            ),
            [
                self.superuser, self.doc_changer, self.report_changer
            ]
        )
        self.assertResultSetEqual(
            self.policy.users_with_any_permission_for_instance(
                ['delete', 'frobnicate'], self.useless_report
            ),
            [self.superuser]
        )

    def test_collections_user_has_permission_for(self):
        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.superuser, 'change',
            ),
            [self.root_collection, self.reports_collection]
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.inactive_superuser, 'change',
            ),
            []
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.doc_changer, 'change',
            ),
            [self.root_collection, self.reports_collection]
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.report_changer, 'change',
            ),
            [self.reports_collection]
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.report_adder, 'change',
            ),
            []
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.report_adder, 'add',
            ),
            [self.reports_collection]
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.useless_user, 'change',
            ),
            []
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.anonymous_user, 'change',
            ),
            []
        )

    def test_collections_user_has_any_permission_for(self):
        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.superuser, ['change', 'delete']
            ),
            [self.root_collection, self.reports_collection]
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.inactive_superuser, ['change', 'delete']
            ),
            []
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.doc_changer, ['change', 'delete']
            ),
            [self.root_collection, self.reports_collection]
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.report_changer, ['change', 'delete']
            ),
            [self.reports_collection]
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.report_adder, ['change', 'delete']
            ),
            []
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.report_adder, ['add', 'delete']
            ),
            [self.reports_collection]
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.useless_user, ['change', 'delete']
            ),
            []
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.anonymous_user, ['change', 'delete']
            ),
            []
        )


class TestCollectionOwnershipPermissionPolicy(PermissionPolicyTestCase):
    def setUp(self):
        super(TestCollectionOwnershipPermissionPolicy, self).setUp()
        self.policy = CollectionOwnershipPermissionPolicy(
            Document, owner_field_name='uploaded_by_user',
        )

    def test_user_has_permission(self):
        self.assertUserPermissionMatrix([
            (self.superuser, True, True, True, True),
            (self.inactive_superuser, False, False, False, False),
            (self.doc_changer, False, True, True, False),
            (self.inactive_doc_changer, False, False, False, False),
            (self.report_changer, False, True, True, False),
            (self.report_adder, True, True, True, False),
            (self.useless_user, False, False, False, False),
            (self.anonymous_user, False, False, False, False),
        ])

    def test_user_has_any_permission(self):
        self.assertTrue(
            self.policy.user_has_any_permission(self.superuser, ['add', 'change'])
        )
        self.assertFalse(
            self.policy.user_has_any_permission(self.inactive_superuser, ['add', 'change'])
        )
        self.assertTrue(
            self.policy.user_has_any_permission(self.report_changer, ['add', 'delete'])
        )
        self.assertTrue(
            self.policy.user_has_any_permission(self.report_adder, ['add', 'change'])
        )
        self.assertTrue(
            self.policy.user_has_any_permission(self.report_adder, ['change', 'delete'])
        )
        self.assertFalse(
            self.policy.user_has_any_permission(self.anonymous_user, ['add', 'change'])
        )

    def test_users_with_any_permission(self):
        users_with_add_or_change_permission = self.policy.users_with_any_permission(
            ['add', 'change']
        )

        self.assertResultSetEqual(users_with_add_or_change_permission, [
            self.superuser,
            self.doc_changer,
            self.report_changer,
            self.report_adder,
        ])

    def test_users_with_permission(self):
        users_with_change_permission = self.policy.users_with_permission('change')

        self.assertResultSetEqual(users_with_change_permission, [
            self.superuser,
            self.doc_changer,
            self.report_changer,
            self.report_adder,
        ])

        users_with_custom_permission = self.policy.users_with_permission('frobnicate')

        self.assertResultSetEqual(users_with_custom_permission, [
            self.superuser,
        ])

    def test_user_has_permission_for_instance(self):
        # document in the root is only editable by users with permissions
        # on the root collection
        self.assertUserInstancePermissionMatrix(self.changer_doc, [
            (self.superuser, True, True, True),
            (self.inactive_superuser, False, False, False),
            (self.doc_changer, True, True, False),
            (self.inactive_doc_changer, False, False, False),
            (self.report_changer, False, False, False),
            (self.report_adder, False, False, False),
            (self.useless_user, False, False, False),
            (self.anonymous_user, False, False, False),
        ])

        # document in 'reports' is editable by users with permissions
        # on 'reports' or the root collection
        self.assertUserInstancePermissionMatrix(self.useless_report, [
            (self.superuser, True, True, True),
            (self.inactive_superuser, False, False, False),
            (self.doc_changer, True, True, False),
            (self.inactive_doc_changer, False, False, False),
            (self.report_changer, True, True, False),
            (self.report_adder, False, False, False),
            (self.useless_user, False, False, False),
            (self.anonymous_user, False, False, False),
        ])

        # adder_report is editable by its owner (who only has 'add' permission)
        self.assertUserInstancePermissionMatrix(self.adder_report, [
            (self.superuser, True, True, True),
            (self.inactive_superuser, False, False, False),
            (self.doc_changer, True, True, False),
            (self.inactive_doc_changer, False, False, False),
            (self.report_changer, True, True, False),
            (self.report_adder, True, True, False),
            (self.useless_user, False, False, False),
            (self.anonymous_user, False, False, False),
        ])

    def test_user_has_any_permission_for_instance(self):
        self.assertTrue(
            self.policy.user_has_any_permission_for_instance(
                self.report_changer, ['change', 'delete'], self.useless_report
            )
        )

        self.assertFalse(
            self.policy.user_has_any_permission_for_instance(
                self.report_changer, ['change', 'delete'], self.changer_doc
            )
        )

        self.assertFalse(
            self.policy.user_has_any_permission_for_instance(
                self.report_adder, ['change', 'delete'], self.changer_doc
            )
        )

        self.assertTrue(
            self.policy.user_has_any_permission_for_instance(
                self.report_adder, ['change', 'delete'], self.adder_report
            )
        )

        self.assertFalse(
            self.policy.user_has_any_permission_for_instance(
                self.anonymous_user, ['change', 'delete'], self.changer_doc
            )
        )

    def test_instances_user_has_permission_for(self):
        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.superuser, 'change',
            ),
            [
                self.changer_doc, self.changer_report, self.adder_report,
                self.useless_report, self.anonymous_report
            ]
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.inactive_superuser, 'change',
            ),
            []
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.doc_changer, 'change',
            ),
            [
                self.changer_doc, self.changer_report, self.adder_report,
                self.useless_report, self.anonymous_report
            ]
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.report_changer, 'change',
            ),
            [
                self.changer_report, self.useless_report, self.adder_report,
                self.anonymous_report
            ]
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.useless_user, 'change',
            ),
            []
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.anonymous_user, 'change',
            ),
            []
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.report_adder, 'change',
            ),
            [
                self.adder_report,
            ]
        )

    def test_instances_user_has_any_permission_for(self):
        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.superuser, ['change', 'delete']
            ),
            [
                self.changer_doc, self.changer_report, self.adder_report,
                self.useless_report, self.anonymous_report
            ]
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.inactive_superuser, ['change', 'delete']
            ),
            []
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.doc_changer, ['change', 'delete']
            ),
            [
                self.changer_doc, self.changer_report, self.adder_report,
                self.useless_report, self.anonymous_report
            ]
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.report_changer, ['change', 'delete']
            ),
            [
                self.changer_report, self.adder_report,
                self.useless_report, self.anonymous_report
            ]
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.useless_user, ['change', 'delete']
            ),
            []
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.anonymous_user, ['change', 'delete']
            ),
            []
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.report_adder, ['change', 'delete'],
            ),
            [
                self.adder_report,
            ]
        )

    def test_users_with_permission_for_instance(self):
        self.assertResultSetEqual(
            self.policy.users_with_permission_for_instance('change', self.changer_doc),
            [
                self.superuser, self.doc_changer
            ]
        )
        self.assertResultSetEqual(
            self.policy.users_with_permission_for_instance('change', self.changer_report),
            [
                self.superuser, self.doc_changer, self.report_changer
            ]
        )
        self.assertResultSetEqual(
            self.policy.users_with_permission_for_instance('change', self.adder_report),
            [
                self.superuser, self.doc_changer, self.report_changer, self.report_adder
            ]
        )
        self.assertResultSetEqual(
            self.policy.users_with_permission_for_instance('change', self.useless_report),
            [
                self.superuser, self.doc_changer, self.report_changer
            ]
        )
        self.assertResultSetEqual(
            self.policy.users_with_permission_for_instance('change', self.anonymous_report),
            [
                self.superuser, self.doc_changer, self.report_changer
            ]
        )

    def test_users_with_any_permission_for_instance(self):
        self.assertResultSetEqual(
            self.policy.users_with_any_permission_for_instance(
                ['change', 'delete'], self.changer_doc
            ),
            [
                self.superuser, self.doc_changer
            ]
        )
        self.assertResultSetEqual(
            self.policy.users_with_any_permission_for_instance(
                ['change', 'delete'], self.adder_report
            ),
            [
                self.superuser, self.doc_changer, self.report_changer, self.report_adder
            ]
        )
        self.assertResultSetEqual(
            self.policy.users_with_any_permission_for_instance(
                ['change', 'delete'], self.useless_report
            ),
            [
                self.superuser, self.doc_changer, self.report_changer
            ]
        )
        self.assertResultSetEqual(
            self.policy.users_with_any_permission_for_instance(
                ['delete', 'frobnicate'], self.useless_report
            ),
            [self.superuser, self.doc_changer, self.report_changer]
        )

    def test_collections_user_has_permission_for(self):
        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.superuser, 'change',
            ),
            [self.root_collection, self.reports_collection]
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.inactive_superuser, 'change',
            ),
            []
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.doc_changer, 'change',
            ),
            [self.root_collection, self.reports_collection]
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.report_changer, 'change',
            ),
            [self.reports_collection]
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.report_adder, 'change',
            ),
            [self.reports_collection]
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.report_adder, 'add',
            ),
            [self.reports_collection]
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.useless_user, 'change',
            ),
            []
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_permission_for(
                self.anonymous_user, 'change',
            ),
            []
        )

    def test_collections_user_has_any_permission_for(self):
        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.superuser, ['change', 'delete']
            ),
            [self.root_collection, self.reports_collection]
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.inactive_superuser, ['change', 'delete']
            ),
            []
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.doc_changer, ['change', 'delete']
            ),
            [self.root_collection, self.reports_collection]
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.report_changer, ['change', 'delete']
            ),
            [self.reports_collection]
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.report_adder, ['change', 'delete']
            ),
            [self.reports_collection]
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.report_adder, ['add', 'delete']
            ),
            [self.reports_collection]
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.useless_user, ['change', 'delete']
            ),
            []
        )

        self.assertResultSetEqual(
            self.policy.collections_user_has_any_permission_for(
                self.anonymous_user, ['change', 'delete']
            ),
            []
        )
