import datetime
from io import BytesIO
from unittest import mock

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core import checks
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings
from django.utils.timezone import make_aware
from openpyxl import load_workbook

from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.admin.panels import FieldPanel, TabbedInterface
from wagtail.contrib.modeladmin.helpers.search import DjangoORMSearchHandler
from wagtail.documents.models import Document
from wagtail.documents.tests.utils import get_test_document_file
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Locale, ModelLogEntry, Page
from wagtail.test.modeladmintest.models import (
    Author,
    Book,
    Publisher,
    RelatedLink,
    Token,
    TranslatableBook,
)
from wagtail.test.modeladmintest.wagtail_hooks import BookModelAdmin, EventsAdminGroup
from wagtail.test.utils import WagtailTestUtils


class TestBookIndexView(WagtailTestUtils, TestCase):
    fixtures = ["modeladmintest_test.json"]

    def setUp(self):
        self.login()

        img = Image.objects.create(
            title="LOTR cover",
            file=get_test_image_file(),
        )
        book = Book.objects.get(title="The Lord of the Rings")
        book.cover_image = img
        book.save()

    def get(self, **params):
        return self.client.get("/admin/modeladmintest/book/", params)

    def test_thumbnail_image_col_header_text(self):
        response = self.get()

        # check thumb_col_header_text is correctly used
        self.assertContains(
            response,
            '<th scope="col" class="column-admin_thumb">The cover</th>',
            html=True,
        )

    def test_simple(self):
        response = self.get()

        self.assertEqual(response.status_code, 200)

        # There are four books in the test data
        self.assertEqual(response.context["result_count"], 4)

        # The result count content is shown in the header
        self.assertContains(
            response, '<span class="result-count">4 out of 4</span>', html=True
        )

        # User has add permission
        self.assertIs(response.context["user_can_create"], True)

    def test_csv_export(self):
        # Export the whole queryset
        response = self.get(export="csv")

        self.assertEqual(response.status_code, 200)
        # Check attachment is present and named correctly using the modeladmin export_filename
        self.assertEqual(
            response.get("content-disposition"),
            'attachment; filename="books-export.csv"',
        )

        # Check response - all books should be in it
        data_lines = response.getvalue().decode().split("\n")
        self.assertEqual(data_lines[0], "Title,Author,Author Date Of Birth\r")
        self.assertEqual(
            data_lines[1], "Charlie and the Chocolate Factory,Roald Dahl,1916-09-13\r"
        )
        self.assertEqual(
            data_lines[2],
            "The Chronicles of the Lord of Narnia,Roald Dahl,1898-11-29\r",
        )
        self.assertEqual(data_lines[3], "The Hobbit,J. R. R. Tolkien,1892-01-03\r")
        self.assertEqual(
            data_lines[4], "The Lord of the Rings,J. R. R. Tolkien,1892-01-03\r"
        )

    def test_xlsx_export(self):
        # Export the whole queryset
        response = self.get(export="xlsx")

        self.assertEqual(response.status_code, 200)
        # Check attachment is present and named correctly using the modeladmin export_filename
        self.assertEqual(
            response.get("content-disposition"),
            'attachment; filename="books-export.xlsx"',
        )

        # Check response - all books should be in it
        workbook_data = response.getvalue()
        worksheet = load_workbook(filename=BytesIO(workbook_data))["Sheet1"]
        cell_array = [[cell.value for cell in row] for row in worksheet.rows]
        self.assertEqual(cell_array[0], ["Title", "Author", "Author Date Of Birth"])
        self.assertEqual(
            cell_array[1],
            ["Charlie and the Chocolate Factory", "Roald Dahl", "1916-09-13"],
        )
        self.assertEqual(
            cell_array[2],
            ["The Chronicles of the Lord of Narnia", "Roald Dahl", "1898-11-29"],
        )
        self.assertEqual(
            cell_array[3], ["The Hobbit", "J. R. R. Tolkien", "1892-01-03"]
        )
        self.assertEqual(
            cell_array[4], ["The Lord of the Rings", "J. R. R. Tolkien", "1892-01-03"]
        )
        self.assertEqual(len(cell_array), 5)

    def test_tr_attributes(self):
        response = self.get()

        # Charlie & The Chocolate factory should be in the list with the
        # `data-author_yob` and `data-object_pk` attributes added
        self.assertContains(response, 'data-author-yob="1916"')
        self.assertContains(response, 'data-object-pk="3"')

        # There should be two odd rows and two even ones, and 'book' should be
        # added to the `class` attribute for every one.
        self.assertContains(response, 'class="book odd"', count=2)
        self.assertContains(response, 'class="book even"', count=2)

    def test_filter(self):
        # Filter by author 1 (JRR Tolkien)
        response = self.get(author__id__exact=1)

        self.assertEqual(response.status_code, 200)

        # JRR Tolkien has two books in the test data
        self.assertEqual(response.context["result_count"], 2)

        # The result count content is shown in the header
        self.assertContains(
            response, '<span class="result-count">2 out of 4</span>', html=True
        )

        # The search form should retain the filter
        self.assertContains(
            response,
            '<input type="hidden" name="author__id__exact" value="1">',
            html=True,
        )

        for book in response.context["object_list"]:
            self.assertEqual(book.author_id, 1)

    def test_filtered_csv_export(self):
        # Filter by author 1 (JRR Tolkien) and export the current selection
        response = self.get(author__id__exact=1, export="csv")

        # Check response - only books by JRR Tolkien should be in it
        self.assertEqual(response.status_code, 200)
        data_lines = response.getvalue().decode().split("\n")
        self.assertEqual(data_lines[0], "Title,Author,Author Date Of Birth\r")
        self.assertEqual(data_lines[1], "The Hobbit,J. R. R. Tolkien,1892-01-03\r")
        self.assertEqual(
            data_lines[2], "The Lord of the Rings,J. R. R. Tolkien,1892-01-03\r"
        )
        self.assertEqual(data_lines[3], "")

    def test_search_form_present(self):
        # Test the backend search handler allows the search form to render
        response = self.get()

        self.assertContains(response, '<input id="id_q"')

    def test_search_form_absent(self):
        # DjangoORMSearchHandler + no search_fields, search form should be absent
        with mock.patch.object(
            BookModelAdmin, "search_handler_class", DjangoORMSearchHandler
        ):
            response = self.get()

            self.assertNotContains(response, '<input id="id_q"')

    def test_ordering(self):
        response = self.get(o="0.1")

        self.assertEqual(response.status_code, 200)

        # There are four books in the test data
        self.assertEqual(response.context["result_count"], 4)

    def test_paging(self):
        # should be corrected to just the first page, as there aren't enough
        # objects to make up more than one page
        response = self.get(p=9)

        self.assertEqual(response.status_code, 200)

        # There are four books in the test data
        self.assertEqual(response.context["result_count"], 4)

        # Should raise a ValueError that gets caught during initialisation
        response = self.get(p="notaninteger")

        self.assertEqual(response.status_code, 200)

        # There are four books in the test data
        self.assertEqual(response.context["result_count"], 4)


class TestBookIndexViewSearch(WagtailTestUtils, TransactionTestCase):
    fixtures = ["modeladmintest_test.json"]

    def setUp(self):
        self.login()

        img = Image.objects.create(
            title="LOTR cover",
            file=get_test_image_file(),
        )
        book = Book.objects.get(title="The Lord of the Rings")
        book.cover_image = img
        book.save()

    def get(self, **params):
        return self.client.get("/admin/modeladmintest/book/", params)

    def test_search_indexed(self):
        response = self.get(q="lord")

        self.assertEqual(response.status_code, 200)

        # There are two books where the title contains 'lord'
        self.assertEqual(response.context["result_count"], 2)

        # The result count content is shown in the header
        self.assertContains(
            response, '<span class="result-count">2 out of 4</span>', html=True
        )


class TestAuthorIndexView(WagtailTestUtils, TestCase):
    fixtures = ["modeladmintest_test.json"]

    def setUp(self):
        self.login()

    def get(self, **params):
        return self.client.get("/admin/modeladmintest/author/", params)

    def test_search(self):
        response = self.get(q="Roald Dahl")

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context["result_count"], 2)

        # The result count content is shown in the header
        self.assertContains(
            response, '<span class="result-count">2 out of 5</span>', html=True
        )

    def test_col_extra_class_names(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        test_html = """
            <td class="field-first_book for-author-1 title">The Lord of the Rings</td>
        """
        self.assertContains(response, test_html, html=True)

    def test_col_extra_attributes(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        test_html = """
            <td class="field-last_book title" data-for_author="1">The Hobbit</td>
        """
        self.assertContains(response, test_html, html=True)

    def test_title_column_links_to_edit_view_by_default(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        test_html = """
            <div class="title-wrapper"><a href="/admin/modeladmintest/author/edit/1/" title="Edit this author">J. R. R. Tolkien</a></div>
        """
        self.assertContains(response, test_html, html=True)

    @mock.patch(
        "wagtail.contrib.modeladmin.helpers.permission.PermissionHelper.user_can_edit_obj",
        return_value=False,
    )
    def test_title_column_links_to_inspect_view_when_user_cannot_edit(self, *mocks):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        test_html = """
            <div class="title-wrapper"><a href="/admin/modeladmintest/author/inspect/1/" title="Inspect this author">J. R. R. Tolkien</a></div>
        """
        self.assertContains(response, test_html, html=True)

    @mock.patch(
        "wagtail.contrib.modeladmin.helpers.permission.PermissionHelper.user_can_inspect_obj",
        return_value=False,
    )
    @mock.patch(
        "wagtail.contrib.modeladmin.helpers.permission.PermissionHelper.user_can_edit_obj",
        return_value=False,
    )
    def test_title_column_is_not_linked_when_user_cannot_edit_or_inspect(self, *mocks):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<td class="field-name title">J. R. R. Tolkien')


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestTranslatableBookIndexView(WagtailTestUtils, TestCase):
    fixtures = ["modeladmintest_test.json"]

    def setUp(self):
        self.login()

    def get(self, **params):
        return self.client.get("/admin/modeladmintest/translatablebook/", params)

    def test_simple(self):
        response = self.get()

        self.assertEqual(response.status_code, 200)

        # There are two books in the test data
        self.assertEqual(response.context["result_count"], 2)

        # Check the locale filter is there
        expected = """
        <ul>
            <li class="selected">
            <a href="?">All</a></li>
            <li>
            <a href="?locale__id__exact=1">English</a></li>
            <li>
            <a href="?locale__id__exact=2">French</a></li>
        </ul>"""
        self.assertContains(response, expected, html=True)

    @override_settings(WAGTAIL_I18N_ENABLED=False)
    def test_locale_selector_not_present_when_i18n_disabled(self):
        response = self.get()

        self.assertNotContains(
            response, '<a href="?locale__id__exact=2">French</a>', html=True
        )

    def test_filter(self):
        # Filter by locale 2 (fr)
        response = self.get(locale__id__exact=2)

        self.assertEqual(response.status_code, 200)

        # Locale fr has one book in the test data
        self.assertEqual(response.context["result_count"], 1)

        for book in response.context["object_list"]:
            self.assertEqual(book.locale_id, 2)

        self.assertContains(response, "Le Seigneur des anneaux", html=True)


class TestCreateView(WagtailTestUtils, TestCase):
    fixtures = ["modeladmintest_test.json"]

    def setUp(self):
        self.login()

    def get(self):
        return self.client.get("/admin/modeladmintest/book/create/")

    def post(self, post_data):
        return self.client.post("/admin/modeladmintest/book/create/", post_data)

    def test_simple(self):
        response = self.get()

        self.assertEqual(response.status_code, 200)

    def test_create(self):
        response = self.post(
            {
                "title": "George's Marvellous Medicine",
                "author": 2,
            }
        )
        # Should redirect back to index
        self.assertRedirects(response, "/admin/modeladmintest/book/")

        # Check that the book was created
        self.assertEqual(
            Book.objects.filter(title="George's Marvellous Medicine").count(), 1
        )

        response = self.client.get("/admin/modeladmintest/publisher/create/")
        self.assertIn("name", response.content.decode("UTF-8"))
        self.assertNotIn("headquartered_in", response.content.decode("UTF-8"))
        self.assertEqual(list(response.context["form"].fields), ["name"])
        self.client.post(
            "/admin/modeladmintest/publisher/create/", {"name": "Sharper Collins"}
        )
        publisher = Publisher.objects.get(name="Sharper Collins")
        self.assertIsNone(publisher.headquartered_in)

    def test_post_invalid(self):
        initial_book_count = Book.objects.count()

        response = self.post(
            {
                "title": "",
                "author": 2,
            }
        )
        final_book_count = Book.objects.count()

        self.assertEqual(response.status_code, 200)
        # Check that the book was not created
        self.assertEqual(initial_book_count, final_book_count)

        # Check that a form error was raised
        self.assertFormError(response, "form", "title", "This field is required.")
        self.assertContains(response, "error-message", count=1)

    def test_exclude_passed_to_extract_panel_definitions(self):
        path_to_form_fields_exclude_property = (
            "wagtail.contrib.modeladmin.options.ModelAdmin.form_fields_exclude"
        )
        with mock.patch(
            "wagtail.contrib.modeladmin.options.extract_panel_definitions_from_model_class"
        ) as m:
            with mock.patch(
                path_to_form_fields_exclude_property, new_callable=mock.PropertyMock
            ) as mock_form_fields_exclude:
                mock_form_fields_exclude.return_value = ["123"]

                self.get()
                self.assertTrue(mock_form_fields_exclude.called)
                m.assert_called_with(
                    Book, exclude=mock_form_fields_exclude.return_value
                )

    def test_clean_form_once(self):
        with mock.patch(
            "wagtail.test.modeladmintest.wagtail_hooks.PublisherModelAdminForm.clean"
        ) as mock_form_clean:
            response = self.client.post(
                "/admin/modeladmintest/publisher/create/", {"name": ""}
            )
            self.assertEqual(response.status_code, 200)

            mock_form_clean.assert_called_once()

    def test_create_view_with_multifieldpanel(self):
        # https://github.com/wagtail/wagtail/issues/6413
        response = self.client.get("/admin/modeladmintest/relatedlink/create/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/admin/modeladmintest/relatedlink/create/",
            {
                "title": "Homepage",
                "link": Page.objects.filter(depth=2).first().id,
            },
        )
        # Should redirect back to index
        self.assertRedirects(response, "/admin/modeladmintest/relatedlink/")

        # Check that the link was created
        self.assertEqual(RelatedLink.objects.filter(title="Homepage").count(), 1)

    def test_prepopulated_field_data_in_context(self):
        response = self.get()
        self.assertIn(
            'data-prepopulated-fields="[{&quot;id&quot;: &quot;#id_title&quot;, &quot;name&quot;: &quot;title&quot;, &quot;dependency_ids&quot;: [&quot;#id_author&quot;], &quot;dependency_list&quot;: [&quot;author&quot;], &quot;maxLength&quot;: 255, &quot;allowUnicode&quot;: false}]"',
            response.content.decode("UTF-8"),
        )


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestTranslatableCreateView(WagtailTestUtils, TestCase):
    fixtures = ["modeladmintest_test.json"]

    def setUp(self):
        self.login()

    def get(self, **params):
        return self.client.get("/admin/modeladmintest/translatablebook/create/", params)

    def test_simple(self):
        response = self.get(locale="fr")

        self.assertEqual(response.status_code, 200)

        # Check that the locale select exists and is set correctly
        self.assertRegex(
            response.content.decode(),
            r"data-locale-selector[^<]+<button[^<]+<svg[^<]+<use[^<]+<\/use[^<]+<\/svg[^<]+French",
        )

        # Check that the other locale link is right
        expected = '<a href="/admin/modeladmintest/translatablebook/create/?locale=en" data-locale-selector-link>'
        self.assertIn(expected, response.content.decode())


class TestRevisableCreateView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

    def post(self, post_data):
        return self.client.post("/admin/modeladmintest/publisher/create/", post_data)

    def test_create_with_revision(self):
        data = {"name": "foo"}
        response = self.post(data)
        self.assertRedirects(response, "/admin/modeladmintest/publisher/")

        instances = Publisher.objects.filter(name="foo")
        instance = instances.first()
        self.assertEqual(instances.count(), 1)

        # The revision should be created
        revisions = instance.revisions
        revision = revisions.first()
        self.assertEqual(revisions.count(), 1)
        self.assertEqual(revision.content["name"], "foo")

        # The log entry should have the revision attached
        log_entries = ModelLogEntry.objects.for_instance(instance).filter(
            action="wagtail.create"
        )
        self.assertEqual(log_entries.count(), 1)
        self.assertEqual(log_entries.first().revision, revision)


class TestInspectView(WagtailTestUtils, TestCase):
    fixtures = ["modeladmintest_test.json"]

    def setUp(self):
        self.login()

        img = Image.objects.create(
            title="LOTR cover",
            file=get_test_image_file(),
        )
        book = Book.objects.get(title="The Lord of the Rings")
        book.cover_image = img
        book.save()

    def get_for_author(self, author_id):
        return self.client.get("/admin/modeladmintest/author/inspect/%d/" % author_id)

    def get_for_book(self, book_id):
        return self.client.get("/admin/modeladmintest/book/inspect/%d/" % book_id)

    def test_author_simple(self):
        response = self.get_for_author(1)
        self.assertEqual(response.status_code, 200)

    def test_author_name_present(self):
        """
        The author name should appear twice. Once in the header, and once
        more in the field listing
        """
        response = self.get_for_author(1)
        self.assertContains(response, "J. R. R. Tolkien", 2)

    def test_author_dob_not_present(self):
        """
        The date of birth shouldn't appear, because the field wasn't included
        in the `inspect_view_fields` list
        """
        response = self.get_for_author(1)
        self.assertNotContains(response, "1892")

    def test_book_simple(self):
        response = self.get_for_book(1)
        self.assertEqual(response.status_code, 200)

    def test_book_title_present(self):
        """
        The book title should appear once only, in the header, as 'title'
        was added to the `inspect_view_fields_ignore` list
        """
        response = self.get_for_book(1)
        self.assertContains(response, "The Lord of the Rings", 1)

    def test_book_author_present(self):
        """
        The author name should appear, because 'author' is not in
        `inspect_view_fields_ignore` and should be returned by the
        `get_inspect_view_fields` method.
        """
        response = self.get_for_book(1)
        self.assertContains(response, "J. R. R. Tolkien", 1)

    def test_book_extract_document_html_escaping(self):
        doc = Document.objects.create(
            title="Title with <script>alert('XSS')</script>",
            file=get_test_document_file(),
        )
        book = Book.objects.get(title="The Lord of the Rings")
        book.extract_document = doc
        book.save()
        response = self.get_for_book(1)
        self.assertNotContains(response, "Title with <script>alert('XSS')</script>")
        self.assertContains(
            response, "Title with &lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;"
        )

    def test_non_existent(self):
        response = self.get_for_book(100)
        self.assertEqual(response.status_code, 404)

    def test_back_to_listing(self):
        response = self.client.get("/admin/modeladmintest/author/inspect/1/")
        # check that back to listing link exists
        expected = """
            <p class="back">
                    <a href="/admin/modeladmintest/author/">
                        <svg class="icon icon-arrow-left default" aria-hidden="true">
                            <use href="#icon-arrow-left"></use>
                        </svg>
                        Back to author list
                    </a>
            </p>
        """
        self.assertContains(response, expected, html=True)


class TestEditView(WagtailTestUtils, TestCase):
    fixtures = ["modeladmintest_test.json"]

    def setUp(self):
        self.user = self.login()
        ModelLogEntry.objects.create(
            content_type=ContentType.objects.get_for_model(Book),
            label="The Lord of the Rings",
            action="wagtail.create",
            timestamp=make_aware(datetime.datetime(2021, 9, 30, 10, 1, 0)),
            object_id="1",
        )

    def get(self, book_id):
        return self.client.get("/admin/modeladmintest/book/edit/%d/" % book_id)

    def post(self, book_id, post_data):
        return self.client.post(
            "/admin/modeladmintest/book/edit/%d/" % book_id, post_data
        )

    def test_simple(self):
        response = self.get(1)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The Lord of the Rings")

        # "Last updated" timestamp should be present
        self.assertContains(response, 'data-tippy-content="Sept. 30, 2021, 10:01 a.m."')
        # History link should be present
        self.assertContains(response, 'href="/admin/modeladmintest/book/history/1/"')

        url_finder = AdminURLFinder(self.user)
        expected_url = "/admin/modeladmintest/book/edit/1/"
        self.assertEqual(url_finder.get_edit_url(Book.objects.get(id=1)), expected_url)

    def test_non_existent(self):
        response = self.get(100)

        self.assertEqual(response.status_code, 404)

    def test_edit(self):
        response = self.post(
            1,
            {
                "title": "The Lady of the Rings",
                "author": 1,
            },
        )

        # Should redirect back to index
        self.assertRedirects(response, "/admin/modeladmintest/book/")

        # Check that the book was updated
        self.assertEqual(Book.objects.get(id=1).title, "The Lady of the Rings")

    def test_post_invalid(self):
        response = self.post(
            1,
            {
                "title": "",
                "author": 1,
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check that the title was not updated
        self.assertEqual(Book.objects.get(id=1).title, "The Lord of the Rings")

        # Check that a form error was raised
        self.assertFormError(response, "form", "title", "This field is required.")
        self.assertContains(response, "error-message", count=1)

    def test_exclude_passed_to_extract_panel_definitions(self):
        path_to_form_fields_exclude_property = (
            "wagtail.contrib.modeladmin.options.ModelAdmin.form_fields_exclude"
        )
        with mock.patch(
            "wagtail.contrib.modeladmin.options.extract_panel_definitions_from_model_class"
        ) as m:
            with mock.patch(
                path_to_form_fields_exclude_property, new_callable=mock.PropertyMock
            ) as mock_form_fields_exclude:
                mock_form_fields_exclude.return_value = ["123"]

                self.get(1)
                self.assertTrue(mock_form_fields_exclude.called)
                m.assert_called_with(
                    Book, exclude=mock_form_fields_exclude.return_value
                )

    def test_clean_form_once(self):
        with mock.patch(
            "wagtail.test.modeladmintest.wagtail_hooks.PublisherModelAdminForm.clean"
        ) as mock_form_clean:
            publisher = Publisher.objects.create(name="Sharper Collins")

            response = self.client.post(
                "/admin/modeladmintest/publisher/edit/%d/" % publisher.pk, {"name": ""}
            )
            self.assertEqual(response.status_code, 200)

            mock_form_clean.assert_called_once()

    def test_edit_view_with_multifieldpanel(self):
        # https://github.com/wagtail/wagtail/issues/6413
        link = RelatedLink.objects.create(
            title="Homepage", link=Page.objects.filter(depth=2).first()
        )
        response = self.client.get(
            "/admin/modeladmintest/relatedlink/edit/%d/" % link.id
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/admin/modeladmintest/relatedlink/edit/%d/" % link.id,
            {
                "title": "Homepage edited",
                "link": Page.objects.filter(depth=2).first().id,
            },
        )
        # Should redirect back to index
        self.assertRedirects(response, "/admin/modeladmintest/relatedlink/")

        # Check that the link was updated
        self.assertEqual(RelatedLink.objects.filter(title="Homepage edited").count(), 1)


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestTranslatableBookEditView(WagtailTestUtils, TestCase):
    fixtures = ["modeladmintest_test.json"]

    def setUp(self):
        self.login()

    def get(self, book_id, **params):
        return self.client.get(
            "/admin/modeladmintest/translatablebook/edit/%d/" % book_id, params
        )

    def test_simple(self):
        book = TranslatableBook.objects.first()
        response = self.get(book.id)
        self.assertEqual(response.status_code, 200)

        # Check the locale switcher isn't there
        self.assertNotContains(response, "English", html=True)

        tbook = book.copy_for_translation(locale=Locale.objects.get(language_code="fr"))
        tbook.save()

        response = self.get(tbook.id)
        self.assertEqual(response.status_code, 200)

        # Check the locale switcher is there
        expected = """
        <a href="/admin/modeladmintest/translatablebook/edit/1/?locale=en" data-locale-selector-link>
            English
        </a>"""
        self.assertContains(response, expected, html=True)


class TestRevisableEditView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()
        self.instance = Publisher.objects.create(name="foo")

    def post(self, post_data):
        return self.client.post(
            "/admin/modeladmintest/publisher/edit/%s/" % self.instance.pk, post_data
        )

    def test_edit_with_revision(self):
        data = {"name": "bar"}
        response = self.post(data)
        self.assertRedirects(response, "/admin/modeladmintest/publisher/")

        instances = Publisher.objects.filter(name="bar")
        instance = instances.first()
        self.assertEqual(instances.count(), 1)

        # The revision should be created
        revisions = instance.revisions
        revision = revisions.first()
        self.assertEqual(revisions.count(), 1)
        self.assertEqual(revision.content["name"], "bar")

        # The log entry should have the revision attached
        log_entries = ModelLogEntry.objects.for_instance(instance).filter(
            action="wagtail.edit"
        )
        self.assertEqual(log_entries.count(), 1)
        self.assertEqual(log_entries.first().revision, revision)


class TestPageSpecificViews(WagtailTestUtils, TestCase):
    fixtures = ["modeladmintest_test.json"]
    expected_status_code = 404

    def setUp(self):
        self.login()

    def test_choose_parent(self):
        response = self.client.get("/admin/modeladmintest/book/choose_parent/")
        self.assertEqual(response.status_code, self.expected_status_code)


class TestConfirmDeleteView(WagtailTestUtils, TestCase):
    fixtures = ["modeladmintest_test.json"]

    def setUp(self):
        self.login()

    def get(self, book_id):
        return self.client.get("/admin/modeladmintest/book/delete/%d/" % book_id)

    def post(self, book_id):
        return self.client.post("/admin/modeladmintest/book/delete/%d/" % book_id)

    def test_simple(self):
        response = self.get(1)

        self.assertEqual(response.status_code, 200)

    def test_non_existent(self):
        response = self.get(100)

        self.assertEqual(response.status_code, 404)

    def test_post(self):
        response = self.post(1)

        # User redirected to index
        self.assertRedirects(response, "/admin/modeladmintest/book/")

        # Book deleted
        self.assertFalse(Book.objects.filter(id=1).exists())


class TestDeleteViewWithProtectedRelation(WagtailTestUtils, TestCase):
    fixtures = ["modeladmintest_test.json"]

    def setUp(self):
        self.login()

    def get(self, author_id):
        return self.client.get("/admin/modeladmintest/author/delete/%d/" % author_id)

    def post(self, author_id):
        return self.client.post("/admin/modeladmintest/author/delete/%d/" % author_id)

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
            response, "'J. R. R. Tolkien' is currently referenced by other objects"
        )
        self.assertContains(response, "<li><b>Book:</b> The Lord of the Rings</li>")

        # Author not deleted
        self.assertTrue(Author.objects.filter(id=1).exists())

    def test_post_without_dependent_object(self):
        response = self.post(4)

        # User redirected to index
        self.assertRedirects(response, "/admin/modeladmintest/author/")

        # Author deleted
        self.assertFalse(Author.objects.filter(id=4).exists())

    def test_post_with_1to1_dependent_object(self):
        response = self.post(5)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "'Harper Lee' is currently referenced by other objects"
        )
        self.assertContains(
            response, "<li><b>Solo Book:</b> To Kill a Mockingbird</li>"
        )

        # Author not deleted
        self.assertTrue(Author.objects.filter(id=5).exists())


class TestDeleteViewModelReprPrimary(WagtailTestUtils, TestCase):
    fixtures = ["modeladmintest_test.json"]

    def setUp(self):
        self.login()

    def test_delete(self):
        response = self.client.post("/admin/modeladmintest/token/delete/boom/")
        self.assertEqual(response.status_code, 302)


class TestEditorAccess(WagtailTestUtils, TestCase):
    fixtures = ["modeladmintest_test.json"]

    def setUp(self):
        # Create a user
        self.user = self.create_user(username="test2", password="password")
        self.group = Group.objects.get(name="Editors")
        self.user.groups.add(self.group)
        self.book_content_type = ContentType.objects.get_for_model(Book)

        # Login
        self.login(username="test2", password="password")

    def test_index_permitted(self):
        response = self.client.get("/admin/modeladmintest/book/")
        self.assertRedirects(response, "/admin/")

        self.group.permissions.add(
            Permission.objects.get(
                codename="add_book", content_type=self.book_content_type
            )
        )
        response = self.client.get("/admin/modeladmintest/book/")
        self.assertEqual(response.status_code, 200)

    def test_inspect_permitted(self):
        response = self.client.get("/admin/modeladmintest/book/inspect/2/")
        self.assertRedirects(response, "/admin/")

        self.group.permissions.add(
            Permission.objects.get(
                codename="add_book", content_type=self.book_content_type
            )
        )
        response = self.client.get("/admin/modeladmintest/book/inspect/2/")
        self.assertEqual(response.status_code, 200)

    def test_create_permitted(self):
        response = self.client.get("/admin/modeladmintest/book/create/")
        self.assertRedirects(response, "/admin/")

        self.group.permissions.add(
            Permission.objects.get(
                codename="add_book", content_type=self.book_content_type
            )
        )
        response = self.client.get("/admin/modeladmintest/book/create/")
        self.assertEqual(response.status_code, 200)

    def test_edit_permitted(self):
        response = self.client.get("/admin/modeladmintest/book/edit/2/")
        self.assertRedirects(response, "/admin/")

        self.group.permissions.add(
            Permission.objects.get(
                codename="change_book", content_type=self.book_content_type
            )
        )
        response = self.client.get("/admin/modeladmintest/book/edit/2/")
        self.assertEqual(response.status_code, 200)

    def test_admin_url_finder_without_permission(self):
        url_finder = AdminURLFinder(self.user)
        self.assertIsNone(url_finder.get_edit_url(Book.objects.get(id=2)))

    def test_admin_url_finder_with_permission(self):
        self.group.permissions.add(
            Permission.objects.get(
                codename="change_book", content_type=self.book_content_type
            )
        )
        url_finder = AdminURLFinder(self.user)
        self.assertEqual(
            url_finder.get_edit_url(Book.objects.get(id=2)),
            "/admin/modeladmintest/book/edit/2/",
        )

    def test_delete_get_permitted(self):
        response = self.client.get("/admin/modeladmintest/book/delete/2/")
        self.assertRedirects(response, "/admin/")

        self.group.permissions.add(
            Permission.objects.get(
                codename="delete_book", content_type=self.book_content_type
            )
        )
        response = self.client.get("/admin/modeladmintest/book/delete/2/")
        self.assertEqual(response.status_code, 200)

    def test_delete_post_permitted(self):
        response = self.client.post("/admin/modeladmintest/book/delete/2/")
        self.assertRedirects(response, "/admin/")

        self.group.permissions.add(
            Permission.objects.get(
                codename="delete_book", content_type=self.book_content_type
            )
        )
        response = self.client.post("/admin/modeladmintest/book/delete/2/")
        self.assertRedirects(response, "/admin/modeladmintest/book/")


class TestHistoryView(WagtailTestUtils, TestCase):
    fixtures = ["modeladmintest_test.json"]

    def setUp(self):
        self.login()
        ModelLogEntry.objects.create(
            content_type=ContentType.objects.get_for_model(Book),
            label="The Lord of the Rings",
            action="wagtail.create",
            timestamp=make_aware(datetime.datetime(2021, 9, 30, 10, 1, 0)),
            object_id="1",
        )

    def test_simple(self):
        response = self.client.get("/admin/modeladmintest/book/history/1/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<td>Created</td>", html=True)
        self.assertContains(
            response,
            'data-tippy-content="Sept. 30, 2021, 10:01 a.m."',
        )


class TestQuoting(WagtailTestUtils, TestCase):
    fixtures = ["modeladmintest_test.json"]
    expected_status_code = 200

    def setUp(self):
        self.login()
        self.tok_reg = Token.objects.create(key="RegularName")
        self.tok_irr = Token.objects.create(key="Irregular_Name")

    def test_action_links(self):
        response = self.client.get("/admin/modeladmintest/token/")

        self.assertContains(
            response, 'href="/admin/modeladmintest/token/edit/RegularName/"'
        )
        self.assertContains(
            response, 'href="/admin/modeladmintest/token/delete/RegularName/"'
        )
        self.assertContains(
            response, 'href="/admin/modeladmintest/token/edit/Irregular_5FName/"'
        )
        self.assertContains(
            response, 'href="/admin/modeladmintest/token/delete/Irregular_5FName/"'
        )

        response = self.client.get("/admin/modeladmintest/token/edit/Irregular_5FName/")
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            "/admin/modeladmintest/token/delete/Irregular_5FName/"
        )
        self.assertEqual(response.status_code, 200)


class TestPanelConfigurationChecks(WagtailTestUtils, TestCase):
    def setUp(self):
        self.warning_id = "wagtailadmin.W002"

        def get_checks_result():
            # run checks only with the 'panels' tag
            checks_result = checks.run_checks(tags=["panels"])
            return [
                warning for warning in checks_result if warning.id == self.warning_id
            ]

        self.get_checks_result = get_checks_result

    def test_model_with_single_tabbed_panel_only(self):
        Publisher.content_panels = [FieldPanel("name"), FieldPanel("headquartered_in")]

        warning = checks.Warning(
            "Publisher.content_panels will have no effect on modeladmin editing",
            hint="""Ensure that Publisher uses `panels` instead of `content_panels`\
or set up an `edit_handler` if you want a tabbed editing interface.
There are no default tabs on non-Page models so there will be no\
 Content tab for the content_panels to render in.""",
            obj=Publisher,
            id="wagtailadmin.W002",
        )

        checks_results = self.get_checks_result()

        self.assertIn(warning, checks_results)

        # clean up for future checks
        delattr(Publisher, "content_panels")

    def test_model_with_two_tabbed_panels_only(self):
        Publisher.settings_panels = [FieldPanel("name")]
        Publisher.promote_panels = [FieldPanel("headquartered_in")]

        warning_1 = checks.Warning(
            "Publisher.promote_panels will have no effect on modeladmin editing",
            hint="""Ensure that Publisher uses `panels` instead of `promote_panels`\
or set up an `edit_handler` if you want a tabbed editing interface.
There are no default tabs on non-Page models so there will be no\
 Promote tab for the promote_panels to render in.""",
            obj=Publisher,
            id="wagtailadmin.W002",
        )

        warning_2 = checks.Warning(
            "Publisher.settings_panels will have no effect on modeladmin editing",
            hint="""Ensure that Publisher uses `panels` instead of `settings_panels`\
or set up an `edit_handler` if you want a tabbed editing interface.
There are no default tabs on non-Page models so there will be no\
 Settings tab for the settings_panels to render in.""",
            obj=Publisher,
            id="wagtailadmin.W002",
        )

        checks_results = self.get_checks_result()

        self.assertIn(warning_1, checks_results)
        self.assertIn(warning_2, checks_results)

        # clean up for future checks
        delattr(Publisher, "settings_panels")
        delattr(Publisher, "promote_panels")

    def test_model_with_single_tabbed_panel_and_edit_handler(self):
        Publisher.content_panels = [FieldPanel("name"), FieldPanel("headquartered_in")]
        Publisher.edit_handler = TabbedInterface(Publisher.content_panels)

        # no errors should occur
        self.assertEqual(self.get_checks_result(), [])

        # clean up for future checks
        delattr(Publisher, "content_panels")
        delattr(Publisher, "edit_handler")


class TestMenuSetting(WagtailTestUtils, TestCase):
    fixtures = ["modeladmintest_test.json"]

    def setUp(self):
        self.login()

    def test_default_menu_setting_model_admin(self):
        modeladmin = BookModelAdmin()

        menu_item = modeladmin.get_menu_item()
        self.assertEqual(menu_item.label, "Books")
        self.assertEqual(menu_item.name, "books")

    def test_custom_menu_setting_model_admin(self):
        modeladmin = BookModelAdmin()
        modeladmin.menu_label = "Book Model Label"
        modeladmin.menu_item_name = "bookitem"

        menu_item = modeladmin.get_menu_item()
        self.assertEqual(menu_item.label, "Book Model Label")
        self.assertEqual(menu_item.name, "bookitem")

    def test_default_menu_setting_model_admin_group(self):
        modeladmin = EventsAdminGroup()

        menu_item = modeladmin.get_menu_item()
        self.assertEqual(menu_item.label, "Events")
        self.assertEqual(menu_item.name, "events")

    def test_custom_menu_setting_model_admin_group(self):
        modeladmin = EventsAdminGroup()
        modeladmin.menu_label = "Event Model Label"
        modeladmin.menu_item_name = "eventitem"

        menu_item = modeladmin.get_menu_item()
        self.assertEqual(menu_item.label, "Event Model Label")
        self.assertEqual(menu_item.name, "eventitem")
