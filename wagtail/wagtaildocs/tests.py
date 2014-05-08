from django.test import TestCase
from wagtail.wagtaildocs import models
from wagtail.tests.utils import login
from django.contrib.auth.models import User, Group, Permission
from django.core.urlresolvers import reverse
from django.core.files.base import ContentFile

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


class TestDocumentIndexView(TestCase):
    def setUp(self):
        login(self.client)

    def get(self, params={}):
        return self.client.get(reverse('wagtaildocs_index'), params)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_search(self):
        response = self.get({'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

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
        return self.client.get(reverse('wagtaildocs_add_document'), params)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)


class TestDocumentEditView(TestCase):
    def setUp(self):
        login(self.client)

        # Create a document to edit
        self.document = models.Document.objects.create(title="Test document")

    def get(self, params={}):
        return self.client.get(reverse('wagtaildocs_edit_document', args=(self.document.id,)), params)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)


class TestDocumentDeleteView(TestCase):
    def setUp(self):
        login(self.client)

        # Create a document to delete
        self.document = models.Document.objects.create(title="Test document")

    def get(self, params={}):
        return self.client.get(reverse('wagtaildocs_delete_document', args=(self.document.id,)), params)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)


class TestDocumentChooserView(TestCase):
    def setUp(self):
        login(self.client)

    def get(self, params={}):
        return self.client.get(reverse('wagtaildocs_chooser'), params)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_search(self):
        response = self.get({'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

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
        return self.client.get(reverse('wagtaildocs_document_chosen', args=(self.document.id,)), params)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)


class TestDocumentChooserUploadView(TestCase):
    def setUp(self):
        login(self.client)

    def get(self, params={}):
        return self.client.get(reverse('wagtaildocs_chooser_upload'), params)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)


class TestDocumentFilenameProperties(TestCase):
    def setUp(self):
        self.document = models.Document(title="Test document")
        self.document.file.save('example.doc', ContentFile("A boring example document"))

        self.extensionless_document = models.Document(title="Test document")
        self.extensionless_document.file.save('example', ContentFile("A boring example document"))

    def test_filename(self):
        self.assertEqual('example.doc', self.document.filename)
        self.assertEqual('example', self.extensionless_document.filename)

    def test_file_extension(self):
        self.assertEqual('doc', self.document.file_extension)
        self.assertEqual('', self.extensionless_document.file_extension)

    def tearDown(self):
        self.document.delete()
        self.extensionless_document.delete()
