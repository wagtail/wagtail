from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailusers.models import UserProfile


class TestUserIndexView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailusers_index'), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailusers/index.html')

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
        return self.client.get(reverse('wagtailusers_create'), params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailusers_create'), post_data)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailusers/create.html')

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
        self.assertRedirects(response, reverse('wagtailusers_index'))

        # Check that the user was created
        users = User.objects.filter(username='testuser')
        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first().email, 'test@user.com')


class TestUserEditView(TestCase, WagtailTestUtils):
    def setUp(self):
        # Create a user to edit
        self.test_user = User.objects.create_user(username='testuser', email='testuser@email.com', password='password')

        # Login
        self.login()

    def get(self, params={}, user_id=None):
        return self.client.get(reverse('wagtailusers_edit', args=(user_id or self.test_user.id, )), params)
 
    def post(self, post_data={}, user_id=None):
        return self.client.post(reverse('wagtailusers_edit', args=(user_id or self.test_user.id, )), post_data)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailusers/edit.html')

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
        self.assertRedirects(response, reverse('wagtailusers_index'))

        # Check that the user was edited
        user = User.objects.get(id=self.test_user.id)
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
        self.test_user = User.objects.create_user(username='testuser', email='testuser@email.com', password='password')

    def test_user_created_without_profile(self):
        self.assertEqual(UserProfile.objects.filter(user=self.test_user).count(), 0)
        with self.assertRaises(UserProfile.DoesNotExist):
            self.test_user.userprofile

    def test_user_profile_created_when_method_called(self):
        self.assertIsInstance(UserProfile.get_for_user(self.test_user), UserProfile)
        # and get it from the db too
        self.assertEqual(UserProfile.objects.filter(user=self.test_user).count(), 1)
