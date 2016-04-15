from __future__ import absolute_import, unicode_literals

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase

from wagtail.tests.testapp.models import BusinessIndex
from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailcore.models import GroupPagePermission, Page


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

    def test_search(self):
        response = self.get(q='Someone')

        self.assertEqual(response.status_code, 200)

        # There are two eventpage's where the title contains 'Someone'
        self.assertEqual(response.context['result_count'], 1)

    def test_ordering(self):
        response = self.get(o='0.1')

        self.assertEqual(response.status_code, 200)

        # There should still be four results
        self.assertEqual(response.context['result_count'], 4)


class TestCreateView(TestCase, WagtailTestUtils):
    fixtures = ['test_specific.json']

    def setUp(self):
        self.login()

    def test_redirect_to_choose_parent(self):
        # When more than one possible parent page exists, redirect to choose_parent
        response = self.client.get('/admin/tests/eventpage/create/')
        self.assertRedirects(response, '/admin/tests/eventpage/choose_parent/')

    def test_one_parent_exists(self):
        # Create a BusinessIndex page that BusinessChild can exist under
        homepage = Page.objects.get(url_path='/home/')
        business_index = BusinessIndex(title='Business Index')
        homepage.add_child(instance=business_index)

        # When one possible parent page exists, redirect straight to the page create view
        response = self.client.get('/admin/tests/businesschild/create/')

        expected_path = '/admin/pages/add/tests/businesschild/%d/' % business_index.pk
        expected_next_path = '/admin/tests/businesschild/'
        self.assertRedirects(response, '%s?next=%s' % (expected_path, expected_next_path))


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

        expected_path = '/admin/pages/4/edit/'
        expected_next_path = '/admin/tests/eventpage/'
        self.assertRedirects(response, '%s?next=%s' % (expected_path, expected_next_path))

    def test_non_existent(self):
        response = self.get(100)

        self.assertEqual(response.status_code, 404)


class TestDeleteView(TestCase, WagtailTestUtils):
    fixtures = ['test_specific.json']

    def setUp(self):
        self.login()

    def get(self, obj_id):
        return self.client.get('/admin/tests/eventpage/delete/%d/' % obj_id)

    def test_simple(self):
        response = self.get(4)

        expected_path = '/admin/pages/4/delete/'
        expected_next_path = '/admin/tests/eventpage/'
        self.assertRedirects(response, '%s?next=%s' % (expected_path, expected_next_path))


class TestChooseParentView(TestCase, WagtailTestUtils):
    fixtures = ['test_specific.json']

    def setUp(self):
        self.login()

    def test_simple(self):
        response = self.client.get('/admin/tests/eventpage/choose_parent/')

        self.assertEqual(response.status_code, 200)

    def test_no_parent_exists(self):
        response = self.client.get('/admin/tests/businesschild/choose_parent/')

        self.assertEqual(response.status_code, 403)

    def test_post(self):
        response = self.client.post('/admin/tests/eventpage/choose_parent/', {
            'parent_page': 2,
        })

        expected_path = '/admin/pages/add/tests/eventpage/2/'
        expected_next_path = '/admin/tests/eventpage/'
        self.assertRedirects(response, '%s?next=%s' % (expected_path, expected_next_path))


class TestChooseParentViewForNonSuperuser(TestCase, WagtailTestUtils):
    fixtures = ['test_specific.json']

    def setUp(self):
        homepage = Page.objects.get(url_path='/home/')
        business_index = BusinessIndex(title='Public Business Index')
        homepage.add_child(instance=business_index)

        another_business_index = BusinessIndex(title='Another Business Index')
        homepage.add_child(instance=another_business_index)

        secret_business_index = BusinessIndex(title='Private Business Index')
        homepage.add_child(instance=secret_business_index)

        business_editors = Group.objects.create(name='Business editors')
        business_editors.permissions.add(Permission.objects.get(codename='access_admin'))
        GroupPagePermission.objects.create(
            group=business_editors,
            page=business_index,
            permission_type='add'
        )
        GroupPagePermission.objects.create(
            group=business_editors,
            page=another_business_index,
            permission_type='add'
        )

        user = get_user_model().objects._create_user(username='test2', email='test2@email.com', password='password', is_staff=True, is_superuser=False)
        user.groups.add(business_editors)
        # Login
        self.client.login(username='test2', password='password')

    def test_simple(self):
        response = self.client.get('/admin/tests/businesschild/choose_parent/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Public Business Index')
        self.assertNotContains(response, 'Private Business Index')


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
