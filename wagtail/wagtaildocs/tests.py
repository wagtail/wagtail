from django.test import TestCase
from wagtail.wagtaildocs import models
from wagtail.wagtailcore.models import Site
from django.contrib.auth.models import User, Group, Permission
from django.core.urlresolvers import reverse

# TODO: Test serve view


class TestDocumentPermissions(TestCase):
    def setUp(self):
        # Create some user accounts for testing permissions
        self.user = User.objects.create_user(username='user', email='user@email.com', password='password')
        self.owner = User.objects.create_user(username='owner', email='owner@email.com', password='password')
        self.editor = User.objects.create_user(username='editor', email='editor@email.com', password='password')
        self.editor.groups.add(Group.objects.get(name='Editors'))
        self.administrator = User.objects.create_superuser(username='administrator', email='administrator@email.com', password='password')

        # Owner user must have the add_document permission
        self.owner.user_permissions.add(Permission.objects.get(codename='add_document'))

        # Create a document for running tests on
        self.document = models.Document.objects.create(title="Test document", uploaded_by_user=self.owner)

    def test_administrator_can_edit(self):
        self.assertTrue(self.document.is_editable_by_user(self.administrator))

    def test_editor_can_edit(self):
        self.assertTrue(self.document.is_editable_by_user(self.editor))

    def test_owner_can_edit(self):
        self.assertTrue(self.document.is_editable_by_user(self.owner))

    def test_user_cant_edit(self):
        self.assertFalse(self.document.is_editable_by_user(self.user))


## ===== ADMIN VIEWS =====

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
        return self.client.get(reverse('wagtaildocs_index'), params, HTTP_HOST=get_default_host())

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
        return self.client.get(reverse('wagtaildocs_add_document'), params, HTTP_HOST=get_default_host())

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)


class TestDocumentEditView(TestCase):
    def setUp(self):
        login(self.client)

        # Create a document to edit
        self.document = models.Document.objects.create(title="Test document")

    def get(self, params={}):
        return self.client.get(reverse('wagtaildocs_edit_document', args=(self.document.id,)), params, HTTP_HOST=get_default_host())

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)


class TestDocumentDeleteView(TestCase):
    def setUp(self):
        login(self.client)

        # Create a document to delete
        self.document = models.Document.objects.create(title="Test document")

    def get(self, params={}):
        return self.client.get(reverse('wagtaildocs_delete_document', args=(self.document.id,)), params, HTTP_HOST=get_default_host())

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)


class TestDocumentChooserView(TestCase):
    def setUp(self):
        login(self.client)

    def get(self, params={}):
        return self.client.get(reverse('wagtaildocs_chooser'), params, HTTP_HOST=get_default_host())

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
        return self.client.get(reverse('wagtaildocs_document_chosen', args=(self.document.id,)), params, HTTP_HOST=get_default_host())

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)


class TestDocumentChooserUploadView(TestCase):
    def setUp(self):
        login(self.client)

    def get(self, params={}):
        return self.client.get(reverse('wagtaildocs_chooser_upload'), params, HTTP_HOST=get_default_host())

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)
