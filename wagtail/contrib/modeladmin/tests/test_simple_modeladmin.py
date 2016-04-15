from __future__ import absolute_import, unicode_literals

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from wagtail.tests.modeladmintest.models import Author, Book
from wagtail.tests.utils import WagtailTestUtils


class TestIndexView(TestCase, WagtailTestUtils):
    fixtures = ['modeladmintest_test.json']

    def setUp(self):
        self.login()

    def get(self, **params):
        return self.client.get('/admin/modeladmintest/book/', params)

    def test_simple(self):
        response = self.get()

        self.assertEqual(response.status_code, 200)

        # There are four books in the test data
        self.assertEqual(response.context['result_count'], 4)

        # User has add permission
        self.assertEqual(response.context['user_can_create'], True)

    def test_filter(self):
        # Filter by author 1 (JRR Tolkien)
        response = self.get(author__id__exact=1)

        self.assertEqual(response.status_code, 200)

        # JRR Tolkien has two books in the test data
        self.assertEqual(response.context['result_count'], 2)

        for book in response.context['object_list']:
            self.assertEqual(book.author_id, 1)

    def test_search(self):
        response = self.get(q='of')

        self.assertEqual(response.status_code, 200)

        # There are two books where the title contains 'of'
        self.assertEqual(response.context['result_count'], 2)

    def test_ordering(self):
        response = self.get(o='0.1')

        self.assertEqual(response.status_code, 200)

        # There are four books in the test data
        self.assertEqual(response.context['result_count'], 4)

    def test_paging(self):
        # should be corrected to just the first page, as there aren't enough
        # objects to make up more than one page
        response = self.get(p=9)

        self.assertEqual(response.status_code, 200)

        # There are four books in the test data
        self.assertEqual(response.context['result_count'], 4)

        # Should raise a ValueError that gets caught during initialisation
        response = self.get(p='notaninteger')

        self.assertEqual(response.status_code, 200)

        # There are four books in the test data
        self.assertEqual(response.context['result_count'], 4)


class TestCreateView(TestCase, WagtailTestUtils):
    fixtures = ['modeladmintest_test.json']

    def setUp(self):
        self.login()

    def get(self):
        return self.client.get('/admin/modeladmintest/book/create/')

    def post(self, post_data):
        return self.client.post('/admin/modeladmintest/book/create/', post_data)

    def test_simple(self):
        response = self.get()

        self.assertEqual(response.status_code, 200)

    def test_create(self):
        response = self.post({
            'title': "George's Marvellous Medicine",
            'author': 2,
        })
        # Should redirect back to index
        self.assertRedirects(response, '/admin/modeladmintest/book/')

        # Check that the book was created
        self.assertEqual(Book.objects.filter(title="George's Marvellous Medicine").count(), 1)

    def test_post_invalid(self):
        initial_book_count = Book.objects.count()

        response = self.post({
            'title': '',
            'author': 2,
        })
        final_book_count = Book.objects.count()

        self.assertEqual(response.status_code, 200)
        # Check that the book was not created
        self.assertEqual(initial_book_count, final_book_count)

        # Check that a form error was raised
        self.assertFormError(response, 'form', 'title', "This field is required.")


class TestInspectView(TestCase, WagtailTestUtils):
    fixtures = ['modeladmintest_test.json']

    def setUp(self):
        self.login()

    def get_for_author(self, author_id):
        return self.client.get('/admin/modeladmintest/author/inspect/%d/' % author_id)

    def get_for_book(self, book_id):
        return self.client.get('/admin/modeladmintest/book/inspect/%d/' % book_id)

    def author_test_simple(self):
        response = self.get_for_author(1)
        self.assertEqual(response.status_code, 200)

    def author_test_name_present(self):
        """
        The author name should appear twice. Once in the header, and once
        more in the field listing
        """
        response = self.get_for_author(1)
        self.assertContains(response, 'J. R. R. Tolkien', 2)

    def author_test_dob_not_present(self):
        """
        The date of birth shouldn't appear, because the field wasn't included
        in the `inspect_view_fields` list
        """
        response = self.get_for_author(1)
        self.assertNotContains(response, '1892', 2)

    def book_test_simple(self):
        response = self.get_for_book(1)
        self.assertEqual(response.status_code, 200)

    def book_test_title_present(self):
        """
        The book title should appear once only, in the header, as 'title'
        was added to the `inspect_view_fields_ignore` list
        """
        response = self.get_for_book(1)
        self.assertContains(response, 'The Lord of the Rings', 1)

    def book_test_author_present(self):
        """
        The author name should appear, because 'author' is not in
        `inspect_view_fields_ignore` and should be returned by the
        `get_inspect_view_fields` method.
        """
        response = self.get_for_book(1)
        self.assertContains(response, 'J. R. R. Tolkien', 1)

    def test_non_existent(self):
        response = self.get_for_book(100)
        self.assertEqual(response.status_code, 404)


class TestEditView(TestCase, WagtailTestUtils):
    fixtures = ['modeladmintest_test.json']

    def setUp(self):
        self.login()

    def get(self, book_id):
        return self.client.get('/admin/modeladmintest/book/edit/%d/' % book_id)

    def post(self, book_id, post_data):
        return self.client.post('/admin/modeladmintest/book/edit/%d/' % book_id, post_data)

    def test_simple(self):
        response = self.get(1)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'The Lord of the Rings')

    def test_non_existent(self):
        response = self.get(100)

        self.assertEqual(response.status_code, 404)

    def test_edit(self):
        response = self.post(1, {
            'title': 'The Lady of the Rings',
            'author': 1,
        })

        # Should redirect back to index
        self.assertRedirects(response, '/admin/modeladmintest/book/')

        # Check that the book was updated
        self.assertEqual(Book.objects.get(id=1).title, 'The Lady of the Rings')

    def test_post_invalid(self):
        response = self.post(1, {
            'title': '',
            'author': 1,
        })

        self.assertEqual(response.status_code, 200)

        # Check that the title was not updated
        self.assertEqual(Book.objects.get(id=1).title, 'The Lord of the Rings')

        # Check that a form error was raised
        self.assertFormError(response, 'form', 'title', "This field is required.")


class TestPageSpecificViews(TestCase, WagtailTestUtils):
    fixtures = ['modeladmintest_test.json']
    expected_status_code = 404

    def setUp(self):
        self.login()

    def test_choose_parent(self):
        response = self.client.get('/admin/modeladmintest/book/choose_parent/')
        self.assertEqual(response.status_code, self.expected_status_code)


class TestConfirmDeleteView(TestCase, WagtailTestUtils):
    fixtures = ['modeladmintest_test.json']

    def setUp(self):
        self.login()

    def get(self, book_id):
        return self.client.get('/admin/modeladmintest/book/delete/%d/' % book_id)

    def post(self, book_id):
        return self.client.post('/admin/modeladmintest/book/delete/%d/' % book_id)

    def test_simple(self):
        response = self.get(1)

        self.assertEqual(response.status_code, 200)

    def test_non_existent(self):
        response = self.get(100)

        self.assertEqual(response.status_code, 404)

    def test_post(self):
        response = self.post(1)

        # User redirected to index
        self.assertRedirects(response, '/admin/modeladmintest/book/')

        # Book deleted
        self.assertFalse(Book.objects.filter(id=1).exists())


class TestDeleteViewWithProtectedRelation(TestCase, WagtailTestUtils):
    fixtures = ['modeladmintest_test.json']

    def setUp(self):
        self.login()

    def get(self, author_id):
        return self.client.get('/admin/modeladmintest/author/delete/%d/' % author_id)

    def post(self, author_id):
        return self.client.post('/admin/modeladmintest/author/delete/%d/' % author_id)

    def test_get_with_dependent_object(self):
        response = self.get(1)

        self.assertEqual(response.status_code, 200)

    def test_get_without_dependent_object(self):
        response = self.get(4)

        self.assertEqual(response.status_code, 200)

    def test_post_with_dependent_object(self):
        response = self.post(1)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "'J. R. R. Tolkien' is currently referenced by other objects"
        )

        # Author not deleted
        self.assertTrue(Author.objects.filter(id=1).exists())

    def test_post_without_dependent_object(self):
        response = self.post(4)

        # User redirected to index
        self.assertRedirects(response, '/admin/modeladmintest/author/')

        # Author deleted
        self.assertFalse(Author.objects.filter(id=4).exists())


class TestEditorAccess(TestCase):
    fixtures = ['modeladmintest_test.json']
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
        response = self.client.get('/admin/modeladmintest/book/')
        self.assertEqual(response.status_code, self.expected_status_code)

    def test_inpspect_permitted(self):
        response = self.client.get('/admin/modeladmintest/book/inspect/2/')
        self.assertEqual(response.status_code, self.expected_status_code)

    def test_create_permitted(self):
        response = self.client.get('/admin/modeladmintest/book/create/')
        self.assertEqual(response.status_code, self.expected_status_code)

    def test_edit_permitted(self):
        response = self.client.get('/admin/modeladmintest/book/edit/2/')
        self.assertEqual(response.status_code, self.expected_status_code)

    def test_delete_get_permitted(self):
        response = self.client.get('/admin/modeladmintest/book/delete/2/')
        self.assertEqual(response.status_code, self.expected_status_code)

    def test_delete_post_permitted(self):
        response = self.client.post('/admin/modeladmintest/book/delete/2/')
        self.assertEqual(response.status_code, self.expected_status_code)
