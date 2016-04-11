from django.test import TestCase
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

from wagtail.tests.utils import WagtailTestUtils


class TestIndexView(TestCase, WagtailTestUtils):
    fixtures = ['test_specific.json']

    def setUp(self):
        self.login()

    def get(self, **params):
        return self.client.get('/admin/tests/eventpage/', params)

    def test_simple(self):
        response = self.get()

        self.assertEqual(response.status_code, 200)

        # There are four event pages in the test data
        self.assertEqual(response.context['result_count'], 4)

        # User has add permission
        self.assertEqual(response.context['user_can_create'], True)

    def test_filter(self):
        # Filter by audience
        response = self.get(audience__exact='public')

        self.assertEqual(response.status_code, 200)

        # Only three of the event page in the test data are 'public'
        self.assertEqual(response.context['result_count'], 3)

        for eventpage in response.context['object_list']:
            self.assertEqual(eventpage.audience, 'public')


class TestCreateView(TestCase, WagtailTestUtils):
    fixtures = ['test_specific.json']

    def setUp(self):
        self.login()

    def get(self):
        return self.client.get('/admin/tests/eventpage/create/')

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 302)


class TestInspectView(TestCase, WagtailTestUtils):
    fixtures = ['test_specific.json']

    def setUp(self):
        self.login()

    def get(self, id):
        return self.client.get('/admin/tests/eventpage/inspect/%d/' % id)

    def test_simple(self):
        response = self.get(4)
        self.assertEqual(response.status_code, 200)

    def test_title_present(self):
        """
        The page title should appear twice. Once in the header, and once
        more in the field listing
        """
        response = self.get(4)
        self.assertContains(response, 'Christmas', 2)

    def test_location_present(self):
        """
        The location should appear once, in the field listing
        """
        response = self.get(4)
        self.assertContains(response, 'The North Pole', 1)

    def test_non_existent(self):
        response = self.get(100)
        self.assertEqual(response.status_code, 404)


class TestEditView(TestCase, WagtailTestUtils):
    fixtures = ['test_specific.json']

    def setUp(self):
        self.login()

    def get(self, obj_id):
        return self.client.get('/admin/tests/eventpage/edit/%d/' % obj_id)

    def test_simple(self):
        response = self.get(4)

        self.assertEqual(response.status_code, 302)

    def test_non_existent(self):
        response = self.get(100)

        self.assertEqual(response.status_code, 404)


class TestChooseParentView(TestCase, WagtailTestUtils):
    fixtures = ['test_specific.json']

    def setUp(self):
        self.login()

    def get(self):
        return self.client.get('/admin/tests/eventpage/choose_parent/')

    def test_simple(self):
        response = self.get()

        self.assertEqual(response.status_code, 200)


class TestEditorAccess(TestCase):
    fixtures = ['test_specific.json']
    expected_status_code = 403

    def login(self):
        # Create a user
        user = get_user_model().objects._create_user(username='test2', email='test2@email.com', password='password', is_staff=True, is_superuser=False)
        user.groups.add(Group.objects.get(pk=2))
        # Login
        self.client.login(username='test2', password='password')
        return user

    def setUp(self):
        self.login()

    def test_delete_permitted(self):
        response = self.client.get('/admin/tests/eventpage/delete/4/')
        self.assertEqual(response.status_code, self.expected_status_code)


class TestModeratorAccess(TestCase):
    fixtures = ['test_specific.json']
    expected_status_code = 302

    def login(self):
        # Create a user
        user = get_user_model().objects._create_user(username='test3', email='test3@email.com', password='password', is_staff=True, is_superuser=False)
        user.groups.add(Group.objects.get(pk=1))
        # Login
        self.client.login(username='test2', password='password')
        return user

    def setUp(self):
        self.login()

    def test_delete_permitted(self):
        response = self.client.get('/admin/tests/eventpage/delete/4/')
        self.assertEqual(response.status_code, self.expected_status_code)
