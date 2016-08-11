from __future__ import absolute_import, unicode_literals

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from wagtail.wagtailcore.permission_policies import (
    AuthenticationOnlyPermissionPolicy, BlanketPermissionPolicy, ModelPermissionPolicy,
    OwnershipPermissionPolicy)
from wagtail.wagtailimages.models import Image
from wagtail.wagtailimages.tests.utils import get_test_image_file


class PermissionPolicyTestUtils(object):
    def assertResultSetEqual(self, actual, expected):
        self.assertEqual(set(actual), set(expected))

    def assertUserPermissionMatrix(self, test_cases):
        """
        Given a list of (user, can_add, can_change, can_delete, can_frobnicate) tuples
        (where 'frobnicate' is an unrecognised action not defined on the model),
        confirm that all tuples correctly represent permissions for that user as
        returned by user_has_permission
        """
        actions = ['add', 'change', 'delete', 'frobnicate']
        for test_case in test_cases:
            user = test_case[0]
            expected_results = zip(actions, test_case[1:])

            for (action, expected_result) in expected_results:
                if expected_result:
                    self.assertTrue(
                        self.policy.user_has_permission(user, action),
                        "User %s should be able to %s, but can't" % (user, action)
                    )
                else:
                    self.assertFalse(
                        self.policy.user_has_permission(user, action),
                        "User %s should not be able to %s, but can" % (user, action)
                    )

    def assertUserInstancePermissionMatrix(self, instance, test_cases):
        """
        Given a list of (user, can_change, can_delete, can_frobnicate) tuples
        (where 'frobnicate' is an unrecognised action not defined on the model),
        confirm that all tuples correctly represent permissions for that user on
        the given instance, as returned by user_has_permission_for_instance
        """
        actions = ['change', 'delete', 'frobnicate']
        for test_case in test_cases:
            user = test_case[0]
            expected_results = zip(actions, test_case[1:])

            for (action, expected_result) in expected_results:
                if expected_result:
                    self.assertTrue(
                        self.policy.user_has_permission_for_instance(user, action, instance),
                        "User %s should be able to %s instance %s, but can't" % (
                            user, action, instance
                        )
                    )
                else:
                    self.assertFalse(
                        self.policy.user_has_permission_for_instance(user, action, instance),
                        "User %s should not be able to %s instance %s, but can" % (
                            user, action, instance
                        )
                    )


class PermissionPolicyTestCase(PermissionPolicyTestUtils, TestCase):
    def setUp(self):
        # Permissions
        image_content_type = ContentType.objects.get_for_model(Image)
        add_image_permission = Permission.objects.get(
            content_type=image_content_type, codename='add_image'
        )
        change_image_permission = Permission.objects.get(
            content_type=image_content_type, codename='change_image'
        )
        delete_image_permission = Permission.objects.get(
            content_type=image_content_type, codename='delete_image'
        )

        # Groups
        image_adders_group = Group.objects.create(name="Image adders")
        image_adders_group.permissions.add(add_image_permission)

        image_changers_group = Group.objects.create(name="Image changers")
        image_changers_group.permissions.add(change_image_permission)

        # Users
        User = get_user_model()

        self.superuser = User.objects.create_superuser(
            'superuser', 'superuser@example.com', 'password'
        )
        self.inactive_superuser = User.objects.create_superuser(
            'inactivesuperuser', 'inactivesuperuser@example.com', 'password', is_active=False
        )

        # a user with add_image permission through the 'Image adders' group
        self.image_adder = User.objects.create_user(
            'imageadder', 'imageadder@example.com', 'password'
        )
        self.image_adder.groups.add(image_adders_group)

        # a user with add_image permission through user_permissions
        self.oneoff_image_adder = User.objects.create_user(
            'oneoffimageadder', 'oneoffimageadder@example.com', 'password'
        )
        self.oneoff_image_adder.user_permissions.add(add_image_permission)

        # a user that has add_image permission, but is inactive
        self.inactive_image_adder = User.objects.create_user(
            'inactiveimageadder', 'inactiveimageadder@example.com', 'password', is_active=False
        )
        self.inactive_image_adder.groups.add(image_adders_group)

        # a user with change_image permission through the 'Image changers' group
        self.image_changer = User.objects.create_user(
            'imagechanger', 'imagechanger@example.com', 'password'
        )
        self.image_changer.groups.add(image_changers_group)

        # a user with change_image permission through user_permissions
        self.oneoff_image_changer = User.objects.create_user(
            'oneoffimagechanger', 'oneoffimagechanger@example.com', 'password'
        )
        self.oneoff_image_changer.user_permissions.add(change_image_permission)

        # a user that has change_image permission, but is inactive
        self.inactive_image_changer = User.objects.create_user(
            'inactiveimagechanger', 'inactiveimagechanger@example.com', 'password',
            is_active=False
        )
        self.inactive_image_changer.groups.add(image_changers_group)

        # a user with delete_image permission through user_permissions
        self.oneoff_image_deleter = User.objects.create_user(
            'oneoffimagedeleter', 'oneoffimagedeleter@example.com', 'password'
        )
        self.oneoff_image_deleter.user_permissions.add(delete_image_permission)

        # a user with no permissions
        self.useless_user = User.objects.create_user(
            'uselessuser', 'uselessuser@example.com', 'password'
        )

        self.anonymous_user = AnonymousUser()

        # Images

        # an image owned by 'imageadder'
        self.adder_image = Image.objects.create(
            title="imageadder's image", file=get_test_image_file(),
            uploaded_by_user=self.image_adder
        )

        # an image owned by 'uselessuser'
        self.useless_image = Image.objects.create(
            title="uselessuser's image", file=get_test_image_file(),
            uploaded_by_user=self.useless_user
        )

        # an image with no owner
        self.anonymous_image = Image.objects.create(
            title="anonymous image", file=get_test_image_file(),
        )


class TestBlanketPermissionPolicy(PermissionPolicyTestCase):
    def setUp(self):
        super(TestBlanketPermissionPolicy, self).setUp()
        self.policy = BlanketPermissionPolicy(Image)

        self.active_users = [
            self.superuser,
            self.image_adder,
            self.oneoff_image_adder,
            self.image_changer,
            self.oneoff_image_changer,
            self.oneoff_image_deleter,
            self.useless_user,
        ]
        self.all_users = self.active_users + [
            self.inactive_superuser,
            self.inactive_image_adder,
            self.inactive_image_changer,
            self.anonymous_user,
        ]

    def test_user_has_permission(self):
        # All users have permission to do everything
        self.assertUserPermissionMatrix([
            (user, True, True, True, True)
            for user in self.all_users
        ])

    def test_user_has_any_permission(self):
        for user in self.all_users:
            self.assertTrue(
                self.policy.user_has_any_permission(user, ['add', 'change'])
            )

    def test_users_with_permission(self):
        # all active users have permission
        users_with_add_permission = self.policy.users_with_permission('add')

        self.assertResultSetEqual(users_with_add_permission, self.active_users)

    def test_users_with_any_permission(self):
        # all active users have permission
        users_with_add_or_change_permission = self.policy.users_with_any_permission(
            ['add', 'change']
        )

        self.assertResultSetEqual(users_with_add_or_change_permission, self.active_users)

    def test_user_has_permission_for_instance(self):
        # All users have permission to do everything on any given instance
        self.assertUserInstancePermissionMatrix(self.adder_image, [
            (user, True, True, True)
            for user in self.all_users
        ])

    def test_user_has_any_permission_for_instance(self):
        for user in self.all_users:
            self.assertTrue(
                self.policy.user_has_any_permission_for_instance(
                    user, ['change', 'delete'], self.adder_image
                )
            )

    def test_instances_user_has_permission_for(self):
        all_images = [
            self.adder_image, self.useless_image, self.anonymous_image
        ]

        # all users can edit all instances
        for user in self.all_users:
            self.assertResultSetEqual(
                self.policy.instances_user_has_permission_for(user, 'change'),
                all_images
            )

    def test_instances_user_has_any_permission_for(self):
        all_images = [
            self.adder_image, self.useless_image, self.anonymous_image
        ]

        for user in self.all_users:
            self.assertResultSetEqual(
                self.policy.instances_user_has_any_permission_for(user, ['change', 'delete']),
                all_images
            )

    def test_users_with_permission_for_instance(self):
        # all active users have permission
        users_with_change_permission = self.policy.users_with_permission_for_instance(
            'change', self.useless_image
        )

        self.assertResultSetEqual(users_with_change_permission, self.active_users)

    def test_users_with_any_permission_for_instance(self):
        # all active users have permission
        users_with_change_or_del_permission = self.policy.users_with_any_permission_for_instance(
            ['change', 'delete'], self.useless_image
        )

        self.assertResultSetEqual(users_with_change_or_del_permission, self.active_users)


class TestAuthenticationOnlyPermissionPolicy(PermissionPolicyTestCase):
    def setUp(self):
        super(TestAuthenticationOnlyPermissionPolicy, self).setUp()
        self.policy = AuthenticationOnlyPermissionPolicy(Image)

    def test_user_has_permission(self):
        # All active authenticated users have permission to do everything;
        # inactive and anonymous users have permission to do nothing
        self.assertUserPermissionMatrix([
            (self.superuser, True, True, True, True),
            (self.inactive_superuser, False, False, False, False),
            (self.image_adder, True, True, True, True),
            (self.oneoff_image_adder, True, True, True, True),
            (self.inactive_image_adder, False, False, False, False),
            (self.image_changer, True, True, True, True),
            (self.oneoff_image_changer, True, True, True, True),
            (self.inactive_image_changer, False, False, False, False),
            (self.oneoff_image_deleter, True, True, True, True),
            (self.useless_user, True, True, True, True),
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
            self.policy.user_has_any_permission(self.useless_user, ['add', 'change'])
        )

        self.assertFalse(
            self.policy.user_has_any_permission(self.anonymous_user, ['add', 'change'])
        )

    def test_users_with_permission(self):
        # all active users have permission
        users_with_add_permission = self.policy.users_with_permission('add')

        self.assertResultSetEqual(users_with_add_permission, [
            self.superuser,
            self.image_adder,
            self.oneoff_image_adder,
            self.image_changer,
            self.oneoff_image_changer,
            self.oneoff_image_deleter,
            self.useless_user,
        ])

    def test_users_with_any_permission(self):
        # all active users have permission
        users_with_add_or_change_permission = self.policy.users_with_any_permission(
            ['add', 'change']
        )

        self.assertResultSetEqual(users_with_add_or_change_permission, [
            self.superuser,
            self.image_adder,
            self.oneoff_image_adder,
            self.image_changer,
            self.oneoff_image_changer,
            self.oneoff_image_deleter,
            self.useless_user,
        ])

    def test_user_has_permission_for_instance(self):
        # Permissions for this policy are applied at the model level,
        # so rules for a specific instance will match rules for the
        # model as a whole
        self.assertUserInstancePermissionMatrix(self.adder_image, [
            (self.superuser, True, True, True),
            (self.inactive_superuser, False, False, False),
            (self.image_adder, True, True, True),
            (self.oneoff_image_adder, True, True, True),
            (self.inactive_image_adder, False, False, False),
            (self.image_changer, True, True, True),
            (self.oneoff_image_changer, True, True, True),
            (self.inactive_image_changer, False, False, False),
            (self.oneoff_image_deleter, True, True, True),
            (self.useless_user, True, True, True),
            (self.anonymous_user, False, False, False),
        ])

    def test_user_has_any_permission_for_instance(self):
        # superuser has permission
        self.assertTrue(
            self.policy.user_has_any_permission_for_instance(
                self.superuser, ['change', 'delete'], self.adder_image
            )
        )

        # inactive user has no permission
        self.assertFalse(
            self.policy.user_has_any_permission_for_instance(
                self.inactive_superuser, ['change', 'delete'], self.adder_image
            )
        )

        # ordinary user has permission
        self.assertTrue(
            self.policy.user_has_any_permission_for_instance(
                self.useless_user, ['change', 'delete'], self.adder_image
            )
        )

        # anonymous user has no permission
        self.assertFalse(
            self.policy.user_has_any_permission_for_instance(
                self.anonymous_user, ['change', 'delete'], self.adder_image
            )
        )

    def test_instances_user_has_permission_for(self):
        all_images = [
            self.adder_image, self.useless_image, self.anonymous_image
        ]
        no_images = []

        # the set of images editable by superuser includes all images
        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.superuser, 'change'
            ),
            all_images
        )

        # the set of images editable by inactive superuser includes no images
        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.inactive_superuser, 'change'
            ),
            no_images
        )

        # the set of images editable by ordinary user includes all images
        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.useless_user, 'change'
            ),
            all_images
        )

        # the set of images editable by anonymous user includes no images
        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.anonymous_user, 'change'
            ),
            no_images
        )

    def test_instances_user_has_any_permission_for(self):
        all_images = [
            self.adder_image, self.useless_image, self.anonymous_image
        ]
        no_images = []

        # the set of images editable by superuser includes all images
        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.superuser, ['change', 'delete']
            ),
            all_images
        )

        # the set of images editable by inactive superuser includes no images
        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.inactive_superuser, ['change', 'delete']
            ),
            no_images
        )

        # the set of images editable by ordinary user includes all images
        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.useless_user, ['change', 'delete']
            ),
            all_images
        )

        # the set of images editable by anonymous user includes no images
        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.anonymous_user, ['change', 'delete']
            ),
            no_images
        )

    def test_users_with_permission_for_instance(self):
        # all active users have permission
        users_with_change_permission = self.policy.users_with_permission_for_instance(
            'change', self.useless_image
        )

        self.assertResultSetEqual(users_with_change_permission, [
            self.superuser,
            self.image_adder,
            self.oneoff_image_adder,
            self.image_changer,
            self.oneoff_image_changer,
            self.oneoff_image_deleter,
            self.useless_user,
        ])

    def test_users_with_any_permission_for_instance(self):
        # all active users have permission
        users_with_change_or_del_permission = self.policy.users_with_any_permission_for_instance(
            ['change', 'delete'], self.useless_image
        )

        self.assertResultSetEqual(users_with_change_or_del_permission, [
            self.superuser,
            self.image_adder,
            self.oneoff_image_adder,
            self.image_changer,
            self.oneoff_image_changer,
            self.oneoff_image_deleter,
            self.useless_user,
        ])


class TestModelPermissionPolicy(PermissionPolicyTestCase):
    def setUp(self):
        super(TestModelPermissionPolicy, self).setUp()
        self.policy = ModelPermissionPolicy(Image)

    def test_user_has_permission(self):
        self.assertUserPermissionMatrix([
            # Superuser has permission to do everything
            (self.superuser, True, True, True, True),

            # Inactive superuser can do nothing
            (self.inactive_superuser, False, False, False, False),

            # User with 'add' permission via group can only add
            (self.image_adder, True, False, False, False),

            # User with 'add' permission via user can only add
            (self.oneoff_image_adder, True, False, False, False),

            # Inactive user with 'add' permission can do nothing
            (self.inactive_image_adder, False, False, False, False),

            # User with 'change' permission via group can only change
            (self.image_changer, False, True, False, False),

            # User with 'change' permission via user can only change
            (self.oneoff_image_changer, False, True, False, False),

            # Inactive user with 'add' permission can do nothing
            (self.inactive_image_changer, False, False, False, False),

            # User with 'delete' permission can only delete
            (self.oneoff_image_deleter, False, False, True, False),

            # User with no permissions can do nothing
            (self.useless_user, False, False, False, False),

            # Anonymous user can do nothing
            (self.anonymous_user, False, False, False, False),
        ])

    def test_user_has_any_permission(self):
        # Superuser can do everything
        self.assertTrue(
            self.policy.user_has_any_permission(self.superuser, ['add', 'change'])
        )

        # Inactive superuser can do nothing
        self.assertFalse(
            self.policy.user_has_any_permission(self.inactive_superuser, ['add', 'change'])
        )

        # Only one of the permissions in the list needs to pass
        # in order for user_has_any_permission to return true
        self.assertTrue(
            self.policy.user_has_any_permission(self.image_adder, ['add', 'change'])
        )
        self.assertTrue(
            self.policy.user_has_any_permission(self.oneoff_image_adder, ['add', 'change'])
        )
        self.assertTrue(
            self.policy.user_has_any_permission(self.image_changer, ['add', 'change'])
        )

        # User with some permission, but not the ones in the list,
        # should return false
        self.assertFalse(
            self.policy.user_has_any_permission(self.image_changer, ['add', 'delete'])
        )

        # Inactive user with the appropriate permissions can do nothing
        self.assertFalse(
            self.policy.user_has_any_permission(self.inactive_image_adder, ['add', 'delete'])
        )

        # User with no permissions can do nothing
        self.assertFalse(
            self.policy.user_has_any_permission(self.useless_user, ['add', 'change'])
        )

        # Anonymous user can do nothing
        self.assertFalse(
            self.policy.user_has_any_permission(self.anonymous_user, ['add', 'change'])
        )

    def test_users_with_permission(self):
        users_with_add_permission = self.policy.users_with_permission('add')

        self.assertResultSetEqual(users_with_add_permission, [
            self.superuser,
            self.image_adder,
            self.oneoff_image_adder,
        ])

        users_with_change_permission = self.policy.users_with_permission('change')

        self.assertResultSetEqual(users_with_change_permission, [
            self.superuser,
            self.image_changer,
            self.oneoff_image_changer,
        ])

    def test_users_with_any_permission(self):
        users_with_add_or_change_permission = self.policy.users_with_any_permission(
            ['add', 'change']
        )

        self.assertResultSetEqual(users_with_add_or_change_permission, [
            self.superuser,
            self.image_adder,
            self.oneoff_image_adder,
            self.image_changer,
            self.oneoff_image_changer,
        ])

        users_with_change_or_delete_permission = self.policy.users_with_any_permission(
            ['change', 'delete']
        )

        self.assertResultSetEqual(users_with_change_or_delete_permission, [
            self.superuser,
            self.image_changer,
            self.oneoff_image_changer,
            self.oneoff_image_deleter,
        ])

    def test_user_has_permission_for_instance(self):
        # Permissions for this policy are applied at the model level,
        # so rules for a specific instance will match rules for the
        # model as a whole
        self.assertUserInstancePermissionMatrix(self.adder_image, [
            (self.superuser, True, True, True),
            (self.inactive_superuser, False, False, False),
            (self.image_adder, False, False, False),
            (self.oneoff_image_adder, False, False, False),
            (self.inactive_image_adder, False, False, False),
            (self.image_changer, True, False, False),
            (self.oneoff_image_changer, True, False, False),
            (self.inactive_image_changer, False, False, False),
            (self.oneoff_image_deleter, False, True, False),
            (self.useless_user, False, False, False),
            (self.anonymous_user, False, False, False),
        ])

    def test_user_has_any_permission_for_instance(self):
        # Superuser can do everything
        self.assertTrue(
            self.policy.user_has_any_permission_for_instance(
                self.superuser, ['change', 'delete'], self.adder_image
            )
        )

        # Inactive superuser can do nothing
        self.assertFalse(
            self.policy.user_has_any_permission_for_instance(
                self.inactive_superuser, ['change', 'delete'], self.adder_image
            )
        )

        # Only one of the permissions in the list needs to pass
        # in order for user_has_any_permission to return true
        self.assertTrue(
            self.policy.user_has_any_permission_for_instance(
                self.image_changer, ['change', 'delete'], self.adder_image
            )
        )
        self.assertTrue(
            self.policy.user_has_any_permission_for_instance(
                self.oneoff_image_changer, ['change', 'delete'], self.adder_image
            )
        )

        # User with some permission, but not the ones in the list,
        # should return false
        self.assertFalse(
            self.policy.user_has_any_permission_for_instance(
                self.image_adder, ['change', 'delete'], self.adder_image
            )
        )

        # Inactive user with the appropriate permissions can do nothing
        self.assertFalse(
            self.policy.user_has_any_permission_for_instance(
                self.inactive_image_changer, ['change', 'delete'], self.adder_image
            )
        )

        # User with no permissions can do nothing
        self.assertFalse(
            self.policy.user_has_any_permission_for_instance(
                self.useless_user, ['change', 'delete'], self.adder_image
            )
        )

        # Anonymous user can do nothing
        self.assertFalse(
            self.policy.user_has_any_permission_for_instance(
                self.anonymous_user, ['change', 'delete'], self.adder_image
            )
        )

    def test_instances_user_has_permission_for(self):
        all_images = [
            self.adder_image, self.useless_image, self.anonymous_image
        ]
        no_images = []

        # the set of images editable by superuser includes all images
        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.superuser, 'change'
            ),
            all_images
        )

        # the set of images editable by inactive superuser includes no images
        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.inactive_superuser, 'change'
            ),
            no_images
        )

        # given the relevant model permission at the group level, a user can edit all images
        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.image_changer, 'change'
            ),
            all_images
        )

        # given the relevant model permission at the user level, a user can edit all images
        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.oneoff_image_changer, 'change'
            ),
            all_images
        )

        # a user with no permission can edit no images
        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.useless_user, 'change'
            ),
            no_images
        )

        # an inactive user with the relevant permission can edit no images
        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.inactive_image_changer, 'change'
            ),
            no_images
        )

        # a user with permission, but not the matching one, can edit no images
        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.image_changer, 'delete'
            ),
            no_images
        )

        # the set of images editable by anonymous user includes no images
        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.anonymous_user, 'change'
            ),
            no_images
        )

    def test_instances_user_has_any_permission_for(self):
        all_images = [
            self.adder_image, self.useless_image, self.anonymous_image
        ]
        no_images = []

        # the set of images editable by superuser includes all images
        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.superuser, ['change', 'delete']
            ),
            all_images
        )

        # the set of images editable by inactive superuser includes no images
        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.inactive_superuser, ['change', 'delete']
            ),
            no_images
        )

        # given the relevant model permission at the group level, a user can edit all images
        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.image_changer, ['change', 'delete']
            ),
            all_images
        )

        # given the relevant model permission at the user level, a user can edit all images
        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.oneoff_image_changer, ['change', 'delete']
            ),
            all_images
        )

        # a user with no permission can edit no images
        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.useless_user, ['change', 'delete']
            ),
            no_images
        )

        # an inactive user with the relevant permission can edit no images
        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.inactive_image_changer, ['change', 'delete']
            ),
            no_images
        )

        # a user with permission, but not the matching one, can edit no images
        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.image_adder, ['change', 'delete']
            ),
            no_images
        )

        # the set of images editable by anonymous user includes no images
        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.anonymous_user, ['change', 'delete']
            ),
            no_images
        )

    def test_users_with_permission_for_instance(self):
        users_with_change_permission = self.policy.users_with_permission_for_instance(
            'change', self.useless_image
        )

        self.assertResultSetEqual(users_with_change_permission, [
            self.superuser,
            self.image_changer,
            self.oneoff_image_changer,
        ])

        users_with_delete_permission = self.policy.users_with_permission_for_instance(
            'delete', self.useless_image
        )

        self.assertResultSetEqual(users_with_delete_permission, [
            self.superuser,
            self.oneoff_image_deleter,
        ])

    def test_users_with_any_permission_for_instance(self):
        users_with_change_or_del_permission = self.policy.users_with_any_permission_for_instance(
            ['change', 'delete'], self.useless_image
        )

        self.assertResultSetEqual(users_with_change_or_del_permission, [
            self.superuser,
            self.image_changer,
            self.oneoff_image_changer,
            self.oneoff_image_deleter,
        ])


class TestOwnershipPermissionPolicy(PermissionPolicyTestCase):
    def setUp(self):
        super(TestOwnershipPermissionPolicy, self).setUp()
        self.policy = OwnershipPermissionPolicy(Image, owner_field_name='uploaded_by_user')

    def test_user_has_permission(self):
        self.assertUserPermissionMatrix([
            # Superuser has permission to do everything
            (self.superuser, True, True, True, True),

            # Inactive superuser can do nothing
            (self.inactive_superuser, False, False, False, False),

            # User with 'add' permission via group can add,
            # and by extension, change and delete their own instances
            (self.image_adder, True, True, True, False),

            # User with 'add' permission via user can add,
            # and by extension, change and delete their own instances
            (self.oneoff_image_adder, True, True, True, False),

            # Inactive user with 'add' permission can do nothing
            (self.inactive_image_adder, False, False, False, False),

            # User with 'change' permission via group can change and delete but not add
            (self.image_changer, False, True, True, False),

            # User with 'change' permission via user can change and delete but not add
            (self.oneoff_image_changer, False, True, True, False),

            # Inactive user with 'change' permission can do nothing
            (self.inactive_image_changer, False, False, False, False),

            # 'delete' permission is ignored for this policy
            (self.oneoff_image_deleter, False, False, False, False),

            # User with no permission can do nothing
            (self.useless_user, False, False, False, False),

            # Anonymous user can do nothing
            (self.anonymous_user, False, False, False, False),
        ])

    def test_user_has_any_permission(self):
        # Superuser can do everything
        self.assertTrue(
            self.policy.user_has_any_permission(self.superuser, ['add', 'change'])
        )

        # Inactive superuser can do nothing
        self.assertFalse(
            self.policy.user_has_any_permission(self.inactive_superuser, ['add', 'change'])
        )

        # Only one of the permissions in the list needs to pass
        # in order for user_has_any_permission to return true
        self.assertTrue(
            self.policy.user_has_any_permission(self.image_changer, ['add', 'change'])
        )
        self.assertTrue(
            self.policy.user_has_any_permission(self.oneoff_image_changer, ['add', 'change'])
        )

        # User with some permission, but not the ones in the list,
        # should return false
        self.assertFalse(
            self.policy.user_has_any_permission(self.oneoff_image_deleter, ['add', 'change'])
        )

        # Inactive user with the appropriate permissions can do nothing
        self.assertFalse(
            self.policy.user_has_any_permission(self.inactive_image_changer, ['add', 'delete'])
        )

        # User with no permissions can do nothing
        self.assertFalse(
            self.policy.user_has_any_permission(self.useless_user, ['add', 'change'])
        )

        # Anonymous user can do nothing
        self.assertFalse(
            self.policy.user_has_any_permission(self.anonymous_user, ['add', 'change'])
        )

    def test_users_with_permission(self):
        users_with_add_permission = self.policy.users_with_permission('add')

        self.assertResultSetEqual(users_with_add_permission, [
            self.superuser,
            self.image_adder,
            self.oneoff_image_adder,
        ])

        # users with add permission have change permission too (i.e. for their own images)
        users_with_change_permission = self.policy.users_with_permission('change')

        self.assertResultSetEqual(users_with_change_permission, [
            self.superuser,
            self.image_adder,
            self.oneoff_image_adder,
            self.image_changer,
            self.oneoff_image_changer,
        ])

        # conditions for deletion are the same as for change; 'delete' permission
        # records in django.contrib.auth are ignored
        users_with_delete_permission = self.policy.users_with_permission('delete')

        self.assertResultSetEqual(users_with_delete_permission, [
            self.superuser,
            self.image_adder,
            self.oneoff_image_adder,
            self.image_changer,
            self.oneoff_image_changer,
        ])

        # non-standard permissions are only available to superusers
        users_with_frobnicate_permission = self.policy.users_with_permission('frobnicate')

        self.assertResultSetEqual(users_with_frobnicate_permission, [
            self.superuser,
        ])

    def test_users_with_any_permission(self):
        users_with_add_or_change_permission = self.policy.users_with_any_permission(
            ['add', 'change']
        )

        self.assertResultSetEqual(users_with_add_or_change_permission, [
            self.superuser,
            self.image_adder,
            self.oneoff_image_adder,
            self.image_changer,
            self.oneoff_image_changer,
        ])

        users_with_add_or_frobnicate_permission = self.policy.users_with_any_permission(
            ['add', 'frobnicate']
        )

        self.assertResultSetEqual(users_with_add_or_frobnicate_permission, [
            self.superuser,
            self.image_adder,
            self.oneoff_image_adder,
        ])

    def test_user_has_permission_for_instance(self):
        # Test permissions for an image owned by image_adder
        self.assertUserInstancePermissionMatrix(self.adder_image, [
            # superuser can do everything
            (self.superuser, True, True, True),

            # inactive superuser can do nothing
            (self.inactive_superuser, False, False, False),

            # image_adder can change and delete their own images,
            # but not perform custom actions
            (self.image_adder, True, True, False),

            # user with add permission cannot edit images owned by others
            (self.oneoff_image_adder, False, False, False),

            # inactive user with 'add' permission can do nothing
            (self.inactive_image_adder, False, False, False),

            # user with change permission can change and delete all images
            (self.image_changer, True, True, False),

            # likewise for change permission specified at the user level
            (self.oneoff_image_changer, True, True, False),

            # inactive user with 'change' permission can do nothing
            (self.inactive_image_changer, False, False, False),

            # delete permissions are ignored
            (self.oneoff_image_deleter, False, False, False),

            # user with no permissions can do nothing
            (self.useless_user, False, False, False),

            # anonymous user can do nothing
            (self.anonymous_user, False, False, False),
        ])

        # Test permissions for an image owned by useless_user
        self.assertUserInstancePermissionMatrix(self.useless_image, [
            # superuser can do everything
            (self.superuser, True, True, True),

            # image_adder cannot edit images owned by others
            (self.image_adder, False, False, False),
            (self.oneoff_image_adder, False, False, False),

            # user with change permission can change and delete all images
            (self.image_changer, True, True, False),
            (self.oneoff_image_changer, True, True, False),

            # inactive users can do nothing
            (self.inactive_superuser, False, False, False),
            (self.inactive_image_adder, False, False, False),
            (self.inactive_image_changer, False, False, False),

            # delete permissions are ignored
            (self.oneoff_image_deleter, False, False, False),

            # user with no permissions can do nothing, even on images
            # they own
            (self.useless_user, False, False, False),

            # anonymous user can do nothing
            (self.anonymous_user, False, False, False),
        ])

        # Instances with a null owner should always follow the same rules
        # as 'an instance owned by someone else'
        self.assertUserInstancePermissionMatrix(self.anonymous_image, [
            (self.superuser, True, True, True),
            (self.image_adder, False, False, False),
            (self.oneoff_image_adder, False, False, False),
            (self.image_changer, True, True, False),
            (self.oneoff_image_changer, True, True, False),
            (self.inactive_superuser, False, False, False),
            (self.inactive_image_adder, False, False, False),
            (self.inactive_image_changer, False, False, False),
            (self.oneoff_image_deleter, False, False, False),
            (self.useless_user, False, False, False),
            (self.anonymous_user, False, False, False),
        ])

    def test_user_has_any_permission_for_instance(self):
        # Superuser can do everything
        self.assertTrue(
            self.policy.user_has_any_permission_for_instance(
                self.superuser, ['change', 'delete'], self.adder_image
            )
        )

        # Inactive superuser can do nothing
        self.assertFalse(
            self.policy.user_has_any_permission_for_instance(
                self.inactive_superuser, ['change', 'delete'], self.adder_image
            )
        )

        # Only one of the permissions in the list needs to pass
        # in order for user_has_any_permission to return true
        self.assertTrue(
            self.policy.user_has_any_permission_for_instance(
                self.image_changer, ['change', 'frobnicate'], self.adder_image
            )
        )
        self.assertTrue(
            self.policy.user_has_any_permission_for_instance(
                self.oneoff_image_changer, ['change', 'frobnicate'], self.adder_image
            )
        )

        # User with some permission, but not the ones in the list,
        # should return false
        self.assertFalse(
            self.policy.user_has_any_permission_for_instance(
                self.oneoff_image_deleter, ['change', 'delete'], self.adder_image
            )
        )

        # Inactive user with the appropriate permissions can do nothing
        self.assertFalse(
            self.policy.user_has_any_permission_for_instance(
                self.inactive_image_changer, ['change', 'delete'], self.adder_image
            )
        )

        # User with no permissions can do nothing
        self.assertFalse(
            self.policy.user_has_any_permission_for_instance(
                self.useless_user, ['change', 'delete'], self.adder_image
            )
        )

        # Anonymous user can do nothing
        self.assertFalse(
            self.policy.user_has_any_permission_for_instance(
                self.anonymous_user, ['change', 'delete'], self.adder_image
            )
        )

    def test_instances_user_has_permission_for(self):
        all_images = [
            self.adder_image, self.useless_image, self.anonymous_image
        ]
        no_images = []

        # the set of images editable by superuser includes all images
        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.superuser, 'change'
            ),
            all_images
        )

        # the set of images editable by inactive superuser includes no images
        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.inactive_superuser, 'change'
            ),
            no_images
        )

        # a user with 'add' permission can change their own images
        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.image_adder, 'change'
            ),
            [self.adder_image]
        )
        # a user with 'add' permission can also delete their own images
        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.image_adder, 'delete'
            ),
            [self.adder_image]
        )

        # a user with 'change' permission can change all images
        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.image_changer, 'change'
            ),
            all_images
        )

        # ditto for 'change' permission assigned at the user level
        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.oneoff_image_changer, 'change'
            ),
            all_images
        )

        # an inactive user with the relevant permission can edit no images
        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.inactive_image_changer, 'change'
            ),
            no_images
        )

        # a user with no permission can edit no images
        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.useless_user, 'change'
            ),
            no_images
        )

        # the set of images editable by anonymous user includes no images
        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.anonymous_user, 'change'
            ),
            no_images
        )

    def test_instances_user_has_any_permission_for(self):
        all_images = [
            self.adder_image, self.useless_image, self.anonymous_image
        ]
        no_images = []

        # the set of images editable by superuser includes all images
        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.superuser, ['change', 'delete']
            ),
            all_images
        )

        # the set of images editable by inactive superuser includes no images
        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.inactive_superuser, ['change', 'delete']
            ),
            no_images
        )

        # a user with 'add' permission can change/delete their own images
        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.image_adder, ['delete', 'frobnicate']
            ),
            [self.adder_image]
        )

        # a user with 'edit' permission can change/delete all images
        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.oneoff_image_changer, ['delete', 'frobnicate']
            ),
            all_images
        )

        # a user with no permission can edit no images
        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.useless_user, ['change', 'delete']
            ),
            no_images
        )

        # an inactive user with the relevant permission can edit no images
        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.inactive_image_changer, ['change', 'delete']
            ),
            no_images
        )

        # a user with permission, but not the matching one, can edit no images
        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.oneoff_image_deleter, ['change', 'delete']
            ),
            no_images
        )

        # the set of images editable by anonymous user includes no images
        self.assertResultSetEqual(
            self.policy.instances_user_has_any_permission_for(
                self.anonymous_user, ['change', 'delete']
            ),
            no_images
        )

    def test_users_with_permission_for_instance(self):
        # adder_image can be edited by its owner (who has add permission) and
        # all users with 'change' permission
        users_with_change_permission = self.policy.users_with_permission_for_instance(
            'change', self.adder_image
        )

        self.assertResultSetEqual(users_with_change_permission, [
            self.superuser,
            self.image_adder,
            self.image_changer,
            self.oneoff_image_changer,
        ])

        # the same set of users can also delete
        users_with_delete_permission = self.policy.users_with_permission_for_instance(
            'delete', self.adder_image
        )

        self.assertResultSetEqual(users_with_delete_permission, [
            self.superuser,
            self.image_adder,
            self.image_changer,
            self.oneoff_image_changer,
        ])

        # custom actions are available to superusers only
        users_with_delete_permission = self.policy.users_with_permission_for_instance(
            'frobnicate', self.adder_image
        )

        self.assertResultSetEqual(users_with_delete_permission, [
            self.superuser,
        ])

        # useless_user can NOT edit their own image, because they do not have
        # 'add' permission
        users_with_change_permission = self.policy.users_with_permission_for_instance(
            'change', self.useless_image
        )

        self.assertResultSetEqual(users_with_change_permission, [
            self.superuser,
            self.image_changer,
            self.oneoff_image_changer,
        ])

        # an image with no owner is treated as if it's owned by 'somebody else' -
        # i.e. users with 'change' permission can edit it
        users_with_change_permission = self.policy.users_with_permission_for_instance(
            'change', self.anonymous_image
        )

        self.assertResultSetEqual(users_with_change_permission, [
            self.superuser,
            self.image_changer,
            self.oneoff_image_changer,
        ])

    def test_users_with_any_permission_for_instance(self):
        users_with_change_or_frob_permission = self.policy.users_with_any_permission_for_instance(
            ['change', 'frobnicate'], self.adder_image
        )

        self.assertResultSetEqual(users_with_change_or_frob_permission, [
            self.superuser,
            self.image_adder,
            self.image_changer,
            self.oneoff_image_changer,
        ])
