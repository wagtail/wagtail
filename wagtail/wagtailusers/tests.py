from __future__ import unicode_literals

import unittest

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.utils import six

from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailcore import hooks
from wagtail.wagtailusers.models import UserProfile
from wagtail.wagtailcore.models import Page, GroupPagePermission


class TestUserIndexView(TestCase, WagtailTestUtils):
    def setUp(self):
        # create a user that should be visible in the listing
        self.test_user = get_user_model().objects.create_user(
            username='testuser',
            email='testuser@email.com',
            password='password'
        )
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailusers_users:index'), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailusers/users/index.html')
        self.assertContains(response, 'testuser')

    def test_allows_negative_ids(self):
        # see https://github.com/torchbox/wagtail/issues/565
        get_user_model().objects.create_user('guardian', 'guardian@example.com', 'gu@rd14n', id=-1)
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')
        self.assertContains(response, 'guardian')

    def test_search(self):
        response = self.get({'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

    def test_pagination(self):
        pages = ['0', '1', '-1', '9999', 'Not a page']
        for page in pages:
            response = self.get({'p': page})
            self.assertEqual(response.status_code, 200)


class TestUserCreateView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailusers_users:add'), params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailusers_users:add'), post_data)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailusers/users/create.html')

    def test_create(self):
        response = self.post({
            'username': "testuser",
            'email': "test@user.com",
            'first_name': "Test",
            'last_name': "User",
            'password1': "password",
            'password2': "password",
        })

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailusers_users:index'))

        # Check that the user was created
        users = get_user_model().objects.filter(username='testuser')
        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first().email, 'test@user.com')

    def test_create_with_password_mismatch(self):
        response = self.post({
            'username': "testuser",
            'email': "test@user.com",
            'first_name': "Test",
            'last_name': "User",
            'password1': "password1",
            'password2': "password2",
        })

        # Should remain on page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailusers/users/create.html')

        self.assertTrue(response.context['form'].errors['password2'])

        # Check that the user was not created
        users = get_user_model().objects.filter(username='testuser')
        self.assertEqual(users.count(), 0)


class TestUserEditView(TestCase, WagtailTestUtils):
    def setUp(self):
        # Create a user to edit
        self.test_user = get_user_model().objects.create_user(
            username='testuser',
            email='testuser@email.com',
            password='password'
        )

        # Login
        self.login()

    def get(self, params={}, user_id=None):
        return self.client.get(reverse('wagtailusers_users:edit', args=(user_id or self.test_user.id, )), params)

    def post(self, post_data={}, user_id=None):
        return self.client.post(reverse('wagtailusers_users:edit', args=(user_id or self.test_user.id, )), post_data)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailusers/users/edit.html')

    def test_nonexistant_redirect(self):
        self.assertEqual(self.get(user_id=100000).status_code, 404)

    def test_edit(self):
        response = self.post({
            'username': "testuser",
            'email': "test@user.com",
            'first_name': "Edited",
            'last_name': "User",
            'password1': "password",
            'password2': "password",
        })

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailusers_users:index'))

        # Check that the user was edited
        user = get_user_model().objects.get(id=self.test_user.id)
        self.assertEqual(user.first_name, 'Edited')

    def test_edit_validation_error(self):
        # Leave "username" field blank. This should give a validation error
        response = self.post({
            'username': "",
            'email': "test@user.com",
            'first_name': "Teset",
            'last_name': "User",
            'password1': "password",
            'password2': "password",
        })

        # Should not redirect to index
        self.assertEqual(response.status_code, 200)


class TestUserProfileCreation(TestCase, WagtailTestUtils):
    def setUp(self):
        # Create a user
        self.test_user = get_user_model().objects.create_user(
            username='testuser',
            email='testuser@email.com',
            password='password'
        )

    def test_user_created_without_profile(self):
        self.assertEqual(UserProfile.objects.filter(user=self.test_user).count(), 0)
        with self.assertRaises(UserProfile.DoesNotExist):
            self.test_user.userprofile

    def test_user_profile_created_when_method_called(self):
        self.assertIsInstance(UserProfile.get_for_user(self.test_user), UserProfile)
        # and get it from the db too
        self.assertEqual(UserProfile.objects.filter(user=self.test_user).count(), 1)


class TestGroupIndexView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailusers_groups:index'), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailusers/groups/index.html')

    def test_search(self):
        response = self.get({'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

    def test_pagination(self):
        pages = ['0', '1', '-1', '9999', 'Not a page']
        for page in pages:
            response = self.get({'p': page})
            self.assertEqual(response.status_code, 200)


class TestGroupCreateView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailusers_groups:add'), params)

    def post(self, post_data={}):
        post_defaults = {
            'page_permissions-TOTAL_FORMS': ['0'],
            'page_permissions-MAX_NUM_FORMS': ['1000'],
            'page_permissions-INITIAL_FORMS': ['0'],
        }
        for k, v in six.iteritems(post_defaults):
            post_data[k] = post_data.get(k, v)
        return self.client.post(reverse('wagtailusers_groups:add'), post_data)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailusers/groups/create.html')

    def test_create_group(self):
        response = self.post({'name': "test group"})

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailusers_groups:index'))

        # Check that the user was created
        groups = Group.objects.filter(name='test group')
        self.assertEqual(groups.count(), 1)

    def test_group_create_adding_permissions(self):
        response = self.post({
            'name': "test group",
            'page_permissions-0-id': [''],
            'page_permissions-0-page': ['1'],
            'page_permissions-0-permission_type': ['publish'],
            'page_permissions-1-id': [''],
            'page_permissions-1-page': ['1'],
            'page_permissions-1-permission_type': ['edit'],
            'page_permissions-TOTAL_FORMS': ['2'],
        })

        self.assertRedirects(response, reverse('wagtailusers_groups:index'))
        # The test group now exists, with two page permissions
        new_group = Group.objects.get(name='test group')
        self.assertEqual(new_group.page_permissions.all().count(), 2)

    @unittest.expectedFailure
    def test_duplicate_page_permissions_error(self):
        # Try to submit duplicate page permission entries
        response = self.post({
            'name': "test group",
            'page_permissions-0-id': [''],
            'page_permissions-0-page': ['1'],
            'page_permissions-0-permission_type': ['publish'],
            'page_permissions-1-id': [''],
            'page_permissions-1-page': ['1'],
            'page_permissions-1-permission_type': ['publish'],
            'page_permissions-TOTAL_FORMS': ['2'],
        })

        self.assertEqual(response.status_code, 200)
        # the second form should have errors
        self.assertEqual(bool(response.context['formset'].errors[0]), False)
        self.assertEqual(bool(response.context['formset'].errors[1]), True)


class TestGroupEditView(TestCase, WagtailTestUtils):
    def setUp(self):
        # Create a group to edit
        self.test_group = Group.objects.create(name='test group')
        self.root_page = Page.objects.get(id=1)
        self.root_add_permission = GroupPagePermission.objects.create(page=self.root_page,
                                                                      permission_type='add',
                                                                      group=self.test_group)
        # Get the hook-registered permissions, and add one to this group
        self.registered_permissions = Permission.objects.none()
        for fn in hooks.get_hooks('register_permissions'):
            self.registered_permissions = self.registered_permissions | fn()
        self.existing_permission = self.registered_permissions.order_by('pk')[0]
        self.another_permission = self.registered_permissions.order_by('pk')[1]

        self.test_group.permissions.add(self.existing_permission)

        # Login
        self.login()

    def get(self, params={}, group_id=None):
        return self.client.get(reverse('wagtailusers_groups:edit', args=(group_id or self.test_group.id, )), params)

    def post(self, post_data={}, group_id=None):
        post_defaults = {
            'name': 'test group',
            'permissions': [self.existing_permission.id],
            'page_permissions-TOTAL_FORMS': ['1'],
            'page_permissions-MAX_NUM_FORMS': ['1000'],
            'page_permissions-INITIAL_FORMS': ['1'],  # as we have one page permission already
            'page_permissions-0-id': [self.root_add_permission.id],
            'page_permissions-0-page': [self.root_add_permission.page.id],
            'page_permissions-0-permission_type': [self.root_add_permission.permission_type]
        }
        for k, v in six.iteritems(post_defaults):
            post_data[k] = post_data.get(k, v)
        return self.client.post(reverse(
            'wagtailusers_groups:edit', args=(group_id or self.test_group.id, )), post_data)

    def add_non_registered_perm(self):
        # Some groups may have django permissions assigned that are not
        # hook-registered as part of the wagtail interface. We need to ensure
        # that these permissions are not overwritten by our views.
        # Tests that use this method are testing the aforementioned
        # functionality.
        self.non_registered_perms = Permission.objects.exclude(id__in=self.registered_permissions)
        self.non_registered_perm = self.non_registered_perms[0]
        self.test_group.permissions.add(self.non_registered_perm)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailusers/groups/edit.html')

    def test_nonexistant_group_redirect(self):
        self.assertEqual(self.get(group_id=100000).status_code, 404)

    def test_group_edit(self):
        response = self.post({'name': "test group edited"})

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailusers_groups:index'))

        # Check that the group was edited
        group = Group.objects.get(id=self.test_group.id)
        self.assertEqual(group.name, 'test group edited')

    def test_group_edit_validation_error(self):
        # Leave "name" field blank. This should give a validation error
        response = self.post({'name': ""})

        # Should not redirect to index
        self.assertEqual(response.status_code, 200)

    def test_group_edit_adding_page_permissions(self):
        # The test group has one page permission to begin with
        self.assertEqual(self.test_group.page_permissions.count(), 1)
        response = self.post({
            'page_permissions-1-id': [''],
            'page_permissions-1-page': ['1'],
            'page_permissions-1-permission_type': ['publish'],
            'page_permissions-2-id': [''],
            'page_permissions-2-page': ['1'],
            'page_permissions-2-permission_type': ['edit'],
            'page_permissions-TOTAL_FORMS': ['3'],
        })

        self.assertRedirects(response, reverse('wagtailusers_groups:index'))
        # The test group now has three page permissions
        self.assertEqual(self.test_group.page_permissions.count(), 3)

    def test_group_edit_deleting_page_permissions(self):
        # The test group has one page permissions to begin with
        self.assertEqual(self.test_group.page_permissions.count(), 1)

        response = self.post({
            'page_permissions-0-DELETE': ['1'],
        })

        self.assertRedirects(response, reverse('wagtailusers_groups:index'))
        # The test group now has zero page permissions
        self.assertEqual(self.test_group.page_permissions.count(), 0)

    def test_group_edit_loads_with_page_permissions_shown(self):
        # The test group has one page permission to begin with
        self.assertEqual(self.test_group.page_permissions.count(), 1)

        response = self.get()

        self.assertEqual(response.context['formset'].management_form['INITIAL_FORMS'].value(), 1)
        self.assertEqual(response.context['formset'].forms[0].instance, self.root_add_permission)

        root_edit_perm = GroupPagePermission.objects.create(page=self.root_page,
                                                            permission_type='edit',
                                                            group=self.test_group)

        # The test group now has two page permissions
        self.assertEqual(self.test_group.page_permissions.count(), 2)

        # Reload the page and check the form instances
        response = self.get()
        self.assertEqual(response.context['formset'].management_form['INITIAL_FORMS'].value(), 2)
        self.assertEqual(response.context['formset'].forms[0].instance, self.root_add_permission)
        self.assertEqual(response.context['formset'].forms[1].instance, root_edit_perm)

    def test_duplicate_page_permissions_error(self):
        # Try to submit duplicate page permission entries
        response = self.post({
            'page_permissions-1-id': [''],
            'page_permissions-1-page': [self.root_add_permission.page.id],
            'page_permissions-1-permission_type': [self.root_add_permission.permission_type],
            'page_permissions-TOTAL_FORMS': ['2'],
        })

        self.assertEqual(response.status_code, 200)
        # the second form should have errors
        self.assertEqual(bool(response.context['formset'].errors[0]), False)
        self.assertEqual(bool(response.context['formset'].errors[1]), True)

    def test_group_add_registered_django_permissions(self):
        # The test group has one django permission to begin with
        self.assertEqual(self.test_group.permissions.count(), 1)
        response = self.post({
            'permissions': [self.existing_permission.id, self.another_permission.id]
        })
        self.assertRedirects(response, reverse('wagtailusers_groups:index'))
        self.assertEqual(self.test_group.permissions.count(), 2)

    def test_group_form_includes_non_registered_permissions_in_initial_data(self):
        self.add_non_registered_perm()
        original_permissions = self.test_group.permissions.all()
        self.assertEqual(original_permissions.count(), 2)

        response = self.get()
        # See that the form is set up with the correct initial data
        self.assertEqual(
            response.context['form'].initial.get('permissions'),
            list(original_permissions.values_list('id', flat=True))
        )

    def test_group_retains_non_registered_permissions_when_editing(self):
        self.add_non_registered_perm()
        original_permissions = list(self.test_group.permissions.all())  # list() to force evaluation

        # submit the form with no changes (only submitting the exsisting
        # permission, as in the self.post function definition)
        self.post()

        # See that the group has the same permissions as before
        self.assertEqual(list(self.test_group.permissions.all()), original_permissions)
        self.assertEqual(self.test_group.permissions.count(), 2)

    def test_group_retains_non_registered_permissions_when_adding(self):
        self.add_non_registered_perm()
        # Add a second registered permission
        self.post({
            'permissions': [self.existing_permission.id, self.another_permission.id]
        })

        # See that there are now three permissions in total
        self.assertEqual(self.test_group.permissions.count(), 3)
        # ...including the non-registered one
        self.assertIn(self.non_registered_perm, self.test_group.permissions.all())

    def test_group_retains_non_registered_permissions_when_deleting(self):
        self.add_non_registered_perm()
        # Delete all registered permissions
        self.post({'permissions': []})

        # See that the non-registered permission is still there
        self.assertEqual(self.test_group.permissions.count(), 1)
        self.assertEqual(self.test_group.permissions.all()[0], self.non_registered_perm)
