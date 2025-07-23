import datetime
import json
import urllib
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile, TemporaryUploadedFile
from django.db.models.lookups import In
from django.template.defaultfilters import filesizeformat
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.html import escape, escapejs
from django.utils.http import RFC3986_SUBDELIMS, urlencode
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from willow.optimizers.base import OptimizerBase
from willow.registry import registry

from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.admin.ui.tables import Table
from wagtail.images import get_image_model
from wagtail.images.utils import generate_signature
from wagtail.images.views.images import BulkActionsColumn, ImagesFilterSet
from wagtail.models import (
    Collection,
    GroupCollectionPermission,
    Page,
    UploadedFile,
    get_root_collection_id,
)
from wagtail.test.testapp.models import (
    CustomImage,
    CustomImageWithAuthor,
    EventPage,
    VariousOnDeleteModel,
)
from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.template_tests import AdminTemplateTestUtils
from wagtail.test.utils.timestamps import local_datetime

from .utils import Image, get_test_image_file, get_test_image_file_svg

# Get the chars that Django considers safe to leave unescaped in a URL
urlquote_safechars = RFC3986_SUBDELIMS + "/~:@"


class TestImageIndexView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()
        self.kitten_image = Image.objects.create(
            title="a cute kitten",
            file=get_test_image_file(size=(1, 1)),
        )
        self.puppy_image = Image.objects.create(
            title="a cute puppy",
            file=get_test_image_file(size=(1, 1)),
        )

    def get(self, params={}):
        return self.client.get(reverse("wagtailimages:index"), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/images/index.html")
        self.assertContains(response, "Add an image")
        # The search box should not raise an error
        self.assertNotContains(response, "This field is required.")
        # all results should be returned
        self.assertContains(response, "a cute kitten")
        self.assertContains(response, "a cute puppy")

    def test_empty_q(self):
        response = self.get({"q": ""})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["query_string"], "")
        self.assertContains(response, "Add an image")
        # The search box should not raise an error
        self.assertNotContains(response, "This field is required.")
        # all results should be returned
        self.assertContains(response, "a cute kitten")
        self.assertContains(response, "a cute puppy")

    def test_pagination(self):
        pages = ["0", "1", "-1", "9999", "Not a page"]
        for page in pages:
            response = self.get({"p": page})
            self.assertEqual(response.status_code, 200)

    def test_pagination_preserves_other_params(self):
        root_collection = Collection.get_first_root_node()
        evil_plans_collection = root_collection.add_child(name="Evil plans")

        for i in range(1, 66):
            self.image = Image.objects.create(
                title="Test image %i" % i,
                file=get_test_image_file(size=(1, 1)),
                collection=evil_plans_collection,
            )

        response = self.get({"collection_id": evil_plans_collection.id, "p": 2})
        self.assertEqual(response.status_code, 200)

        response_body = response.content.decode("utf8")

        # prev link should exist and include collection_id
        self.assertTrue(
            ("?p=1&amp;collection_id=%i" % evil_plans_collection.id) in response_body
            or ("?collection_id=%i&amp;p=1" % evil_plans_collection.id) in response_body
        )
        # next link should exist and include collection_id
        self.assertTrue(
            ("?p=3&amp;collection_id=%i" % evil_plans_collection.id) in response_body
            or ("?collection_id=%i&amp;p=3" % evil_plans_collection.id) in response_body
        )

    def test_order_by_title(self):
        response = self.get({"ordering": "title"})
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertEqual(context["page_obj"].object_list[0], self.kitten_image)
        self.assertEqual(context["page_obj"].object_list[1], self.puppy_image)

    def test_valid_orderings(self):
        orderings = [
            "title",
            "-title",
            "created_at",
            "-created_at",
            "file_size",
            "-file_size",
            "usage_count",
            "-usage_count",
        ]
        for ordering in orderings:
            response = self.get({"ordering": ordering})
            self.assertEqual(response.status_code, 200)

            context = response.context
            self.assertEqual(context["current_ordering"], ordering)

    def test_default_ordering_used_if_invalid_ordering_provided(self):
        response = self.get({"ordering": "bogus"})
        self.assertEqual(response.status_code, 200)

        context = response.context
        default_ordering = "-created_at"
        self.assertEqual(context["current_ordering"], default_ordering)
        self.assertEqual(context["page_obj"].object_list[0], self.puppy_image)
        self.assertEqual(context["page_obj"].object_list[1], self.kitten_image)

    @override_settings(WAGTAILIMAGES_INDEX_PAGE_SIZE=15)
    def test_default_entries_per_page(self):
        images = [
            Image(
                title="Test image %i" % i,
                file=get_test_image_file(size=(1, 1)),
            )
            for i in range(1, 33)
        ]
        Image.objects.bulk_create(images)

        response = self.get()
        self.assertEqual(response.status_code, 200)

        object_list = response.context["page_obj"].object_list
        # The number of images shown is 15
        self.assertEqual(len(object_list), 15)

    def test_default_entries_per_page_uses_default(self):
        images = [
            Image(
                title="Test image %i" % i,
                file=get_test_image_file(size=(1, 1)),
            )
            for i in range(1, 33)
        ]
        Image.objects.bulk_create(images)

        default_num_entries_per_page = 30
        response = self.get()
        self.assertEqual(response.status_code, 200)

        object_list = response.context["page_obj"].object_list
        self.assertEqual(len(object_list), default_num_entries_per_page)

    def test_collection_order(self):
        root_collection = Collection.get_first_root_node()
        root_collection.add_child(name="Evil plans")
        root_collection.add_child(name="Good plans")

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

    def test_collection_nesting(self):
        root_collection = Collection.get_first_root_node()
        evil_plans = root_collection.add_child(name="Evil plans")
        evil_plans.add_child(name="Eviler plans")

        response = self.get()
        # "Eviler Plans" should be prefixed with &#x21b3 (↳) and 4 non-breaking spaces.
        self.assertContains(response, "&nbsp;&nbsp;&nbsp;&nbsp;&#x21b3 Eviler plans")

    def test_edit_image_link_contains_next_url(self):
        root_collection = Collection.get_first_root_node()
        evil_plans_collection = root_collection.add_child(name="Evil plans")

        image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(size=(1, 1)),
            collection=evil_plans_collection,
        )

        response = self.get({"collection_id": evil_plans_collection.id})
        self.assertEqual(response.status_code, 200)

        edit_url = reverse("wagtailimages:edit", args=(image.id,))
        next_url = urllib.parse.quote(response._request.get_full_path())
        self.assertContains(response, f"{edit_url}?next={next_url}")

    def test_tags(self):
        image_two_tags = Image.objects.create(
            title="Test image with two tags",
            file=get_test_image_file(),
        )
        image_two_tags.tags.add("one", "two")

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
        Image.objects.create(
            title="Test image with no tags",
            file=get_test_image_file(),
        )

        image_one_tag = Image.objects.create(
            title="Test image with one tag",
            file=get_test_image_file(),
        )
        image_one_tag.tags.add("one")

        image_two_tags = Image.objects.create(
            title="Test image with two tags",
            file=get_test_image_file(),
        )
        image_two_tags.tags.add("one", "two")

        image_unrelated_tag = Image.objects.create(
            title="Test image with a different tag",
            file=get_test_image_file(),
        )
        image_unrelated_tag.tags.add("unrelated")

        # no filtering
        response = self.get()
        # four images created above plus the two untagged ones created in setUp()
        self.assertEqual(response.context["page_obj"].paginator.count, 6)

        # filter all images with tag 'one'
        response = self.get({"tag": "one"})
        self.assertEqual(response.context["page_obj"].paginator.count, 2)

        # filter all images with tag 'two'
        response = self.get({"tag": "two"})
        self.assertEqual(response.context["page_obj"].paginator.count, 1)

        # filter all images with tag 'one' or 'unrelated'
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
            image = Image.objects.create(
                title="Test image %i" % i,
                file=get_test_image_file(size=(1, 1)),
            )
            if i % 2 != 0:
                image.tags.add("even")
                image.save()

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

    def test_search_form_rendered(self):
        response = self.get()
        html = response.content.decode()
        search_url = reverse("wagtailimages:index_results")

        # Search form in the header should be rendered.
        self.assertTagInHTML(
            f"""<form action="{search_url}" method="get" role="search">""",
            html,
            count=1,
            allow_extra_attrs=True,
        )

    @override_settings(
        CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
    )
    def test_num_queries(self):
        # Warm up cache so that result is the same when running this test in isolation
        # as when running it within the full test suite.
        self.get()

        # Initial number of queries.
        with self.assertNumQueries(12):
            self.get()

        # Add 5 images.
        for i in range(5):
            self.image = Image.objects.create(
                title="Test image %i" % i,
                file=get_test_image_file(size=(1, 1)),
            )

        with self.assertNumQueries(32):
            # The renditions needed don't exist yet. We have 20 = 5 * 4 additional queries.
            self.get()

        with self.assertNumQueries(12):
            # No extra additional queries since renditions exist and are saved in
            # the prefetched objects cache.
            self.get()

    def test_empty_tag_filter_does_not_perform_id_filtering(self):
        image_one_tag = Image.objects.create(
            title="Test image with one tag",
            file=get_test_image_file(),
        )
        image_one_tag.tags.add("one")

        request = RequestFactory().get(reverse("wagtailimages:index"))
        request.user = self.user
        filterset = ImagesFilterSet(
            data={}, queryset=Image.objects.all(), request=request, is_searching=True
        )

        # Filtering on tags during a search would normally apply a `pk__in` filter, but this should not happen
        # when the tag filter is empty.
        in_clauses = [
            clause
            for clause in filterset.qs.query.where.children
            if isinstance(clause, In)
        ]
        self.assertEqual(len(in_clauses), 0)

    def test_correct_layout_is_passed_to_context(self):
        response = self.client.get(reverse("wagtailimages:index"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["layout"], "grid")

        response = self.client.get(reverse("wagtailimages:index"), {"layout": "list"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["layout"], "list")

        response = self.client.get(reverse("wagtailimages:index"), {"layout": "grid"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["layout"], "grid")

    def test_layout_when_layout_is_list(self):
        response = self.client.get(reverse("wagtailimages:index"), {"layout": "list"})
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)

        table = soup.find("table", class_="listing")
        self.assertIsNotNone(
            table, "Expected a table element to be present in list layout."
        )

        grid_ul = soup.find("ul", class_="listing horiz images")
        self.assertIsNone(
            grid_ul,
            "Expected no ul element with class 'listing horiz images' in list layout.",
        )

    def test_layout_when_layout_is_grid(self):
        response = self.client.get(reverse("wagtailimages:index"), {"layout": "grid"})
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)

        table = soup.find("table", class_="listing")
        self.assertIsNone(
            table, "Expected no table element with class 'listing' in grid layout."
        )

        grid_ul = soup.find("ul", class_="listing horiz images")
        self.assertIsNotNone(
            grid_ul,
            "Expected a ul element with class 'listing horiz images' in grid layout.",
        )

    def test_layout_when_no_layout_is_passed(self):
        response = self.client.get(reverse("wagtailimages:index"))
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)

        table = soup.find("table", class_="listing")
        self.assertIsNone(
            table,
            "If no layout is passed, it should default to grid layout (no table) - table found",
        )

        grid_ul = soup.find("ul", class_="listing horiz images")
        self.assertIsNotNone(
            grid_ul,
            "If no layout is passed, it should default to grid layout (ul not found)",
        )

    def test_layout_when_layout_is_invalid(self):
        response = self.client.get(
            reverse("wagtailimages:index"), {"layout": "invalid"}
        )
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)

        table = soup.find("table", class_="listing")
        self.assertIsNone(
            table,
            "If invalid layout is passed, it should default to grid layout (no table) - table found",
        )

        grid_ul = soup.find("ul", class_="listing horiz images")
        self.assertIsNotNone(
            grid_ul,
            "If invalid layout is passed, it should default to grid layout (ul not found)",
        )

    def test_image_is_present_in_image_preview_column(self):
        response = self.client.get(reverse("wagtailimages:index"), {"layout": "list"})
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)

        image_preview_wrapper = soup.find("td", class_="image-preview")
        self.assertIsNotNone(
            image_preview_wrapper,
            "Expected a <td> with class image-preview' inside the listing table",
        )

        preview_image = image_preview_wrapper.find("img")
        self.assertIsNotNone(
            preview_image, "Expected an <img> element inside image-preview <td>"
        )

    def test_title_and_filename_are_present_in_title_column(self):
        response = self.client.get(reverse("wagtailimages:index"), {"layout": "list"})
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)

        title_and_filename_wrapper = soup.select_one("td.title.title-with-filename")
        self.assertIsNotNone(
            title_and_filename_wrapper,
            "Expected a <td> with class 'title and title-with-filename' inside the listing table.",
        )

        title_wrapper_div = title_and_filename_wrapper.find(
            "div", class_="title-wrapper"
        )
        self.assertIsNotNone(
            title_wrapper_div,
            "Expected a <div> with class 'title-wrapper' inside the title-with-filename <td>",
        )

        filename_wrapper_div = title_and_filename_wrapper.find(
            "div", class_="filename-wrapper"
        )
        self.assertIsNotNone(
            filename_wrapper_div,
            "Expected a <div> with class 'filename-wrapper' inside the title-with-filename <td>",
        )

    def test_list_layout_contains_required_table_headers(self):
        response = self.client.get(reverse("wagtailimages:index"), {"layout": "list"})
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)

        headers = soup.find_all("th")
        header_texts = [th.get_text(strip=True) for th in headers]

        expected_headers = ["Preview", "Title", "Collection", "Created"]
        for expected_header in expected_headers:
            self.assertIn(
                expected_header,
                header_texts,
                f"Expected header '{expected_header}' not found in list layout",
            )

    def test_layout_toggle_button_in_list_layout(self):
        response = self.client.get(reverse("wagtailimages:index"), {"layout": "list"})
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)

        layout_toggle_button = soup.find("label", class_="w-layout-toggle-button")
        self.assertIsNotNone(
            layout_toggle_button, "Expected layout toggle button in list layout"
        )

    def test_layout_toggle_button_in_grid_layout(self):
        response = self.client.get(reverse("wagtailimages:index"), {"layout": "grid"})
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)

        layout_toggle_button = soup.find("label", class_="w-layout-toggle-button")
        self.assertIsNotNone(
            layout_toggle_button, "Expected layout toggle button in grid layout"
        )

    def test_usage_count_column(self):
        with self.captureOnCommitCallbacks(execute=True):
            VariousOnDeleteModel.objects.create(protected_image=self.kitten_image)

        response = self.client.get(reverse("wagtailimages:index"), {"layout": "list"})
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)

        expected_url = reverse(
            "wagtailimages:image_usage",
            args=(self.kitten_image.pk,),
        )
        link = soup.select_one(f"a[href='{expected_url}']")
        self.assertIsNotNone(link)
        self.assertEqual(link.text.strip(), "Used 1 time")

        expected_url = reverse(
            "wagtailimages:image_usage",
            args=(self.puppy_image.pk,),
        )
        link = soup.select_one(f"a[href='{expected_url}']")
        self.assertIsNotNone(link)
        self.assertEqual(link.text.strip(), "Used 0 times")

    def test_order_by_usage_count(self):
        with self.captureOnCommitCallbacks(execute=True):
            VariousOnDeleteModel.objects.create(protected_image=self.kitten_image)
            VariousOnDeleteModel.objects.create(protected_image=self.kitten_image)
            VariousOnDeleteModel.objects.create(protected_image=self.puppy_image)

        cases = {
            "usage_count": [self.puppy_image, self.kitten_image],
            "-usage_count": [self.kitten_image, self.puppy_image],
        }
        for layout in ["list", "grid"]:
            for ordering, expected_order in cases.items():
                with self.subTest(layout=layout, ordering=ordering):
                    response = self.client.get(
                        reverse("wagtailimages:index"),
                        {"ordering": ordering, "layout": layout},
                    )
                    self.assertEqual(response.status_code, 200)
                    context = response.context
                    self.assertSequenceEqual(
                        context["page_obj"].object_list,
                        expected_order,
                    )


class TestBulkActionsColumn(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()
        self.root_collection = Collection.get_first_root_node()
        self.test_collection = self.root_collection.add_child(name="Test Collection")

    def test_get_header_context_data_with_current_collection(self):
        column = BulkActionsColumn("bulk_actions")
        table = Table(columns=[column], data=[])

        parent_context = {
            "table": table,
            "current_collection": self.test_collection,
        }

        context = column.get_header_context_data(parent_context)

        self.assertEqual(context["parent"], self.test_collection.id)

    def test_get_header_context_data_without_current_collection(self):
        column = BulkActionsColumn("bulk_actions")
        table = Table(columns=[column], data=[])

        parent_context = {
            "table": table,
            "current_collection": None,
        }

        context = column.get_header_context_data(parent_context)

        self.assertNotIn("parent", context)


class TestImageIndexViewSearch(WagtailTestUtils, TransactionTestCase):
    fixtures = ["test_empty.json"]

    def setUp(self):
        self.login()
        self.kitten_image = Image.objects.create(
            title="a cute kitten",
            file=get_test_image_file(size=(1, 1)),
        )
        self.puppy_image = Image.objects.create(
            title="a cute puppy",
            file=get_test_image_file(size=(1, 1)),
        )
        # The created_at field uses auto_now_add, so changing it needs to be
        # done after the image is created.
        self.kitten_image.created_at = local_datetime(2020, 1, 1)
        self.kitten_image.save()
        self.puppy_image.created_at = local_datetime(2022, 2, 2)
        self.puppy_image.save()

    def get(self, params={}):
        return self.client.get(reverse("wagtailimages:index"), params)

    def test_search(self):
        response = self.get({"q": "kitten"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["query_string"], "kitten")
        self.assertContains(response, "a cute kitten")
        self.assertNotContains(response, "a cute puppy")

    def test_search_partial_match(self):
        response = self.get({"q": "kit"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["query_string"], "kit")
        self.assertContains(response, "a cute kitten")
        self.assertNotContains(response, "a cute puppy")

    def test_collection_query_search(self):
        root_collection = Collection.get_first_root_node()
        child_collection = [
            root_collection.add_child(name="Baker Collection"),
            root_collection.add_child(name="Other Collection"),
        ]
        title_list = ["Baker", "Other"]
        answer_list = []
        for i in range(10):
            self.image = Image.objects.create(
                title=f"{title_list[i % 2]} {i}",
                file=get_test_image_file(size=(1, 1)),
                collection=child_collection[i % 2],
            )
            if i % 2 == 0:
                answer_list.append(self.image)
        response = self.get({"q": "Baker", "collection_id": child_collection[0].id})
        status_code = response.status_code
        query_string = response.context["query_string"]
        response_list = response.context["page_obj"].object_list
        response_body = response.content.decode("utf-8")

        self.assertEqual(status_code, 200)
        self.assertEqual(query_string, "Baker")
        self.assertCountEqual(answer_list, response_list)
        for i in range(0, 10, 2):
            self.assertIn("Baker %i" % i, response_body)

        # should append the correct params to the add images button
        url = reverse("wagtailimages:add_multiple")
        self.assertContains(
            response,
            f'<a href="{url}?collection_id={child_collection[0].pk}"',
        )

    def test_search_and_order_by_created_at(self):
        old_image = Image.objects.create(
            title="decades old cute tortoise",
            file=get_test_image_file(size=(1, 1)),
        )
        old_image.created_at = local_datetime(2000, 1, 1)
        old_image.save()
        response = self.get({"q": "cute", "ordering": "created_at"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["query_string"], "cute")
        self.assertEqual(
            list(response.context["page_obj"].object_list),
            [old_image, self.kitten_image, self.puppy_image],
        )
        soup = self.get_soup(response.content)
        option = soup.select_one('select[name="ordering"] option[selected]')
        self.assertIsNotNone(option)
        self.assertEqual(option["value"], "created_at")
        self.assertEqual(option.get_text(strip=True), "Oldest")

    def test_tag_filtering_with_search_term(self):
        Image.objects.create(
            title="Test image with no tags",
            file=get_test_image_file(),
        )

        image_one_tag = Image.objects.create(
            title="Test image with one tag",
            file=get_test_image_file(),
        )
        image_one_tag.tags.add("one")

        image_two_tags = Image.objects.create(
            title="Test image with two tags",
            file=get_test_image_file(),
        )
        image_two_tags.tags.add("one", "two")

        # The tag shouldn't be ignored, so the result should be the images
        # that have the "one" tag and "test" in the title.
        response = self.get({"tag": "one", "q": "test"})
        self.assertEqual(response.context["page_obj"].paginator.count, 2)

    def test_image_search_when_layout_is_list(self):
        response = self.client.get(
            reverse("wagtailimages:index"), {"q": "A", "layout": "list"}
        )
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)

        table = soup.find("table", class_="listing")
        self.assertIsNotNone(
            table,
            "Expected a table element to be present in list layout when searching for images.",
        )

        grid_ul = soup.find("ul", class_="listing horiz images")
        self.assertIsNone(
            grid_ul,
            "Expected no ul element with class 'listing horiz images' in list layout when searching for images.",
        )

    def test_image_search_when_layout_is_grid(self):
        response = self.client.get(
            reverse("wagtailimages:index"), {"q": "A", "layout": "grid"}
        )
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)

        table = soup.find("table", class_="listing")
        self.assertIsNone(
            table,
            "Expected no table element with class 'listing' in grid layout when searching for images.",
        )

        grid_ul = soup.find("ul", class_="listing horiz images")
        self.assertIsNotNone(
            grid_ul,
            "Expected a ul element with class 'listing horiz images' in grid layout when searching for images.",
        )


class TestImageListingResultsView(WagtailTestUtils, TransactionTestCase):
    fixtures = ["test_empty.json"]

    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse("wagtailimages:index_results"), params)

    def test_search(self):
        monster = Image.objects.create(
            title="A scary monster",
            file=get_test_image_file(),
        )

        response = self.get({"q": "monster"})
        self.assertEqual(response.status_code, 200)
        # 'next' param on edit page link should point back to the images index, not the results view
        self.assertContains(
            response,
            "/admin/images/%d/?next=/admin/images/%%3Fq%%3Dmonster" % monster.id,
        )


class TestImageAddView(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse("wagtailimages:add"), params)

    def post(self, post_data={}):
        return self.client.post(reverse("wagtailimages:add"), post_data)

    def test_get(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/images/add.html")

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
                {"url": reverse("wagtailimages:index"), "label": "Images"},
                {"url": "", "label": "New: Image"},
            ],
            response.content,
        )

    def test_get_with_collections(self):
        root_collection = Collection.get_first_root_node()
        root_collection.add_child(name="Evil plans")

        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/images/add.html")

        self.assertContains(
            response,
            '<label class="w-field__label" for="id_collection" id="id_collection-label">',
        )
        self.assertContains(response, "Evil plans")

    def test_get_with_collection_nesting(self):
        root_collection = Collection.get_first_root_node()
        evil_plans = root_collection.add_child(name="Evil plans")
        evil_plans.add_child(name="Eviler plans")

        response = self.get()
        # "Eviler Plans" should be prefixed with &#x21b3 (↳) and 4 non-breaking spaces.
        self.assertContains(response, "&nbsp;&nbsp;&nbsp;&nbsp;&#x21b3 Eviler plans")

    @override_settings(WAGTAILIMAGES_IMAGE_MODEL="tests.CustomImage")
    def test_get_with_custom_image_model(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/images/add.html")

        # Ensure the form supports file uploads
        self.assertContains(response, 'enctype="multipart/form-data"')

        # custom fields should be included
        self.assertContains(response, 'name="fancy_caption"')

        # form media should be imported
        self.assertContains(response, "wagtailadmin/js/draftail.js")

    def test_add(self):
        response = self.post(
            {
                "title": "Test image",
                "file": SimpleUploadedFile(
                    "test.png", get_test_image_file().file.getvalue()
                ),
            }
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailimages:index"))

        # Check that the image was created
        images = Image.objects.filter(title="Test image")
        self.assertEqual(images.count(), 1)

        # Test that size was populated correctly
        image = images.first()
        self.assertEqual(image.width, 640)
        self.assertEqual(image.height, 480)

        # Test that the file_size/hash fields were set
        self.assertTrue(image.file_size)
        self.assertTrue(image.file_hash)

        # Test that it was placed in the root collection
        root_collection = Collection.get_first_root_node()
        self.assertEqual(image.collection, root_collection)

    def test_add_svg_denied(self):
        """
        SVGs should be disallowed by default
        """
        response = self.post(
            {
                "title": "Test image",
                "file": SimpleUploadedFile(
                    "test.svg",
                    get_test_image_file_svg().file.getvalue(),
                    content_type="text/html",
                ),
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "file",
            "Not a supported image format. Supported formats: AVIF, GIF, JPG, JPEG, PNG, WEBP.",
        )

    @override_settings(WAGTAILIMAGES_EXTENSIONS=["svg"])
    def test_add_svg(self):
        response = self.post(
            {
                "title": "Test image",
                "file": SimpleUploadedFile(
                    "test.svg",
                    get_test_image_file_svg().file.getvalue(),
                    content_type="text/html",
                ),
            }
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailimages:index"))

        # Check that the image was created
        images = Image.objects.filter(title="Test image")
        self.assertEqual(images.count(), 1)

    def test_add_temporary_uploaded_file(self):
        """
        Test that uploading large files (spooled to the filesystem) work as expected
        """
        test_image_file = get_test_image_file()
        uploaded_file = TemporaryUploadedFile(
            "test.png", "image/png", test_image_file.size, "utf-8"
        )
        uploaded_file.write(test_image_file.file.getvalue())
        uploaded_file.seek(0)

        response = self.post(
            {
                "title": "Test image",
                "file": uploaded_file,
            }
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailimages:index"))

        # Check that the image was created
        images = Image.objects.filter(title="Test image")
        self.assertEqual(images.count(), 1)

        # Test that size was populated correctly
        image = images.first()
        self.assertEqual(image.width, 640)
        self.assertEqual(image.height, 480)

        # Test that the file_size/hash fields were set
        self.assertTrue(image.file_size)
        self.assertTrue(image.file_hash)

        # Test that it was placed in the root collection
        root_collection = Collection.get_first_root_node()
        self.assertEqual(image.collection, root_collection)

    @override_settings(
        STORAGES={
            **settings.STORAGES,
            "default": {
                "BACKEND": "wagtail.test.dummy_external_storage.DummyExternalStorage"
            },
        },
    )
    def test_add_with_external_file_storage(self):
        response = self.post(
            {
                "title": "Test image",
                "file": SimpleUploadedFile(
                    "test.png", get_test_image_file().file.getvalue()
                ),
            }
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailimages:index"))

        # Check that the image was created
        self.assertTrue(Image.objects.filter(title="Test image").exists())

    def test_add_no_file_selected(self):
        response = self.post(
            {
                "title": "Test image",
            }
        )

        # Shouldn't redirect anywhere
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/images/add.html")

        # The form should have an error
        self.assertFormError(
            response.context["form"], "file", "This field is required."
        )

    @override_settings(WAGTAILIMAGES_MAX_UPLOAD_SIZE=1)
    def test_add_too_large_file(self):
        file_content = get_test_image_file().file.getvalue()

        response = self.post(
            {
                "title": "Test image",
                "file": SimpleUploadedFile("test.png", file_content),
            }
        )

        # Shouldn't redirect anywhere
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/images/add.html")

        # The form should have an error
        self.assertFormError(
            response.context["form"],
            "file",
            "This file is too big ({file_size}). Maximum filesize {max_file_size}.".format(
                file_size=filesizeformat(len(file_content)),
                max_file_size=filesizeformat(1),
            ),
        )

    @override_settings(WAGTAILIMAGES_MAX_IMAGE_PIXELS=1)
    def test_add_too_many_pixels(self):
        file_content = get_test_image_file().file.getvalue()

        response = self.post(
            {
                "title": "Test image",
                "file": SimpleUploadedFile("test.png", file_content),
            }
        )

        # Shouldn't redirect anywhere
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/images/add.html")

        # The form should have an error
        self.assertFormError(
            response.context["form"],
            "file",
            "This file has too many pixels (307200). Maximum pixels 1.",
        )

    def test_add_with_collections(self):
        root_collection = Collection.get_first_root_node()
        evil_plans_collection = root_collection.add_child(name="Evil plans")

        response = self.post(
            {
                "title": "Test image",
                "file": SimpleUploadedFile(
                    "test.png", get_test_image_file().file.getvalue()
                ),
                "collection": evil_plans_collection.id,
            }
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailimages:index"))

        # Check that the image was created
        images = Image.objects.filter(title="Test image")
        self.assertEqual(images.count(), 1)

        # Test that it was placed in the Evil Plans collection
        image = images.first()
        self.assertEqual(image.collection, evil_plans_collection)

    def test_add_with_selected_collection(self):
        root_collection = Collection.get_first_root_node()
        collection = root_collection.add_child(name="Travel pics")

        response = self.client.get(
            reverse("wagtailimages:add_multiple") + f"?collection_id={collection.pk}"
        )
        self.assertEqual(response.status_code, 200)

        # collection chooser should have selected collection passed with parameter
        self.assertContains(response, f'option value="{collection.pk}" selected')

    @override_settings(WAGTAILIMAGES_IMAGE_MODEL="tests.CustomImage")
    def test_unique_together_validation_error(self):
        root_collection = Collection.get_first_root_node()
        evil_plans_collection = root_collection.add_child(name="Evil plans")

        # another image with a title to collide with
        CustomImage.objects.create(
            title="Test image",
            file=get_test_image_file(),
            collection=evil_plans_collection,
        )

        response = self.post(
            {
                "title": "Test image",
                "file": SimpleUploadedFile(
                    "test.png", get_test_image_file().file.getvalue()
                ),
                "collection": evil_plans_collection.id,
            }
        )

        # Shouldn't redirect anywhere
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/images/add.html")

        # error message should be output on the page as a non-field error
        self.assertContains(
            response, "Custom image with this Title and Collection already exists."
        )


class TestImageAddViewWithLimitedCollectionPermissions(WagtailTestUtils, TestCase):
    def setUp(self):
        add_image_permission = Permission.objects.get(
            content_type__app_label="wagtailimages", codename="add_image"
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
            permission=add_image_permission,
        )

        user = self.create_user(
            username="moriarty", email="moriarty@example.com", password="password"
        )
        user.groups.add(conspirators_group)

        self.login(username="moriarty", password="password")

    def get(self, params={}):
        return self.client.get(reverse("wagtailimages:add"), params)

    def post(self, post_data={}):
        return self.client.post(reverse("wagtailimages:add"), post_data)

    def test_get(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/images/add.html")

        # user only has access to one collection, so no 'Collection' option
        # is displayed on the form
        self.assertNotContains(
            response,
            '<label class="w-field__label" for="id_collection" id="id_collection-label">',
        )

    def test_get_with_collection_nesting(self):
        self.evil_plans_collection.add_child(name="Eviler plans")

        response = self.get()
        self.assertEqual(response.status_code, 200)
        # Unlike the above test, the user should have access to multiple Collections.
        self.assertContains(
            response,
            '<label class="w-field__label" for="id_collection" id="id_collection-label">',
        )
        # "Eviler Plans" should be prefixed with &#x21b3 (↳) and 4 non-breaking spaces.
        self.assertContains(response, "&nbsp;&nbsp;&nbsp;&nbsp;&#x21b3 Eviler plans")

    def test_add(self):
        response = self.post(
            {
                "title": "Test image",
                "file": SimpleUploadedFile(
                    "test.png", get_test_image_file().file.getvalue()
                ),
            }
        )

        # User should be redirected back to the index
        self.assertRedirects(response, reverse("wagtailimages:index"))

        # Image should be created in the 'evil plans' collection,
        # despite there being no collection field in the form, because that's the
        # only one the user has access to
        self.assertTrue(Image.objects.filter(title="Test image").exists())
        self.assertEqual(
            Image.objects.get(title="Test image").collection, self.evil_plans_collection
        )


class TestImageEditView(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()

        # Create an image to edit
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

        self.storage = self.image.file.storage

    def update_from_db(self):
        self.image = Image.objects.get(pk=self.image.pk)

    def get(self, params={}):
        return self.client.get(
            reverse("wagtailimages:edit", args=(self.image.id,)), params
        )

    def post(self, post_data={}):
        return self.client.post(
            reverse("wagtailimages:edit", args=(self.image.id,)), post_data
        )

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/images/edit.html")

        # Ensure the form supports file uploads
        self.assertContains(response, 'enctype="multipart/form-data"')

        # draftail should NOT be a standard JS include on this page
        # (see TestImageEditViewWithCustomImageModel - this confirms that form media
        # definitions are being respected)
        self.assertNotContains(response, "wagtailadmin/js/draftail.js")

        self.assertBreadcrumbsItemsRendered(
            [
                {"url": reverse("wagtailimages:index"), "label": "Images"},
                {"url": "", "label": "Test image"},
            ],
            response.content,
        )

    def test_simple_with_collection_nesting(self):
        root_collection = Collection.get_first_root_node()
        evil_plans = root_collection.add_child(name="Evil plans")
        evil_plans.add_child(name="Eviler plans")

        response = self.get()
        # "Eviler Plans" should be prefixed with &#x21b3 (↳) and 4 non-breaking spaces.
        self.assertContains(response, "&nbsp;&nbsp;&nbsp;&nbsp;&#x21b3 Eviler plans")

    def test_next_url_is_present_in_edit_form(self):
        root_collection = Collection.get_first_root_node()
        evil_plans_collection = root_collection.add_child(name="Evil plans")
        image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(size=(1, 1)),
            collection=evil_plans_collection,
        )
        expected_next_url = (
            reverse("wagtailimages:index")
            + "?"
            + urlencode({"collection_id": evil_plans_collection.id})
        )

        response = self.client.get(
            reverse("wagtailimages:edit", args=(image.id,)), {"next": expected_next_url}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, f'<input type="hidden" value="{expected_next_url}" name="next">'
        )

    def test_with_usage_count(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/images/edit.html")
        self.assertContains(response, "Used 0 times")
        expected_url = "/admin/images/usage/%d/" % self.image.id
        self.assertContains(response, expected_url)

    @override_settings(
        STORAGES={
            **settings.STORAGES,
            "default": {
                "BACKEND": "wagtail.test.dummy_external_storage.DummyExternalStorage"
            },
        },
    )
    def test_simple_with_external_storage(self):
        # The view calls get_file_size on the image that closes the file if
        # file_size wasn't previously populated.

        # The view then attempts to reopen the file when rendering the template
        # which caused crashes when certain storage backends were in use.
        # See #1397

        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/images/edit.html")

    def test_edit(self):
        response = self.post(
            {
                "title": "Edited",
            }
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailimages:index"))

        self.update_from_db()
        self.assertEqual(self.image.title, "Edited")

        url_finder = AdminURLFinder(self.user)
        expected_url = "/admin/images/%d/" % self.image.id
        self.assertEqual(url_finder.get_edit_url(self.image), expected_url)

    def test_edit_with_next_url(self):
        root_collection = Collection.get_first_root_node()
        evil_plans_collection = root_collection.add_child(name="Evil plans")
        image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(size=(1, 1)),
            collection=evil_plans_collection,
        )
        expected_next_url = (
            reverse("wagtailimages:index")
            + "?"
            + urlencode({"collection_id": evil_plans_collection.id})
        )

        response = self.client.post(
            reverse("wagtailimages:edit", args=(image.id,)),
            {
                "title": "Edited",
                "collection": evil_plans_collection.id,
                "next": expected_next_url,
            },
        )
        self.assertRedirects(response, expected_next_url)

        image.refresh_from_db()
        self.assertEqual(image.title, "Edited")

    def test_edit_with_limited_permissions(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.post(
            {
                "title": "Edited",
            }
        )
        self.assertEqual(response.status_code, 302)

        url_finder = AdminURLFinder(self.user)
        self.assertIsNone(url_finder.get_edit_url(self.image))

    def test_edit_with_new_image_file(self):
        file_content = get_test_image_file().file.getvalue()

        # Change the file size/hash of the image
        self.image.file_size = 100000
        self.image.file_hash = "abcedf"
        self.image.save()

        response = self.post(
            {
                "title": "Edited",
                "file": SimpleUploadedFile("new.png", file_content),
            }
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailimages:index"))

        self.update_from_db()
        self.assertNotEqual(self.image.file_size, 100000)
        self.assertNotEqual(self.image.file_hash, "abcedf")

    @override_settings(
        STORAGES={
            **settings.STORAGES,
            "default": {
                "BACKEND": "wagtail.test.dummy_external_storage.DummyExternalStorage"
            },
        },
    )
    def test_edit_with_new_image_file_and_external_storage(self):
        file_content = get_test_image_file().file.getvalue()

        # Change the file size/hash of the image
        self.image.file_size = 100000
        self.image.file_hash = "abcedf"
        self.image.save()

        response = self.post(
            {
                "title": "Edited",
                "file": SimpleUploadedFile("new.png", file_content),
            }
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailimages:index"))

        self.update_from_db()
        self.assertNotEqual(self.image.file_size, 100000)
        self.assertNotEqual(self.image.file_hash, "abcedf")

    def test_with_missing_image_file(self):
        self.image.file.delete(False)

        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/images/edit.html")

    def check_get_missing_file_displays_warning(self):
        # Need to recreate image to use a custom storage per test.
        image = Image.objects.create(title="Test image", file=get_test_image_file())
        image.file.storage.delete(image.file.name)

        response = self.client.get(reverse("wagtailimages:edit", args=(image.pk,)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/images/edit.html")
        self.assertContains(response, "File not found")

    def test_get_missing_file_displays_warning_with_default_storage(self):
        self.check_get_missing_file_displays_warning()

    @override_settings(
        STORAGES={
            **settings.STORAGES,
            "default": {
                "BACKEND": "wagtail.test.dummy_external_storage.DummyExternalStorage"
            },
        },
    )
    def test_get_missing_file_displays_warning_with_custom_storage(self):
        self.check_get_missing_file_displays_warning()

    def get_content(self, f=None):
        if f is None:
            f = self.image.file
        try:
            if f.closed:
                f.open("rb")
            return f.read()
        finally:
            f.close()

    def test_reupload_same_name(self):
        """
        Checks that reuploading the image file with the same file name
        changes the file name, to avoid browser cache issues (see #3817).
        """
        old_file = self.image.file
        old_size = self.image.file_size
        old_data = self.get_content()

        old_rendition = self.image.get_rendition("fill-5x5")
        old_rendition_data = self.get_content(old_rendition.file)

        new_name = self.image.filename
        new_file = SimpleUploadedFile(
            new_name, get_test_image_file(colour="red").file.getvalue()
        )
        new_size = new_file.size

        response = self.post(
            {
                "title": self.image.title,
                "file": new_file,
            }
        )
        self.assertRedirects(response, reverse("wagtailimages:index"))
        self.update_from_db()
        self.assertFalse(self.storage.exists(old_file.name))
        self.assertTrue(self.storage.exists(self.image.file.name))
        self.assertNotEqual(self.image.file.name, "original_images/" + new_name)
        self.assertNotEqual(self.image.file_size, old_size)
        self.assertEqual(self.image.file_size, new_size)
        self.assertNotEqual(self.get_content(), old_data)

        new_rendition = self.image.get_rendition("fill-5x5")
        self.assertNotEqual(old_rendition.file.name, new_rendition.file.name)
        self.assertNotEqual(self.get_content(new_rendition.file), old_rendition_data)

        with self.assertRaises(type(old_rendition).DoesNotExist):
            old_rendition.refresh_from_db()

    def test_reupload_different_name(self):
        """
        Checks that reuploading the image file with a different file name
        correctly uses the new file name.
        """
        old_file = self.image.file
        old_size = self.image.file_size
        old_data = self.get_content()

        old_rendition = self.image.get_rendition("fill-5x5")
        old_rendition_data = self.get_content(old_rendition.file)

        new_name = "test_reupload_different_name.png"
        new_file = SimpleUploadedFile(
            new_name, get_test_image_file(colour="red").file.getvalue()
        )
        new_size = new_file.size

        response = self.post(
            {
                "title": self.image.title,
                "file": new_file,
            }
        )
        self.assertRedirects(response, reverse("wagtailimages:index"))
        self.update_from_db()
        self.assertFalse(self.storage.exists(old_file.name))
        self.assertTrue(self.storage.exists(self.image.file.name))
        self.assertEqual(self.image.file.name, "original_images/" + new_name)
        self.assertNotEqual(self.image.file_size, old_size)
        self.assertEqual(self.image.file_size, new_size)
        self.assertNotEqual(self.get_content(), old_data)

        new_rendition = self.image.get_rendition("fill-5x5")
        self.assertNotEqual(old_rendition.file.name, new_rendition.file.name)
        self.assertNotEqual(self.get_content(new_rendition.file), old_rendition_data)

        with self.assertRaises(type(old_rendition).DoesNotExist):
            old_rendition.refresh_from_db()

    @override_settings(USE_L10N=True, USE_THOUSAND_SEPARATOR=True)
    def test_no_thousand_separators_in_focal_point_editor(self):
        large_image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(size=(3840, 2160)),
            focal_point_x=2048,
            focal_point_y=1001,
            focal_point_width=1009,
            focal_point_height=1002,
        )
        response = self.client.get(
            reverse("wagtailimages:edit", args=(large_image.id,))
        )
        self.assertContains(response, 'data-original-width="3840"')
        self.assertContains(response, 'data-focal-point-x="2048"')
        self.assertContains(response, 'data-focal-point-y="1001"')
        self.assertContains(response, 'data-focal-point-width="1009"')
        self.assertContains(response, 'data-focal-point-height="1002"')

    @override_settings(WAGTAILIMAGES_IMAGE_MODEL="tests.CustomImage")
    def test_unique_together_validation_error(self):
        root_collection = Collection.get_first_root_node()
        evil_plans_collection = root_collection.add_child(name="Evil plans")

        # Create an image to edit
        self.image = CustomImage.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

        # another image with a title to collide with
        CustomImage.objects.create(
            title="Edited", file=get_test_image_file(), collection=evil_plans_collection
        )

        response = self.post(
            {
                "title": "Edited",
                "collection": evil_plans_collection.id,
            }
        )

        # Shouldn't redirect anywhere
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/images/edit.html")

        # error message should be output on the page as a non-field error
        self.assertContains(
            response, "Custom image with this Title and Collection already exists."
        )


@override_settings(WAGTAILIMAGES_IMAGE_MODEL="tests.CustomImage")
class TestImageEditViewWithCustomImageModel(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

        # Create an image to edit
        self.image = CustomImage.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

        self.storage = self.image.file.storage

    def get(self, params={}):
        return self.client.get(
            reverse("wagtailimages:edit", args=(self.image.id,)), params
        )

    def test_get_with_custom_image_model(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/images/edit.html")

        # Ensure the form supports file uploads
        self.assertContains(response, 'enctype="multipart/form-data"')

        # form media should be imported
        self.assertContains(response, "wagtailadmin/js/draftail.js")


class TestImageDeleteView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()

        # Create an image to edit
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

        self.delete_url = reverse("wagtailimages:delete", args=(self.image.id,))

    def get(self, params={}):
        return self.client.get(self.delete_url, params)

    def post(self, post_data={}, **kwargs):
        return self.client.post(self.delete_url, post_data, **kwargs)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/images/confirm_delete.html")
        self.assertTemplateUsed(response, "wagtailadmin/shared/usage_summary.html")
        self.assertNotContains(
            response,
            "One or more references to this image prevent it from being deleted.",
        )
        self.assertContains(response, "Yes, delete")
        self.assertContains(response, "No, don't delete")
        self.assertContains(
            response,
            f'<form action="{self.delete_url}" method="POST">',
        )

    def test_usage_link(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/images/confirm_delete.html")
        self.assertContains(response, "This image is referenced 0 times")
        expected_url = "/admin/images/usage/%d/" % self.image.id
        self.assertContains(response, expected_url)

    def test_delete(self):
        response = self.post(follow=True)

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailimages:index"))

        # Check that the image was deleted
        images = Image.objects.filter(title="Test image")
        self.assertEqual(images.count(), 0)

        # Message should be shown
        self.assertEqual(
            [m.message.strip() for m in response.context["messages"]],
            [escape("Image 'Test image' deleted.")],
        )

    def test_delete_with_limited_permissions(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.post()
        self.assertEqual(response.status_code, 302)

    def test_delete_get_with_protected_reference(self):
        with self.captureOnCommitCallbacks(execute=True):
            VariousOnDeleteModel.objects.create(protected_image=self.image)
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/images/confirm_delete.html")
        self.assertTemplateUsed(response, "wagtailadmin/shared/usage_summary.html")
        self.assertContains(
            response,
            reverse("wagtailimages:image_usage", args=(self.image.id,))
            + "?describe_on_delete=1",
        )
        self.assertContains(
            response,
            "One or more references to this image prevent it from being deleted.",
        )
        self.assertNotContains(response, "Are you sure you want to delete this image?")
        self.assertNotContains(response, "Yes, delete")
        self.assertNotContains(response, "No, don't delete")
        self.assertNotContains(
            response,
            f'<form action="{self.delete_url}" method="POST">',
        )

    def test_delete_post_with_protected_reference(self):
        with self.captureOnCommitCallbacks(execute=True):
            VariousOnDeleteModel.objects.create(protected_image=self.image)
        response = self.post()
        self.assertRedirects(response, reverse("wagtailadmin_home"))
        self.assertTrue(Image.objects.filter(id=self.image.id).exists())


class TestUsage(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

        # Create an image to edit
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def test_usage_page(self):
        with self.captureOnCommitCallbacks(execute=True):
            home_page = Page.objects.get(id=2)
            home_page.add_child(
                instance=EventPage(
                    title="Christmas",
                    slug="christmas",
                    feed_image=self.image,
                    date_from=datetime.date.today(),
                    audience="private",
                    location="Test",
                    cost="Test",
                )
            ).save_revision().publish()

        response = self.client.get(
            reverse("wagtailimages:image_usage", args=[self.image.id])
        )
        self.assertContains(response, "Christmas")
        self.assertContains(response, '<table class="listing">')
        self.assertContains(response, "<td>Event page</td>", html=True)

    def test_usage_page_no_usage(self):
        response = self.client.get(
            reverse("wagtailimages:image_usage", args=[self.image.id])
        )
        # There's no usage so there should be no listing table
        self.assertNotContains(response, '<table class="listing">')

    def test_usage_no_tags(self):
        with self.captureOnCommitCallbacks(execute=True):
            # tags should not count towards an image's references
            self.image.tags.add("illustration")
            self.image.save()
        response = self.client.get(
            reverse("wagtailimages:image_usage", args=[self.image.id])
        )
        # There's no usage so there should be no listing table
        self.assertNotContains(response, '<table class="listing">')

    def test_usage_page_with_only_change_permission(self):
        with self.captureOnCommitCallbacks(execute=True):
            home_page = Page.objects.get(id=2)
            home_page.add_child(
                instance=EventPage(
                    title="Christmas",
                    slug="christmas",
                    feed_image=self.image,
                    date_from=datetime.date.today(),
                    audience="private",
                    location="Test",
                    cost="Test",
                )
            ).save_revision().publish()

        # Create a user with change_image permission but not add_image
        user = self.create_user(
            username="changeonly", email="changeonly@example.com", password="password"
        )
        change_permission = Permission.objects.get(
            content_type__app_label="wagtailimages", codename="change_image"
        )
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        self.changers_group = Group.objects.create(name="Image changers")
        GroupCollectionPermission.objects.create(
            group=self.changers_group,
            collection=Collection.get_first_root_node(),
            permission=change_permission,
        )
        user.groups.add(self.changers_group)

        user.user_permissions.add(admin_permission)
        self.login(username="changeonly", password="password")

        response = self.client.get(
            reverse("wagtailimages:image_usage", args=[self.image.id])
        )

        self.assertEqual(response.status_code, 200)
        # User has no permission over the page linked to, so should not see its details
        self.assertNotContains(response, "Christmas")
        self.assertContains(response, "(Private page)")
        self.assertContains(response, "<td>Event page</td>", html=True)

    def test_usage_page_without_change_permission(self):
        # Create a user with add_image permission but not change_image
        user = self.create_user(
            username="addonly", email="addonly@example.com", password="password"
        )
        add_permission = Permission.objects.get(
            content_type__app_label="wagtailimages", codename="add_image"
        )
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        self.adders_group = Group.objects.create(name="Image adders")
        GroupCollectionPermission.objects.create(
            group=self.adders_group,
            collection=Collection.get_first_root_node(),
            permission=add_permission,
        )
        user.groups.add(self.adders_group)

        user.user_permissions.add(admin_permission)
        self.login(username="addonly", password="password")

        response = self.client.get(
            reverse("wagtailimages:image_usage", args=[self.image.id])
        )

        self.assertEqual(response.status_code, 302)


class TestImageChooserView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()

    def get(self, params={}):
        return self.client.get(reverse("wagtailimages_chooser:choose"), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json["step"], "choose")
        self.assertTemplateUsed(response, "wagtailimages/chooser/chooser.html")

        # draftail should NOT be a standard JS include on this page
        self.assertNotIn("wagtailadmin/js/draftail.js", response_json["html"])

        # upload file field should have an explicit 'accept' case for image/avif
        soup = self.get_soup(response_json["html"])
        self.assertEqual(
            soup.select_one('input[type="file"]').get("accept"), "image/*, image/avif"
        )

    def test_simple_with_collection_nesting(self):
        root_collection = Collection.get_first_root_node()
        evil_plans = root_collection.add_child(name="Evil plans")
        evil_plans.add_child(name="Eviler plans")

        response = self.get()
        # "Eviler Plans" should be prefixed with &#x21b3 (↳) and 4 non-breaking spaces.
        self.assertContains(response, "&nbsp;&nbsp;&nbsp;&nbsp;&#x21b3 Eviler plans")

    @override_settings(
        WAGTAILIMAGES_EXTENSIONS=["gif", "jpg", "jpeg", "png", "webp", "avif", "heic"]
    )
    def test_upload_field_accepts_heic(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json["step"], "choose")
        self.assertTemplateUsed(response, "wagtailimages/chooser/chooser.html")

        # upload file field should have an explicit 'accept' case for image/heic and image/avif
        soup = self.get_soup(response_json["html"])
        self.assertEqual(
            soup.select_one('input[type="file"]').get("accept"),
            "image/*, image/heic, image/avif",
        )

    @override_settings(WAGTAILIMAGES_EXTENSIONS=["gif", "jpg", "jpeg", "png", "webp"])
    def test_upload_field_without_avif(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json["step"], "choose")
        self.assertTemplateUsed(response, "wagtailimages/chooser/chooser.html")

        soup = self.get_soup(response_json["html"])
        self.assertEqual(soup.select_one('input[type="file"]').get("accept"), "image/*")

    def test_choose_permissions(self):
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
                content_type__app_label="wagtailimages", codename="choose_image"
            ),
        )
        # Create the "Office" Collection and _don't_ grant any permissions to the Bakers group.
        office_collection = root.add_child(instance=Collection(name="Office"))

        # Create a new user in the Bakers group, and log in as them.
        # Can't use self.user because it's a superuser.
        baker = self.create_user(username="baker", password="password")
        baker.groups.add(bakers_group)
        self.login(username="baker", password="password")

        # Add an image to each Collection.
        sweet_buns = Image.objects.create(
            title="SweetBuns.jpg",
            file=get_test_image_file(),
            collection=bakery_collection,
        )
        poster = Image.objects.create(
            title="PromotionalPoster.jpg",
            file=get_test_image_file(),
            collection=office_collection,
        )

        # Open the image chooser
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/chooser/chooser.html")

        # Confirm that the Baker can see the sweet buns, but not the promotional poster.
        self.assertContains(response, sweet_buns.title)
        self.assertNotContains(response, poster.title)

        # Confirm that the Collection chooser is not visible, because the Baker cannot
        # choose from multiple Collections.
        self.assertNotContains(response, "Collection")

        # We now let the Baker choose from the Office collection.
        GroupCollectionPermission.objects.create(
            group=Group.objects.get(name="Bakers"),
            collection=Collection.objects.get(name="Office"),
            permission=Permission.objects.get(
                content_type__app_label="wagtailimages", codename="choose_image"
            ),
        )

        # Open the image chooser again.
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/chooser/chooser.html")

        # Confirm that the Baker can now see both images.
        self.assertContains(response, sweet_buns.title)
        self.assertContains(response, poster.title)

        # Ensure that the Collection chooser IS visible, because the Baker can now
        # choose from multiple Collections.
        self.assertContains(response, "Collection")

    @override_settings(WAGTAILIMAGES_IMAGE_MODEL="tests.CustomImage")
    def test_with_custom_image_model(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json["step"], "choose")
        self.assertTemplateUsed(response, "wagtailimages/chooser/chooser.html")

        # custom form fields should be present
        self.assertIn(
            'name="image-chooser-upload-fancy_caption"', response_json["html"]
        )

        # form media imports should appear on the page
        self.assertIn("wagtailadmin/js/draftail.js", response_json["html"])

    def test_search(self):
        response = self.get({"q": "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["search_query"], "Hello")

    def test_pagination(self):
        # page numbers in range should be accepted
        response = self.get({"p": 1})
        self.assertEqual(response.status_code, 200)
        # page numbers out of range should return 404
        response = self.get({"p": 9999})
        self.assertEqual(response.status_code, 404)

    @override_settings(WAGTAILIMAGES_CHOOSER_PAGE_SIZE=4)
    def test_chooser_page_size(self):
        images = [
            Image(
                title="Test image %i" % i,
                file=get_test_image_file(size=(1, 1)),
            )
            for i in range(1, 12)
        ]
        Image.objects.bulk_create(images)

        response = self.get()

        self.assertContains(response, "Page 1 of 3")
        self.assertEqual(response.status_code, 200)

    def test_filter_by_tag(self):
        for i in range(0, 10):
            image = Image.objects.create(
                title="Test image %d is even better than the last one" % i,
                file=get_test_image_file(),
            )
            if i % 2 == 0:
                image.tags.add("even")

        response = self.get({"tag": "even"})
        self.assertEqual(response.status_code, 200)

        # Results should include images tagged 'even'
        self.assertContains(response, "Test image 2 is even better")

        # Results should not include images that just have 'even' in the title
        self.assertNotContains(response, "Test image 3 is even better")

    def test_construct_queryset_hook_browse(self):
        image = Image.objects.create(
            title="Test image shown",
            file=get_test_image_file(),
            uploaded_by_user=self.user,
        )
        Image.objects.create(
            title="Test image not shown",
            file=get_test_image_file(),
        )

        def filter_images(images, request):
            # Filter on `uploaded_by_user` because it is
            # the only default FilterField in search_fields
            return images.filter(uploaded_by_user=self.user)

        with self.register_hook("construct_image_chooser_queryset", filter_images):
            response = self.get()
        self.assertEqual(len(response.context["results"]), 1)
        self.assertEqual(response.context["results"][0], image)

    @override_settings(
        CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
    )
    def test_num_queries(self):
        # Initial number of queries.
        with self.assertNumQueries(8):
            self.get()

        # Add 5 images.
        for i in range(5):
            self.image = Image.objects.create(
                title="Test image %i" % i,
                file=get_test_image_file(size=(1, 1)),
            )

        with self.assertNumQueries(30):
            # The renditions needed don't exist yet. We have 21 = 5 * 4 + 2 additional queries.
            self.get()

        with self.assertNumQueries(10):
            # No extra additional queries since renditions exist and are saved in
            # the prefetched objects cache.
            self.get()


class TestImageChooserViewSearch(WagtailTestUtils, TransactionTestCase):
    fixtures = ["test_empty.json"]

    def setUp(self):
        self.user = self.login()

    def get(self, params={}):
        return self.client.get(reverse("wagtailimages_chooser:choose"), params)

    def test_construct_queryset_hook_search(self):
        image = Image.objects.create(
            title="Test image shown",
            file=get_test_image_file(),
            uploaded_by_user=self.user,
        )
        Image.objects.create(
            title="Test image not shown",
            file=get_test_image_file(),
        )

        def filter_images(images, request):
            # Filter on `uploaded_by_user` because it is
            # the only default FilterField in search_fields
            return images.filter(uploaded_by_user=self.user)

        with self.register_hook("construct_image_chooser_queryset", filter_images):
            response = self.get({"q": "Test"})
        self.assertEqual(len(response.context["results"]), 1)
        self.assertEqual(response.context["results"][0], image)


class TestImageChooserChosenView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

        # Create an image to edit
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
            description="Test description",
        )

    def get(self, params={}):
        return self.client.get(
            reverse("wagtailimages_chooser:chosen", args=(self.image.id,)), params
        )

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json["step"], "chosen")
        self.assertEqual(response_json["result"]["title"], "Test image")
        self.assertEqual(
            set(response_json["result"]["preview"].keys()), {"url", "width", "height"}
        )
        self.assertEqual(
            response_json["result"]["default_alt_text"], "Test description"
        )

    def test_with_multiple_flag(self):
        # if 'multiple' is passed as a URL param, the result should be returned as a single-item list
        response = self.get(params={"multiple": 1})
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json["step"], "chosen")
        self.assertEqual(len(response_json["result"]), 1)
        self.assertEqual(response_json["result"][0]["title"], "Test image")
        self.assertEqual(
            set(response_json["result"][0]["preview"].keys()),
            {"url", "width", "height"},
        )
        self.assertEqual(
            response_json["result"][0]["default_alt_text"], "Test description"
        )


class TestImageChooserChosenMultipleView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

        # Create an image to edit
        self.image1 = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
            description="Test description",
        )
        self.image2 = Image.objects.create(
            title="Another test image",
            file=get_test_image_file(),
            description="Another test description",
        )

        self.image3 = Image.objects.create(
            title="Unchosen test image",
            file=get_test_image_file(),
            description="Unchosen test description",
        )

    def get(self, params={}):
        return self.client.get(
            "%s?id=%d&id=%d"
            % (
                reverse("wagtailimages_chooser:chosen_multiple"),
                self.image1.pk,
                self.image2.pk,
            )
        )

    def test_get(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json["step"], "chosen")
        self.assertEqual(len(response_json["result"]), 2)
        titles = {item["title"] for item in response_json["result"]}
        self.assertEqual(titles, {"Test image", "Another test image"})
        alt_texts = {item["default_alt_text"] for item in response_json["result"]}
        self.assertEqual(alt_texts, {"Test description", "Another test description"})


class TestImageChooserSelectFormatView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

        # Create an image to edit
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def get(self, params={}):
        return self.client.get(
            reverse("wagtailimages_chooser:select_format", args=(self.image.id,)),
            params,
        )

    def post(self, post_data={}):
        return self.client.post(
            reverse("wagtailimages_chooser:select_format", args=(self.image.id,)),
            post_data,
        )

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json["step"], "select_format")
        self.assertTemplateUsed(response, "wagtailimages/chooser/select_format.html")

    def test_with_edit_params(self):
        response = self.get(params={"alt_text": "some previous alt text"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value=\\"some previous alt text\\"')
        self.assertNotContains(
            response, 'id=\\"id_image-chooser-insertion-image_is_decorative\\" checked'
        )

    def test_with_edit_params_no_alt_text_marks_as_decorative(self):
        response = self.get(params={"alt_text": ""})
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, 'id=\\"id_image-chooser-insertion-image_is_decorative\\" checked'
        )

    def test_post_response(self):
        response = self.post(
            {
                "image-chooser-insertion-format": "left",
                "image-chooser-insertion-image_is_decorative": False,
                "image-chooser-insertion-alt_text": 'Arthur "two sheds" Jackson',
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json["step"], "chosen")
        result = response_json["result"]

        self.assertEqual(result["id"], str(self.image.id))
        self.assertEqual(result["title"], "Test image")
        self.assertEqual(result["format"], "left")
        self.assertEqual(result["alt"], 'Arthur "two sheds" Jackson')
        self.assertIn('alt="Arthur &quot;two sheds&quot; Jackson"', result["html"])

    def test_post_response_image_is_decorative_discards_alt_text(self):
        response = self.post(
            {
                "image-chooser-insertion-format": "left",
                "image-chooser-insertion-alt_text": 'Arthur "two sheds" Jackson',
                "image-chooser-insertion-image_is_decorative": True,
            }
        )
        response_json = json.loads(response.content.decode())
        result = response_json["result"]

        self.assertEqual(result["alt"], "")
        self.assertIn('alt=""', result["html"])

    def test_post_response_image_is_not_decorative_missing_alt_text(self):
        response = self.post(
            {
                "image-chooser-insertion-format": "left",
                "image-chooser-insertion-alt_text": "",
                "image-chooser-insertion-image_is_decorative": False,
            }
        )
        response_json = json.loads(response.content.decode())
        self.assertIn(
            "Please add some alt text for your image or mark it as decorative",
            response_json["html"],
        )


class TestImageChooserUploadView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse("wagtailimages_chooser:create"), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/generic/chooser/creation_form.html"
        )
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json["step"], "reshow_creation_form")

    def test_upload(self):
        response = self.client.post(
            reverse("wagtailimages_chooser:create"),
            {
                "image-chooser-upload-title": "Test image",
                "image-chooser-upload-file": SimpleUploadedFile(
                    "test.png", get_test_image_file().file.getvalue()
                ),
            },
        )

        # Check response
        self.assertEqual(response.status_code, 200)

        # Check that the image was created
        images = Image.objects.filter(title="Test image")
        self.assertEqual(images.count(), 1)

        # Test that size was populated correctly
        image = images.first()
        self.assertEqual(image.width, 640)
        self.assertEqual(image.height, 480)

        # Test that the file_size/hash fields were set
        self.assertTrue(image.file_size)
        self.assertTrue(image.file_hash)

    def test_upload_no_file_selected(self):
        response = self.client.post(
            reverse("wagtailimages_chooser:create"),
            {
                "image-chooser-upload-title": "Test image",
            },
        )

        # Shouldn't redirect anywhere
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/generic/chooser/creation_form.html"
        )

        # The form should have an error
        self.assertFormError(
            response.context["form"], "file", "This field is required."
        )

    def test_upload_duplicate(self):
        def post_image(title="Test image"):
            return self.client.post(
                reverse("wagtailimages_chooser:create"),
                {
                    "image-chooser-upload-title": title,
                    "image-chooser-upload-file": SimpleUploadedFile(
                        "test.png", get_test_image_file().file.getvalue()
                    ),
                },
            )

        # Post image then post duplicate
        post_image()
        response = post_image(title="Test duplicate image")

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailimages/chooser/confirm_duplicate_upload.html"
        )

        # Check context
        Image = get_image_model()
        new_image = Image.objects.get(title="Test duplicate image")
        existing_image = Image.objects.get(title="Test image")
        self.assertEqual(response.context["new_image"], new_image)
        self.assertEqual(response.context["existing_image"], existing_image)

        choose_new_image_action = reverse(
            "wagtailimages_chooser:chosen", args=(new_image.id,)
        )
        self.assertEqual(
            response.context["confirm_duplicate_upload_action"], choose_new_image_action
        )

        choose_existing_image_action = (
            reverse("wagtailimages:delete", args=(new_image.id,))
            + "?"
            + urlencode(
                {
                    "next": reverse(
                        "wagtailimages_chooser:chosen", args=(existing_image.id,)
                    )
                }
            )
        )
        self.assertEqual(
            response.context["cancel_duplicate_upload_action"],
            choose_existing_image_action,
        )

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json["step"], "duplicate_found")

    def test_upload_duplicate_select_format(self):
        def post_image(title="Test image"):
            return self.client.post(
                reverse("wagtailimages_chooser:create") + "?select_format=true",
                {
                    "image-chooser-upload-title": title,
                    "image-chooser-upload-file": SimpleUploadedFile(
                        "test.png", get_test_image_file().file.getvalue()
                    ),
                },
            )

        # Post image then post duplicate
        post_image()
        response = post_image(title="Test duplicate image")

        # Check response
        self.assertEqual(response.status_code, 200)

        # Check context
        Image = get_image_model()
        new_image = Image.objects.get(title="Test duplicate image")
        existing_image = Image.objects.get(title="Test image")

        choose_new_image_action = (
            reverse("wagtailimages_chooser:select_format", args=(new_image.id,))
            + "?select_format=true"
        )
        self.assertEqual(
            response.context["confirm_duplicate_upload_action"], choose_new_image_action
        )

        choose_existing_image_action = (
            reverse("wagtailimages:delete", args=(new_image.id,))
            + "?"
            + urlencode(
                {
                    "next": reverse(
                        "wagtailimages_chooser:select_format", args=(existing_image.id,)
                    )
                    + "?select_format=true"
                }
            )
        )
        self.assertEqual(
            response.context["cancel_duplicate_upload_action"],
            choose_existing_image_action,
        )

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json["step"], "duplicate_found")

    def test_select_format_flag_after_upload_form_error(self):
        submit_url = reverse("wagtailimages_chooser:create") + "?select_format=true"
        response = self.client.post(
            submit_url,
            {
                "image-chooser-upload-title": "Test image",
                "image-chooser-upload-file": SimpleUploadedFile(
                    "not_an_image.txt", b"this is not an image"
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/generic/chooser/creation_form.html"
        )
        self.assertFormError(
            response.context["form"],
            "file",
            "Upload a valid image. The file you uploaded was either not an image or a corrupted image.",
        )

        # the action URL of the re-rendered form should include the select_format=true parameter
        # (NB the HTML in the response is embedded in a JS string, so need to escape accordingly)
        expected_action_attr = 'action=\\"%s\\"' % submit_url
        self.assertContains(response, expected_action_attr)

    def test_select_format_flag_after_upload_form_error_bad_extension(self):
        """
        Check the error message is accruate for a valid imate bug invalid file extension.
        """
        submit_url = reverse("wagtailimages_chooser:create") + "?select_format=true"
        response = self.client.post(
            submit_url,
            {
                "image-chooser-upload-title": "accidental markdown extension",
                "image-chooser-upload-file": SimpleUploadedFile(
                    "not-an-image.md", get_test_image_file().file.getvalue()
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/generic/chooser/creation_form.html"
        )
        self.assertFormError(
            response.context["form"],
            "file",
            "Not a supported image format. Supported formats: AVIF, GIF, JPG, JPEG, PNG, WEBP.",
        )

        # the action URL of the re-rendered form should include the select_format=true parameter
        # (NB the HTML in the response is embedded in a JS string, so need to escape accordingly)
        expected_action_attr = 'action=\\"%s\\"' % submit_url
        self.assertContains(response, expected_action_attr)

    @override_settings(
        STORAGES={
            **settings.STORAGES,
            "default": {
                "BACKEND": "wagtail.test.dummy_external_storage.DummyExternalStorage"
            },
        },
    )
    def test_upload_with_external_storage(self):
        response = self.client.post(
            reverse("wagtailimages_chooser:create"),
            {
                "image-chooser-upload-title": "Test image",
                "image-chooser-upload-file": SimpleUploadedFile(
                    "test.png", get_test_image_file().file.getvalue()
                ),
            },
        )

        # Check response
        self.assertEqual(response.status_code, 200)

        # Check that the image was created
        self.assertTrue(Image.objects.filter(title="Test image").exists())

    @override_settings(WAGTAILIMAGES_IMAGE_MODEL="tests.CustomImage")
    def test_unique_together_validation(self):
        root_collection = Collection.get_first_root_node()
        evil_plans_collection = root_collection.add_child(name="Evil plans")
        # another image with a title to collide with
        CustomImage.objects.create(
            title="Test image",
            file=get_test_image_file(),
            collection=evil_plans_collection,
        )

        response = self.client.post(
            reverse("wagtailimages_chooser:create"),
            {
                "image-chooser-upload-title": "Test image",
                "image-chooser-upload-file": SimpleUploadedFile(
                    "test.png", get_test_image_file().file.getvalue()
                ),
                "image-chooser-upload-collection": evil_plans_collection.id,
            },
        )

        # Shouldn't redirect anywhere
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/generic/chooser/creation_form.html"
        )

        # The form should have an error
        self.assertContains(
            response, "Custom image with this Title and Collection already exists."
        )


class TestImageChooserUploadViewWithLimitedPermissions(WagtailTestUtils, TestCase):
    def setUp(self):
        add_image_permission = Permission.objects.get(
            content_type__app_label="wagtailimages", codename="add_image"
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
            permission=add_image_permission,
        )

        user = self.create_user(
            username="moriarty", email="moriarty@example.com", password="password"
        )
        user.groups.add(conspirators_group)

        self.login(username="moriarty", password="password")

    def test_get(self):
        response = self.client.get(reverse("wagtailimages_chooser:create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/generic/chooser/creation_form.html"
        )

        # user only has access to one collection, so no 'Collection' option
        # is displayed on the form
        self.assertNotContains(
            response,
            '<label class="w-field__label" for="id_collection" id="id_collection-label">',
        )

    def test_get_chooser(self):
        response = self.client.get(reverse("wagtailimages_chooser:choose"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/chooser/chooser.html")

        # user only has access to one collection, so no 'Collection' option
        # is displayed on the form
        self.assertNotContains(
            response,
            '<label class="w-field__label" for="id_collection" id="id_collection-label">',
        )

    def test_add(self):
        response = self.client.post(
            reverse("wagtailimages_chooser:create"),
            {
                "image-chooser-upload-title": "Test image",
                "image-chooser-upload-file": SimpleUploadedFile(
                    "test.png", get_test_image_file().file.getvalue()
                ),
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check that the image was created
        images = Image.objects.filter(title="Test image")
        self.assertEqual(images.count(), 1)

        # Image should be created in the 'evil plans' collection,
        # despite there being no collection field in the form, because that's the
        # only one the user has access to
        self.assertTrue(Image.objects.filter(title="Test image").exists())
        self.assertEqual(
            Image.objects.get(title="Test image").collection, self.evil_plans_collection
        )


class TestMultipleImageUploader(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    """
    This tests the multiple image upload views located in wagtailimages/views/multiple.py
    """

    def setUp(self):
        self.user = self.login()

        # Create an image for running tests on
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def test_add(self):
        """
        This tests that the add view responds correctly on a GET request
        """
        # Send request
        response = self.client.get(reverse("wagtailimages:add_multiple"))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/multiple/add.html")

        # multiple upload file field should have 'accept' attr with an explicit
        # case for image/avif
        soup = self.get_soup(response.content)
        self.assertEqual(
            soup.select_one("input[type='file'][multiple]").get("accept"),
            "image/*, image/avif",
        )

        # draftail should NOT be a standard JS include on this page
        # (see TestMultipleImageUploaderWithCustomImageModel - this confirms that form media
        # definitions are being respected)
        self.assertNotContains(response, "wagtailadmin/js/draftail.js")

        self.assertBreadcrumbsItemsRendered(
            [
                {
                    "url": reverse("wagtailimages:index"),
                    "label": capfirst(self.image._meta.verbose_name_plural),
                },
                {"url": "", "label": "Add images"},
            ],
            response.content,
        )

    @override_settings(
        WAGTAILIMAGES_EXTENSIONS=["gif", "jpg", "jpeg", "png", "webp", "avif", "heic"]
    )
    def test_multiple_upload_field_accepts_heic(self):
        response = self.client.get(reverse("wagtailimages:add_multiple"))

        self.assertEqual(response.status_code, 200)

        # multiple upload file field should have explicit 'accept' case for image/heic and image/avif
        soup = self.get_soup(response.content)
        self.assertEqual(
            soup.select_one("input[type='file'][multiple]").get("accept"),
            "image/*, image/heic, image/avif",
        )

    @override_settings(WAGTAILIMAGES_EXTENSIONS=["gif", "jpg", "jpeg", "png", "webp"])
    def test_multiple_upload_field_without_avif(self):
        response = self.client.get(reverse("wagtailimages:add_multiple"))

        self.assertEqual(response.status_code, 200)

        soup = self.get_soup(response.content)
        self.assertEqual(
            soup.select_one("input[type='file'][multiple]").get("accept"), "image/*"
        )

    @override_settings(WAGTAILIMAGES_MAX_UPLOAD_SIZE=1000)
    def test_add_max_file_size_context_variables(self):
        response = self.client.get(reverse("wagtailimages:add_multiple"))

        self.assertEqual(response.context["max_filesize"], 1000)
        self.assertEqual(
            response.context["error_max_file_size"],
            "This file is too big. Maximum filesize 1000\xa0bytes.",
        )

    def test_add_error_max_file_size_escaped(self):
        url = reverse("wagtailimages:add_multiple")
        template_name = "wagtailimages/multiple/add.html"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, template_name)

        value = "Too big. <br/><br/><a href='/admin/images/add/'>Try this.</a>"
        response_content = force_str(response.content)
        self.assertNotIn(value, response_content)
        self.assertNotIn(escapejs(value), response_content)

        request = RequestFactory().get(url)
        request.user = self.user
        context = response.context_data.copy()
        context["error_max_file_size"] = mark_safe(force_str(value))
        data = render_to_string(
            template_name,
            context=context,
            request=request,
        )
        self.assertNotIn(value, data)
        self.assertIn(escapejs(value), data)

    def test_add_error_accepted_file_types_escaped(self):
        url = reverse("wagtailimages:add_multiple")
        template_name = "wagtailimages/multiple/add.html"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, template_name)

        value = "Invalid image type. <a href='/help'>Get help.</a>"
        response_content = force_str(response.content)
        self.assertNotIn(value, response_content)
        self.assertNotIn(escapejs(value), response_content)

        request = RequestFactory().get(url)
        request.user = self.user
        context = response.context_data.copy()
        context["error_accepted_file_types"] = mark_safe(force_str(value))
        data = render_to_string(
            template_name,
            context=context,
            request=request,
        )
        self.assertNotIn(value, data)
        self.assertIn(escapejs(value), data)

    def test_add_post(self):
        """
        This tests that a POST request to the add view saves the image and returns an edit form
        """
        response = self.client.post(
            reverse("wagtailimages:add_multiple"),
            {
                "title": "test title",
                "files[]": SimpleUploadedFile(
                    "test.png", get_test_image_file().file.getvalue()
                ),
            },
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertTemplateUsed(
            response, "wagtailadmin/generic/multiple_upload/edit_form.html"
        )

        # Check image
        self.assertIn("image", response.context)
        self.assertEqual(response.context["image"].title, "test title")
        self.assertTrue(response.context["image"].file_size)
        self.assertTrue(response.context["image"].file_hash)

        # Check image title
        image = get_image_model().objects.get(title="test title")
        self.assertNotIn("title", image.filename)
        self.assertIn(".png", image.filename)

        # Check form
        self.assertIn("form", response.context)
        self.assertEqual(
            response.context["edit_action"],
            "/admin/images/multiple/%d/" % response.context["image"].id,
        )
        self.assertEqual(
            response.context["delete_action"],
            "/admin/images/multiple/%d/delete/" % response.context["image"].id,
        )
        self.assertEqual(response.context["form"].initial["title"], "test title")

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn("form", response_json)
        self.assertIn("image_id", response_json)
        self.assertIn("success", response_json)
        self.assertIn("duplicate", response_json)
        self.assertEqual(response_json["image_id"], response.context["image"].id)
        self.assertTrue(response_json["success"])
        self.assertFalse(response_json["duplicate"])

    def test_add_post_no_title(self):
        """
        A POST request to the add view without the title value saves the image and uses file title if needed
        """
        response = self.client.post(
            reverse("wagtailimages:add_multiple"),
            {
                "files[]": SimpleUploadedFile(
                    "no-title.png", get_test_image_file().file.getvalue()
                ),
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        # Check image
        self.assertIn("image", response.context)
        self.assertTrue(response.context["image"].file_size)
        self.assertTrue(response.context["image"].file_hash)

        # Check image title
        image = get_image_model().objects.get(title="no-title.png")
        self.assertEqual("no-title.png", image.filename)
        self.assertIn(".png", image.filename)

        # Check form
        self.assertIn("form", response.context)
        self.assertEqual(response.context["form"].initial["title"], "no-title.png")

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn("form", response_json)
        self.assertIn("success", response_json)

    def test_add_post_nofile(self):
        """
        This tests that the add view checks for a file when a user POSTs to it
        """
        response = self.client.post(reverse("wagtailimages:add_multiple"), {})

        # Check response
        self.assertEqual(response.status_code, 400)

    def test_add_post_badfile(self):
        """
        The add view must check that the uploaded file is a valid image
        """
        response = self.client.post(
            reverse("wagtailimages:add_multiple"),
            {
                "files[]": SimpleUploadedFile("test.png", b"This is not an image!"),
            },
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertNotIn("image_id", response_json)
        self.assertNotIn("form", response_json)
        self.assertIn("success", response_json)
        self.assertIn("error_message", response_json)
        self.assertFalse(response_json["success"])
        self.assertEqual(
            response_json["error_message"],
            "Upload a valid image. The file you uploaded was either not an image or a corrupted image.",
        )

    @override_settings(WAGTAILIMAGES_EXTENSIONS=["jpg", "gif"])
    def test_add_post_bad_extension(self):
        """
        The add view must check that the uploaded file extension is a valid
        """
        response = self.client.post(
            reverse("wagtailimages:add_multiple"),
            {
                "files[]": SimpleUploadedFile(
                    "test.txt", get_test_image_file().file.getvalue()
                ),
            },
        )

        post_with_invalid_extension = self.client.post(
            reverse("wagtailimages:add_multiple"),
            {
                "files[]": SimpleUploadedFile(
                    "test.png", get_test_image_file().file.getvalue()
                ),
            },
        )
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertNotIn("image_id", response_json)
        self.assertNotIn("form", response_json)
        self.assertIn("success", response_json)
        self.assertIn("error_message", response_json)
        self.assertFalse(response_json["success"])
        self.assertEqual(
            response_json["error_message"],
            "Not a supported image format. Supported formats: JPG, GIF.",
        )

        # Check post_with_invalid_extension
        self.assertEqual(post_with_invalid_extension.status_code, 200)
        self.assertEqual(
            post_with_invalid_extension["Content-Type"], "application/json"
        )

        # Check JSON
        response_json = json.loads(post_with_invalid_extension.content.decode())
        self.assertNotIn("image_id", response_json)
        self.assertNotIn("form", response_json)
        self.assertIn("success", response_json)
        self.assertIn("error_message", response_json)
        self.assertFalse(response_json["success"])
        self.assertEqual(
            response_json["error_message"],
            "Not a supported image format. Supported formats: JPG, GIF.",
        )

    def test_add_post_duplicate(self):
        """
        When a duplicate image is saved, the add view shows that it's a duplicate
        and prompts user to confirm the upload.
        """

        def post_image(title="test title"):
            return self.client.post(
                reverse("wagtailimages:add_multiple"),
                {
                    "title": title,
                    "files[]": SimpleUploadedFile(
                        "test.png", get_test_image_file().file.getvalue()
                    ),
                },
            )

        # Post image then post duplicate
        post_image()
        response = post_image(title="test title duplicate")

        # Check response
        self.assertEqual(response.status_code, 200)

        # Check template used
        self.assertTemplateUsed(
            response, "wagtailimages/images/confirm_duplicate_upload.html"
        )

        # Check image
        self.assertEqual(response.context["image"].title, "test title duplicate")

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn("form", response_json)
        self.assertIn("confirm_duplicate_upload", response_json)
        self.assertTrue(response_json["success"])
        self.assertTrue(response_json["duplicate"])

    def test_add_post_duplicate_choose_permission(self):
        """
        When a duplicate image is added but the user doesn't have permission to choose the original image,
        the add views lets the user upload it as if it weren't a duplicate.
        """

        # Create group with access to admin and add permission.
        bakers_group = Group.objects.create(name="Bakers")
        access_admin_perm = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        bakers_group.permissions.add(access_admin_perm)

        # Create the "Bakery" Collection and grant "add" permission to the Bakers group.
        root = Collection.objects.get(id=get_root_collection_id())
        bakery_collection = root.add_child(instance=Collection(name="Bakery"))
        GroupCollectionPermission.objects.create(
            group=bakers_group,
            collection=bakery_collection,
            permission=Permission.objects.get(
                content_type__app_label="wagtailimages", codename="add_image"
            ),
        )

        def post_image(title="test title"):
            # Add image in the "Bakery" Collection
            return self.client.post(
                reverse("wagtailimages:add_multiple"),
                {
                    "title": title,
                    "files[]": SimpleUploadedFile(
                        "test.png", get_test_image_file().file.getvalue()
                    ),
                    "collection": bakery_collection.id,
                },
            )

        # Post image
        post_image()

        # Remove privileges from user
        self.user.is_superuser = False
        self.user.groups.add(bakers_group)
        self.user.save()

        # Post duplicate
        response = post_image(title="test title duplicate")

        # Check response
        self.assertEqual(response.status_code, 200)

        # Check template used
        self.assertTemplateNotUsed(
            response, "wagtailimages/images/confirm_duplicate_upload.html"
        )

        # Check image
        self.assertEqual(response.context["image"].title, "test title duplicate")

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertTrue(response_json["success"])
        self.assertFalse(response_json["duplicate"])
        self.assertIn("form", response_json)
        self.assertNotIn("confirm_duplicate_upload", response_json)

    def test_edit_get(self):
        """
        This tests that a GET request to the edit view returns a 405 "METHOD NOT ALLOWED" response
        """
        # Send request
        response = self.client.get(
            reverse("wagtailimages:edit_multiple", args=(self.image.id,))
        )

        # Check response
        self.assertEqual(response.status_code, 405)

    def test_edit_post(self):
        """
        This tests that a POST request to the edit view edits the image
        """
        # Send request
        response = self.client.post(
            reverse("wagtailimages:edit_multiple", args=(self.image.id,)),
            {
                ("image-%d-title" % self.image.id): "New title!",
                ("image-%d-tags" % self.image.id): "cromarty, finisterre",
            },
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn("image_id", response_json)
        self.assertNotIn("form", response_json)
        self.assertIn("success", response_json)
        self.assertEqual(response_json["image_id"], self.image.id)
        self.assertTrue(response_json["success"])

        # test that changes have been applied to the image
        image = Image.objects.get(id=self.image.id)
        self.assertEqual(image.title, "New title!")
        self.assertIn("cromarty", image.tags.names())

    def test_edit_post_validation_error(self):
        """
        This tests that a POST request to the edit page returns a json document with "success=False"
        and a form with the validation error indicated
        """
        # Send request
        response = self.client.post(
            reverse("wagtailimages:edit_multiple", args=(self.image.id,)),
            {
                ("image-%d-title" % self.image.id): "",  # Required
                ("image-%d-tags" % self.image.id): "",
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
        self.assertIn("image_id", response_json)
        self.assertIn("form", response_json)
        self.assertIn("success", response_json)
        self.assertEqual(response_json["image_id"], self.image.id)
        self.assertFalse(response_json["success"])

    def test_delete_get(self):
        """
        This tests that a GET request to the delete view returns a 405 "METHOD NOT ALLOWED" response
        """
        # Send request
        response = self.client.get(
            reverse("wagtailimages:delete_multiple", args=(self.image.id,))
        )

        # Check response
        self.assertEqual(response.status_code, 405)

    def test_delete_post(self):
        """
        This tests that a POST request to the delete view deletes the image
        """
        # Send request
        response = self.client.post(
            reverse("wagtailimages:delete_multiple", args=(self.image.id,))
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        # Make sure the image is deleted
        self.assertFalse(Image.objects.filter(id=self.image.id).exists())

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn("image_id", response_json)
        self.assertIn("success", response_json)
        self.assertEqual(response_json["image_id"], self.image.id)
        self.assertTrue(response_json["success"])


@override_settings(WAGTAILIMAGES_IMAGE_MODEL="tests.CustomImage")
class TestMultipleImageUploaderWithCustomImageModel(WagtailTestUtils, TestCase):
    """
    This tests the multiple image upload views located in wagtailimages/views/multiple.py
    with a custom image model
    """

    def setUp(self):
        self.login()

        # Create an image for running tests on
        self.image = CustomImage.objects.create(
            title="test-image.png",
            file=get_test_image_file(),
        )

    def test_add(self):
        """
        This tests that the add view responds correctly on a GET request
        """
        # Send request
        response = self.client.get(reverse("wagtailimages:add_multiple"))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/multiple/add.html")

        # response should include form media for the image edit form
        self.assertContains(response, "wagtailadmin/js/draftail.js")

    def test_add_post(self):
        """
        This tests that a POST request to the add view saves the image and returns an edit form
        """
        response = self.client.post(
            reverse("wagtailimages:add_multiple"),
            {
                "files[]": SimpleUploadedFile(
                    "test.png", get_test_image_file().file.getvalue()
                ),
            },
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertTemplateUsed(
            response, "wagtailadmin/generic/multiple_upload/edit_form.html"
        )

        # Check image
        self.assertIn("image", response.context)
        self.assertEqual(response.context["image"].title, "test.png")
        self.assertTrue(response.context["image"].file_size)
        self.assertTrue(response.context["image"].file_hash)

        # Check form
        self.assertIn("form", response.context)
        self.assertEqual(response.context["form"].initial["title"], "test.png")
        self.assertIn("caption", response.context["form"].fields)
        self.assertNotIn("not_editable_field", response.context["form"].fields)
        self.assertEqual(
            response.context["edit_action"],
            "/admin/images/multiple/%d/" % response.context["image"].id,
        )
        self.assertEqual(
            response.context["delete_action"],
            "/admin/images/multiple/%d/delete/" % response.context["image"].id,
        )

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn("form", response_json)
        self.assertIn("success", response_json)
        self.assertIn("duplicate", response_json)
        self.assertTrue(response_json["success"])
        self.assertFalse(response_json["duplicate"])

    def test_add_post_badfile(self):
        """
        The add view must check that the uploaded file is a valid image
        """
        response = self.client.post(
            reverse("wagtailimages:add_multiple"),
            {
                "files[]": SimpleUploadedFile("test.png", b"This is not an image!"),
            },
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertNotIn("image_id", response_json)
        self.assertNotIn("form", response_json)
        self.assertIn("success", response_json)
        self.assertIn("error_message", response_json)
        self.assertFalse(response_json["success"])
        self.assertEqual(
            response_json["error_message"],
            "Upload a valid image. The file you uploaded was either not an image or a corrupted image.",
        )

    def test_add_post_duplicate(self):
        def post_image(title="test title"):
            return self.client.post(
                reverse("wagtailimages:add_multiple"),
                {
                    "title": title,
                    "files[]": SimpleUploadedFile(
                        "test.png", get_test_image_file().file.getvalue()
                    ),
                },
            )

        # Post image then post duplicate
        post_image()
        response = post_image(title="test title duplicate")

        # Check response
        self.assertEqual(response.status_code, 200)

        # Check template used
        self.assertTemplateUsed(
            response, "wagtailimages/images/confirm_duplicate_upload.html"
        )

        # Check image
        self.assertEqual(response.context["image"].title, "test title duplicate")
        self.assertIn("caption", response.context["form"].fields)
        self.assertNotIn("not_editable_field", response.context["form"].fields)

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn("form", response_json)
        self.assertIn("confirm_duplicate_upload", response_json)
        self.assertTrue(response_json["success"])
        self.assertTrue(response_json["duplicate"])

    def test_unique_together_validation_error(self):
        """
        If unique_together validation fails, create an UploadedFile and return a form so the
        user can fix it
        """
        root_collection = Collection.get_first_root_node()
        new_collection = root_collection.add_child(name="holiday snaps")
        self.image.collection = new_collection
        self.image.save()

        image_count_before = CustomImage.objects.count()
        uploaded_image_count_before = UploadedFile.objects.count()

        response = self.client.post(
            reverse("wagtailimages:add_multiple"),
            {
                "files[]": SimpleUploadedFile(
                    "test-image.png", get_test_image_file().file.getvalue()
                ),
                "collection": new_collection.id,
            },
        )

        image_count_after = CustomImage.objects.count()
        uploaded_image_count_after = UploadedFile.objects.count()

        # an UploadedFile should have been created now, but not a CustomImage
        self.assertEqual(image_count_after, image_count_before)
        self.assertEqual(uploaded_image_count_after, uploaded_image_count_before + 1)

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertTemplateUsed(
            response, "wagtailadmin/generic/multiple_upload/edit_form.html"
        )

    def test_edit_post(self):
        """
        This tests that a POST request to the edit view edits the image
        """
        # Send request
        response = self.client.post(
            reverse("wagtailimages:edit_multiple", args=(self.image.id,)),
            {
                ("image-%d-title" % self.image.id): "New title!",
                ("image-%d-tags" % self.image.id): "footwear, dystopia",
                (
                    "image-%d-caption" % self.image.id
                ): "a boot stamping on a human face, forever",
            },
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn("image_id", response_json)
        self.assertNotIn("form", response_json)
        self.assertIn("success", response_json)
        self.assertEqual(response_json["image_id"], self.image.id)
        self.assertTrue(response_json["success"])

        # check that image has been updated
        new_image = CustomImage.objects.get(id=self.image.id)
        self.assertEqual(new_image.title, "New title!")
        self.assertEqual(new_image.caption, "a boot stamping on a human face, forever")
        self.assertIn("footwear", new_image.tags.names())

    def test_edit_fails_unique_together_validation(self):
        """
        Check that the form returned on failing a unique-together validation error
        includes that error message, despite it being a non-field error
        """
        root_collection = Collection.get_first_root_node()
        new_collection = root_collection.add_child(name="holiday snaps")
        # create another image for the edited title to collide with
        CustomImage.objects.create(
            title="The Eiffel Tower",
            file=get_test_image_file(),
            collection=new_collection,
        )

        response = self.client.post(
            reverse("wagtailimages:edit_multiple", args=(self.image.id,)),
            {
                ("image-%d-title" % self.image.id): "The Eiffel Tower",
                ("image-%d-collection" % self.image.id): new_collection.id,
                ("image-%d-tags" % self.image.id): "",
                ("image-%d-caption" % self.image.id): "ooh la la",
            },
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertTemplateUsed(
            response, "wagtailadmin/generic/multiple_upload/edit_form.html"
        )

        response_json = json.loads(response.content.decode())
        # Check JSON
        self.assertEqual(response_json["image_id"], self.image.id)
        self.assertFalse(response_json["success"])

        # Check that a form error was raised
        self.assertIn(
            "Custom image with this Title and Collection already exists.",
            response_json["form"],
        )

    def test_delete_post(self):
        """
        This tests that a POST request to the delete view deletes the image
        """
        # Send request
        response = self.client.post(
            reverse("wagtailimages:delete_multiple", args=(self.image.id,))
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        # Make sure the image is deleted
        self.assertFalse(Image.objects.filter(id=self.image.id).exists())

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn("image_id", response_json)
        self.assertIn("success", response_json)
        self.assertEqual(response_json["image_id"], self.image.id)
        self.assertTrue(response_json["success"])

        # check that image has been deleted
        self.assertEqual(CustomImage.objects.filter(id=self.image.id).count(), 0)


@override_settings(WAGTAILIMAGES_IMAGE_MODEL="tests.CustomImageWithAuthor")
class TestMultipleImageUploaderWithCustomRequiredFields(WagtailTestUtils, TestCase):
    """
    This tests the multiple image upload views located in wagtailimages/views/multiple.py
    with a custom image model
    """

    def setUp(self):
        self.user = self.login()

        # Create an UploadedFile for running tests on
        self.uploaded_image = UploadedFile.objects.create(
            for_content_type=ContentType.objects.get_for_model(get_image_model()),
            file=get_test_image_file(),
            uploaded_by_user=self.user,
        )

    def test_add(self):
        """
        This tests that the add view responds correctly on a GET request
        """
        # Send request
        response = self.client.get(reverse("wagtailimages:add_multiple"))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/multiple/add.html")

    def test_add_post(self):
        """
        A POST request to the add view should create an UploadedFile rather than an image,
        as we do not have enough data to pass CustomImageWithAuthor's validation yet
        """
        image_count_before = CustomImageWithAuthor.objects.count()
        uploaded_image_count_before = UploadedFile.objects.count()

        response = self.client.post(
            reverse("wagtailimages:add_multiple"),
            {
                "files[]": SimpleUploadedFile(
                    "test.png", get_test_image_file().file.getvalue()
                ),
            },
        )

        image_count_after = CustomImageWithAuthor.objects.count()
        uploaded_image_count_after = UploadedFile.objects.count()

        # an UploadedFile should have been created now, but not a CustomImageWithAuthor
        self.assertEqual(image_count_after, image_count_before)
        self.assertEqual(uploaded_image_count_after, uploaded_image_count_before + 1)

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertTemplateUsed(
            response, "wagtailadmin/generic/multiple_upload/edit_form.html"
        )

        # Check image
        self.assertIn("uploaded_image", response.context)
        self.assertTrue(response.context["uploaded_image"].file.name)

        # Check form
        self.assertIn("form", response.context)
        self.assertEqual(response.context["form"].initial["title"], "test.png")
        self.assertIn("author", response.context["form"].fields)
        self.assertEqual(
            response.context["edit_action"],
            "/admin/images/multiple/create_from_uploaded_image/%d/"
            % response.context["uploaded_image"].id,
        )
        self.assertEqual(
            response.context["delete_action"],
            "/admin/images/multiple/delete_upload/%d/"
            % response.context["uploaded_image"].id,
        )

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn("form", response_json)
        self.assertIn("success", response_json)
        self.assertTrue(response_json["success"])

    def test_add_post_badfile(self):
        """
        The add view must check that the uploaded file is a valid image
        """
        response = self.client.post(
            reverse("wagtailimages:add_multiple"),
            {
                "files[]": SimpleUploadedFile("test.png", b"This is not an image!"),
            },
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertNotIn("image_id", response_json)
        self.assertNotIn("form", response_json)
        self.assertIn("success", response_json)
        self.assertIn("error_message", response_json)
        self.assertFalse(response_json["success"])
        self.assertEqual(
            response_json["error_message"],
            "Upload a valid image. The file you uploaded was either not an image or a corrupted image.",
        )

    def test_create_from_upload_invalid_post(self):
        """
        Posting an invalid form to the create_from_uploaded_image view throws a validation error and leaves the
        UploadedFile intact
        """
        image_count_before = CustomImageWithAuthor.objects.count()
        uploaded_image_count_before = UploadedFile.objects.count()

        # Send request
        response = self.client.post(
            reverse(
                "wagtailimages:create_multiple_from_uploaded_image",
                args=(self.uploaded_image.id,),
            ),
            {
                ("uploaded-image-%d-title" % self.uploaded_image.id): "New title!",
                ("uploaded-image-%d-tags" % self.uploaded_image.id): "",
                ("uploaded-image-%d-author" % self.uploaded_image.id): "",
            },
        )

        image_count_after = CustomImageWithAuthor.objects.count()
        uploaded_image_count_after = UploadedFile.objects.count()

        # no changes to image / UploadedFile count
        self.assertEqual(image_count_after, image_count_before)
        self.assertEqual(uploaded_image_count_after, uploaded_image_count_before)

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        # Check form
        self.assertIn("form", response.context)
        self.assertIn("author", response.context["form"].fields)
        self.assertEqual(
            response.context["edit_action"],
            "/admin/images/multiple/create_from_uploaded_image/%d/"
            % response.context["uploaded_image"].id,
        )
        self.assertEqual(
            response.context["delete_action"],
            "/admin/images/multiple/delete_upload/%d/"
            % response.context["uploaded_image"].id,
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
        Posting a valid form to the create_from_uploaded_image view will create the image
        """
        image_count_before = CustomImageWithAuthor.objects.count()
        uploaded_image_count_before = UploadedFile.objects.count()

        # Send request
        response = self.client.post(
            reverse(
                "wagtailimages:create_multiple_from_uploaded_image",
                args=(self.uploaded_image.id,),
            ),
            {
                ("uploaded-image-%d-title" % self.uploaded_image.id): "New title!",
                (
                    "uploaded-image-%d-tags" % self.uploaded_image.id
                ): "abstract, squares",
                ("uploaded-image-%d-author" % self.uploaded_image.id): "Piet Mondrian",
            },
        )

        image_count_after = CustomImageWithAuthor.objects.count()
        uploaded_image_count_after = UploadedFile.objects.count()

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn("image_id", response_json)
        self.assertTrue(response_json["success"])

        # Image should have been created, UploadedFile deleted
        self.assertEqual(image_count_after, image_count_before + 1)
        self.assertEqual(uploaded_image_count_after, uploaded_image_count_before - 1)

        image = CustomImageWithAuthor.objects.get(id=response_json["image_id"])
        self.assertEqual(image.title, "New title!")
        self.assertEqual(image.author, "Piet Mondrian")
        self.assertTrue(image.file.name)
        self.assertTrue(image.file_hash)
        self.assertTrue(image.file_size)
        self.assertEqual(image.width, 640)
        self.assertEqual(image.height, 480)
        self.assertIn("abstract", image.tags.names())

    def test_delete_uploaded_image(self):
        """
        This tests that a POST request to the delete view deletes the UploadedFile
        """
        # Send request
        response = self.client.post(
            reverse(
                "wagtailimages:delete_upload_multiple", args=(self.uploaded_image.id,)
            )
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        # Make sure the image is deleted
        self.assertFalse(
            UploadedFile.objects.filter(id=self.uploaded_image.id).exists()
        )

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertTrue(response_json["success"])


class TestURLGeneratorView(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    def setUp(self):
        # Create an image for running tests on
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

        # Login
        self.user = self.login()

    def test_get(self):
        """
        This tests that the view responds correctly for a user with edit permissions on this image
        """
        # Get
        response = self.client.get(
            reverse("wagtailimages:url_generator", args=(self.image.id,))
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/images/url_generator.html")
        self.assertTemplateUsed(response, "wagtailadmin/generic/base.html")

        self.assertBreadcrumbsItemsRendered(
            [
                {"url": reverse("wagtailimages:index"), "label": "Images"},
                {
                    "url": reverse("wagtailimages:edit", args=(self.image.id,)),
                    "label": "Test image",
                },
                {"url": "", "label": "Generate URL", "sublabel": "Test image"},
            ],
            response.content,
        )

    def test_get_bad_permissions(self):
        """
        This tests that the view returns a "permission denied" redirect if a user without correct
        permissions attempts to access it
        """
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        # Get
        response = self.client.get(
            reverse("wagtailimages:url_generator", args=(self.image.id,))
        )

        # Check response
        self.assertRedirects(response, reverse("wagtailadmin_home"))


class TestGenerateURLView(WagtailTestUtils, TestCase):
    def setUp(self):
        # Create an image for running tests on
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

        # Login
        self.user = self.login()

    def test_get(self):
        """
        This tests that the view responds correctly for a user with edit permissions on this image
        """
        # Get
        response = self.client.get(
            reverse("wagtailimages:generate_url", args=(self.image.id, "fill-800x600"))
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        # Check JSON
        content_json = json.loads(response.content.decode())

        self.assertEqual(set(content_json.keys()), {"url", "preview_url"})

        expected_url = (
            "http://localhost/images/%(signature)s/%(image_id)d/fill-800x600/"
            % {
                "signature": urllib.parse.quote(
                    generate_signature(self.image.id, "fill-800x600"),
                    safe=urlquote_safechars,
                ),
                "image_id": self.image.id,
            }
        )
        self.assertEqual(content_json["url"], expected_url)

        expected_preview_url = reverse(
            "wagtailimages:preview", args=(self.image.id, "fill-800x600")
        )
        self.assertEqual(content_json["preview_url"], expected_preview_url)

    def test_get_bad_permissions(self):
        """
        This tests that the view gives a 403 if a user without correct permissions attempts to access it
        """
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        # Get
        response = self.client.get(
            reverse("wagtailimages:generate_url", args=(self.image.id, "fill-800x600"))
        )

        # Check response
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response["Content-Type"], "application/json")

        # Check JSON
        self.assertJSONEqual(
            response.content.decode(),
            json.dumps(
                {
                    "error": "You do not have permission to generate a URL for this image.",
                }
            ),
        )

    def test_get_bad_image(self):
        """
        This tests that the view gives a 404 response if a user attempts to use it with an image which doesn't exist
        """
        # Get
        response = self.client.get(
            reverse(
                "wagtailimages:generate_url", args=(self.image.id + 1, "fill-800x600")
            )
        )

        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response["Content-Type"], "application/json")

        # Check JSON
        self.assertJSONEqual(
            response.content.decode(),
            json.dumps(
                {
                    "error": "Cannot find image.",
                }
            ),
        )

    def test_get_bad_filter_spec(self):
        """
        This tests that the view gives a 400 response if the user attempts to use it with an invalid filter spec
        """
        # Get
        response = self.client.get(
            reverse(
                "wagtailimages:generate_url", args=(self.image.id, "bad-filter-spec")
            )
        )

        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response["Content-Type"], "application/json")

        # Check JSON
        self.assertJSONEqual(
            response.content.decode(),
            json.dumps(
                {
                    "error": "Invalid filter spec.",
                }
            ),
        )


class TestPreviewView(WagtailTestUtils, TestCase):
    def setUp(self):
        # Create an image for running tests on
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

        # Login
        self.user = self.login()

    def test_get(self):
        """
        Test a valid GET request to the view
        """
        # Get the image
        response = self.client.get(
            reverse("wagtailimages:preview", args=(self.image.id, "fill-800x600"))
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")

    def test_preview_with_optimizer(self):
        """
        Test that preview works with optimizers

        Willow optimizers require
        """

        class DummyOptimizer(OptimizerBase):
            library_name = "dummy"
            image_format = "png"

            @classmethod
            def check_library(cls):
                return True

            @classmethod
            def process(cls, file_path: str):
                pass

        # Get the image
        with patch.object(registry, "_registered_optimizers", [DummyOptimizer]):
            response = self.client.get(
                reverse("wagtailimages:preview", args=(self.image.id, "fill-800x600"))
            )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")

    def test_get_invalid_filter_spec(self):
        """
        Test that an invalid filter spec returns a 400 response

        This is very unlikely to happen in reality. A user would have
        to create signature for the invalid filter spec which can't be
        done with Wagtails built in URL generator. We should test it
        anyway though.
        """
        # Get the image
        response = self.client.get(
            reverse("wagtailimages:preview", args=(self.image.id, "bad-filter-spec"))
        )

        # Check response
        self.assertEqual(response.status_code, 400)


class TestEditOnlyPermissions(WagtailTestUtils, TestCase):
    def setUp(self):
        # Create an image to edit
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

        # Create a user with change_image permission but not add_image
        user = self.create_user(
            username="changeonly", email="changeonly@example.com", password="password"
        )
        change_permission = Permission.objects.get(
            content_type__app_label="wagtailimages", codename="change_image"
        )
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )

        image_changers_group = Group.objects.create(name="Image changers")
        image_changers_group.permissions.add(admin_permission)
        GroupCollectionPermission.objects.create(
            group=image_changers_group,
            collection=Collection.get_first_root_node(),
            permission=change_permission,
        )

        user.groups.add(image_changers_group)
        self.login(username="changeonly", password="password")

    def test_get_index(self):
        response = self.client.get(reverse("wagtailimages:index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/images/index.html")

        # user should not get an "Add an image" button
        self.assertNotContains(response, "Add an image")

        # user should be able to see images not owned by them
        self.assertContains(response, "Test image")

    def test_search(self):
        response = self.client.get(reverse("wagtailimages:index"), {"q": "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["query_string"], "Hello")

    def test_get_add(self):
        response = self.client.get(reverse("wagtailimages:add"))
        # permission should be denied
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_get_edit(self):
        response = self.client.get(reverse("wagtailimages:edit", args=(self.image.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/images/edit.html")

    def test_get_delete(self):
        response = self.client.get(
            reverse("wagtailimages:delete", args=(self.image.id,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/images/confirm_delete.html")

    def test_get_add_multiple(self):
        response = self.client.get(reverse("wagtailimages:add_multiple"))
        # permission should be denied
        self.assertRedirects(response, reverse("wagtailadmin_home"))


class TestImageAddMultipleView(WagtailTestUtils, TestCase):
    def test_as_superuser(self):
        self.login()
        response = self.client.get(reverse("wagtailimages:add_multiple"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/multiple/add.html")

    def test_as_ordinary_editor(self):
        user = self.create_user(username="editor", password="password")

        add_permission = Permission.objects.get(
            content_type__app_label="wagtailimages", codename="add_image"
        )
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        image_adders_group = Group.objects.create(name="Image adders")
        image_adders_group.permissions.add(admin_permission)
        GroupCollectionPermission.objects.create(
            group=image_adders_group,
            collection=Collection.get_first_root_node(),
            permission=add_permission,
        )
        user.groups.add(image_adders_group)

        self.login(username="editor", password="password")

        response = self.client.get(reverse("wagtailimages:add_multiple"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailimages/multiple/add.html")
