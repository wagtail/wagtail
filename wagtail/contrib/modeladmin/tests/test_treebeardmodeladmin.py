from django.test import TestCase
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

from wagtail.tests.utils import WagtailTestUtils
from wagtail.tests.modeladmintest.models import TreebeardCategory


class TestIndexView(TestCase, WagtailTestUtils):
    fixtures = ['treebeardmodeladmin_test.json']

    def setUp(self):
        self.login()

    def get(self, **params):
        return self.client.get('/admin/modeladmin/modeladmintest/treebeardcategory/', params)

    def test_simple(self):
        response = self.get()

        self.assertEqual(response.status_code, 200)

        # There are fourteen categories in the test data
        self.assertEqual(response.context['result_count'], 14)

        # User has add permission
        self.assertEqual(response.context['has_add_permission'], True)

    def test_filter(self):
        # Get only root-level categories
        response = self.get(depth__exact=1)

        self.assertEqual(response.status_code, 200)

        # There are only 3 root-level categories in the test data
        self.assertEqual(response.context['result_count'], 3)

        for obj in response.context['object_list']:
            self.assertEqual(obj.depth, 1)


class TestCreateView(TestCase, WagtailTestUtils):
    fixtures = ['treebeardmodeladmin_test.json']

    def setUp(self):
        self.login()

    def get(self, **params):
        return self.client.get('/admin/modeladmin/modeladmintest/treebeardcategory/create/', params)

    def test_add_root(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)

    def test_add_child(self):
        response = self.get(parent_id=14)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context['parent_obj'].pk, 14)

    def test_add_sibling(self):
        response = self.get(sibling_id=12)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context['sibling_obj'].pk, 12)


class TestEditView(TestCase, WagtailTestUtils):
    fixtures = ['treebeardmodeladmin_test.json']

    def setUp(self):
        self.login()

    def get(self, obj_id):
        return self.client.get('/admin/modeladmin/modeladmintest/treebeardcategory/edit/%d/' % obj_id)

    def test_simple(self):
        response = self.get(1)

        self.assertEqual(response.status_code, 200)

    def test_non_existent(self):
        response = self.get(100)

        self.assertEqual(response.status_code, 404)


class TestMoveView(TestCase, WagtailTestUtils):
    fixtures = ['treebeardmodeladmin_test.json']

    def setUp(self):
        self.login()

    def get(self, obj_id):
        return self.client.get('/admin/modeladmin/modeladmintest/treebeardcategory/move/%d/' % obj_id)

    def test_simple(self):
        response = self.get(1)

        self.assertEqual(response.status_code, 200)

    def test_non_existent(self):
        response = self.get(100)

        self.assertEqual(response.status_code, 404)


class TestConfirmDeleteView(TestCase, WagtailTestUtils):
    fixtures = ['treebeardmodeladmin_test.json']

    def setUp(self):
        self.login()

    def get(self, obj_id):
        return self.client.get('/admin/modeladmin/modeladmintest/treebeardcategory/confirm_delete/%d/' % obj_id)

    def post(self, obj_id):
        return self.client.post('/admin/modeladmin/modeladmintest/treebeardcategory/confirm_delete/%d/' % obj_id)

    def test_simple(self):
        # In the test data, 12 is a leaf, so should be deletable
        response = self.get(12)

        self.assertEqual(response.status_code, 200)

    def test_non_existent(self):
        # In the test data, 100 doesn't exist
        response = self.get(100)

        self.assertEqual(response.status_code, 404)

    def test_post(self):
        response = self.post(12)

        # User redirected to index
        self.assertRedirects(response, '/admin/modeladmin/modeladmintest/treebeardcategory/')

        # Category has been deleted
        self.assertFalse(TreebeardCategory.objects.filter(id=12).exists())

    def test_not_permitted(self):
        # In the test data, 1 has sub-categories, so shouldn't be deletable
        response = self.get(1)

        self.assertEqual(response.status_code, 403)

    def test_post_not_permitted(self):
        # In the test data, 1 has sub-categories, so shouldn't be deletable
        response = self.get(1)

        self.assertEqual(response.status_code, 403)


class TestEditorAccess(TestCase):
    fixtures = ['treebeardmodeladmin_test.json']
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

    def test_index_permitted(self):
        response = self.client.get('/admin/modeladmin/modeladmintest/treebeardcategory/')
        self.assertEqual(response.status_code, self.expected_status_code)

    def test_create_permitted(self):
        response = self.client.get('/admin/modeladmin/modeladmintest/treebeardcategory/create/')
        self.assertEqual(response.status_code, self.expected_status_code)

    def test_edit_permitted(self):
        response = self.client.get('/admin/modeladmin/modeladmintest/treebeardcategory/edit/2/')
        self.assertEqual(response.status_code, self.expected_status_code)

    def test_delete_get_permitted(self):
        response = self.client.get('/admin/modeladmin/modeladmintest/treebeardcategory/confirm_delete/11/')
        self.assertEqual(response.status_code, self.expected_status_code)

    def test_delete_post_permitted(self):
        response = self.client.post('/admin/modeladmin/modeladmintest/treebeardcategory/confirm_delete/11/')
        self.assertEqual(response.status_code, self.expected_status_code)
