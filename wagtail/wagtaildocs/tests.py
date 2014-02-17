from django.test import TestCase
from wagtail.wagtaildocs import models


class TestDocument(TestCase):
    pass # TODO: Write some tests


from wagtail.wagtailcore.models import Site
from django.contrib.auth.models import User


def get_default_host():
    return Site.objects.filter(is_default_site=True).first().root_url.split('://')[1]


def login(client):
    # Create a user
    User.objects.create_superuser(username='test', email='test@email.com', password='password')

    # Login
    client.login(username='test', password='password')


class TestDocumentIndexView(TestCase):
    def setUp(self):
        login(self.client)

    def get(self, params={}):
        return self.client.get('/admin/documents/', params, HTTP_HOST=get_default_host())

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_search(self):
        response = self.get({'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_query'], "Hello")

    def test_pagination(self):
        pages = ['0', '1', '-1', '9999', 'Not a page']
        for page in pages:
            response = self.get({'p': page})
            self.assertEqual(response.status_code, 200)

    def test_ordering(self):
        orderings = ['title', '-created_at']
        for ordering in orderings:
            response = self.get({'ordering': ordering})
            self.assertEqual(response.status_code, 200)


class TestDocumentAddView(TestCase):
    def setUp(self):
        login(self.client)

    def get(self, params={}):
        return self.client.get('/admin/documents/add/', params, HTTP_HOST=get_default_host())

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)


class TestDocumentEditView(TestCase):
    def setUp(self):
        login(self.client)

        # Create a document to edit
        self.document = models.Document.objects.create(title="Test document")

    def get(self, params={}):
        return self.client.get('/admin/documents/edit/' + str(self.document.id) + '/', params, HTTP_HOST=get_default_host())

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)


class TestDocumentDeleteView(TestCase):
    def setUp(self):
        login(self.client)

        # Create a document to delete
        self.document = models.Document.objects.create(title="Test document")

    def get(self, params={}):
        return self.client.get('/admin/documents/delete/' + str(self.document.id) + '/', params, HTTP_HOST=get_default_host())

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)


class TestDocumentChooserView(TestCase):
    def setUp(self):
        login(self.client)

    def get(self, params={}):
        return self.client.get('/admin/documents/chooser/', params, HTTP_HOST=get_default_host())

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_search(self):
        response = self.get({'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_query'], "Hello")

    def test_pagination(self):
        pages = ['0', '1', '-1', '9999', 'Not a page']
        for page in pages:
            response = self.get({'p': page})
            self.assertEqual(response.status_code, 200)


class TestDocumentChooserChosenView(TestCase):
    def setUp(self):
        login(self.client)

        # Create a document to choose
        self.document = models.Document.objects.create(title="Test document")

    def get(self, params={}):
        return self.client.get('/admin/documents/chooser/' + str(self.document.id) + '/', params, HTTP_HOST=get_default_host())

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)


class TestDocumentChooserUploadView(TestCase):
    def setUp(self):
        login(self.client)

    def get(self, params={}):
        return self.client.get('/admin/documents/chooser/upload/', params, HTTP_HOST=get_default_host())

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)
