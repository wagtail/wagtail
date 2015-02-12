from six import b
import mock

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.urlresolvers import reverse
from django.core.files.base import ContentFile
from django.test.utils import override_settings

from wagtail.tests.utils import unittest, WagtailTestUtils
from wagtail.wagtailcore.models import Page

from wagtail.tests.models import EventPage, EventPageRelatedLink
from wagtail.wagtaildocs.models import Document

from wagtail.wagtaildocs import models


class TestDocumentPermissions(TestCase):
    def setUp(self):
        # Create some user accounts for testing permissions
        User = get_user_model()
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

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_unused_document_usage_count(self):
        doc = Document.objects.get(id=1)
        self.assertEqual(doc.get_usage().count(), 0)

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_used_document_usage_count(self):
        doc = Document.objects.get(id=1)
        page = EventPage.objects.get(id=4)
        event_page_related_link = EventPageRelatedLink()
        event_page_related_link.page = page
        event_page_related_link.link_document = doc
        event_page_related_link.save()
        self.assertEqual(doc.get_usage().count(), 1)

    def test_usage_count_does_not_appear(self):
        doc = Document.objects.get(id=1)
        page = EventPage.objects.get(id=4)
        event_page_related_link = EventPageRelatedLink()
        event_page_related_link.page = page
        event_page_related_link.link_document = doc
        event_page_related_link.save()
        response = self.client.get(reverse('wagtaildocs_edit_document',
                                           args=(1,)))
        self.assertNotContains(response, 'Used 1 time')

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_usage_count_appears(self):
        doc = Document.objects.get(id=1)
        page = EventPage.objects.get(id=4)
        event_page_related_link = EventPageRelatedLink()
        event_page_related_link.page = page
        event_page_related_link.link_document = doc
        event_page_related_link.save()
        response = self.client.get(reverse('wagtaildocs_edit_document',
                                           args=(1,)))
        self.assertContains(response, 'Used 1 time')

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_usage_count_zero_appears(self):
        response = self.client.get(reverse('wagtaildocs_edit_document',
                                           args=(1,)))
        self.assertContains(response, 'Used 0 times')


class TestGetUsage(TestCase, WagtailTestUtils):
    fixtures = ['wagtail/tests/fixtures/test.json']

    def setUp(self):
        self.login()

    def test_document_get_usage_not_enabled(self):
        doc = Document.objects.get(id=1)
        self.assertEqual(list(doc.get_usage()), [])

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_unused_document_get_usage(self):
        doc = Document.objects.get(id=1)
        self.assertEqual(list(doc.get_usage()), [])

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_used_document_get_usage(self):
        doc = Document.objects.get(id=1)
        page = EventPage.objects.get(id=4)
        event_page_related_link = EventPageRelatedLink()
        event_page_related_link.page = page
        event_page_related_link.link_document = doc
        event_page_related_link.save()
        self.assertTrue(issubclass(Page, type(doc.get_usage()[0])))

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
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

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_usage_page_no_usage(self):
        response = self.client.get(reverse('wagtaildocs_document_usage',
                                           args=(1,)))
        # There's no usage so there should be no table rows
        self.assertRegex(response.content, b'<tbody>(\s|\n)*</tbody>')


class TestIssue613(TestCase, WagtailTestUtils):
    def get_elasticsearch_backend(self):
        from django.conf import settings
        from wagtail.wagtailsearch.backends import get_search_backend

        backend_path = 'wagtail.wagtailsearch.backends.elasticsearch.ElasticSearch'

        # Search WAGTAILSEARCH_BACKENDS for an entry that uses the given backend path
        for backend_name, backend_conf in settings.WAGTAILSEARCH_BACKENDS.items():
            if backend_conf['BACKEND'] == backend_path:
                return get_search_backend(backend_name)
        else:
            # no conf entry found - skip tests for this backend
            raise unittest.SkipTest("No WAGTAILSEARCH_BACKENDS entry for the backend %s" % backend_path)

    def setUp(self):
        self.search_backend = self.get_elasticsearch_backend()
        self.login()

    def add_document(self, **params):
        # Build a fake file
        fake_file = ContentFile(b("A boring example document"))
        fake_file.name = 'test.txt'

        # Submit
        post_data = {
            'title': "Test document",
            'file': fake_file,
        }
        post_data.update(params)
        response = self.client.post(reverse('wagtaildocs_add_document'), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtaildocs_index'))

        # Document should be created
        doc = models.Document.objects.filter(title=post_data['title'])
        self.assertTrue(doc.exists())
        return doc.first()

    def edit_document(self, **params):
        # Build a fake file
        fake_file = ContentFile(b("A boring example document"))
        fake_file.name = 'test.txt'

        # Create a document without tags to edit
        document = models.Document.objects.create(title="Test document", file=fake_file)

        # Build another fake file
        another_fake_file = ContentFile(b("A boring example document"))
        another_fake_file.name = 'test.txt'

        # Submit
        post_data = {
            'title': "Test document changed!",
            'file': another_fake_file,
        }
        post_data.update(params)
        response = self.client.post(reverse('wagtaildocs_edit_document', args=(document.id,)), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtaildocs_index'))

        # Document should be changed
        doc = models.Document.objects.filter(title=post_data['title'])
        self.assertTrue(doc.exists())
        return doc.first()

    def test_issue_613_on_add(self):
        # Reset the search index
        self.search_backend.reset_index()
        self.search_backend.add_type(Document)

        # Add a document with some tags
        document = self.add_document(tags="hello")
        self.search_backend.refresh_index()

        # Search for it by tag
        results = self.search_backend.search("hello", Document)

        # Check
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, document.id)

    def test_issue_613_on_edit(self):
        # Reset the search index
        self.search_backend.reset_index()
        self.search_backend.add_type(Document)

        # Add a document with some tags
        document = self.edit_document(tags="hello")
        self.search_backend.refresh_index()

        # Search for it by tag
        results = self.search_backend.search("hello", Document)

        # Check
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, document.id)


class TestServeView(TestCase):
    def setUp(self):
        self.document = models.Document(title="Test document")
        self.document.file.save('example.doc', ContentFile("A boring example document"))

    def get(self):
        return self.client.get(reverse('wagtaildocs_serve', args=(self.document.id, 'example.doc')))

    def test_response_code(self):
        self.assertEqual(self.get().status_code, 200)

    @unittest.expectedFailure # Filename has a random string appended to it
    def test_content_disposition_header(self):
        self.assertEqual(self.get()['Content-Disposition'], 'attachment; filename=example.doc')

    def test_content_length_header(self):
        self.assertEqual(self.get()['Content-Length'], '25')

    def test_is_streaming_response(self):
        self.assertTrue(self.get().streaming)

    def test_content(self):
        self.assertEqual(b"".join(self.get().streaming_content), b"A boring example document")

    def test_document_served_fired(self):
        mock_handler = mock.MagicMock()
        models.document_served.connect(mock_handler)

        self.get()

        self.assertEqual(mock_handler.call_count, 1)
        self.assertEqual(mock_handler.mock_calls[0][2]['sender'], self.document)

    def test_with_nonexistent_document(self):
        response = self.client.get(reverse('wagtaildocs_serve', args=(1000, 'blahblahblah', )))
        self.assertEqual(response.status_code, 404)

    @unittest.expectedFailure
    def test_with_incorrect_filename(self):
        response = self.client.get(reverse('wagtaildocs_serve', args=(self.document.id, 'incorrectfilename')))
        self.assertEqual(response.status_code, 404)
