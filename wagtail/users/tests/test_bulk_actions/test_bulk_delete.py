from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse
from django.test import TestCase
from django.urls import reverse

from wagtail.tests.utils import WagtailTestUtils
from wagtail.users.views.bulk_actions.user_bulk_action import UserBulkAction


User = get_user_model()


class TestUserDeleteView(TestCase, WagtailTestUtils):
    def setUp(self):
        # create a set of test users
        self.test_users = [
            self.create_user(
                username=f'testuser-{i}',
                email=f'testuser{i}@email.com',
                password=f'password-{i}'
            ) for i in range(1, 6)
        ]
        # also create a superuser to delete
        self.superuser = self.create_superuser(
            username='testsuperuser',
            email='testsuperuser@email.com',
            password='password'
        )
        self.current_user = self.login()
        self.url = reverse('wagtail_bulk_action', args=(User._meta.app_label, User._meta.model_name, 'delete',)) + '?'
        for user in self.test_users:
            self.url += f'id={user.pk}&'

        self.self_delete_url = self.url + f'id={self.current_user.pk}'
        self.superuser_delete_url = self.url + f'id={self.superuser.pk}'

    def test_simple(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailusers/bulk_actions/confirm_bulk_delete.html')

    def test_bulk_delete(self):
        response = self.client.post(self.url)

        # Should redirect back to index
        self.assertEqual(response.status_code, 302)

        # Check that the users were deleted
        for user in self.test_users:
            self.assertFalse(User.objects.filter(email=user.email).exists())

    def test_user_cannot_delete_self(self):
        response = self.client.get(self.self_delete_url)

        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertInHTML("<p>You don't have permission to delete this user</p>", html)

        needle = '<ul>'
        needle += '<li>{user_email}</li>'.format(user_email=self.current_user.email)
        needle += '</ul>'
        self.assertInHTML(needle, html)

        response = self.client.post(self.self_delete_url)

        # Check user was not deleted
        self.assertTrue(User.objects.filter(pk=self.current_user.pk).exists())

    def test_user_can_delete_other_superuser(self):
        response = self.client.get(self.superuser_delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailusers/bulk_actions/confirm_bulk_delete.html')

        response = self.client.post(self.superuser_delete_url)
        # Should redirect back to index
        self.assertEqual(response.status_code, 302)

        # Check that the user was deleted
        users = User.objects.filter(email=self.superuser.email)
        self.assertEqual(users.count(), 0)

    def test_before_delete_user_hook_post(self):
        def hook_func(request, action_type, users, action_class_instance):
            self.assertEqual(action_type, 'delete')
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(action_class_instance, UserBulkAction)
            self.assertCountEqual([user.pk for user in self.test_users], [user.pk for user in users])

            return HttpResponse("Overridden!")

        with self.register_hook('before_bulk_action', hook_func):
            response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        for user in self.test_users:
            self.assertTrue(User.objects.filter(email=user.email).exists())

    def test_after_delete_user_hook(self):
        def hook_func(request, action_type, users, action_class_instance):
            self.assertEqual(action_type, 'delete')
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(action_class_instance, UserBulkAction)

            return HttpResponse("Overridden!")

        with self.register_hook('after_bulk_action', hook_func):
            response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        for user in self.test_users:
            self.assertFalse(User.objects.filter(email=user.email).exists())
