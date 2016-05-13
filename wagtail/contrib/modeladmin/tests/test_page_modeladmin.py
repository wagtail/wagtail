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


class TestIndexViewWithExplorablePageVisibility(TestCase, WagtailTestUtils):
    """
    See wagtail.wagtailadmin.tests.test_pages_views.TestExplorablePageVisibility for an explanation about
    how the DB is set up, as many of the same rules will apply to these tests.
    """

    fixtures = ['test_explorable_pages.json']

    def get(self, **params):
        return self.client.get('/admin/tests/eventpage/', params)

    def test_admin_can_see_every_page(self):
        self.assertTrue(self.client.login(username='superman', password='password'))
        response = self.get()

        self.assertEqual(response.status_code, 200)
        # There are 9 EventPages in the test data, and the superuser should see all of them.
        self.assertEqual(response.context['result_count'], 9)

    def test_admin_can_see_any_filtered_page(self):
        self.assertTrue(self.client.login(username='superman', password='password'))
        response = self.get(audience__exact='private')

        self.assertEqual(response.status_code, 200)
        # There is 1 private page, but even though it's on "exmaple.com", the superuser should see it anyway.
        self.assertEqual(response.context['result_count'], 1)

    def test_admin_can_search_for_any_page(self):
        self.assertTrue(self.client.login(username='superman', password='password'))
        response = self.get(q='Welcome!')

        self.assertEqual(response.status_code, 200)
        # Every EventPage's body is "Welcome!", so the superuser should see all of them.
        self.assertEqual(response.context['result_count'], 9)

    def test_user_lists_only_explorable_pages(self):
        self.assertTrue(self.client.login(username='jane', password='password'))
        response = self.get(o='-0')

        self.assertEqual(response.status_code, 200)
        # There are two pages on testserver, which is all that "jane" should see. The "o='-0'" setting we used above
        # sorts them in reverse title order.
        self.assertEqual(response.context['result_count'], 2)
        self.assertEqual(response.context['object_list'][0].title, 'Welcome to testserver!')
        self.assertEqual(response.context['object_list'][1].title, 'About us')

        self.assertTrue(self.client.login(username='mary', password='password'))
        response = self.get()

        self.assertEqual(response.status_code, 200)
        # The user "mary" can view the admin, but has no explorable pages.
        self.assertEqual(response.context['result_count'], 0)

        self.assertTrue(self.client.login(username='sam', password='password'))
        response = self.get(o='0')

        self.assertEqual(response.status_code, 200)
        # The user "sam" should see only the 2 pages in testserver, and example.com's Page 1. His required ancestors
        # should NOT be visible.
        self.assertEqual(response.context['result_count'], 3)
        self.assertEqual(response.context['object_list'][0].title, 'About us')
        self.assertEqual(response.context['object_list'][1].title, 'Page 1')
        self.assertEqual(response.context['object_list'][2].title, 'Welcome to testserver!')

    def test_user_can_see_only_explorable_pages_in_filtered_results(self):
        self.assertTrue(self.client.login(username='jane', password='password'))
        response = self.get(audience__exact='private')

        self.assertEqual(response.status_code, 200)
        # There is 1 private page on "exmaple.com", but jane should not be able to see it.
        self.assertEqual(response.context['result_count'], 0)

        response = self.get(audience__exact='public')

        self.assertEqual(response.status_code, 200)
        # There are 2 public pages on testserver, both of which Jane can see.
        self.assertEqual(response.context['result_count'], 2)

    def test_user_can_see_only_explorable_pages_in_search_results(self):
        self.assertTrue(self.client.login(username='jane', password='password'))
        response = self.get(q='Welcome to example.com')

        self.assertEqual(response.status_code, 200)
        # jane can only see testserver pages, so this search should match nothing.
        self.assertEqual(response.context['result_count'], 0)

        response = self.get(q='Welcome!')

        self.assertEqual(response.status_code, 200)
        # jane can only see the two pages on testserver.
        self.assertEqual(response.context['result_count'], 2)


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
