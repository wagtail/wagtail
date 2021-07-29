from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.http import HttpRequest, HttpResponse
from django.test import TestCase
from django.urls import reverse

from wagtail.tests.utils import WagtailTestUtils
from wagtail.users.views.bulk_actions.user_bulk_action import UserBulkAction


class TestUserToggleActivityView(TestCase, WagtailTestUtils):
    def setUp(self):
        # create a set of test users
        self.test_users = [
            self.create_user(
                username=f'testuser-{i}',
                email=f'testuser{i}@email.com',
                password=f'password-{i}',
            ) for i in range(1, 6)
        ]
        self.new_group = Group.objects.create(name='group')
        self.current_user = self.login()
        self.url = reverse('wagtailusers_users:user_bulk_action', args=('assign_role',)) + '?'
        self.self_toggle_url = self.url + f'id={self.current_user.pk}'
        for user in self.test_users:
            self.url += f'id={user.pk}&'
        self.post_data = {'role': self.new_group.pk}

    def test_simple(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailusers/bulk_actions/confirm_bulk_assign_role.html')

    def test_bulk_toggle(self):
        response = self.client.post(self.url, self.post_data)

        # Should redirect back to index
        self.assertEqual(response.status_code, 302)

        # Check that the users were added to the new group
        for user in self.test_users:
            self.assertTrue(get_user_model().objects.get(email=user.email).groups.filter(name=self.new_group).exists())

    def test_user_cannot_mark_self_as_not_admin(self):
        response = self.client.post(self.self_toggle_url, self.post_data)

        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertInHTML("<p>A superuser cannot change his/her role</p>", html)

        needle = '<ul>'
        needle += '<li>{user_email}</li>'.format(user_email=self.current_user.email)
        needle += '</ul>'
        self.assertInHTML(needle, html)

        # Check user was not added to the group
        self.assertFalse(get_user_model().objects.get(email=self.current_user.email).groups.filter(name=self.new_group).exists())

    def test_before_toggle_user_hook_post(self):
        def hook_func(request, action_type, users, action_class_instance):
            self.assertEqual(action_type, 'assign_role')
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(action_class_instance, UserBulkAction)
            self.assertCountEqual([user.pk for user in self.test_users], [user.pk for user in users])

            return HttpResponse("Overridden!")

        with self.register_hook('before_bulk_action', hook_func):
            response = self.client.post(self.url, self.post_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        for user in self.test_users:
            self.assertFalse(get_user_model().objects.get(email=user.email).groups.filter(name=self.new_group).exists())

    def test_after_toggle_user_hook(self):
        def hook_func(request, action_type, users, action_class_instance):
            self.assertEqual(action_type, 'assign_role')
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(action_class_instance, UserBulkAction)
            self.assertCountEqual([user.pk for user in self.test_users], [user.pk for user in users])

            return HttpResponse("Overridden!")

        with self.register_hook('after_bulk_action', hook_func):
            response = self.client.post(self.url, self.post_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        for user in self.test_users:
            self.assertTrue(get_user_model().objects.get(email=user.email).groups.filter(name=self.new_group).exists())
