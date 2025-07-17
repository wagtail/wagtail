import json
from unittest import mock

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.html import escape
from django.utils.http import urlencode
from django.utils.text import capfirst

from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.documents import get_document_model, models
from wagtail.documents.tests.utils import get_test_document_file
from wagtail.models import (
    Collection,
    GroupCollectionPermission,
    Page,
    ReferenceIndex,
    UploadedFile,
)
from wagtail.test.testapp.models import (
    CustomDocument,
    CustomDocumentWithAuthor,
    EventPage,
    EventPageRelatedLink,
    VariousOnDeleteModel,
)
from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.template_tests import AdminTemplateTestUtils
from wagtail.test.utils.timestamps import local_datetime


class TestDocumentIndexView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse("wagtaildocs:index"), params)

    def test_simple(self):
        models.Document.objects.create(title="Hello document")
        models.Document.objects.create(title="Bonjour document")

        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaildocs/documents/index.html")
        self.assertContains(response, "Add a document")
        self.assertContains(response, "Hello document")
        self.assertContains(response, "Bonjour document")

    def make_docs(self):
        for i in range(50):
            document = models.Document(title="Test " + str(i))
            document.save()

    def test_pagination(self):
        self.make_docs()

        response = self.client.get(reverse("wagtaildocs:index"), {"p": 2})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaildocs/documents/index.html")

        # Check that we got the correct page
        self.assertEqual(response.context["page_obj"].number, 2)

    def test_pagination_invalid(self):
        self.make_docs()

        response = self.get({"p": "Hello World!"})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaildocs/documents/index.html")

        # Check that we got page one
        self.assertEqual(response.context["page_obj"].number, 1)

    def test_pagination_out_of_range(self):
        self.make_docs()

        response = self.get({"p": 99999})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaildocs/documents/index.html")

        # Check that we got the last page
        self.assertEqual(
            response.context["page_obj"].number,
            response.context["paginator"].num_pages,
        )

    def test_ordering(self):
        orderings = ["title", "created_at", "-created_at"]
        for ordering in orderings:
            response = self.get({"ordering": ordering})
            self.assertEqual(response.status_code, 200)

    def test_index_without_collections(self):
        self.make_docs()

        response = self.get()
        self.assertNotContains(response, "<th>Collection</th>", html=True)
        self.assertNotContains(response, "<td>Root</td>", html=True)
        soup = self.get_soup(response.content)
        collection_select = soup.select_one('select[name="collection_id"]')
        self.assertIsNone(collection_select)

    def test_index_with_collection(self):
        root_collection = Collection.get_first_root_node()
        root_collection.add_child(name="Evil plans")
        root_collection.add_child(name="Good plans")

        self.make_docs()

        response = self.get()
        self.assertContains(response, "<th>Collection</th>", html=True)
        self.assertContains(response, "<td>Root</td>", html=True)

        response = self.get()
        soup = self.get_soup(response.content)
        collection_options = soup.select(
            'select[name="collection_id"] option[value]:not(option[value=""])'
        )

        self.assertEqual(
            [
                collection.get_text(strip=True).lstrip("↳ ")
                for collection in collection_options
            ],
            ["Root", "Evil plans", "Good plans"],
        )

    def test_index_with_collection_filtered(self):
        root_collection = Collection.get_first_root_node()
        travel_plans = root_collection.add_child(name="Travel plans")
        models.Document.objects.create(title="Itinerary", collection=travel_plans)

        self.make_docs()

        response = self.get({"collection_id": travel_plans.pk})
        # should append the correct params to the add document button
        url = reverse("wagtaildocs:add_multiple")
        self.assertContains(
            response, f'<a href="{url}?collection_id={travel_plans.pk}"'
        )

        # List should be filtered
        self.assertEqual(len(response.context["page_obj"]), 1)
        self.assertContains(response, "Itinerary")
        self.assertNotContains(response, "Test 42")

        # Should render the "Select all" with the correct collection ID
        # twice, one for the column header and one in the footer.
        self.assertContains(
            response,
            f"""
            <input data-bulk-action-parent-id="{travel_plans.pk}"
                   data-bulk-action-select-all-checkbox
                   type="checkbox"
                   aria-label="Select all"
            />""",
            html=True,
            count=2,
        )

    def test_collection_nesting(self):
        root_collection = Collection.get_first_root_node()
        evil_plans = root_collection.add_child(name="Evil plans")
        evil_plans.add_child(name="Eviler plans")

        response = self.get()
        # "Eviler Plans" should be prefixed with &#x21b3 (↳) and 4 non-breaking spaces.
        self.assertContains(response, "&nbsp;&nbsp;&nbsp;&nbsp;&#x21b3 Eviler plans")

    def test_edit_document_link_contains_next_url(self):
        root_collection = Collection.get_first_root_node()
        evil_plans_collection = root_collection.add_child(name="Evil plans")

        doc = models.Document.objects.create(
            title="Test doc", collection=evil_plans_collection
        )

        response = self.get({"collection_id": evil_plans_collection.id})
        self.assertEqual(response.status_code, 200)

        edit_url = reverse("wagtaildocs:edit", args=(doc.id,))
        params = urlencode({"next": response._request.get_full_path()})
        self.assertContains(response, f"{edit_url}?{params}")

    def test_search_form_rendered(self):
        response = self.get()
        html = response.content.decode()
        search_url = reverse("wagtaildocs:index_results")

        # Search form in the header should be rendered.
        self.assertTagInHTML(
            f"""<form action="{search_url}" method="get" role="search">""",
            html,
            count=1,
            allow_extra_attrs=True,
        )

    def test_tags(self):
        document_two_tags = models.Document.objects.create(
            title="Test document with two tags"
        )
        document_two_tags.tags.add("one", "two")

        response = self.get()
        self.assertEqual(response.status_code, 200)

        soup = self.get_soup(response.content)
        current_tags = soup.select("input[name=tag][checked]")
        self.assertFalse(current_tags)

        tags = soup.select("#id_tag label")
        self.assertCountEqual(
            [tags.get_text(strip=True) for tags in tags],
            ["one", "two"],
        )

    def test_tag_filtering(self):
        models.Document.objects.create(title="Test document with no tags")

        document_one_tag = models.Document.objects.create(
            title="Test document with one tag"
        )
        document_one_tag.tags.add("one")

        document_two_tags = models.Document.objects.create(
            title="Test document with two tags"
        )
        document_two_tags.tags.add("one", "two")

        document_unrelated_tag = models.Document.objects.create(
            title="Test document with a different tag"
        )
        document_unrelated_tag.tags.add("unrelated")

        # no filtering
        response = self.get()
        # four documents created above
        self.assertEqual(response.context["page_obj"].paginator.count, 4)

        # filter all documents with tag 'one'
        response = self.get({"tag": "one"})
        self.assertEqual(response.context["page_obj"].paginator.count, 2)

        # filter all documents with tag 'two'
        response = self.get({"tag": "two"})
        self.assertEqual(response.context["page_obj"].paginator.count, 1)

        # filter all documents with tag 'one' or 'unrelated'
        response = self.get({"tag": ["one", "unrelated"]})
        self.assertEqual(response.context["page_obj"].paginator.count, 3)

        soup = self.get_soup(response.content)

        # Should check the 'one' and 'unrelated' tags checkboxes
        tags = soup.select("#id_tag label")
        self.assertCountEqual(
            [
                tag.get_text(strip=True)
                for tag in tags
                if tag.select_one("input[checked]") is not None
            ],
            ["one", "unrelated"],
        )

        # Should render the active filter pills separately for each tag
        active_filters = soup.select('[data-w-active-filter-id="id_tag"]')
        self.assertCountEqual(
            [filter.get_text(separator=" ", strip=True) for filter in active_filters],
            ["Tag: one", "Tag: unrelated"],
        )

    def test_tag_filtering_preserves_other_params(self):
        for i in range(1, 130):
            document = models.Document.objects.create(title="Test document %i" % i)
            if i % 2 != 0:
                document.tags.add("even")
                document.save()

        response = self.get({"tag": "even", "p": 2})
        self.assertEqual(response.status_code, 200)

        response_body = response.content.decode("utf8")

        # prev link should exist and include tag
        self.assertTrue(
            "?p=1&amp;tag=even" in response_body or "?tag=even&amp;p=1" in response_body
        )
        # next link should exist and include tag
        self.assertTrue(
            "?p=3&amp;tag=even" in response_body or "?tag=even&amp;p=3" in response_body
        )


class TestDocumentIndexViewSearch(WagtailTestUtils, TransactionTestCase):
    def setUp(self):
        Collection.add_root(name="Root")
        self.login()

    def get(self, params={}):
        return self.client.get(reverse("wagtaildocs:index"), params)

    def make_docs(self):
        for i in range(50):
            document = models.Document(title="Test " + str(i))
            document.save()

    def test_search(self):
        models.Document.objects.create(title="Hello document")
        models.Document.objects.create(title="Bonjour document")

        response = self.get({"q": "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["query_string"], "Hello")
        self.assertContains(response, "Hello document")
        self.assertNotContains(response, "Bonjour document")

    def test_search_partial(self):
        models.Document.objects.create(title="Hello document")
        models.Document.objects.create(title="Bonjour document")

        response = self.get({"q": "bonj"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["query_string"], "bonj")
        self.assertNotContains(response, "Hello document")
        self.assertContains(response, "Bonjour document")

    def test_empty_q(self):
        models.Document.objects.create(title="Hello document")
        models.Document.objects.create(title="Bonjour document")

        response = self.get({"q": ""})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "This field is required.")
        self.assertContains(response, "Hello document")
        self.assertContains(response, "Bonjour document")

    def test_pagination_q(self):
        self.make_docs()

        response = self.get({"q": "Test"})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaildocs/documents/index.html")
        self.assertContains(response, "There are 50 matches")

    def test_tag_filtering_with_search_term(self):
        models.Document.objects.create(title="Test document with no tags")

        document_one_tag = models.Document.objects.create(
            title="Test document with one tag"
        )
        document_one_tag.tags.add("one")

        document_two_tags = models.Document.objects.create(
            title="Test document with two tags"
        )
        document_two_tags.tags.add("one", "two")

        # The tag shouldn't be ignored, so the result should be the documents
        # that have the "one" tag and "test" in the title.
        response = self.get({"tag": "one", "q": "test"})
        self.assertEqual(response.context["page_obj"].paginator.count, 2)

    def test_search_and_order_by_created_at(self):
        # Create Documents, change their created_at dates after creation as
        # the field has auto_now_add=True
        doc1 = models.Document.objects.create(title="recent good Document")
        doc1.created_at = local_datetime(2024, 1, 1)
        doc1.save()

        doc2 = models.Document.objects.create(title="latest ok Document")
        doc2.created_at = local_datetime(2025, 1, 1)
        doc2.save()

        doc3 = models.Document.objects.create(title="oldest good document")
        doc3.created_at = local_datetime(2023, 1, 1)
        doc3.save()

        cases = [
            ("created_at", [doc3, doc1]),
            ("-created_at", [doc1, doc3]),
        ]

        for ordering, expected_docs in cases:
            with self.subTest(ordering=ordering):
                response = self.get({"q": "good", "ordering": ordering})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["query_string"], "good")

                # Check that the documents are filtered by the search query
                # and are in the correct order
                documents = list(response.context["page_obj"].object_list)
                self.assertEqual(documents, expected_docs)
                self.assertIn("ordering", response.context)
                self.assertEqual(response.context["ordering"], ordering)


class TestDocumentIndexResultsView(WagtailTestUtils, TransactionTestCase):
    def setUp(self):
        Collection.add_root(name="Root")
        self.login()

    def get(self, params={}):
        return self.client.get(reverse("wagtaildocs:index_results"), params)

    def test_search(self):
        doc = models.Document.objects.create(title="A boring report")

        response = self.get({"q": "boring"})
        params = urlencode({"next": "/admin/documents/?q=boring"})
        self.assertEqual(response.status_code, 200)
        # 'next' param on edit page link should point back to the documents index, not the results view
        self.assertContains(response, f"/admin/documents/edit/{doc.pk}/?{params}")
        self.assertNotContains(response, "<th>Collection</th>", html=True)
        self.assertNotContains(response, "<td>Root</td>", html=True)

    def test_search_with_collection(self):
        root_collection = Collection.get_first_root_node()
        root_collection.add_child(name="Evil plans")
        doc = models.Document.objects.create(title="A boring report")

        response = self.get({"q": "boring"})
        params = urlencode({"next": "/admin/documents/?q=boring"})
        self.assertEqual(response.status_code, 200)
        # 'next' param on edit page link should point back to the documents index, not the results view
        self.assertContains(response, f"/admin/documents/edit/{doc.pk}/?{params}")
        self.assertContains(response, "<th>Collection</th>", html=True)
        self.assertContains(response, "<td>Root</td>", html=True)


class TestDocumentAddView(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

    def test_get(self):
        response = self.client.get(reverse("wagtaildocs:add"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaildocs/documents/add.html")

        # as standard, only the root collection exists and so no 'Collection' option
        # is displayed on the form
        self.assertNotContains(
            response,
            '<label class="w-field__label" for="id_collection" id="id_collection-label">',
        )

        # Ensure the form supports file uploads
        self.assertContains(response, 'enctype="multipart/form-data"')

        # draftail should NOT be a standard JS include on this page
        self.assertNotContains(response, "wagtailadmin/js/draftail.js")

        self.assertBreadcrumbsItemsRendered(
            [
                {"url": reverse("wagtaildocs:index"), "label": "Documents"},
                {"url": "", "label": "New: Document"},
            ],
            response.content,
        )

    def test_get_with_collections(self):
        root_collection = Collection.get_first_root_node()
        root_collection.add_child(name="Evil plans")

        response = self.client.get(reverse("wagtaildocs:add"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaildocs/documents/add.html")

        self.assertContains(
            response,
            '<label class="w-field__label" for="id_collection" id="id_collection-label">',
        )
        self.assertContains(response, "Evil plans")

    def test_get_with_collection_nesting(self):
        root_collection = Collection.get_first_root_node()
        evil_plans = root_collection.add_child(name="Evil plans")
        evil_plans.add_child(name="Eviler plans")

        response = self.client.get(reverse("wagtaildocs:add"))
        # "Eviler Plans" should be prefixed with &#x21b3 (↳) and 4 non-breaking spaces.
        self.assertContains(response, "&nbsp;&nbsp;&nbsp;&nbsp;&#x21b3 Eviler plans")

    @override_settings(WAGTAILDOCS_DOCUMENT_MODEL="tests.CustomDocument")
    def test_get_with_custom_document_model(self):
        response = self.client.get(reverse("wagtaildocs:add"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaildocs/documents/add.html")

        # Ensure the form supports file uploads
        self.assertContains(response, 'enctype="multipart/form-data"')

        # custom fields should be included
        self.assertContains(response, 'name="fancy_description"')

        # form media should be imported
        self.assertContains(response, "wagtailadmin/js/draftail.js")

    def test_post(self):
        # Build a fake file
        fake_file = get_test_document_file()

        # Submit
        post_data = {
            "title": "Test document",
            "file": fake_file,
        }
        response = self.client.post(reverse("wagtaildocs:add"), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse("wagtaildocs:index"))

        # Document should be created, and be placed in the root collection
        document = models.Document.objects.get(title="Test document")
        root_collection = Collection.get_first_root_node()
        self.assertEqual(document.collection, root_collection)

        # Check that the file_size/hash field was set
        self.assertTrue(document.file_size)
        self.assertTrue(document.file_hash)

    def test_post_with_collections(self):
        root_collection = Collection.get_first_root_node()
        evil_plans_collection = root_collection.add_child(name="Evil plans")

        # Build a fake file
        fake_file = get_test_document_file()

        # Submit
        post_data = {
            "title": "Test document",
            "file": fake_file,
            "collection": evil_plans_collection.id,
        }
        response = self.client.post(reverse("wagtaildocs:add"), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse("wagtaildocs:index"))

        # Document should be created, and be placed in the Evil Plans collection
        self.assertTrue(models.Document.objects.filter(title="Test document").exists())
        root_collection = Collection.get_first_root_node()
        self.assertEqual(
            models.Document.objects.get(title="Test document").collection,
            evil_plans_collection,
        )

    @override_settings(WAGTAILDOCS_DOCUMENT_MODEL="tests.CustomDocument")
    def test_unique_together_validation_error(self):
        root_collection = Collection.get_first_root_node()
        evil_plans_collection = root_collection.add_child(name="Evil plans")

        # another document with a title to collide with
        CustomDocument.objects.create(
            title="Test document",
            file=get_test_document_file(),
            collection=evil_plans_collection,
        )

        post_data = {
            "title": "Test document",
            "file": get_test_document_file(),
            "collection": evil_plans_collection.id,
        }
        response = self.client.post(reverse("wagtaildocs:add"), post_data)

        # Shouldn't redirect anywhere
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaildocs/documents/add.html")

        # error message should be output on the page as a non-field error
        self.assertContains(
            response, "Custom document with this Title and Collection already exists."
        )


class TestDocumentAddViewWithLimitedCollectionPermissions(WagtailTestUtils, TestCase):
    def setUp(self):
        add_doc_permission = Permission.objects.get(
            content_type__app_label="wagtaildocs", codename="add_document"
        )
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )

        root_collection = Collection.get_first_root_node()
        self.evil_plans_collection = root_collection.add_child(name="Evil plans")

        conspirators_group = Group.objects.create(name="Evil conspirators")
        conspirators_group.permissions.add(admin_permission)
        GroupCollectionPermission.objects.create(
            group=conspirators_group,
            collection=self.evil_plans_collection,
            permission=add_doc_permission,
        )

        user = self.create_user(
            username="moriarty", email="moriarty@example.com", password="password"
        )
        user.groups.add(conspirators_group)

        self.login(username="moriarty", password="password")

    def test_get(self):
        response = self.client.get(reverse("wagtaildocs:add"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaildocs/documents/add.html")

        # user only has access to one collection, so no 'Collection' option
        # is displayed on the form
        self.assertNotContains(
            response,
            '<label class="w-field__label" for="id_collection" id="id_collection-label">',
        )

    def test_get_with_collection_nesting(self):
        self.evil_plans_collection.add_child(name="Eviler plans")

        response = self.client.get(reverse("wagtaildocs:add"))
        self.assertEqual(response.status_code, 200)
        # Unlike the above test, the user should have access to multiple Collections.
        self.assertContains(
            response,
            '<label class="w-field__label" for="id_collection" id="id_collection-label">',
        )
        # "Eviler Plans" should be prefixed with &#x21b3 (↳) and 4 non-breaking spaces.
        self.assertContains(response, "&nbsp;&nbsp;&nbsp;&nbsp;&#x21b3 Eviler plans")

    def test_post(self):
        # Build a fake file
        fake_file = get_test_document_file()

        # Submit
        post_data = {
            "title": "Test document",
            "file": fake_file,
        }
        response = self.client.post(reverse("wagtaildocs:add"), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse("wagtaildocs:index"))

        # Document should be created in the 'evil plans' collection,
        # despite there being no collection field in the form, because that's the
        # only one the user has access to
        self.assertTrue(models.Document.objects.filter(title="Test document").exists())
        self.assertEqual(
            models.Document.objects.get(title="Test document").collection,
            self.evil_plans_collection,
        )


class TestDocumentEditView(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()

        # Build a fake file
        fake_file = get_test_document_file()

        # Create a document to edit
        self.document = models.Document.objects.create(
            title="Test document", file=fake_file
        )

    def test_get_with_limited_permissions(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.client.get(
            reverse("wagtaildocs:edit", args=(self.document.id,))
        )
        self.assertEqual(response.status_code, 302)

        url_finder = AdminURLFinder(self.user)
        self.assertIsNone(url_finder.get_edit_url(self.document))

    def test_post_with_limited_permissions(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.client.post(
            reverse("wagtaildocs:edit", args=(self.document.id,)),
            {"title": "TestDoc", "file": get_test_document_file()},
        )
        self.assertEqual(response.status_code, 302)

    def test_simple(self):
        response = self.client.get(
            reverse("wagtaildocs:edit", args=(self.document.id,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaildocs/documents/edit.html")

        # Ensure the form supports file uploads
        self.assertContains(response, 'enctype="multipart/form-data"')

        # draftail should NOT be a standard JS include on this page
        # (see TestDocumentEditViewWithCustomDocumentModel - this confirms that form media
        # definitions are being respected)
        self.assertNotContains(response, "wagtailadmin/js/draftail.js")

        self.assertBreadcrumbsItemsRendered(
            [
                {"url": reverse("wagtaildocs:index"), "label": "Documents"},
                {"url": "", "label": "Test document"},
            ],
            response.content,
        )

        url_finder = AdminURLFinder(self.user)
        expected_url = "/admin/documents/edit/%d/" % self.document.id
        self.assertEqual(url_finder.get_edit_url(self.document), expected_url)

    def test_simple_with_collection_nesting(self):
        root_collection = Collection.get_first_root_node()
        evil_plans = root_collection.add_child(name="Evil plans")
        evil_plans.add_child(name="Eviler plans")

        response = self.client.get(
            reverse("wagtaildocs:edit", args=(self.document.id,))
        )
        # "Eviler Plans" should be prefixed with &#x21b3 (↳) and 4 non-breaking spaces.
        self.assertContains(response, "&nbsp;&nbsp;&nbsp;&nbsp;&#x21b3 Eviler plans")

    def test_next_url_is_present_in_edit_form(self):
        root_collection = Collection.get_first_root_node()
        evil_plans_collection = root_collection.add_child(name="Evil plans")
        doc = models.Document.objects.create(
            title="Test doc",
            file=get_test_document_file(),
            collection=evil_plans_collection,
        )
        expected_next_url = (
            reverse("wagtaildocs:index")
            + "?"
            + urlencode({"collection_id": evil_plans_collection.id})
        )

        response = self.client.get(
            reverse("wagtaildocs:edit", args=(doc.id,)), {"next": expected_next_url}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, f'<input type="hidden" value="{expected_next_url}" name="next">'
        )

    def test_post(self):
        # Build a fake file
        fake_file = get_test_document_file()

        # Submit title change
        post_data = {
            "title": "Test document changed!",
            "file": fake_file,
        }
        response = self.client.post(
            reverse("wagtaildocs:edit", args=(self.document.id,)), post_data
        )

        # User should be redirected back to the index
        self.assertRedirects(response, reverse("wagtaildocs:index"))

        # Document title should be changed
        self.assertEqual(
            models.Document.objects.get(id=self.document.id).title,
            "Test document changed!",
        )

    def test_edit_with_next_url(self):
        root_collection = Collection.get_first_root_node()
        evil_plans_collection = root_collection.add_child(name="Evil plans")
        doc = models.Document.objects.create(
            title="Test doc",
            file=get_test_document_file(),
            collection=evil_plans_collection,
        )
        expected_next_url = (
            reverse("wagtaildocs:index")
            + "?"
            + urlencode({"collection_id": evil_plans_collection.id})
        )

        response = self.client.post(
            reverse("wagtaildocs:edit", args=(doc.id,)),
            {
                "title": "Edited",
                "collection": evil_plans_collection.id,
                "next": expected_next_url,
            },
        )
        self.assertRedirects(response, expected_next_url)

        doc.refresh_from_db()
        self.assertEqual(doc.title, "Edited")

    def test_with_missing_source_file(self):
        # Build a fake file
        fake_file = get_test_document_file()

        # Create a new document to delete the source for
        document = models.Document.objects.create(
            title="Test missing source document", file=fake_file
        )
        document.file.delete(False)

        response = self.client.get(reverse("wagtaildocs:edit", args=(document.id,)), {})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaildocs/documents/edit.html")

        self.assertContains(response, "File not found")

    def test_usage_link(self):
        response = self.client.get(
            reverse("wagtaildocs:edit", args=(self.document.id,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaildocs/documents/edit.html")
        self.assertContains(response, self.document.usage_url)
        self.assertContains(response, "Used 0 times")

    def test_reupload_different_file_size_and_file_hash(self):
        """
        Checks that reuploading the document file with a different file
        changes the file size and file hash (see #5704).
        """
        # Build a fake file, and create it through the admin view
        # since self.document doesn't have a file_size set.
        fake_file = SimpleUploadedFile("some_file.txt", b"this is the content")
        post_data = {
            "title": "My doc",
            "file": fake_file,
        }
        self.client.post(reverse("wagtaildocs:add"), post_data)

        document = models.Document.objects.get(title="My doc")
        old_file_size, old_file_hash = document.file_size, document.file_hash

        new_file = SimpleUploadedFile(document.filename, b"less content")

        self.client.post(
            reverse("wagtaildocs:edit", args=(document.pk,)),
            {
                "title": document.title,
                "file": new_file,
            },
        )

        document.refresh_from_db()

        self.assertNotEqual(document.file_size, old_file_size)
        self.assertNotEqual(document.file_hash, old_file_hash)

    def test_reupload_same_name(self):
        """
        Checks that reuploading the document file with the same file name
        changes the file name, to avoid browser cache issues (see #3816).
        """
        old_filename = self.document.file.name
        new_name = self.document.filename
        new_file = SimpleUploadedFile(new_name, b"An updated test content.")

        response = self.client.post(
            reverse("wagtaildocs:edit", args=(self.document.pk,)),
            {
                "title": self.document.title,
                "file": new_file,
            },
        )
        self.assertRedirects(response, reverse("wagtaildocs:index"))
        self.document.refresh_from_db()
        self.assertEqual(old_filename, self.document.file.name)
        self.assertEqual(self.document.file.name, "documents/" + new_name)
        self.assertEqual(self.document.file.read(), b"An updated test content.")

    def test_reupload_different_name(self):
        """
        Checks that reuploading the document file with a different file name
        correctly uses the new file name.
        """
        old_filename = self.document.file.name
        new_name = "test_reupload_different_name.txt"
        new_file = SimpleUploadedFile(new_name, b"An updated test content.")

        response = self.client.post(
            reverse("wagtaildocs:edit", args=(self.document.pk,)),
            {
                "title": self.document.title,
                "file": new_file,
            },
        )
        self.assertRedirects(response, reverse("wagtaildocs:index"))
        self.document.refresh_from_db()
        self.assertFalse(self.document.file.storage.exists(old_filename))
        self.assertTrue(self.document.file.storage.exists(self.document.file.name))
        self.assertEqual(self.document.file.name, "documents/" + new_name)
        self.assertEqual(self.document.file.read(), b"An updated test content.")


@override_settings(WAGTAILDOCS_DOCUMENT_MODEL="tests.CustomDocument")
class TestDocumentEditViewWithCustomDocumentModel(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

        # Create a document to edit
        self.document = CustomDocument.objects.create(
            title="Test document",
            file=get_test_document_file(),
        )

        self.storage = self.document.file.storage

    def get(self, params={}):
        return self.client.get(
            reverse("wagtaildocs:edit", args=(self.document.id,)), params
        )

    def test_get_with_custom_document_model(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaildocs/documents/edit.html")

        # Ensure the form supports file uploads
        self.assertContains(response, 'enctype="multipart/form-data"')

        # form media should be imported
        self.assertContains(response, "wagtailadmin/js/draftail.js")

    def test_unique_together_validation_error(self):
        root_collection = Collection.get_first_root_node()
        evil_plans_collection = root_collection.add_child(name="Evil plans")

        # another document with a title to collide with
        CustomDocument.objects.create(
            title="Updated",
            file=get_test_document_file(),
            collection=evil_plans_collection,
        )

        post_data = {
            "title": "Updated",
            "collection": evil_plans_collection.id,
        }
        response = self.client.post(
            reverse("wagtaildocs:edit", args=(self.document.id,)), post_data
        )

        # Shouldn't redirect anywhere
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaildocs/documents/edit.html")

        # error message should be output on the page as a non-field error
        self.assertContains(
            response, "Custom document with this Title and Collection already exists."
        )


class TestDocumentDeleteView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()

        # Create a document to delete
        self.document = models.Document.objects.create(title="Test document")

        self.delete_url = reverse("wagtaildocs:delete", args=(self.document.id,))

    def test_delete_with_limited_permissions(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response_get = self.client.get(self.delete_url)
        response_post = self.client.post(self.delete_url)

        self.assertEqual(response_get.status_code, 302)
        self.assertEqual(response_post.status_code, 302)
        self.assertTrue(
            get_document_model().objects.filter(id=self.document.id).exists()
        )

    def test_delete_get_with_protected_reference(self):
        with self.captureOnCommitCallbacks(execute=True):
            VariousOnDeleteModel.objects.create(protected_document=self.document)
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/confirm_delete.html")
        self.assertTemplateUsed(response, "wagtailadmin/shared/usage_summary.html")
        self.assertContains(
            response,
            reverse("wagtaildocs:document_usage", args=(self.document.id,))
            + "?describe_on_delete=1",
        )
        self.assertContains(
            response,
            "One or more references to this document prevent it from being deleted.",
        )
        self.assertNotContains(response, "Yes, delete")
        self.assertNotContains(response, "No, don't delete")
        self.assertNotContains(
            response,
            f'<form action="{self.delete_url}" method="POST">',
        )

    def test_delete_post_with_protected_reference(self):
        with self.captureOnCommitCallbacks(execute=True):
            VariousOnDeleteModel.objects.create(protected_document=self.document)
        response = self.client.post(self.delete_url)
        self.assertRedirects(response, reverse("wagtailadmin_home"))
        self.assertTrue(
            get_document_model().objects.filter(id=self.document.id).exists()
        )

    def test_simple(self):
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/confirm_delete.html")
        self.assertTemplateUsed(response, "wagtailadmin/shared/usage_summary.html")
        self.assertNotContains(
            response,
            "One or more references to this document prevent it from being deleted.",
        )
        self.assertContains(response, "Yes, delete")
        self.assertContains(response, "No, don't delete")
        self.assertContains(
            response,
            f'<form action="{self.delete_url}" method="POST">',
        )

    def test_delete(self):
        # Submit title change
        response = self.client.post(
            reverse("wagtaildocs:delete", args=(self.document.id,)), follow=True
        )

        # User should be redirected back to the index
        self.assertRedirects(response, reverse("wagtaildocs:index"))

        # Document should be deleted
        self.assertFalse(models.Document.objects.filter(id=self.document.id).exists())

        # Message should be shown
        self.assertEqual(
            [m.message.strip() for m in response.context["messages"]],
            [escape("Document 'Test document' deleted.")],
        )

    def test_usage_link(self):
        response = self.client.get(
            reverse("wagtaildocs:delete", args=(self.document.id,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/confirm_delete.html")
        self.assertContains(response, self.document.usage_url)
        self.assertContains(response, "This document is referenced 0 times")


class TestMultipleDocumentUploader(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    """
    This tests the multiple document upload views located in wagtaildocs/views/multiple.py
    """

    edit_post_data = {
        "title": "New title!",
        "tags": "cromarty, finisterre",
    }

    def setUp(self):
        self.user = self.login()

        # Create a document for running tests on
        self.doc = get_document_model().objects.create(
            title="Test document",
            file=get_test_document_file(),
        )

    def check_doc_after_edit(self):
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.title, "New title!")
        self.assertIn("cromarty", self.doc.tags.names())

    def check_form_media_in_response(self, response):
        # draftail should NOT be a standard JS include on this page
        self.assertNotContains(response, "wagtailadmin/js/draftail.js")

    def test_add(self):
        """
        This tests that the add view responds correctly on a GET request
        """
        # Send request
        response = self.client.get(reverse("wagtaildocs:add_multiple"))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaildocs/multiple/add.html")

        self.assertBreadcrumbsItemsRendered(
            [
                {
                    "url": reverse("wagtaildocs:index"),
                    "label": capfirst(self.doc._meta.verbose_name_plural),
                },
                {"url": "", "label": "Add documents"},
            ],
            response.content,
        )

        # no collection chooser when only one collection exists
        self.assertNotContains(response, "id_adddocument_collection")

        self.check_form_media_in_response(response)

    def test_add_with_collections(self):
        root_collection = Collection.get_first_root_node()
        root_collection.add_child(name="Evil plans")

        # Send request
        response = self.client.get(reverse("wagtaildocs:add_multiple"))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaildocs/multiple/add.html")

        # collection chooser should exist
        self.assertContains(response, "id_adddocument_collection")
        self.assertContains(response, "Evil plans")

    def test_add_with_selected_collection(self):
        root_collection = Collection.get_first_root_node()
        collection = root_collection.add_child(name="Evil plans")

        response = self.client.get(
            reverse("wagtaildocs:add_multiple") + f"?collection_id={collection.pk}"
        )
        self.assertEqual(response.status_code, 200)
        # collection chooser should have selected collection passed with parameter
        self.assertContains(response, f'<option value="{collection.pk}" selected>')

    def test_add_post(self):
        """
        This tests that a POST request to the add view saves the document and returns an edit form
        """
        response = self.client.post(
            reverse("wagtaildocs:add_multiple"),
            {
                "files[]": SimpleUploadedFile("test.png", b"Simple text document"),
            },
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertTemplateUsed(
            response, "wagtailadmin/generic/multiple_upload/edit_form.html"
        )

        # Check document
        self.assertIn("doc", response.context)
        self.assertEqual(response.context["doc"].title, "test.png")
        self.assertTrue(response.context["doc"].file_size)
        self.assertTrue(response.context["doc"].file_hash)
        self.assertEqual(
            response.context["edit_action"],
            "/admin/documents/multiple/%d/" % response.context["doc"].id,
        )
        self.assertEqual(
            response.context["delete_action"],
            "/admin/documents/multiple/%d/delete/" % response.context["doc"].id,
        )

        # check that it is in the root collection
        doc = get_document_model().objects.get(title="test.png")
        root_collection = Collection.get_first_root_node()
        self.assertEqual(doc.collection, root_collection)

        # Check form
        self.assertIn("form", response.context)
        self.assertEqual(
            set(response.context["form"].fields),
            set(get_document_model().admin_form_fields) - {"file", "collection"},
        )
        self.assertEqual(response.context["form"].initial["title"], "test.png")

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn("doc_id", response_json)
        self.assertIn("form", response_json)
        self.assertIn("success", response_json)
        self.assertEqual(response_json["doc_id"], response.context["doc"].id)
        self.assertTrue(response_json["success"])

        # form should not contain a collection chooser
        self.assertNotIn("Collection", response_json["form"])

    def test_add_post_with_title(self):
        """
        This tests that a POST request to the add view saves the document with a supplied title and returns an edit form
        """
        response = self.client.post(
            reverse("wagtaildocs:add_multiple"),
            {
                "title": "(TXT) test title",
                "files[]": SimpleUploadedFile("test.txt", b"Simple text document"),
            },
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertTemplateUsed(
            response, "wagtailadmin/generic/multiple_upload/edit_form.html"
        )

        # Check document
        self.assertIn("doc", response.context)
        self.assertEqual(response.context["doc"].title, "(TXT) test title")
        self.assertIn(".txt", response.context["doc"].filename)
        self.assertTrue(response.context["doc"].file_size)
        self.assertTrue(response.context["doc"].file_hash)
        self.assertEqual(
            response.context["edit_action"],
            "/admin/documents/multiple/%d/" % response.context["doc"].id,
        )
        self.assertEqual(
            response.context["delete_action"],
            "/admin/documents/multiple/%d/delete/" % response.context["doc"].id,
        )

        # check that it is in the root collection
        doc = get_document_model().objects.get(title="(TXT) test title")
        root_collection = Collection.get_first_root_node()
        self.assertEqual(doc.collection, root_collection)

        # Check form
        self.assertIn("form", response.context)
        self.assertEqual(
            set(response.context["form"].fields),
            set(get_document_model().admin_form_fields) - {"file", "collection"},
        )
        self.assertEqual(response.context["form"].initial["title"], "(TXT) test title")

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn("doc_id", response_json)
        self.assertIn("form", response_json)
        self.assertIn("success", response_json)
        self.assertEqual(response_json["doc_id"], response.context["doc"].id)
        self.assertTrue(response_json["success"])

        # form should not contain a collection chooser
        self.assertNotIn("Collection", response_json["form"])

    def test_add_post_with_collections(self):
        """
        This tests that a POST request to the add view saves the document
        and returns an edit form, when collections are active
        """

        root_collection = Collection.get_first_root_node()
        evil_plans_collection = root_collection.add_child(name="Evil plans")

        response = self.client.post(
            reverse("wagtaildocs:add_multiple"),
            {
                "files[]": SimpleUploadedFile("test.png", b"Simple text document"),
                "collection": evil_plans_collection.id,
            },
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertTemplateUsed(
            response, "wagtailadmin/generic/multiple_upload/edit_form.html"
        )

        # Check document
        self.assertIn("doc", response.context)
        self.assertEqual(response.context["doc"].title, "test.png")
        self.assertTrue(response.context["doc"].file_size)
        self.assertTrue(response.context["doc"].file_hash)

        # check that it is in the 'evil plans' collection
        doc = get_document_model().objects.get(title="test.png")
        root_collection = Collection.get_first_root_node()
        self.assertEqual(doc.collection, evil_plans_collection)

        # Check form
        self.assertIn("form", response.context)
        self.assertEqual(
            set(response.context["form"].fields),
            set(get_document_model().admin_form_fields) - {"file"} | {"collection"},
        )
        self.assertEqual(response.context["form"].initial["title"], "test.png")

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn("doc_id", response_json)
        self.assertIn("form", response_json)
        self.assertIn("success", response_json)
        self.assertEqual(response_json["doc_id"], response.context["doc"].id)
        self.assertTrue(response_json["success"])

        # form should contain a collection chooser
        self.assertIn("Collection", response_json["form"])

    def test_add_post_nofile(self):
        """
        This tests that the add view checks for a file when a user POSTs to it
        """
        response = self.client.post(reverse("wagtaildocs:add_multiple"))

        # Check response
        self.assertEqual(response.status_code, 400)

    def test_edit_get(self):
        """
        This tests that a GET request to the edit view returns a 405 "METHOD NOT ALLOWED" response
        """
        # Send request
        response = self.client.get(
            reverse("wagtaildocs:edit_multiple", args=(self.doc.id,))
        )

        # Check response
        self.assertEqual(response.status_code, 405)

    def test_edit_post(self):
        """
        This tests that a POST request to the edit view edits the document
        """
        # Send request
        response = self.client.post(
            reverse("wagtaildocs:edit_multiple", args=(self.doc.id,)),
            {
                "doc-%d-%s" % (self.doc.id, field): data
                for field, data in self.edit_post_data.items()
            },
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn("doc_id", response_json)
        self.assertNotIn("form", response_json)
        self.assertIn("success", response_json)
        self.assertEqual(response_json["doc_id"], self.doc.id)
        self.assertTrue(response_json["success"])

        self.check_doc_after_edit()

    def test_edit_post_validation_error(self):
        """
        This tests that a POST request to the edit page returns a json document with "success=False"
        and a form with the validation error indicated
        """
        # Send request
        response = self.client.post(
            reverse("wagtaildocs:edit_multiple", args=(self.doc.id,)),
            {
                ("doc-%d-title" % self.doc.id): "",  # Required
                ("doc-%d-tags" % self.doc.id): "",
            },
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertTemplateUsed(
            response, "wagtailadmin/generic/multiple_upload/edit_form.html"
        )

        # Check that a form error was raised
        self.assertFormError(
            response.context["form"], "title", "This field is required."
        )

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn("doc_id", response_json)
        self.assertIn("form", response_json)
        self.assertIn("success", response_json)
        self.assertEqual(response_json["doc_id"], self.doc.id)
        self.assertFalse(response_json["success"])

    def test_delete_get(self):
        """
        This tests that a GET request to the delete view returns a 405 "METHOD NOT ALLOWED" response
        """
        # Send request
        response = self.client.get(
            reverse("wagtaildocs:delete_multiple", args=(self.doc.id,))
        )

        # Check response
        self.assertEqual(response.status_code, 405)

    def test_delete_post(self):
        """
        This tests that a POST request to the delete view deletes the document
        """
        # Send request
        response = self.client.post(
            reverse("wagtaildocs:delete_multiple", args=(self.doc.id,))
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        # Make sure the document is deleted
        self.assertFalse(get_document_model().objects.filter(id=self.doc.id).exists())

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn("doc_id", response_json)
        self.assertIn("success", response_json)
        self.assertEqual(response_json["doc_id"], self.doc.id)
        self.assertTrue(response_json["success"])


@override_settings(WAGTAILDOCS_DOCUMENT_MODEL="tests.CustomDocument")
class TestMultipleCustomDocumentUploader(TestMultipleDocumentUploader):
    edit_post_data = dict(
        TestMultipleDocumentUploader.edit_post_data, description="New description."
    )

    def check_doc_after_edit(self):
        super().check_doc_after_edit()
        self.assertEqual(self.doc.description, "New description.")

    def check_form_media_in_response(self, response):
        # form media should be imported
        self.assertContains(response, "wagtailadmin/js/draftail.js")


class TestMultipleCustomDocumentUploaderNoCollection(
    TestMultipleCustomDocumentUploader
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Document = get_document_model()
        fields = tuple(f for f in Document.admin_form_fields if f != "collection")
        cls.__patcher = mock.patch.object(Document, "admin_form_fields", fields)
        cls.__patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.__patcher.stop()
        super().tearDownClass()


@override_settings(WAGTAILDOCS_DOCUMENT_MODEL="tests.CustomDocumentWithAuthor")
class TestMultipleCustomDocumentUploaderWithRequiredField(TestMultipleDocumentUploader):
    edit_post_data = dict(
        TestMultipleDocumentUploader.edit_post_data, author="William Shakespeare"
    )

    def setUp(self):
        super().setUp()

        # Create an UploadedFile for running tests on
        self.uploaded_document = UploadedFile.objects.create(
            for_content_type=ContentType.objects.get_for_model(get_document_model()),
            file=get_test_document_file(),
            uploaded_by_user=self.user,
        )

    def test_add_post(self):
        """
        This tests that a POST request to the add view saves the document as an UploadedFile
        and returns an edit form
        """
        response = self.client.post(
            reverse("wagtaildocs:add_multiple"),
            {
                "files[]": SimpleUploadedFile("test.png", b"Simple text document"),
            },
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertTemplateUsed(
            response, "wagtailadmin/generic/multiple_upload/edit_form.html"
        )

        # Check document
        self.assertIn("uploaded_document", response.context)
        self.assertTrue(response.context["uploaded_document"].file.size)
        self.assertEqual(
            response.context["edit_action"],
            "/admin/documents/multiple/create_from_uploaded_document/%d/"
            % response.context["uploaded_document"].id,
        )
        self.assertEqual(
            response.context["delete_action"],
            "/admin/documents/multiple/delete_upload/%d/"
            % response.context["uploaded_document"].id,
        )

        # Check form
        self.assertIn("form", response.context)
        self.assertEqual(
            set(response.context["form"].fields),
            set(get_document_model().admin_form_fields) - {"file", "collection"},
        )
        self.assertEqual(response.context["form"].initial["title"], "test.png")

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn("uploaded_file_id", response_json)
        self.assertIn("form", response_json)
        self.assertIn("success", response_json)
        self.assertEqual(
            response_json["uploaded_file_id"],
            response.context["uploaded_document"].id,
        )
        self.assertTrue(response_json["success"])

        # form should not contain a collection chooser
        self.assertNotIn("Collection", response_json["form"])

    def test_add_post_with_title(self):
        """
        This tests that a POST request to the add view saves the document with a supplied title and returns an edit form
        """
        response = self.client.post(
            reverse("wagtaildocs:add_multiple"),
            {
                "title": "(TXT) test title",
                "files[]": SimpleUploadedFile("test.txt", b"Simple text document"),
            },
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertTemplateUsed(
            response, "wagtailadmin/generic/multiple_upload/edit_form.html"
        )

        # Check document
        self.assertIn("uploaded_document", response.context)
        self.assertIn(".txt", response.context["uploaded_document"].file.name)

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn("uploaded_file_id", response_json)
        self.assertIn("form", response_json)
        self.assertEqual(
            response_json["uploaded_file_id"],
            response.context["uploaded_document"].id,
        )
        self.assertTrue(response_json["success"])

    def test_add_post_with_collections(self):
        """
        This tests that a POST request to the add view saves the document
        and returns an edit form, when collections are active
        """

        root_collection = Collection.get_first_root_node()
        evil_plans_collection = root_collection.add_child(name="Evil plans")

        response = self.client.post(
            reverse("wagtaildocs:add_multiple"),
            {
                "files[]": SimpleUploadedFile("test.png", b"Simple text document"),
                "collection": evil_plans_collection.id,
            },
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertTemplateUsed(
            response, "wagtailadmin/generic/multiple_upload/edit_form.html"
        )

        # Check document
        self.assertIn("uploaded_document", response.context)
        self.assertTrue(response.context["uploaded_document"].file.size)
        self.assertEqual(
            response.context["edit_action"],
            "/admin/documents/multiple/create_from_uploaded_document/%d/"
            % response.context["uploaded_document"].id,
        )
        self.assertEqual(
            response.context["delete_action"],
            "/admin/documents/multiple/delete_upload/%d/"
            % response.context["uploaded_document"].id,
        )

        # Check form
        self.assertIn("form", response.context)
        self.assertEqual(
            set(response.context["form"].fields),
            set(get_document_model().admin_form_fields) - {"file"} | {"collection"},
        )
        self.assertEqual(response.context["form"].initial["title"], "test.png")

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn("uploaded_file_id", response_json)
        self.assertIn("form", response_json)
        self.assertIn("success", response_json)
        self.assertEqual(
            response_json["uploaded_file_id"],
            response.context["uploaded_document"].id,
        )
        self.assertTrue(response_json["success"])

        # form should contain a collection chooser
        self.assertIn("Collection", response_json["form"])

    def check_doc_after_edit(self):
        super().check_doc_after_edit()
        self.assertEqual(self.doc.author, "William Shakespeare")

    def test_create_from_upload_invalid_post(self):
        """
        Posting an invalid form to the create_from_uploaded_document view throws a validation error
        and leaves the UploadedFile intact
        """
        doc_count_before = CustomDocumentWithAuthor.objects.count()
        uploaded_doc_count_before = UploadedFile.objects.count()

        # Send request
        response = self.client.post(
            reverse(
                "wagtaildocs:create_multiple_from_uploaded_document",
                args=(self.uploaded_document.id,),
            ),
            {
                (
                    "uploaded-document-%d-title" % self.uploaded_document.id
                ): "New title!",
                ("uploaded-document-%d-tags" % self.uploaded_document.id): "",
                ("uploaded-document-%d-author" % self.uploaded_document.id): "",
            },
        )

        doc_count_after = CustomDocumentWithAuthor.objects.count()
        uploaded_doc_count_after = UploadedFile.objects.count()

        # no changes to document / UploadedFile count
        self.assertEqual(doc_count_after, doc_count_before)
        self.assertEqual(uploaded_doc_count_after, uploaded_doc_count_before)

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        # Check form
        self.assertIn("form", response.context)
        self.assertIn("author", response.context["form"].fields)
        self.assertEqual(
            response.context["edit_action"],
            "/admin/documents/multiple/create_from_uploaded_document/%d/"
            % response.context["uploaded_document"].id,
        )
        self.assertEqual(
            response.context["delete_action"],
            "/admin/documents/multiple/delete_upload/%d/"
            % response.context["uploaded_document"].id,
        )
        self.assertFormError(
            response.context["form"], "author", "This field is required."
        )

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn("form", response_json)
        self.assertIn("New title!", response_json["form"])
        self.assertFalse(response_json["success"])

    def test_create_from_upload(self):
        """
        Posting a valid form to the create_from_uploaded_document view will create the document
        """
        doc_count_before = CustomDocumentWithAuthor.objects.count()
        uploaded_doc_count_before = UploadedFile.objects.count()

        # Send request
        response = self.client.post(
            reverse(
                "wagtaildocs:create_multiple_from_uploaded_document",
                args=(self.uploaded_document.id,),
            ),
            {
                (
                    "uploaded-document-%d-title" % self.uploaded_document.id
                ): "New title!",
                (
                    "uploaded-document-%d-tags" % self.uploaded_document.id
                ): "fairies, donkey",
                (
                    "uploaded-document-%d-author" % self.uploaded_document.id
                ): "William Shakespeare",
            },
        )

        doc_count_after = CustomDocumentWithAuthor.objects.count()
        uploaded_doc_count_after = UploadedFile.objects.count()

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn("doc_id", response_json)
        self.assertTrue(response_json["success"])

        # Document should have been created, UploadedFile deleted
        self.assertEqual(doc_count_after, doc_count_before + 1)
        self.assertEqual(uploaded_doc_count_after, uploaded_doc_count_before - 1)

        doc = CustomDocumentWithAuthor.objects.get(id=response_json["doc_id"])
        self.assertEqual(doc.title, "New title!")
        self.assertEqual(doc.author, "William Shakespeare")
        self.assertTrue(doc.file.name)
        self.assertTrue(doc.file_hash)
        self.assertTrue(doc.file_size)
        self.assertIn("donkey", doc.tags.names())

    def test_delete_uploaded_document(self):
        """
        This tests that a POST request to the delete view deletes the UploadedFile
        """
        # Send request
        response = self.client.post(
            reverse(
                "wagtaildocs:delete_upload_multiple", args=(self.uploaded_document.id,)
            )
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        # Make sure the document is deleted
        self.assertFalse(
            UploadedFile.objects.filter(id=self.uploaded_document.id).exists()
        )

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertTrue(response_json["success"])


class TestDocumentChooserView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()

    def test_simple(self):
        response = self.client.get(reverse("wagtaildocs_chooser:choose"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/chooser/chooser.html")
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json["step"], "choose")

        # draftail should NOT be a standard JS include on this page
        self.assertNotIn("wagtailadmin/js/draftail.js", response_json["html"])

    def test_simple_with_collection_nesting(self):
        root_collection = Collection.get_first_root_node()
        evil_plans = root_collection.add_child(name="Evil plans")
        evil_plans.add_child(name="Eviler plans")

        response = self.client.get(reverse("wagtaildocs_chooser:choose"))
        # "Eviler Plans" should be prefixed with &#x21b3 (↳) and 4 non-breaking spaces.
        self.assertContains(response, "&nbsp;&nbsp;&nbsp;&nbsp;&#x21b3 Eviler plans")

    @override_settings(WAGTAILDOCS_DOCUMENT_MODEL="tests.CustomDocument")
    def test_with_custom_document_model(self):
        response = self.client.get(reverse("wagtaildocs_chooser:choose"))
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json["step"], "choose")
        self.assertTemplateUsed(response, "wagtailadmin/generic/chooser/chooser.html")

        # custom form fields should be present
        self.assertIn(
            'name="document-chooser-upload-fancy_description"', response_json["html"]
        )

        # form media imports should appear on the page
        self.assertIn("wagtailadmin/js/draftail.js", response_json["html"])

    def test_search(self):
        response = self.client.get(
            reverse("wagtaildocs_chooser:choose_results"), {"q": "Hello"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["search_query"], "Hello")

    def make_docs(self):
        for i in range(50):
            document = models.Document(title="Test " + str(i))
            document.save()

    def test_pagination(self):
        self.make_docs()

        response = self.client.get(
            reverse("wagtaildocs_chooser:choose_results"), {"p": 2}
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaildocs/chooser/results.html")

        # Check that we got the correct page
        self.assertEqual(response.context["results"].number, 2)

    def test_pagination_invalid(self):
        self.make_docs()

        response = self.client.get(
            reverse("wagtaildocs_chooser:choose_results"), {"p": "Hello World!"}
        )

        # Check response
        self.assertEqual(response.status_code, 404)

    def test_pagination_out_of_range(self):
        self.make_docs()

        response = self.client.get(
            reverse("wagtaildocs_chooser:choose_results"), {"p": 99999}
        )

        # Check response
        self.assertEqual(response.status_code, 404)

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

        with self.register_hook(
            "construct_document_chooser_queryset", filter_documents
        ):
            response = self.client.get(reverse("wagtaildocs_chooser:choose"))
        self.assertEqual(len(response.context["results"]), 1)
        self.assertEqual(response.context["results"][0], document)

    def test_index_without_collections(self):
        self.make_docs()

        response = self.client.get(reverse("wagtaildocs:index"))
        self.assertNotContains(response, "<th>Collection</th>", html=True)
        self.assertNotContains(response, "<td>Root</td>", html=True)

    def test_index_with_collection(self):
        root_collection = Collection.get_first_root_node()
        root_collection.add_child(name="Evil plans")

        self.make_docs()

        response = self.client.get(reverse("wagtaildocs:index"))
        self.assertContains(response, "<th>Collection</th>", html=True)
        self.assertContains(response, "<td>Root</td>", html=True)


class TestDocumentChooserViewSearch(WagtailTestUtils, TransactionTestCase):
    fixtures = ["test_empty.json"]

    def setUp(self):
        self.user = self.login()

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

        with self.register_hook(
            "construct_document_chooser_queryset", filter_documents
        ):
            response = self.client.get(
                reverse("wagtaildocs_chooser:choose_results"), {"q": "Test"}
            )
        self.assertEqual(len(response.context["results"]), 1)
        self.assertEqual(response.context["results"][0], document)


class TestDocumentChooserChosenView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

        # Create a document to choose
        self.document = models.Document.objects.create(title="Test document")

    def test_simple(self):
        response = self.client.get(
            reverse("wagtaildocs_chooser:chosen", args=(self.document.id,))
        )
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json["step"], "chosen")


class TestDocumentChooserUploadView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

    def test_simple(self):
        response = self.client.get(reverse("wagtaildocs_chooser:create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/generic/chooser/creation_form.html"
        )
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json["step"], "reshow_creation_form")

    def test_post(self):
        # Build a fake file
        fake_file = get_test_document_file()

        # Submit
        post_data = {
            "document-chooser-upload-title": "Test document",
            "document-chooser-upload-file": fake_file,
        }
        response = self.client.post(reverse("wagtaildocs_chooser:create"), post_data)

        # Check that the response is the 'chosen' step
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json["step"], "chosen")

        # Document should be created
        self.assertTrue(models.Document.objects.filter(title="Test document").exists())

    @override_settings(WAGTAILDOCS_DOCUMENT_MODEL="tests.CustomDocument")
    def test_unique_together_validation(self):
        root_collection = Collection.get_first_root_node()
        evil_plans_collection = root_collection.add_child(name="Evil plans")
        # another document with a title to collide with
        CustomDocument.objects.create(
            title="Test document",
            file=get_test_document_file(),
            collection=evil_plans_collection,
        )

        response = self.client.post(
            reverse("wagtaildocs_chooser:create"),
            {
                "document-chooser-upload-title": "Test document",
                "document-chooser-upload-file": get_test_document_file(),
                "document-chooser-upload-collection": evil_plans_collection.id,
            },
        )

        # Shouldn't redirect anywhere
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/generic/chooser/creation_form.html"
        )

        # The form should have an error
        self.assertContains(
            response, "Custom document with this Title and Collection already exists."
        )


class TestDocumentChooserUploadViewWithLimitedPermissions(WagtailTestUtils, TestCase):
    def setUp(self):
        add_doc_permission = Permission.objects.get(
            content_type__app_label="wagtaildocs", codename="add_document"
        )
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )

        root_collection = Collection.get_first_root_node()
        self.evil_plans_collection = root_collection.add_child(name="Evil plans")

        conspirators_group = Group.objects.create(name="Evil conspirators")
        conspirators_group.permissions.add(admin_permission)
        GroupCollectionPermission.objects.create(
            group=conspirators_group,
            collection=self.evil_plans_collection,
            permission=add_doc_permission,
        )

        user = self.create_user(
            username="moriarty", email="moriarty@example.com", password="password"
        )
        user.groups.add(conspirators_group)

        self.login(username="moriarty", password="password")

    def test_simple(self):
        response = self.client.get(reverse("wagtaildocs_chooser:create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/generic/chooser/creation_form.html"
        )
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json["step"], "reshow_creation_form")

        # user only has access to one collection -> should not see the collections field
        self.assertNotIn("id_collection", response_json["htmlFragment"])

    def test_chooser_view(self):
        # The main chooser view also includes the form, so need to test there too
        response = self.client.get(reverse("wagtaildocs_chooser:choose"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/chooser/chooser.html")
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json["step"], "choose")

        # user only has access to one collection -> should not see the collections field
        self.assertNotIn("id_collection", response_json["html"])

    def test_post(self):
        # Build a fake file
        fake_file = get_test_document_file()

        # Submit
        post_data = {
            "document-chooser-upload-title": "Test document",
            "document-chooser-upload-file": fake_file,
        }
        response = self.client.post(reverse("wagtaildocs_chooser:create"), post_data)

        # Check that the response is the 'chosen' step
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json["step"], "chosen")

        # Document should be created
        doc = models.Document.objects.filter(title="Test document")
        self.assertTrue(doc.exists())

        # Document should be in the 'evil plans' collection
        self.assertEqual(doc.get().collection, self.evil_plans_collection)


class TestUsageCount(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.login()

    def test_unused_document_usage_count(self):
        doc = models.Document.objects.get(id=1)
        self.assertEqual(doc.get_usage().count(), 0)

    def test_used_document_usage_count(self):
        with self.captureOnCommitCallbacks(execute=True):
            doc = models.Document.objects.get(id=1)
            page = EventPage.objects.get(id=4)
            event_page_related_link = EventPageRelatedLink()
            event_page_related_link.page = page
            event_page_related_link.link_document = doc
            event_page_related_link.save()
        self.assertEqual(doc.get_usage().count(), 1)

    def test_usage_count_appears(self):
        with self.captureOnCommitCallbacks(execute=True):
            doc = models.Document.objects.get(id=1)
            page = EventPage.objects.get(id=4)
            event_page_related_link = EventPageRelatedLink()
            event_page_related_link.page = page
            event_page_related_link.link_document = doc
            event_page_related_link.save()
        response = self.client.get(reverse("wagtaildocs:edit", args=(1,)))
        self.assertContains(response, "Used 1 time")

    def test_usage_count_zero_appears(self):
        response = self.client.get(reverse("wagtaildocs:edit", args=(1,)))
        self.assertContains(response, "Used 0 times")

    def test_usage_count_column_with_document_usage(self):
        with self.captureOnCommitCallbacks(execute=True):
            doc = models.Document.objects.get(id=1)
            page = EventPage.objects.get(id=4)
            event_page_related_link = EventPageRelatedLink()
            event_page_related_link.page = page
            event_page_related_link.link_document = doc
            event_page_related_link.save()

        response = self.client.get(reverse("wagtaildocs:index"), {"layout": "list"})
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Used 1 time")

        expected_url = "/admin/documents/usage/1/"
        self.assertContains(response, expected_url)

    def test_usage_count_column_no_document_usage(self):
        response = self.client.get(reverse("wagtaildocs:index"), {"layout": "list"})
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Used 0 times")

        expected_url = "/admin/documents/usage/1/"
        self.assertContains(response, expected_url)


class TestGetUsage(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.login()

    def test_unused_document_get_usage(self):
        doc = models.Document.objects.get(id=1)
        self.assertEqual(list(doc.get_usage()), [])

    def test_used_document_get_usage(self):
        with self.captureOnCommitCallbacks(execute=True):
            doc = models.Document.objects.get(id=1)
            page = EventPage.objects.get(id=4)
            event_page_related_link = EventPageRelatedLink()
            event_page_related_link.page = page
            event_page_related_link.link_document = doc
            event_page_related_link.save()

        self.assertIsInstance(doc.get_usage()[0], tuple)
        self.assertIsInstance(doc.get_usage()[0][0], Page)
        self.assertIsInstance(doc.get_usage()[0][1], list)
        self.assertIsInstance(doc.get_usage()[0][1][0], ReferenceIndex)

    def test_usage_page(self):
        with self.captureOnCommitCallbacks(execute=True):
            doc = models.Document.objects.get(id=1)
            page = EventPage.objects.get(id=4)
            event_page_related_link = EventPageRelatedLink()
            event_page_related_link.page = page
            event_page_related_link.link_document = doc
            event_page_related_link.save()
        response = self.client.get(reverse("wagtaildocs:document_usage", args=(1,)))
        self.assertContains(response, "Christmas")
        self.assertContains(response, '<table class="listing">')
        self.assertContains(response, "<td>Event page</td>", html=True)
        self.assertBreadcrumbsItemsRendered(
            [
                {
                    "url": reverse("wagtaildocs:index"),
                    "label": "Documents",
                },
                {
                    "url": reverse("wagtaildocs:edit", args=(1,)),
                    "label": "test document",
                },
                {
                    "url": "",
                    "label": "Usage",
                    "sublabel": "test document",
                },
            ],
            response.content,
        )

    def test_usage_page_no_usage(self):
        response = self.client.get(reverse("wagtaildocs:document_usage", args=(1,)))
        # There's no usage so there should be no listing table
        self.assertNotContains(response, '<table class="listing">')

    def test_usage_page_with_only_change_permission(self):
        with self.captureOnCommitCallbacks(execute=True):
            doc = models.Document.objects.get(id=1)
            page = EventPage.objects.get(id=4)
            event_page_related_link = EventPageRelatedLink()
            event_page_related_link.page = page
            event_page_related_link.link_document = doc
            event_page_related_link.save()

        # Create a user with change_document permission but not add_document
        user = self.create_user(
            username="changeonly", email="changeonly@example.com", password="password"
        )
        change_permission = Permission.objects.get(
            content_type__app_label="wagtaildocs", codename="change_document"
        )
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        self.changers_group = Group.objects.create(name="Document changers")
        GroupCollectionPermission.objects.create(
            group=self.changers_group,
            collection=Collection.get_first_root_node(),
            permission=change_permission,
        )
        user.groups.add(self.changers_group)

        user.user_permissions.add(admin_permission)
        self.login(username="changeonly", password="password")

        response = self.client.get(reverse("wagtaildocs:document_usage", args=[1]))

        self.assertEqual(response.status_code, 200)
        # User has no permission over the page linked to, so should not see its details
        self.assertNotContains(response, "Christmas")
        self.assertContains(response, "(Private page)")
        self.assertContains(response, "<td>Event page</td>", html=True)

    def test_usage_page_without_change_permission(self):
        # Create a user with add_document permission but not change_document
        user = self.create_user(
            username="addonly", email="addonly@example.com", password="password"
        )
        add_permission = Permission.objects.get(
            content_type__app_label="wagtaildocs", codename="add_document"
        )
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        self.adders_group = Group.objects.create(name="Document adders")
        GroupCollectionPermission.objects.create(
            group=self.adders_group,
            collection=Collection.get_first_root_node(),
            permission=add_permission,
        )
        user.groups.add(self.adders_group)

        user.user_permissions.add(admin_permission)
        self.login(username="addonly", password="password")

        response = self.client.get(reverse("wagtaildocs:document_usage", args=[1]))

        self.assertEqual(response.status_code, 302)


class TestEditOnlyPermissions(WagtailTestUtils, TestCase):
    def setUp(self):
        # Build a fake file
        fake_file = get_test_document_file()

        self.root_collection = Collection.get_first_root_node()
        self.evil_plans_collection = self.root_collection.add_child(name="Evil plans")
        self.nice_plans_collection = self.root_collection.add_child(name="Nice plans")

        # Create a document to edit
        self.document = models.Document.objects.create(
            title="Test document", file=fake_file, collection=self.nice_plans_collection
        )

        # Create a user with change_document permission but not add_document
        user = self.create_user(
            username="changeonly", email="changeonly@example.com", password="password"
        )
        change_permission = Permission.objects.get(
            content_type__app_label="wagtaildocs", codename="change_document"
        )
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        self.changers_group = Group.objects.create(name="Document changers")
        GroupCollectionPermission.objects.create(
            group=self.changers_group,
            collection=self.root_collection,
            permission=change_permission,
        )
        user.groups.add(self.changers_group)

        user.user_permissions.add(admin_permission)
        self.login(username="changeonly", password="password")

    def test_get_index(self):
        response = self.client.get(reverse("wagtaildocs:index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaildocs/documents/index.html")

        # user should not get an "Add a document" button
        self.assertNotContains(response, "Add a document")

        # user should be able to see documents not owned by them
        self.assertContains(response, "Test document")

    def test_search(self):
        response = self.client.get(reverse("wagtaildocs:index"), {"q": "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["query_string"], "Hello")

    def test_get_add(self):
        response = self.client.get(reverse("wagtaildocs:add"))
        # permission should be denied
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_get_edit(self):
        response = self.client.get(
            reverse("wagtaildocs:edit", args=(self.document.id,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaildocs/documents/edit.html")

        # documents can only be moved to collections you have add permission for,
        # so the 'collection' field is not available here
        self.assertNotContains(
            response,
            '<label class="w-field__label" for="id_collection" id="id_collection-label">',
        )

        # if the user has add permission on a different collection,
        # they should have option to move the document
        add_permission = Permission.objects.get(
            content_type__app_label="wagtaildocs", codename="add_document"
        )
        GroupCollectionPermission.objects.create(
            group=self.changers_group,
            collection=self.evil_plans_collection,
            permission=add_permission,
        )
        response = self.client.get(
            reverse("wagtaildocs:edit", args=(self.document.id,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<label class="w-field__label" for="id_collection" id="id_collection-label">',
        )
        self.assertContains(response, "Nice plans")
        self.assertContains(response, "Evil plans")

    def test_post_edit(self):
        # Submit title change
        response = self.client.post(
            reverse("wagtaildocs:edit", args=(self.document.id,)),
            {
                "title": "Test document changed!",
                "file": "",
            },
        )

        # User should be redirected back to the index
        self.assertRedirects(response, reverse("wagtaildocs:index"))

        # Document title should be changed
        self.assertEqual(
            models.Document.objects.get(id=self.document.id).title,
            "Test document changed!",
        )

        # collection should be unchanged
        self.assertEqual(
            models.Document.objects.get(id=self.document.id).collection,
            self.nice_plans_collection,
        )

        # if the user has add permission on a different collection,
        # they should have option to move the document
        add_permission = Permission.objects.get(
            content_type__app_label="wagtaildocs", codename="add_document"
        )
        GroupCollectionPermission.objects.create(
            group=self.changers_group,
            collection=self.evil_plans_collection,
            permission=add_permission,
        )
        self.client.post(
            reverse("wagtaildocs:edit", args=(self.document.id,)),
            {
                "title": "Test document changed!",
                "collection": self.evil_plans_collection.id,
                "file": "",
            },
        )
        self.assertEqual(
            models.Document.objects.get(id=self.document.id).collection,
            self.evil_plans_collection,
        )

    def test_get_delete(self):
        response = self.client.get(
            reverse("wagtaildocs:delete", args=(self.document.id,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/confirm_delete.html")

    def test_get_add_multiple(self):
        response = self.client.get(reverse("wagtaildocs:add_multiple"))
        # permission should be denied
        self.assertRedirects(response, reverse("wagtailadmin_home"))
