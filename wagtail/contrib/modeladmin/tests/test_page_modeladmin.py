from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase

from wagtail.core.models import GroupPagePermission, Page
from wagtail.tests.testapp.models import BusinessIndex, EventCategory, EventPage
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


class TestExcludeFromExplorer(TestCase, WagtailTestUtils):
    fixtures = ['modeladmintest_test.json']

    def setUp(self):
        self.login()

    def test_attribute_effects_explorer(self):
        # The two VenuePages should appear in the venuepage list
        response = self.client.get('/admin/modeladmintest/venuepage/')
        self.assertContains(response, "Santa&#39;s Grotto")
        self.assertContains(response, "Santa&#39;s Workshop")

        # But when viewing the children of 'Christmas' event in explorer
        response = self.client.get('/admin/pages/4/')
        self.assertNotContains(response, "Santa&#39;s Grotto")
        self.assertNotContains(response, "Santa&#39;s Workshop")

        # But the other test page should...
        self.assertContains(response, "Claim your free present!")


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
        The page title should appear three times. Once in the header, and two times
        in the field listing (as the actual title and as the draft title)
        """
        response = self.get(4)
        self.assertContains(response, 'Christmas', 3)

    def test_manytomany_output(self):
        """
        Because ManyToMany fields are output InspectView by default, the
        `categories` for the event should output as a comma separated list
        once populated.
        """
        eventpage = EventPage.objects.get(pk=4)
        free_category = EventCategory.objects.create(name='Free')
        child_friendly_category = EventCategory.objects.create(name='Child-friendly')
        eventpage.categories = (free_category, child_friendly_category)
        eventpage.save()
        response = self.get(4)
        self.assertContains(response, '<dd>Free, Child-friendly</dd>', html=True)

    def test_false_values_displayed(self):
        """
        Boolean fields with False values should display False, rather than the
        value of `get_empty_value_display()`. For this page, those should be
        `locked`, `expired` and `has_unpublished_changes`
        """
        response = self.get(4)
        self.assertContains(response, '<dd>False</dd>', count=3, html=True)

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
        business_index = BusinessIndex(
            title='Public Business Index',
            draft_title='Public Business Index',
        )
        homepage.add_child(instance=business_index)

        another_business_index = BusinessIndex(
            title='Another Business Index',
            draft_title='Another Business Index',
        )
        homepage.add_child(instance=another_business_index)

        secret_business_index = BusinessIndex(
            title='Private Business Index',
            draft_title='Private Business Index',
        )
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


class TestHeaderBreadcrumbs(TestCase, WagtailTestUtils):
    """
        Test that the <ul class="breadcrumbs">... is inserted within the
        <header> tag for potential future regression.
        See https://github.com/wagtail/wagtail/issues/3889
    """
    fixtures = ['test_specific.json']

    def setUp(self):
        self.login()

    def test_choose_parent_page(self):
        response = self.client.get('/admin/tests/eventpage/choose_parent/')

        # check correct templates were used
        self.assertTemplateUsed(response, 'modeladmin/includes/breadcrumb.html')
        self.assertTemplateUsed(response, 'wagtailadmin/shared/header.html')

        # check that home breadcrumb link exists
        self.assertContains(response, '<li class="home"><a href="/admin/" class="icon icon-home text-replace">Home</a></li>', html=True)

        # check that the breadcrumbs are after the header opening tag
        content_str = str(response.content)
        position_of_header = content_str.index('<header')  # intentionally not closing tag
        position_of_breadcrumbs = content_str.index('<ul class="breadcrumb">')
        self.assertLess(position_of_header, position_of_breadcrumbs)

    def test_choose_inspect_page(self):
        response = self.client.get('/admin/tests/eventpage/inspect/4/')

        # check correct templates were used
        self.assertTemplateUsed(response, 'modeladmin/includes/breadcrumb.html')
        self.assertTemplateUsed(response, 'wagtailadmin/shared/header.html')

        # check that home breadcrumb link exists
        self.assertContains(response, '<li class="home"><a href="/admin/" class="icon icon-home text-replace">Home</a></li>', html=True)

        # check that the breadcrumbs are after the header opening tag
        content_str = str(response.content)
        position_of_header = content_str.index('<header')  # intentionally not closing tag
        position_of_breadcrumbs = content_str.index('<ul class="breadcrumb">')
        self.assertLess(position_of_header, position_of_breadcrumbs)
