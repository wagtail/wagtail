from six import b

from django.test import TestCase

from django.contrib.auth.models import User, Group, Permission
from django.core.urlresolvers import reverse
from django.core.files.base import ContentFile
from django.test.utils import override_settings

from wagtail.wagtaildocs import models
from wagtail.tests.utils import WagtailTestUtils

from wagtail.tests.models import EventPage, EventPageRelatedLink
from wagtail.wagtaildocs.models import Document

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


class TestDocumentIndexView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def test_simple(self):
        response = self.client.get(reverse('wagtaildocs_index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/documents/index.html')

    def test_search(self):
        response = self.client.get(reverse('wagtaildocs_index'), {'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

    def make_docs(self):
        for i in range(50):
            document = models.Document(title="Test " + str(i))
            document.save()

    def test_pagination(self):
        self.make_docs()

        response = self.client.get(reverse('wagtaildocs_index'), {'p': 2})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/documents/index.html')

        # Check that we got the correct page
        self.assertEqual(response.context['documents'].number, 2)

    def test_pagination_invalid(self):
        self.make_docs()

        response = self.client.get(reverse('wagtaildocs_index'), {'p': 'Hello World!'})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/documents/index.html')

        # Check that we got page one
        self.assertEqual(response.context['documents'].number, 1)

    def test_pagination_out_of_range(self):
        self.make_docs()

        response = self.client.get(reverse('wagtaildocs_index'), {'p': 99999})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/documents/index.html')

        # Check that we got the last page
        self.assertEqual(response.context['documents'].number, response.context['documents'].paginator.num_pages)

    def test_ordering(self):
        orderings = ['title', '-created_at']
        for ordering in orderings:
            response = self.client.get(reverse('wagtaildocs_index'), {'ordering': ordering})
            self.assertEqual(response.status_code, 200)


class TestDocumentAddView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def test_simple(self):
        response = self.client.get(reverse('wagtaildocs_add_document'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/documents/add.html')

    def test_post(self):
        # Build a fake file
        fake_file = ContentFile(b("A boring example document"))
        fake_file.name = 'test.txt'

        # Submit
        post_data = {
            'title': "Test document",
            'file': fake_file,
        }
        response = self.client.post(reverse('wagtaildocs_add_document'), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtaildocs_index'))

        # Document should be created
        self.assertTrue(models.Document.objects.filter(title="Test document").exists())


class TestDocumentEditView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Build a fake file
        fake_file = ContentFile(b("A boring example document"))
        fake_file.name = 'test.txt'

        # Create a document to edit
        self.document = models.Document.objects.create(title="Test document", file=fake_file)

    def test_simple(self):
        response = self.client.get(reverse('wagtaildocs_edit_document', args=(self.document.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/documents/edit.html')

    def test_post(self):
        # Build a fake file
        fake_file = ContentFile(b("A boring example document"))
        fake_file.name = 'test.txt'

        # Submit title change
        post_data = {
            'title': "Test document changed!",
            'file': fake_file,
        }
        response = self.client.post(reverse('wagtaildocs_edit_document', args=(self.document.id,)), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtaildocs_index'))

        # Document title should be changed
        self.assertEqual(models.Document.objects.get(id=self.document.id).title, "Test document changed!")


class TestDocumentDeleteView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create a document to delete
        self.document = models.Document.objects.create(title="Test document")

    def test_simple(self):
        response = self.client.get(reverse('wagtaildocs_delete_document', args=(self.document.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/documents/confirm_delete.html')

    def test_delete(self):
        # Submit title change
        post_data = {
            'foo': 'bar'
        }
        response = self.client.post(reverse('wagtaildocs_delete_document', args=(self.document.id,)), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtaildocs_index'))

        # Document should be deleted
        self.assertFalse(models.Document.objects.filter(id=self.document.id).exists())


class TestDocumentChooserView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def test_simple(self):
        response = self.client.get(reverse('wagtaildocs_chooser'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/chooser/chooser.html')
        self.assertTemplateUsed(response, 'wagtaildocs/chooser/chooser.js')

    def test_search(self):
        response = self.client.get(reverse('wagtaildocs_chooser'), {'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

    def make_docs(self):
        for i in range(50):
            document = models.Document(title="Test " + str(i))
            document.save()

    def test_pagination(self):
        self.make_docs()

        response = self.client.get(reverse('wagtaildocs_chooser'), {'p': 2})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/documents/list.html')

        # Check that we got the correct page
        self.assertEqual(response.context['documents'].number, 2)

    def test_pagination_invalid(self):
        self.make_docs()

        response = self.client.get(reverse('wagtaildocs_chooser'), {'p': 'Hello World!'})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/documents/list.html')

        # Check that we got page one
        self.assertEqual(response.context['documents'].number, 1)

    def test_pagination_out_of_range(self):
        self.make_docs()

        response = self.client.get(reverse('wagtaildocs_chooser'), {'p': 99999})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/documents/list.html')

        # Check that we got the last page
        self.assertEqual(response.context['documents'].number, response.context['documents'].paginator.num_pages)


class TestDocumentChooserChosenView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create a document to choose
        self.document = models.Document.objects.create(title="Test document")

    def test_simple(self):
        response = self.client.get(reverse('wagtaildocs_document_chosen', args=(self.document.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/chooser/document_chosen.js')


class TestDocumentChooserUploadView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def test_simple(self):
        response = self.client.get(reverse('wagtaildocs_chooser_upload'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/chooser/chooser.html')
        self.assertTemplateUsed(response, 'wagtaildocs/chooser/chooser.js')

    def test_post(self):
        # Build a fake file
        fake_file = ContentFile(b("A boring example document"))
        fake_file.name = 'test.txt'

        # Submit
        post_data = {
            'title': "Test document",
            'file': fake_file,
        }
        response = self.client.post(reverse('wagtaildocs_chooser_upload'), post_data)

        # Check that the response is a javascript file saying the document was chosen
        self.assertTemplateUsed(response, 'wagtaildocs/chooser/document_chosen.js')
        self.assertContains(response, "modal.respond('documentChosen'")

        # Document should be created
        self.assertTrue(models.Document.objects.filter(title="Test document").exists())


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


class TestUsageCount(TestCase, WagtailTestUtils):
    fixtures = ['wagtail/tests/fixtures/test.json']

    def setUp(self):
        self.login()

    def test_document_usage_count_not_enabled(self):
        doc = Document.objects.get(id=1)
        self.assertEqual(doc.usage_count, None)

    @override_settings(USAGE_COUNT=True)
    def test_unused_document_usage_count(self):
        doc = Document.objects.get(id=1)
        self.assertEqual(doc.usage_count, 0)

    @override_settings(USAGE_COUNT=True)
    def test_used_document_usage_count(self):
        doc = Document.objects.get(id=1)
        page = EventPage.objects.get(id=4)
        event_page_related_link = EventPageRelatedLink()
        event_page_related_link.page = page
        event_page_related_link.link_document = doc
        event_page_related_link.save()
        self.assertEqual(doc.usage_count, 1)

    def test_usage_count_does_not_appear(self):
        doc = Document.objects.get(id=1)
        page = EventPage.objects.get(id=4)
        event_page_related_link = EventPageRelatedLink()
        event_page_related_link.page = page
        event_page_related_link.link_document = doc
        event_page_related_link.save()
        response = self.client.get(reverse('wagtaildocs_edit_document',
                                           args=(1,)))
        self.assertNotContains(response, 'Used 1 Time')

    @override_settings(USAGE_COUNT=True)
    def test_usage_count_appears(self):
        doc = Document.objects.get(id=1)
        page = EventPage.objects.get(id=4)
        event_page_related_link = EventPageRelatedLink()
        event_page_related_link.page = page
        event_page_related_link.link_document = doc
        event_page_related_link.save()
        response = self.client.get(reverse('wagtaildocs_edit_document',
                                           args=(1,)))
        self.assertContains(response, 'Used 1 Time')

    @override_settings(USAGE_COUNT=True)
    def test_usage_count_zero_appears(self):
        response = self.client.get(reverse('wagtaildocs_edit_document',
                                           args=(1,)))
        self.assertContains(response, 'Used 0 Times')


class TestUsedBy(TestCase, WagtailTestUtils):
    fixtures = ['wagtail/tests/fixtures/test.json']

    def setUp(self):
        self.login()

    def test_document_used_by_not_enabled(self):
        doc = Document.objects.get(id=1)
        self.assertEqual(doc.used_by, [])

    @override_settings(USAGE_COUNT=True)
    def test_unused_document_used_by(self):
        doc = Document.objects.get(id=1)
        self.assertEqual(doc.used_by, [])

    @override_settings(USAGE_COUNT=True)
    def test_used_document_used_by(self):
        doc = Document.objects.get(id=1)
        page = EventPage.objects.get(id=4)
        event_page_related_link = EventPageRelatedLink()
        event_page_related_link.page = page
        event_page_related_link.link_document = doc
        event_page_related_link.save()
        self.assertEqual(doc.used_by, [page])

    @override_settings(USAGE_COUNT=True)
    def test_usage_page(self):
        doc = Document.objects.get(id=1)
        page = EventPage.objects.get(id=4)
        event_page_related_link = EventPageRelatedLink()
        event_page_related_link.page = page
        event_page_related_link.link_document = doc
        event_page_related_link.save()
        response = self.client.get(reverse('wagtaildocs_document_usage',
                                           args=(1,)))
        self.assertContains(response, 'Christmas')

    @override_settings(USAGE_COUNT=True)
    def test_usage_page_no_usage(self):
        response = self.client.get(reverse('wagtaildocs_document_usage',
                                           args=(1,)))
        # There's no usage so there should be no table rows
        self.assertRegex(response.content, '<tbody>(\s|\n)*</tbody>')
