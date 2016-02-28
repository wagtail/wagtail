from django.test import TestCase

from wagtail.tests.utils import WagtailTestUtils
from wagtail.tests.modeladmintest.models import Book


class TestIndexView(TestCase, WagtailTestUtils):
    fixtures = ['modeladmintest_test.json']

    def setUp(self):
        self.login()

    def get(self, **params):
        return self.client.get('/admin/modeladmin/modeladmintest/book/', params)

    def test_simple(self):
        response = self.get()

        self.assertEqual(response.status_code, 200)

        # There are four books in the test data
        self.assertEqual(response.context['result_count'], 4)

        # User has add permission
        self.assertEqual(response.context['has_add_permission'], True)

    def test_filter(self):
        # Filter by author 1 (JRR Tolkien)
        response = self.get(author__id__exact=1)

        self.assertEqual(response.status_code, 200)

        # JRR Tolkien has two books in the test data
        self.assertEqual(response.context['result_count'], 2)

        for book in response.context['object_list']:
            self.assertEqual(book.author_id, 1)


class TestCreateView(TestCase, WagtailTestUtils):
    fixtures = ['modeladmintest_test.json']

    def setUp(self):
        self.login()

    def get(self):
        return self.client.get('/admin/modeladmin/modeladmintest/book/create/')

    def test_simple(self):
        response = self.get()

        self.assertEqual(response.status_code, 200)


class TestEditView(TestCase, WagtailTestUtils):
    fixtures = ['modeladmintest_test.json']

    def setUp(self):
        self.login()

    def get(self, book_id):
        return self.client.get('/admin/modeladmin/modeladmintest/book/edit/%d/' % book_id)

    def test_simple(self):
        response = self.get(1)

        self.assertEqual(response.status_code, 200)

    def test_non_existent(self):
        response = self.get(100)

        self.assertEqual(response.status_code, 404)


class TestConfirmDeleteView(TestCase, WagtailTestUtils):
    fixtures = ['modeladmintest_test.json']

    def setUp(self):
        self.login()

    def get(self, book_id):
        return self.client.get('/admin/modeladmin/modeladmintest/book/confirm_delete/%d/' % book_id)

    def post(self, book_id):
        return self.client.post('/admin/modeladmin/modeladmintest/book/confirm_delete/%d/' % book_id, {
            'foo': 'bar'
        })

    def test_simple(self):
        response = self.get(1)

        self.assertEqual(response.status_code, 200)

    def test_non_existent(self):
        response = self.get(100)

        self.assertEqual(response.status_code, 404)

    def test_post(self):
        response = self.post(1)

        # User redirected to index
        self.assertRedirects(response, '/admin/modeladmin/modeladmintest/book/')

        # Book deleted
        self.assertFalse(Book.objects.filter(id=1).exists())
