from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.documents.models import Document
from wagtail.models import (
    Collection,
    GroupCollectionPermission,
    Page,
    get_root_collection_id,
)
from wagtail.test.utils import WagtailTestUtils


class TestChooser(TestCase, WagtailTestUtils):
    """Test chooser panel rendered by `wagtaildocs_chooser:choose` view"""

    _NO_DOCS_TEXT = "You haven't uploaded any documents."
    _NO_COLLECTION_DOCS_TEXT = "You haven't uploaded any documents in this collection."
    _UPLOAD_ONE_TEXT = "upload one now"  # text from the link that opens upload form

    def setUp(self):
        self.root_page = Page.objects.get(id=2)

    def login_as_superuser(self):
        self.login()

    def login_as_editor(self):
        # Create group with access to admin
        editors_group = Group.objects.create(name="The Editors")
        access_admin_perm = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        editors_group.permissions.add(access_admin_perm)
        # Grant "choose" permission to the Editors group on the Root Collection.
        choose_document_permission = Permission.objects.get(
            content_type__app_label="wagtaildocs", codename="choose_document"
        )
        GroupCollectionPermission.objects.create(
            group=editors_group,
            collection=Collection.objects.get(depth=1),
            permission=choose_document_permission,
        )

        # Create a non-superuser editor
        user = self.create_user(username="editor", password="password")
        user.groups.add(editors_group)

        # Log in as a non-superuser editor
        self.login(user)

    def login_as_baker(self):
        # Create group with access to admin and Chooser permission on one Collection, but not another.
        bakers_group = Group.objects.create(name="Bakers")
        access_admin_perm = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        bakers_group.permissions.add(access_admin_perm)
        # Create the "Bakery" Collection and grant "choose" permission to the Bakers group.
        root = Collection.objects.get(id=get_root_collection_id())
        bakery_collection = root.add_child(instance=Collection(name="Bakery"))
        GroupCollectionPermission.objects.create(
            group=bakers_group,
            collection=bakery_collection,
            permission=Permission.objects.get(
                content_type__app_label="wagtaildocs", codename="choose_document"
            ),
        )
        # Create the "Office" Collection and _don't_ grant any permissions to the Bakers group.
        root.add_child(instance=Collection(name="Office"))

        # Create a Baker user.
        user = self.create_user(username="baker", password="password")
        user.groups.add(bakers_group)

        # Log in as the baker.
        self.login(user)

    def get(self, params=None):
        return self.client.get(reverse("wagtaildocs_chooser:choose"), params or {})

    def test_chooser_docs_exist(self):
        # given an editor with access to admin panel
        self.login_as_editor()
        # and a document in the database
        doc_title = "document.pdf"
        Document.objects.create(title=doc_title)

        # when opening chooser
        response = self.get()

        # then chooser template is used
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/chooser/chooser.html")
        # and document is displayed
        self.assertContains(response, doc_title)
        # and no hints are displayed
        self.assertNotContains(response, self._NO_DOCS_TEXT)
        self.assertNotContains(response, self._NO_COLLECTION_DOCS_TEXT)
        self.assertNotContains(response, self._UPLOAD_ONE_TEXT)

    def test_chooser_only_docs_in_chooseable_collection_appear(self):
        # Log in as a baker, who has choose permission on the Bakery but not the Office.
        self.login_as_baker()
        # And a document to the Bakery and to the Office.
        bun_recipe_title = "bun_recipe.pdf"
        Document.objects.create(
            title=bun_recipe_title, collection=Collection.objects.get(name="Bakery")
        )
        payroll_title = "payroll.xlsx"
        Document.objects.create(
            title=payroll_title, collection=Collection.objects.get(name="Office")
        )

        # Open the doc chooser.
        response = self.get()

        # Confirm that the chooser opened successfully.
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/chooser/chooser.html")
        # Ensure that the bun recipe is visible, but the payroll is not.
        self.assertContains(response, bun_recipe_title)
        self.assertNotContains(response, payroll_title)

    def test_chooser_collection_selector_appears_only_if_multiple_collections_are_choosable(
        self,
    ):
        # Log in as a baker, who has choose permission on the Bakery but not the Office.
        self.login_as_baker()

        # Open the doc chooser.
        response = self.get()

        # Confirm that the chooser opened successfully.
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/chooser/chooser.html")
        # Ensure that the Collection chooser is not visible, because the Baker cannot
        # choose from multiple Collections.
        self.assertNotContains(response, "Collection:")

        # Let the Baker choose from the Office Collection.
        GroupCollectionPermission.objects.create(
            group=Group.objects.get(name="Bakers"),
            collection=Collection.objects.get(name="Office"),
            permission=Permission.objects.get(
                content_type__app_label="wagtaildocs", codename="choose_document"
            ),
        )

        # Open the doc chooser again.
        response = self.get()

        # Confirm that the chooser opened successfully.
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/chooser/chooser.html")
        # Ensure that the Collection chooser IS visible, because the Baker can now
        # choose from multiple Collections.
        self.assertContains(response, "Collection:")

    def test_chooser_no_docs_upload_allowed(self):
        # given a superuser and no documents in the database
        self.login_as_superuser()

        # when opening chooser
        response = self.get()

        # then chooser template is used
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/chooser/chooser.html")
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
        self.assertTemplateUsed(response, "wagtailadmin/generic/chooser/chooser.html")
        # and the following hint is displayed:
        # "You haven't uploaded any documents in this collection. Why not upload one now?"
        self.assertContains(response, self._NO_DOCS_TEXT)
        self.assertNotContains(response, self._UPLOAD_ONE_TEXT)

    def test_results_docs_exist(self):
        # given a superuser
        self.login_as_superuser()
        # and a document in the database
        doc_title = "document.pdf"
        Document.objects.create(title=doc_title)

        # when searching for any documents at chooser panel
        response = self.get({"q": ""})

        # then results template is used
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaildocs/chooser/results.html")
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
        response = self.get({"q": ""})

        # then results template is used
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaildocs/chooser/results.html")
        # and hint "You haven't uploaded any documents. Why not upload one now?" is displayed
        self.assertContains(response, self._NO_DOCS_TEXT)
        self.assertContains(response, self._UPLOAD_ONE_TEXT)

    def test_results_no_docs_upload_forbidden(self):
        # given an editor with access to admin panel
        # and no documents in the database
        self.login_as_editor()

        # when searching for any documents at chooser panel
        response = self.get({"q": ""})

        # then results template is used
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaildocs/chooser/results.html")
        # and hint "You haven't uploaded any documents." is displayed
        self.assertContains(response, self._NO_DOCS_TEXT)
        self.assertNotContains(response, self._UPLOAD_ONE_TEXT)

    def test_results_no_collection_docs_upload_allowed(self):
        # given a superuser
        self.login_as_superuser()
        # and a document in a collection
        root_id = get_root_collection_id()
        root = Collection.objects.get(id=root_id)
        empty_collection = Collection(name="Nothing to see here")
        root.add_child(instance=empty_collection)

        doc_title = "document.pdf"
        Document.objects.create(title=doc_title, collection=root)

        # when searching for documents in another collection at chooser panel
        response = self.get({"q": "", "collection_id": empty_collection.id})

        # then results template is used
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaildocs/chooser/results.html")
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
        empty_collection = Collection(name="Nothing to see here")
        root.add_child(instance=empty_collection)
        Document.objects.create(collection=root)

        # when searching for documents in another collection at chooser panel
        response = self.get({"q": "", "collection_id": empty_collection.id})

        # then results template is used
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaildocs/chooser/results.html")
        # and hint "You haven't uploaded any documents in this collection." is displayed
        self.assertContains(response, self._NO_COLLECTION_DOCS_TEXT)
        self.assertNotContains(response, self._UPLOAD_ONE_TEXT)
