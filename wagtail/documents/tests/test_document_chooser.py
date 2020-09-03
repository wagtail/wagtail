from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.core.models import Collection, Page, get_root_collection_id
from wagtail.documents.models import Document
from wagtail.tests.utils import WagtailTestUtils


class TestChooser(TestCase, WagtailTestUtils):
    """Test chooser panel rendered by `wagtaildocs:chooser` view"""

    _NO_DOCS_TEXT = "You haven't uploaded any documents."
    _NO_COLLECTION_DOCS_TEXT = "You haven't uploaded any documents in this collection."
    _UPLOAD_ONE_TEXT = "upload one now"  # text from the link that opens upload form

    def setUp(self):
        self.root_page = Page.objects.get(id=2)

    def login_as_superuser(self):
        self.login()

    def login_as_editor(self):
        # Create group with access to admin
        editors_group = Group.objects.create(name='The Editors')
        access_admin_perm = Permission.objects.get(
            content_type__app_label='wagtailadmin',
            codename='access_admin'
        )
        editors_group.permissions.add(access_admin_perm)

        # Create a non-superuser editor
        user = self.create_user(username="editor", password="password")
        user.groups.add(editors_group)

        # Log in as a non-superuser editor
        self.login(user)

    def get(self, params=None):
        return self.client.get(reverse('wagtaildocs:chooser'), params or {})

    def test_chooser_docs_exist(self):
        # given an editor with access to admin panel
        self.login_as_editor()
        # and a document in the database
        doc_title = 'document.pdf'
        Document.objects.create(title=doc_title)

        # when opening chooser
        response = self.get()

        # then chooser template is used
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/chooser/chooser.html')
        # and document is displayed
        self.assertContains(response, doc_title)
        # and no hints are displayed
        self.assertNotContains(response, self._NO_DOCS_TEXT)
        self.assertNotContains(response, self._NO_COLLECTION_DOCS_TEXT)
        self.assertNotContains(response, self._UPLOAD_ONE_TEXT)

    def test_chooser_no_docs_upload_allowed(self):
        # given a superuser and no documents in the database
        self.login_as_superuser()

        # when opening chooser
        response = self.get()

        # then chooser template is used
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/chooser/chooser.html')
        # and hint "You haven't uploaded any documents. Why not upload one now?" is displayed
        self.assertContains(response, self._NO_DOCS_TEXT)
        self.assertContains(response, self._UPLOAD_ONE_TEXT)

    def test_chooser_no_docs_upload_forbidden(self):
        # given an editor with access to admin panel
        # and no documents in the database
        self.login_as_editor()

        # when opening chooser
        response = self.get()

        # then chooser template is used
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/chooser/chooser.html')
        # and the following hint is displayed:
        # "You haven't uploaded any documents in this collection. Why not upload one now?"
        self.assertContains(response, self._NO_DOCS_TEXT)
        self.assertNotContains(response, self._UPLOAD_ONE_TEXT)

    def test_results_docs_exist(self):
        # given a superuser
        self.login_as_superuser()
        # and a document in the database
        doc_title = 'document.pdf'
        Document.objects.create(title=doc_title)

        # when searching for any documents at chooser panel
        response = self.get({'q': ''})

        # then results template is used
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/chooser/results.html')
        # and document is displayed
        self.assertContains(response, doc_title)
        # and no hints are displayed
        self.assertNotContains(response, self._NO_DOCS_TEXT)
        self.assertNotContains(response, self._NO_COLLECTION_DOCS_TEXT)
        self.assertNotContains(response, self._UPLOAD_ONE_TEXT)

    def test_results_no_docs_upload_allowed(self):
        # given a superuser and no documents in the database
        self.login_as_superuser()

        # when searching for any documents at chooser panel
        response = self.get({'q': ''})

        # then results template is used
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/chooser/results.html')
        # and hint "You haven't uploaded any documents. Why not upload one now?" is displayed
        self.assertContains(response, self._NO_DOCS_TEXT)
        self.assertContains(response, self._UPLOAD_ONE_TEXT)

    def test_results_no_docs_upload_forbidden(self):
        # given an editor with access to admin panel
        # and no documents in the database
        self.login_as_editor()

        # when searching for any documents at chooser panel
        response = self.get({'q': ''})

        # then results template is used
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/chooser/results.html')
        # and hint "You haven't uploaded any documents." is displayed
        self.assertContains(response, self._NO_DOCS_TEXT)
        self.assertNotContains(response, self._UPLOAD_ONE_TEXT)

    def test_results_no_collection_docs_upload_allowed(self):
        # given a superuser
        self.login_as_superuser()
        # and a document in a collection
        root_id = get_root_collection_id()
        root = Collection.objects.get(id=root_id)
        doc_title = 'document.pdf'
        Document.objects.create(title=doc_title, collection=root)

        # when searching for documents in another collection at chooser panel
        non_root_id = root_id + 10**10
        response = self.get({'q': '', 'collection_id': non_root_id})

        # then results template is used
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/chooser/results.html')
        # and the following hint is displayed:
        # "You haven't uploaded any documents in this collection. Why not upload one now?"
        self.assertContains(response, self._NO_COLLECTION_DOCS_TEXT)
        self.assertContains(response, self._UPLOAD_ONE_TEXT)

    def test_results_no_collection_docs_upload_forbidden(self):
        # given an editor with access to admin panel
        self.login_as_editor()
        # and a document in a collection
        root_id = get_root_collection_id()
        root = Collection.objects.get(id=root_id)
        Document.objects.create(collection=root)

        # when searching for documents in another collection at chooser panel
        non_root_id = root_id + 10**10
        response = self.get({'q': '', 'collection_id': non_root_id})

        # then results template is used
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/chooser/results.html')
        # and hint "You haven't uploaded any documents in this collection." is displayed
        self.assertContains(response, self._NO_COLLECTION_DOCS_TEXT)
        self.assertNotContains(response, self._UPLOAD_ONE_TEXT)
