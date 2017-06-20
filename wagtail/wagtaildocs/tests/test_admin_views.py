from __future__ import absolute_import, unicode_literals

import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
from django.utils.six import b

from wagtail.tests.testapp.models import EventPage, EventPageRelatedLink
from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailcore.models import Collection, GroupCollectionPermission, Page
from wagtail.wagtaildocs import models


class TestDocumentIndexView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def test_simple(self):
        response = self.client.get(reverse('wagtaildocs:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/documents/index.html')
        self.assertContains(response, "Add a document")

    def test_search(self):
        response = self.client.get(reverse('wagtaildocs:index'), {'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

    def make_docs(self):
        for i in range(50):
            document = models.Document(title="Test " + str(i))
            document.save()

    def test_pagination(self):
        self.make_docs()

        response = self.client.get(reverse('wagtaildocs:index'), {'p': 2})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/documents/index.html')

        # Check that we got the correct page
        self.assertEqual(response.context['documents'].number, 2)

    def test_pagination_invalid(self):
        self.make_docs()

        response = self.client.get(reverse('wagtaildocs:index'), {'p': 'Hello World!'})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/documents/index.html')

        # Check that we got page one
        self.assertEqual(response.context['documents'].number, 1)

    def test_pagination_out_of_range(self):
        self.make_docs()

        response = self.client.get(reverse('wagtaildocs:index'), {'p': 99999})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/documents/index.html')

        # Check that we got the last page
        self.assertEqual(response.context['documents'].number, response.context['documents'].paginator.num_pages)

    def test_ordering(self):
        orderings = ['title', '-created_at']
        for ordering in orderings:
            response = self.client.get(reverse('wagtaildocs:index'), {'ordering': ordering})
            self.assertEqual(response.status_code, 200)


class TestDocumentAddView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def test_get(self):
        response = self.client.get(reverse('wagtaildocs:add'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/documents/add.html')

        # as standard, only the root collection exists and so no 'Collection' option
        # is displayed on the form
        self.assertNotContains(response, '<label for="id_collection">')

        # Ensure the form supports file uploads
        self.assertContains(response, 'enctype="multipart/form-data"')

    def test_get_with_collections(self):
        root_collection = Collection.get_first_root_node()
        root_collection.add_child(name="Evil plans")

        response = self.client.get(reverse('wagtaildocs:add'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/documents/add.html')

        self.assertContains(response, '<label for="id_collection">')
        self.assertContains(response, "Evil plans")

    def test_post(self):
        # Build a fake file
        fake_file = ContentFile(b("A boring example document"))
        fake_file.name = 'test.txt'

        # Submit
        post_data = {
            'title': "Test document",
            'file': fake_file,
        }
        response = self.client.post(reverse('wagtaildocs:add'), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtaildocs:index'))

        # Document should be created, and be placed in the root collection
        self.assertTrue(models.Document.objects.filter(title="Test document").exists())
        root_collection = Collection.get_first_root_node()
        self.assertEqual(
            models.Document.objects.get(title="Test document").collection,
            root_collection
        )

    def test_post_with_collections(self):
        root_collection = Collection.get_first_root_node()
        evil_plans_collection = root_collection.add_child(name="Evil plans")

        # Build a fake file
        fake_file = ContentFile(b("A boring example document"))
        fake_file.name = 'test.txt'

        # Submit
        post_data = {
            'title': "Test document",
            'file': fake_file,
            'collection': evil_plans_collection.id,
        }
        response = self.client.post(reverse('wagtaildocs:add'), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtaildocs:index'))

        # Document should be created, and be placed in the Evil Plans collection
        self.assertTrue(models.Document.objects.filter(title="Test document").exists())
        root_collection = Collection.get_first_root_node()
        self.assertEqual(
            models.Document.objects.get(title="Test document").collection,
            evil_plans_collection
        )


class TestDocumentAddViewWithLimitedCollectionPermissions(TestCase, WagtailTestUtils):
    def setUp(self):
        add_doc_permission = Permission.objects.get(
            content_type__app_label='wagtaildocs', codename='add_document'
        )
        admin_permission = Permission.objects.get(
            content_type__app_label='wagtailadmin', codename='access_admin'
        )

        root_collection = Collection.get_first_root_node()
        self.evil_plans_collection = root_collection.add_child(name="Evil plans")

        conspirators_group = Group.objects.create(name="Evil conspirators")
        conspirators_group.permissions.add(admin_permission)
        GroupCollectionPermission.objects.create(
            group=conspirators_group,
            collection=self.evil_plans_collection,
            permission=add_doc_permission
        )

        user = get_user_model().objects.create_user(
            username='moriarty',
            email='moriarty@example.com',
            password='password'
        )
        user.groups.add(conspirators_group)

        self.client.login(username='moriarty', password='password')

    def test_get(self):
        response = self.client.get(reverse('wagtaildocs:add'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/documents/add.html')

        # user only has access to one collection, so no 'Collection' option
        # is displayed on the form
        self.assertNotContains(response, '<label for="id_collection">')

    def test_post(self):
        # Build a fake file
        fake_file = ContentFile(b("A boring example document"))
        fake_file.name = 'test.txt'

        # Submit
        post_data = {
            'title': "Test document",
            'file': fake_file,
        }
        response = self.client.post(reverse('wagtaildocs:add'), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtaildocs:index'))

        # Document should be created in the 'evil plans' collection,
        # despite there being no collection field in the form, because that's the
        # only one the user has access to
        self.assertTrue(models.Document.objects.filter(title="Test document").exists())
        self.assertEqual(
            models.Document.objects.get(title="Test document").collection,
            self.evil_plans_collection
        )


class TestDocumentEditView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Build a fake file
        fake_file = ContentFile(b("A boring example document"))
        fake_file.name = 'test.txt'

        # Create a document to edit
        self.document = models.Document.objects.create(title="Test document", file=fake_file)

    def test_simple(self):
        response = self.client.get(reverse('wagtaildocs:edit', args=(self.document.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/documents/edit.html')

        # Ensure the form supports file uploads
        self.assertContains(response, 'enctype="multipart/form-data"')

    def test_post(self):
        # Build a fake file
        fake_file = ContentFile(b("A boring example document"))
        fake_file.name = 'test.txt'

        # Submit title change
        post_data = {
            'title': "Test document changed!",
            'file': fake_file,
        }
        response = self.client.post(reverse('wagtaildocs:edit', args=(self.document.id,)), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtaildocs:index'))

        # Document title should be changed
        self.assertEqual(models.Document.objects.get(id=self.document.id).title, "Test document changed!")

    def test_with_missing_source_file(self):
        # Build a fake file
        fake_file = ContentFile(b("An ephemeral document"))
        fake_file.name = 'to-be-deleted.txt'

        # Create a new document to delete the source for
        document = models.Document.objects.create(title="Test missing source document", file=fake_file)
        document.file.delete(False)

        response = self.client.get(reverse('wagtaildocs:edit', args=(document.id,)), {})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/documents/edit.html')

        self.assertContains(response, 'File not found')


class TestDocumentDeleteView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create a document to delete
        self.document = models.Document.objects.create(title="Test document")

    def test_simple(self):
        response = self.client.get(reverse('wagtaildocs:delete', args=(self.document.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/documents/confirm_delete.html')

    def test_delete(self):
        # Submit title change
        response = self.client.post(reverse('wagtaildocs:delete', args=(self.document.id,)))

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtaildocs:index'))

        # Document should be deleted
        self.assertFalse(models.Document.objects.filter(id=self.document.id).exists())


class TestMultipleDocumentUploader(TestCase, WagtailTestUtils):
    """
    This tests the multiple document upload views located in wagtaildocs/views/multiple.py
    """
    def setUp(self):
        self.login()

        # Create a document for running tests on
        self.doc = models.Document.objects.create(
            title="Test document",
            file=ContentFile(b("Simple text document")),
        )

    def test_add(self):
        """
        This tests that the add view responds correctly on a GET request
        """
        # Send request
        response = self.client.get(reverse('wagtaildocs:add_multiple'))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/multiple/add.html')

        # no collection chooser when only one collection exists
        self.assertNotContains(response, '<label for="id_adddocument_collection">')

    def test_add_with_collections(self):
        root_collection = Collection.get_first_root_node()
        root_collection.add_child(name="Evil plans")

        # Send request
        response = self.client.get(reverse('wagtaildocs:add_multiple'))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/multiple/add.html')

        # collection chooser should exisst
        self.assertContains(response, '<label for="id_adddocument_collection">')
        self.assertContains(response, 'Evil plans')

    def test_add_post(self):
        """
        This tests that a POST request to the add view saves the document and returns an edit form
        """
        response = self.client.post(reverse('wagtaildocs:add_multiple'), {
            'files[]': SimpleUploadedFile('test.png', b"Simple text document"),
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertTemplateUsed(response, 'wagtaildocs/multiple/edit_form.html')

        # Check document
        self.assertIn('doc', response.context)
        self.assertEqual(response.context['doc'].title, 'test.png')
        self.assertTrue(response.context['doc'].file_size)

        # check that it is in the root collection
        doc = models.Document.objects.get(title='test.png')
        root_collection = Collection.get_first_root_node()
        self.assertEqual(doc.collection, root_collection)

        # Check form
        self.assertIn('form', response.context)
        self.assertEqual(response.context['form'].initial['title'], 'test.png')

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn('doc_id', response_json)
        self.assertIn('form', response_json)
        self.assertIn('success', response_json)
        self.assertEqual(response_json['doc_id'], response.context['doc'].id)
        self.assertTrue(response_json['success'])

        # form should not contain a collection chooser
        self.assertNotIn('Collection', response_json['form'])

    def test_add_post_with_collections(self):
        """
        This tests that a POST request to the add view saves the document
        and returns an edit form, when collections are active
        """

        root_collection = Collection.get_first_root_node()
        evil_plans_collection = root_collection.add_child(name="Evil plans")

        response = self.client.post(reverse('wagtaildocs:add_multiple'), {
            'files[]': SimpleUploadedFile('test.png', b"Simple text document"),
            'collection': evil_plans_collection.id
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertTemplateUsed(response, 'wagtaildocs/multiple/edit_form.html')

        # Check document
        self.assertIn('doc', response.context)
        self.assertEqual(response.context['doc'].title, 'test.png')
        self.assertTrue(response.context['doc'].file_size)

        # check that it is in the 'evil plans' collection
        doc = models.Document.objects.get(title='test.png')
        root_collection = Collection.get_first_root_node()
        self.assertEqual(doc.collection, evil_plans_collection)

        # Check form
        self.assertIn('form', response.context)
        self.assertEqual(response.context['form'].initial['title'], 'test.png')

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn('doc_id', response_json)
        self.assertIn('form', response_json)
        self.assertIn('success', response_json)
        self.assertEqual(response_json['doc_id'], response.context['doc'].id)
        self.assertTrue(response_json['success'])

        # form should contain a collection chooser
        self.assertIn('Collection', response_json['form'])

    def test_add_post_noajax(self):
        """
        This tests that only AJAX requests are allowed to POST to the add view
        """
        response = self.client.post(reverse('wagtaildocs:add_multiple'))

        # Check response
        self.assertEqual(response.status_code, 400)

    def test_add_post_nofile(self):
        """
        This tests that the add view checks for a file when a user POSTs to it
        """
        response = self.client.post(reverse('wagtaildocs:add_multiple'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check response
        self.assertEqual(response.status_code, 400)

    def test_edit_get(self):
        """
        This tests that a GET request to the edit view returns a 405 "METHOD NOT ALLOWED" response
        """
        # Send request
        response = self.client.get(reverse('wagtaildocs:edit_multiple', args=(self.doc.id, )))

        # Check response
        self.assertEqual(response.status_code, 405)

    def test_edit_post(self):
        """
        This tests that a POST request to the edit view edits the document
        """
        # Send request
        response = self.client.post(reverse('wagtaildocs:edit_multiple', args=(self.doc.id, )), {
            ('doc-%d-title' % self.doc.id): "New title!",
            ('doc-%d-tags' % self.doc.id): "",
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn('doc_id', response_json)
        self.assertNotIn('form', response_json)
        self.assertIn('success', response_json)
        self.assertEqual(response_json['doc_id'], self.doc.id)
        self.assertTrue(response_json['success'])

    def test_edit_post_noajax(self):
        """
        This tests that a POST request to the edit view without AJAX returns a 400 response
        """
        # Send request
        response = self.client.post(reverse('wagtaildocs:edit_multiple', args=(self.doc.id, )), {
            ('doc-%d-title' % self.doc.id): "New title!",
            ('doc-%d-tags' % self.doc.id): "",
        })

        # Check response
        self.assertEqual(response.status_code, 400)

    def test_edit_post_validation_error(self):
        """
        This tests that a POST request to the edit page returns a json document with "success=False"
        and a form with the validation error indicated
        """
        # Send request
        response = self.client.post(reverse('wagtaildocs:edit_multiple', args=(self.doc.id, )), {
            ('doc-%d-title' % self.doc.id): "",  # Required
            ('doc-%d-tags' % self.doc.id): "",
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertTemplateUsed(response, 'wagtaildocs/multiple/edit_form.html')

        # Check that a form error was raised
        self.assertFormError(response, 'form', 'title', "This field is required.")

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn('doc_id', response_json)
        self.assertIn('form', response_json)
        self.assertIn('success', response_json)
        self.assertEqual(response_json['doc_id'], self.doc.id)
        self.assertFalse(response_json['success'])

    def test_delete_get(self):
        """
        This tests that a GET request to the delete view returns a 405 "METHOD NOT ALLOWED" response
        """
        # Send request
        response = self.client.get(reverse('wagtaildocs:delete_multiple', args=(self.doc.id, )))

        # Check response
        self.assertEqual(response.status_code, 405)

    def test_delete_post(self):
        """
        This tests that a POST request to the delete view deletes the document
        """
        # Send request
        response = self.client.post(reverse('wagtaildocs:delete_multiple', args=(self.doc.id, )), HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        # Make sure the document is deleted
        self.assertFalse(models.Document.objects.filter(id=self.doc.id).exists())

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn('doc_id', response_json)
        self.assertIn('success', response_json)
        self.assertEqual(response_json['doc_id'], self.doc.id)
        self.assertTrue(response_json['success'])

    def test_delete_post_noajax(self):
        """
        This tests that a POST request to the delete view without AJAX returns a 400 response
        """
        # Send request
        response = self.client.post(reverse('wagtaildocs:delete_multiple', args=(self.doc.id, )))

        # Check response
        self.assertEqual(response.status_code, 400)


class TestDocumentChooserView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()

    def test_simple(self):
        response = self.client.get(reverse('wagtaildocs:chooser'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/chooser/chooser.html')
        self.assertTemplateUsed(response, 'wagtaildocs/chooser/chooser.js')

    def test_search(self):
        response = self.client.get(reverse('wagtaildocs:chooser'), {'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

    def make_docs(self):
        for i in range(50):
            document = models.Document(title="Test " + str(i))
            document.save()

    def test_pagination(self):
        self.make_docs()

        response = self.client.get(reverse('wagtaildocs:chooser'), {'p': 2})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/documents/list.html')

        # Check that we got the correct page
        self.assertEqual(response.context['documents'].number, 2)

    def test_pagination_invalid(self):
        self.make_docs()

        response = self.client.get(reverse('wagtaildocs:chooser'), {'p': 'Hello World!'})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/documents/list.html')

        # Check that we got page one
        self.assertEqual(response.context['documents'].number, 1)

    def test_pagination_out_of_range(self):
        self.make_docs()

        response = self.client.get(reverse('wagtaildocs:chooser'), {'p': 99999})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/documents/list.html')

        # Check that we got the last page
        self.assertEqual(response.context['documents'].number, response.context['documents'].paginator.num_pages)

    def test_construct_queryset_hook_browse(self):
        document = models.Document.objects.create(
            title="Test document shown",
            uploaded_by_user=self.user,
        )
        models.Document.objects.create(
            title="Test document not shown",
        )

        def filter_documents(documents, request):
            # Filter on `uploaded_by_user` because it is
            # the only default FilterField in search_fields
            return documents.filter(uploaded_by_user=self.user)

        with self.register_hook('construct_document_chooser_queryset', filter_documents):
            response = self.client.get(reverse('wagtaildocs:chooser'))
        self.assertEqual(len(response.context['documents']), 1)
        self.assertEqual(response.context['documents'][0], document)

    def test_construct_queryset_hook_search(self):
        document = models.Document.objects.create(
            title="Test document shown",
            uploaded_by_user=self.user,
        )
        models.Document.objects.create(
            title="Test document not shown",
        )

        def filter_documents(documents, request):
            # Filter on `uploaded_by_user` because it is
            # the only default FilterField in search_fields
            return documents.filter(uploaded_by_user=self.user)

        with self.register_hook('construct_document_chooser_queryset', filter_documents):
            response = self.client.get(reverse('wagtaildocs:chooser'), {'q': 'Test'})
        self.assertEqual(len(response.context['documents']), 1)
        self.assertEqual(response.context['documents'][0], document)


class TestDocumentChooserChosenView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create a document to choose
        self.document = models.Document.objects.create(title="Test document")

    def test_simple(self):
        response = self.client.get(reverse('wagtaildocs:document_chosen', args=(self.document.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/chooser/document_chosen.js')


class TestDocumentChooserUploadView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def test_simple(self):
        response = self.client.get(reverse('wagtaildocs:chooser_upload'))
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
        response = self.client.post(reverse('wagtaildocs:chooser_upload'), post_data)

        # Check that the response is a javascript file saying the document was chosen
        self.assertTemplateUsed(response, 'wagtaildocs/chooser/document_chosen.js')
        self.assertContains(response, "modal.respond('documentChosen'")

        # Document should be created
        self.assertTrue(models.Document.objects.filter(title="Test document").exists())


class TestDocumentChooserUploadViewWithLimitedPermissions(TestCase, WagtailTestUtils):
    def setUp(self):
        add_doc_permission = Permission.objects.get(
            content_type__app_label='wagtaildocs', codename='add_document'
        )
        admin_permission = Permission.objects.get(
            content_type__app_label='wagtailadmin', codename='access_admin'
        )

        root_collection = Collection.get_first_root_node()
        self.evil_plans_collection = root_collection.add_child(name="Evil plans")

        conspirators_group = Group.objects.create(name="Evil conspirators")
        conspirators_group.permissions.add(admin_permission)
        GroupCollectionPermission.objects.create(
            group=conspirators_group,
            collection=self.evil_plans_collection,
            permission=add_doc_permission
        )

        user = get_user_model().objects.create_user(
            username='moriarty',
            email='moriarty@example.com',
            password='password'
        )
        user.groups.add(conspirators_group)

        self.client.login(username='moriarty', password='password')

    def test_simple(self):
        response = self.client.get(reverse('wagtaildocs:chooser_upload'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/chooser/chooser.html')
        self.assertTemplateUsed(response, 'wagtaildocs/chooser/chooser.js')

        # user only has access to one collection -> should not see the collections field
        self.assertNotContains(response, 'id_collection')

    def test_chooser_view(self):
        # The main chooser view also includes the form, so need to test there too
        response = self.client.get(reverse('wagtaildocs:chooser'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/chooser/chooser.html')
        self.assertTemplateUsed(response, 'wagtaildocs/chooser/chooser.js')

        # user only has access to one collection -> should not see the collections field
        self.assertNotContains(response, 'id_collection')

    def test_post(self):
        # Build a fake file
        fake_file = ContentFile(b("A boring example document"))
        fake_file.name = 'test.txt'

        # Submit
        post_data = {
            'title': "Test document",
            'file': fake_file,
        }
        response = self.client.post(reverse('wagtaildocs:chooser_upload'), post_data)

        # Check that the response is a javascript file saying the document was chosen
        self.assertTemplateUsed(response, 'wagtaildocs/chooser/document_chosen.js')
        self.assertContains(response, "modal.respond('documentChosen'")

        # Document should be created
        doc = models.Document.objects.filter(title="Test document")
        self.assertTrue(doc.exists())

        # Document should be in the 'evil plans' collection
        self.assertEqual(doc.get().collection, self.evil_plans_collection)


class TestUsageCount(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.login()

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_unused_document_usage_count(self):
        doc = models.Document.objects.get(id=1)
        self.assertEqual(doc.get_usage().count(), 0)

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_used_document_usage_count(self):
        doc = models.Document.objects.get(id=1)
        page = EventPage.objects.get(id=4)
        event_page_related_link = EventPageRelatedLink()
        event_page_related_link.page = page
        event_page_related_link.link_document = doc
        event_page_related_link.save()
        self.assertEqual(doc.get_usage().count(), 1)

    def test_usage_count_does_not_appear(self):
        doc = models.Document.objects.get(id=1)
        page = EventPage.objects.get(id=4)
        event_page_related_link = EventPageRelatedLink()
        event_page_related_link.page = page
        event_page_related_link.link_document = doc
        event_page_related_link.save()
        response = self.client.get(reverse('wagtaildocs:edit',
                                           args=(1,)))
        self.assertNotContains(response, 'Used 1 time')

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_usage_count_appears(self):
        doc = models.Document.objects.get(id=1)
        page = EventPage.objects.get(id=4)
        event_page_related_link = EventPageRelatedLink()
        event_page_related_link.page = page
        event_page_related_link.link_document = doc
        event_page_related_link.save()
        response = self.client.get(reverse('wagtaildocs:edit',
                                           args=(1,)))
        self.assertContains(response, 'Used 1 time')

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_usage_count_zero_appears(self):
        response = self.client.get(reverse('wagtaildocs:edit',
                                           args=(1,)))
        self.assertContains(response, 'Used 0 times')


class TestGetUsage(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.login()

    def test_document_get_usage_not_enabled(self):
        doc = models.Document.objects.get(id=1)
        self.assertEqual(list(doc.get_usage()), [])

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_unused_document_get_usage(self):
        doc = models.Document.objects.get(id=1)
        self.assertEqual(list(doc.get_usage()), [])

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_used_document_get_usage(self):
        doc = models.Document.objects.get(id=1)
        page = EventPage.objects.get(id=4)
        event_page_related_link = EventPageRelatedLink()
        event_page_related_link.page = page
        event_page_related_link.link_document = doc
        event_page_related_link.save()
        self.assertTrue(issubclass(Page, type(doc.get_usage()[0])))

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_usage_page(self):
        doc = models.Document.objects.get(id=1)
        page = EventPage.objects.get(id=4)
        event_page_related_link = EventPageRelatedLink()
        event_page_related_link.page = page
        event_page_related_link.link_document = doc
        event_page_related_link.save()
        response = self.client.get(reverse('wagtaildocs:document_usage',
                                           args=(1,)))
        self.assertContains(response, 'Christmas')

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_usage_page_no_usage(self):
        response = self.client.get(reverse('wagtaildocs:document_usage',
                                           args=(1,)))
        # There's no usage so there should be no table rows
        self.assertRegex(response.content, b'<tbody>(\s|\n)*</tbody>')


class TestEditOnlyPermissions(TestCase, WagtailTestUtils):
    def setUp(self):
        # Build a fake file
        fake_file = ContentFile(b("A boring example document"))
        fake_file.name = 'test.txt'

        self.root_collection = Collection.get_first_root_node()
        self.evil_plans_collection = self.root_collection.add_child(name="Evil plans")
        self.nice_plans_collection = self.root_collection.add_child(name="Nice plans")

        # Create a document to edit
        self.document = models.Document.objects.create(
            title="Test document", file=fake_file, collection=self.nice_plans_collection
        )

        # Create a user with change_document permission but not add_document
        user = get_user_model().objects.create_user(
            username='changeonly',
            email='changeonly@example.com',
            password='password'
        )
        change_permission = Permission.objects.get(
            content_type__app_label='wagtaildocs', codename='change_document'
        )
        admin_permission = Permission.objects.get(
            content_type__app_label='wagtailadmin', codename='access_admin'
        )
        self.changers_group = Group.objects.create(name='Document changers')
        GroupCollectionPermission.objects.create(
            group=self.changers_group, collection=self.root_collection,
            permission=change_permission
        )
        user.groups.add(self.changers_group)

        user.user_permissions.add(admin_permission)
        self.assertTrue(self.client.login(username='changeonly', password='password'))

    def test_get_index(self):
        response = self.client.get(reverse('wagtaildocs:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/documents/index.html')

        # user should not get an "Add a document" button
        self.assertNotContains(response, "Add a document")

        # user should be able to see documents not owned by them
        self.assertContains(response, "Test document")

    def test_search(self):
        response = self.client.get(reverse('wagtaildocs:index'), {'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

    def test_get_add(self):
        response = self.client.get(reverse('wagtaildocs:add'))
        # permission should be denied
        self.assertRedirects(response, reverse('wagtailadmin_home'))

    def test_get_edit(self):
        response = self.client.get(reverse('wagtaildocs:edit', args=(self.document.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/documents/edit.html')

        # documents can only be moved to collections you have add permission for,
        # so the 'collection' field is not available here
        self.assertNotContains(response, '<label for="id_collection">')

        # if the user has add permission on a different collection,
        # they should have option to move the document
        add_permission = Permission.objects.get(
            content_type__app_label='wagtaildocs', codename='add_document'
        )
        GroupCollectionPermission.objects.create(
            group=self.changers_group, collection=self.evil_plans_collection,
            permission=add_permission
        )
        response = self.client.get(reverse('wagtaildocs:edit', args=(self.document.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<label for="id_collection">')
        self.assertContains(response, 'Nice plans')
        self.assertContains(response, 'Evil plans')

    def test_post_edit(self):
        # Submit title change
        response = self.client.post(
            reverse('wagtaildocs:edit', args=(self.document.id,)), {
                'title': "Test document changed!",
                'file': '',
            }
        )

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtaildocs:index'))

        # Document title should be changed
        self.assertEqual(
            models.Document.objects.get(id=self.document.id).title,
            "Test document changed!"
        )

        # collection should be unchanged
        self.assertEqual(
            models.Document.objects.get(id=self.document.id).collection,
            self.nice_plans_collection
        )

        # if the user has add permission on a different collection,
        # they should have option to move the document
        add_permission = Permission.objects.get(
            content_type__app_label='wagtaildocs', codename='add_document'
        )
        GroupCollectionPermission.objects.create(
            group=self.changers_group, collection=self.evil_plans_collection,
            permission=add_permission
        )
        response = self.client.post(
            reverse('wagtaildocs:edit', args=(self.document.id,)), {
                'title': "Test document changed!",
                'collection': self.evil_plans_collection.id,
                'file': '',
            }
        )
        self.assertEqual(
            models.Document.objects.get(id=self.document.id).collection,
            self.evil_plans_collection
        )

    def test_get_delete(self):
        response = self.client.get(reverse('wagtaildocs:delete', args=(self.document.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/documents/confirm_delete.html')

    def test_get_add_multiple(self):
        response = self.client.get(reverse('wagtaildocs:add_multiple'))
        # permission should be denied
        self.assertRedirects(response, reverse('wagtailadmin_home'))
