from datetime import datetime
from io import BytesIO
from unittest import mock

from django.conf import settings
from django.contrib.admin.utils import quote
from django.contrib.auth import get_permission_codename
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.template.defaultfilters import date
from django.test import SimpleTestCase, TestCase, TransactionTestCase, override_settings
from django.urls import NoReverseMatch, resolve, reverse
from django.utils.timezone import now
from openpyxl import load_workbook

from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.menu import admin_menu, settings_menu
from wagtail.admin.panels import get_edit_handler
from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.views.mixins import ExcelDateFormatter
from wagtail.blocks.field_block import FieldBlockAdapter
from wagtail.coreutils import get_dummy_request
from wagtail.documents import get_document_model
from wagtail.documents.tests.utils import get_test_document_file
from wagtail.images import get_image_model
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Locale, Workflow, WorkflowContentType
from wagtail.snippets.blocks import SnippetChooserBlock
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from wagtail.snippets.widgets import AdminSnippetChooser
from wagtail.test.testapp.models import (
    Advert,
    DraftStateModel,
    FullFeaturedSnippet,
    ModeratedModel,
    RevisableChildModel,
    RevisableModel,
    SnippetChooserModel,
    VariousOnDeleteModel,
)
from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.template_tests import AdminTemplateTestUtils
from wagtail.utils.timestamps import render_timestamp


class TestIncorrectRegistration(SimpleTestCase):
    def test_no_model_set_or_passed(self):
        # The base SnippetViewSet class has no `model` attribute set,
        # so using it directly should raise an error
        with self.assertRaises(ImproperlyConfigured) as cm:
            register_snippet(SnippetViewSet)
        message = str(cm.exception)
        self.assertIn("ModelViewSet", message)
        self.assertIn(
            "must define a `model` attribute or pass a `model` argument",
            message,
        )


class BaseSnippetViewSetTests(WagtailTestUtils, TestCase):
    model = None

    def setUp(self):
        self.user = self.login()

    def get_url(self, url_name, args=()):
        return reverse(self.model.snippet_viewset.get_url_name(url_name), args=args)


class TestCustomIcon(BaseSnippetViewSetTests):
    model = FullFeaturedSnippet

    def setUp(self):
        super().setUp()
        self.object = self.model.objects.create(text="test snippet with custom icon")
        self.revision_1 = self.object.save_revision()
        self.revision_1.publish()
        self.object.text = "test snippet with custom icon (updated)"
        self.revision_2 = self.object.save_revision()

    def test_get_views(self):
        pk = quote(self.object.pk)
        views = [
            ("list", [], "headers/slim_header.html"),
            ("add", [], "headers/slim_header.html"),
            ("edit", [pk], "headers/slim_header.html"),
            ("delete", [pk], "header.html"),
            ("usage", [pk], "headers/slim_header.html"),
            ("unpublish", [pk], "header.html"),
            ("workflow_history", [pk], "headers/slim_header.html"),
            ("revisions_revert", [pk, self.revision_1.id], "headers/slim_header.html"),
            (
                "revisions_compare",
                [pk, self.revision_1.id, self.revision_2.id],
                "headers/slim_header.html",
            ),
            ("revisions_unschedule", [pk, self.revision_2.id], "header.html"),
        ]
        for view_name, args, header in views:
            with self.subTest(view_name=view_name):
                response = self.client.get(self.get_url(view_name, args))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["header_icon"], "cog")
                self.assertContains(response, "icon icon-cog", count=1)
                self.assertTemplateUsed(response, f"wagtailadmin/shared/{header}")

    def test_get_history(self):
        response = self.client.get(self.get_url("history", [quote(self.object.pk)]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "wagtailadmin/shared/headers/slim_header.html",
        )
        # History view icon is not configurable for consistency with pages
        self.assertEqual(response.context["header_icon"], "history")
        self.assertContains(response, "icon icon-history")
        self.assertNotContains(response, "icon icon-cog")
        self.assertTemplateNotUsed(response, "wagtailadmin/shared/header.html")

    def test_get_workflow_history_detail(self):
        # Assign default workflow to the snippet model
        self.content_type = ContentType.objects.get_for_model(type(self.object))
        self.workflow = Workflow.objects.first()
        WorkflowContentType.objects.create(
            content_type=self.content_type,
            workflow=self.workflow,
        )
        self.object.text = "Edited!"
        self.object.save_revision()
        workflow_state = self.workflow.start(self.object, self.user)
        response = self.client.get(
            self.get_url(
                "workflow_history_detail", [quote(self.object.pk), workflow_state.id]
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateNotUsed(response, "wagtailadmin/shared/header.html")
        self.assertEqual(response.context["header_icon"], "cog")
        self.assertContains(response, "icon icon-clipboard-list")
        self.assertContains(response, "icon icon-cog")


class TestSnippetChooserBlockWithIcon(TestCase):
    def test_adapt(self):
        block = SnippetChooserBlock(FullFeaturedSnippet)

        block.set_name("test_snippetchooserblock")
        js_args = FieldBlockAdapter().js_args(block)

        self.assertEqual(js_args[0], "test_snippetchooserblock")
        self.assertIsInstance(js_args[1], AdminSnippetChooser)
        self.assertEqual(js_args[1].model, FullFeaturedSnippet)
        # It should use the icon defined in the FullFeaturedSnippetViewSet
        self.assertEqual(js_args[2]["icon"], "cog")

    def test_adapt_with_explicit_icon(self):
        block = SnippetChooserBlock(FullFeaturedSnippet, icon="thumbtack")

        block.set_name("test_snippetchooserblock")
        js_args = FieldBlockAdapter().js_args(block)

        self.assertEqual(js_args[2]["icon"], "thumbtack")

    def test_adapt_with_explicit_default_icon(self):
        block = SnippetChooserBlock(FullFeaturedSnippet, icon="snippet")

        block.set_name("test_snippetchooserblock")
        js_args = FieldBlockAdapter().js_args(block)

        self.assertEqual(js_args[2]["icon"], "snippet")

    def test_adapt_with_no_icon_specified_on_block_or_viewset(self):
        block = SnippetChooserBlock(Advert)

        block.set_name("test_snippetchooserblock")
        js_args = FieldBlockAdapter().js_args(block)

        self.assertEqual(js_args[2]["icon"], "snippet")

    def test_deconstruct(self):
        block = SnippetChooserBlock(FullFeaturedSnippet, required=False)
        path, args, kwargs = block.deconstruct()
        self.assertEqual(path, "wagtail.snippets.blocks.SnippetChooserBlock")
        self.assertEqual(args, (FullFeaturedSnippet,))
        # It should not add any extra kwargs for the icon
        self.assertEqual(kwargs, {"required": False})


class TestSnippetChooserPanelWithIcon(BaseSnippetViewSetTests):
    def setUp(self):
        super().setUp()
        self.request = get_dummy_request()
        self.request.user = self.user
        self.text = "Test full-featured snippet with icon text"
        self.full_featured_snippet = FullFeaturedSnippet.objects.create(text=self.text)
        test_snippet = SnippetChooserModel.objects.create(
            advert=Advert.objects.create(text="foo"),
            full_featured=self.full_featured_snippet,
        )

        self.edit_handler = get_edit_handler(SnippetChooserModel)
        self.form_class = self.edit_handler.get_form_class()
        form = self.form_class(instance=test_snippet)
        edit_handler = self.edit_handler.get_bound_panel(
            instance=test_snippet, form=form, request=self.request
        )

        self.object_chooser_panel = [
            panel
            for panel in edit_handler.children
            if getattr(panel, "field_name", None) == "full_featured"
        ][0]

    def test_render_html(self):
        field_html = self.object_chooser_panel.render_html()
        self.assertIn(self.text, field_html)
        self.assertIn("Choose full-featured snippet", field_html)
        self.assertIn("Choose another full-featured snippet", field_html)
        self.assertIn("icon icon-cog icon", field_html)

        # make sure no snippet icons remain
        self.assertNotIn("icon-snippet", field_html)

    def test_render_as_empty_field(self):
        test_snippet = SnippetChooserModel()
        form = self.form_class(instance=test_snippet)
        edit_handler = self.edit_handler.get_bound_panel(
            instance=test_snippet, form=form, request=self.request
        )

        snippet_chooser_panel = [
            panel
            for panel in edit_handler.children
            if getattr(panel, "field_name", None) == "full_featured"
        ][0]

        field_html = snippet_chooser_panel.render_html()
        self.assertIn("Choose full-featured snippet", field_html)
        self.assertIn("Choose another full-featured snippet", field_html)
        self.assertIn("icon icon-cog icon", field_html)

        # make sure no snippet icons remain
        self.assertNotIn("icon-snippet", field_html)

    def test_chooser_popup(self):
        chooser_viewset = FullFeaturedSnippet.snippet_viewset.chooser_viewset
        response = self.client.get(reverse(chooser_viewset.get_url_name("choose")))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["header_icon"], "cog")
        self.assertContains(response, "icon icon-cog", count=1)
        self.assertEqual(response.context["icon"], "cog")

        # make sure no snippet icons remain
        for key in response.context.keys():
            if "icon" in key:
                self.assertNotIn("snippet", response.context[key])

        # chooser should include the creation form
        response_json = response.json()
        soup = self.get_soup(response_json["html"])
        self.assertTrue(soup.select_one("form[data-chooser-modal-creation-form]"))

    def test_chosen(self):
        chooser_viewset = FullFeaturedSnippet.snippet_viewset.chooser_viewset
        response = self.client.get(
            reverse(
                chooser_viewset.get_url_name("chosen"),
                args=[self.full_featured_snippet.pk],
            )
        )
        response_json = response.json()
        self.assertEqual(response_json["step"], "chosen")
        self.assertEqual(
            response_json["result"]["id"], str(self.full_featured_snippet.pk)
        )
        self.assertEqual(response_json["result"]["string"], self.text)

    def test_create_from_chooser(self):
        chooser_viewset = FullFeaturedSnippet.snippet_viewset.chooser_viewset
        response = self.client.post(
            reverse(chooser_viewset.get_url_name("create")),
            {
                "text": "New snippet",
            },
        )
        response_json = response.json()
        self.assertEqual(response_json["step"], "chosen")
        self.assertEqual(response_json["result"]["string"], "New snippet")


class TestAdminURLs(BaseSnippetViewSetTests):
    def test_default_url_namespace(self):
        snippet = Advert.objects.create(text="foo")
        viewset = snippet.snippet_viewset
        # Accessed via the viewset
        self.assertEqual(
            viewset.get_admin_url_namespace(),
            "wagtailsnippets_tests_advert",
        )
        # Get specific URL name
        self.assertEqual(
            viewset.get_url_name("edit"),
            "wagtailsnippets_tests_advert:edit",
        )
        # Chooser namespace
        self.assertEqual(
            viewset.get_chooser_admin_url_namespace(),
            "wagtailsnippetchoosers_tests_advert",
        )
        # Get specific chooser URL name
        self.assertEqual(
            viewset.chooser_viewset.get_url_name("choose"),
            "wagtailsnippetchoosers_tests_advert:choose",
        )

    def test_default_admin_base_path(self):
        snippet = Advert.objects.create(text="foo")
        viewset = snippet.snippet_viewset
        pk = quote(snippet.pk)
        expected_url = f"/admin/snippets/tests/advert/edit/{pk}/"
        expected_choose_url = "/admin/snippets/choose/tests/advert/"

        # Accessed via the viewset
        self.assertEqual(viewset.get_admin_base_path(), "snippets/tests/advert")
        # Get specific URL
        self.assertEqual(reverse(viewset.get_url_name("edit"), args=[pk]), expected_url)
        # Ensure AdminURLFinder returns the correct URL
        url_finder = AdminURLFinder(self.user)
        self.assertEqual(url_finder.get_edit_url(snippet), expected_url)
        # Chooser base path
        self.assertEqual(
            viewset.get_chooser_admin_base_path(),
            "snippets/choose/tests/advert",
        )
        # Get specific chooser URL
        self.assertEqual(
            reverse(viewset.chooser_viewset.get_url_name("choose")),
            expected_choose_url,
        )

    def test_custom_url_namespace(self):
        snippet = FullFeaturedSnippet.objects.create(text="customised")
        viewset = snippet.snippet_viewset
        # Accessed via the viewset
        self.assertEqual(viewset.get_admin_url_namespace(), "some_namespace")
        # Get specific URL name
        self.assertEqual(viewset.get_url_name("edit"), "some_namespace:edit")
        # Chooser namespace
        self.assertEqual(
            viewset.get_chooser_admin_url_namespace(),
            "my_chooser_namespace",
        )
        # Get specific chooser URL name
        self.assertEqual(
            viewset.chooser_viewset.get_url_name("choose"),
            "my_chooser_namespace:choose",
        )

    def test_custom_admin_base_path(self):
        snippet = FullFeaturedSnippet.objects.create(text="customised")
        viewset = snippet.snippet_viewset
        pk = quote(snippet.pk)
        expected_url = f"/admin/deep/within/the/admin/edit/{pk}/"
        expected_choose_url = "/admin/choose/wisely/"
        # Accessed via the viewset
        self.assertEqual(viewset.get_admin_base_path(), "deep/within/the/admin")
        # Get specific URL
        self.assertEqual(reverse(viewset.get_url_name("edit"), args=[pk]), expected_url)
        # Ensure AdminURLFinder returns the correct URL
        url_finder = AdminURLFinder(self.user)
        self.assertEqual(url_finder.get_edit_url(snippet), expected_url)
        # Chooser base path
        self.assertEqual(
            viewset.get_chooser_admin_base_path(),
            "choose/wisely",
        )
        # Get specific chooser URL
        self.assertEqual(
            reverse(viewset.chooser_viewset.get_url_name("choose")),
            expected_choose_url,
        )


class TestPagination(BaseSnippetViewSetTests):
    @classmethod
    def setUpTestData(cls):
        default_locale = Locale.get_default()
        objects = [
            FullFeaturedSnippet(text=f"Snippet {i}", locale=default_locale)
            for i in range(32)
        ]
        FullFeaturedSnippet.objects.bulk_create(objects)
        objects = [Advert(text=f"Snippet {i}") for i in range(32)]
        Advert.objects.bulk_create(objects)

    def test_default_list_pagination(self):
        list_url = reverse(Advert.snippet_viewset.get_url_name("list"))
        response = self.client.get(list_url)

        # Default is 20 per page
        self.assertEqual(Advert.objects.all().count(), 32)
        self.assertContains(response, "Page 1 of 2")
        self.assertContains(response, "Next")
        self.assertContains(response, list_url + "?p=2")

    def test_custom_list_pagination(self):
        list_url = reverse(FullFeaturedSnippet.snippet_viewset.get_url_name("list"))
        response = self.client.get(list_url)

        # FullFeaturedSnippet is set to display 5 per page
        self.assertEqual(FullFeaturedSnippet.objects.all().count(), 32)
        self.assertContains(response, "Page 1 of 7")
        self.assertContains(response, "Next")
        self.assertContains(response, list_url + "?p=2")

    def test_default_chooser_pagination(self):
        chooser_viewset = Advert.snippet_viewset.chooser_viewset
        choose_url = reverse(chooser_viewset.get_url_name("choose"))
        choose_results_url = reverse(chooser_viewset.get_url_name("choose_results"))
        response = self.client.get(choose_url)

        # Default is 10 per page
        self.assertEqual(Advert.objects.all().count(), 32)
        self.assertContains(response, "Page 1 of 4")
        self.assertContains(response, "Next")
        self.assertContains(response, choose_results_url + "?p=2")

    def test_custom_chooser_pagination(self):
        chooser_viewset = FullFeaturedSnippet.snippet_viewset.chooser_viewset
        choose_url = reverse(chooser_viewset.get_url_name("choose"))
        choose_results_url = reverse(chooser_viewset.get_url_name("choose_results"))
        response = self.client.get(choose_url)

        # FullFeaturedSnippet is set to display 15 per page
        self.assertEqual(FullFeaturedSnippet.objects.all().count(), 32)
        self.assertContains(response, "Page 1 of 3")
        self.assertContains(response, "Next")
        self.assertContains(response, choose_results_url + "?p=2")


class TestFilterSetClass(BaseSnippetViewSetTests):
    model = FullFeaturedSnippet

    def get(self, params={}):
        return self.client.get(self.get_url("list"), params)

    def create_test_snippets(self):
        FullFeaturedSnippet.objects.create(
            text="Nasi goreng from Indonesia", country_code="ID", some_number=123
        )
        FullFeaturedSnippet.objects.create(
            text="Fish and chips from the UK", country_code="UK", some_number=456
        )

    def test_get_include_filters_form_media(self):
        response = self.get()
        html = response.content.decode()
        datetime_js = versioned_static("wagtailadmin/js/date-time-chooser.js")

        # The script file for the date time chooser should be included
        self.assertTagInHTML(f'<script src="{datetime_js}"></script>', html)

    def test_unfiltered_no_results(self):
        response = self.get()
        self.assertContains(response, "There are no full-featured snippets to display.")
        self.assertContains(
            response,
            '<label for="id_country_code_0"><input type="radio" name="country_code" value="" id="id_country_code_0" checked>All</label>',
            html=True,
        )

    def test_unfiltered_with_results(self):
        self.create_test_snippets()
        response = self.get()
        self.assertContains(response, "Nasi goreng from Indonesia")
        self.assertContains(response, "Fish and chips from the UK")
        self.assertNotContains(response, "There are 2 matches")
        self.assertContains(
            response,
            '<label for="id_country_code_0"><input type="radio" name="country_code" value="" id="id_country_code_0" checked>All</label>',
            html=True,
        )

    def test_empty_filter_with_results(self):
        self.create_test_snippets()
        response = self.get({"country_code": ""})
        self.assertContains(response, "Nasi goreng from Indonesia")
        self.assertContains(response, "Fish and chips from the UK")
        self.assertNotContains(response, "There are 2 matches")
        self.assertContains(
            response,
            '<label for="id_country_code_0"><input type="radio" name="country_code" value="" id="id_country_code_0" checked>All</label>',
            html=True,
        )

    def test_filtered_no_results(self):
        self.create_test_snippets()
        response = self.get({"country_code": "PH"})
        self.assertContains(response, "No full-featured snippets match your query")
        self.assertContains(
            response,
            '<label for="id_country_code_2"><input type="radio" name="country_code" value="PH" id="id_country_code_2" checked>Philippines</label>',
            html=True,
        )
        # Should render the active filters even when there are no results
        soup = self.get_soup(response.content)
        active_filters = soup.select_one(".w-active-filters")
        self.assertIsNotNone(active_filters)
        clear = active_filters.select_one(".w-pill__remove")
        self.assertIsNotNone(clear)
        url, params = clear.attrs.get("data-w-swap-src-value").split("?", 1)
        self.assertEqual(url, self.get_url("list_results"))
        self.assertNotIn("country_code=PH", params)

    def test_filtered_with_results(self):
        self.create_test_snippets()
        response = self.get({"country_code": "ID"})
        self.assertContains(response, "Nasi goreng from Indonesia")
        self.assertContains(response, "There is 1 match")
        self.assertContains(
            response,
            '<label for="id_country_code_1"><input type="radio" name="country_code" value="ID" id="id_country_code_1" checked>Indonesia</label>',
            html=True,
        )
        # Should render the active filters
        soup = self.get_soup(response.content)
        active_filters = soup.select_one(".w-active-filters")
        self.assertIsNotNone(active_filters)
        clear = active_filters.select_one(".w-pill__remove")
        self.assertIsNotNone(clear)
        url, params = clear.attrs.get("data-w-swap-src-value").split("?", 1)
        self.assertEqual(url, self.get_url("list_results"))
        self.assertNotIn("country_code=ID", params)

    def test_range_filter(self):
        self.create_test_snippets()
        response = self.get({"some_number_min": 100, "some_number_max": 200})
        self.assertContains(response, "Nasi goreng from Indonesia")
        self.assertNotContains(response, "Fish and chips from the UK")
        self.assertContains(response, "There is 1 match")
        # Should render the active filters
        soup = self.get_soup(response.content)
        active_filters = soup.select_one(".w-active-filters")
        self.assertIsNotNone(active_filters)
        pill = active_filters.select_one(".w-pill")
        self.assertIsNotNone(pill)
        self.assertEqual(
            pill.get_text(separator=" ", strip=True),
            "Number range: 100 - 200",
        )
        clear = pill.select_one(".w-pill__remove")
        self.assertIsNotNone(clear)
        url, params = clear.attrs.get("data-w-swap-src-value").split("?", 1)
        self.assertEqual(url, self.get_url("list_results"))
        self.assertNotIn("some_number_min=100", params)
        self.assertNotIn("some_number_max=200", params)


class TestFilterSetClassSearch(WagtailTestUtils, TransactionTestCase):
    fixtures = ["test_empty.json"]

    def setUp(self):
        self.login()

    def get_url(self, url_name, args=()):
        return reverse(
            FullFeaturedSnippet.snippet_viewset.get_url_name(url_name), args=args
        )

    def get(self, params={}):
        return self.client.get(self.get_url("list"), params)

    def create_test_snippets(self):
        FullFeaturedSnippet.objects.create(
            text="Nasi goreng from Indonesia", country_code="ID"
        )
        FullFeaturedSnippet.objects.create(
            text="Fish and chips from the UK", country_code="UK"
        )

    def test_filtered_searched_no_results(self):
        self.create_test_snippets()
        response = self.get({"country_code": "ID", "q": "chips"})
        self.assertContains(response, "No full-featured snippets match your query")
        self.assertContains(
            response,
            '<label for="id_country_code_1"><input type="radio" name="country_code" value="ID" id="id_country_code_1" checked>Indonesia</label>',
            html=True,
        )

    def test_filtered_searched_with_results(self):
        self.create_test_snippets()
        response = self.get({"country_code": "UK", "q": "chips"})
        self.assertContains(response, "Fish and chips from the UK")
        self.assertContains(response, "There is 1 match")
        self.assertContains(
            response,
            '<label for="id_country_code_3"><input type="radio" name="country_code" value="UK" id="id_country_code_3" checked>United Kingdom</label>',
            html=True,
        )


class TestListFilterWithList(BaseSnippetViewSetTests):
    model = DraftStateModel

    def setUp(self):
        super().setUp()
        self.date = now()
        self.date_str = self.date.isoformat()

    def get(self, params={}):
        return self.client.get(self.get_url("list"), params)

    def create_test_snippets(self):
        self.model.objects.create(text="The first created object")
        self.model.objects.create(
            text="A second one after that",
            first_published_at=self.date,
        )

    def test_get_include_filters_form_media(self):
        response = self.get()
        html = response.content.decode()
        datetime_js = versioned_static("wagtailadmin/js/date-time-chooser.js")

        # The script file for the date time chooser should be included
        self.assertTagInHTML(f'<script src="{datetime_js}"></script>', html)

    def test_unfiltered_no_results(self):
        response = self.get()
        add_url = self.get_url("add")
        self.assertContains(
            response,
            f"""<p>There are no {self.model._meta.verbose_name_plural} to display.
            Why not <a href="{add_url}">add one</a>?</p>""",
            html=True,
        )
        self.assertContains(
            response,
            '<label class="w-field__label" for="id_first_published_at" id="id_first_published_at-label">First published at</label>',
            html=True,
        )
        self.assertContains(
            response,
            '<input type="text" name="first_published_at" autocomplete="off" id="id_first_published_at">',
            html=True,
        )

    def test_unfiltered_with_results(self):
        self.create_test_snippets()
        response = self.get()
        self.assertContains(response, "The first created object")
        self.assertContains(response, "A second one after that")
        self.assertNotContains(response, "There are 2 matches")
        self.assertContains(
            response,
            '<label class="w-field__label" for="id_first_published_at" id="id_first_published_at-label">First published at</label>',
            html=True,
        )
        self.assertContains(
            response,
            '<input type="text" name="first_published_at" autocomplete="off" id="id_first_published_at">',
            html=True,
        )

    def test_empty_filter_with_results(self):
        self.create_test_snippets()
        response = self.get({"first_published_at": ""})
        self.assertContains(response, "The first created object")
        self.assertContains(response, "A second one after that")
        self.assertNotContains(response, "There are 2 matches")
        self.assertContains(
            response,
            '<label class="w-field__label" for="id_first_published_at" id="id_first_published_at-label">First published at</label>',
            html=True,
        )
        self.assertContains(
            response,
            '<input type="text" name="first_published_at" value="" autocomplete="off" id="id_first_published_at">',
            html=True,
        )

    def test_filtered_no_results(self):
        self.create_test_snippets()
        response = self.get({"first_published_at": "1970-01-01"})
        self.assertContains(
            response,
            f"No {self.model._meta.verbose_name_plural} match your query",
        )
        self.assertContains(
            response,
            '<label class="w-field__label" for="id_first_published_at" id="id_first_published_at-label">First published at</label>',
            html=True,
        )
        self.assertContains(
            response,
            '<input type="text" name="first_published_at" value="1970-01-01" autocomplete="off" id="id_first_published_at">',
            html=True,
        )

    def test_filtered_with_results(self):
        self.create_test_snippets()
        response = self.get({"first_published_at": self.date_str})
        self.assertContains(response, "A second one after that")
        self.assertContains(response, "There is 1 match")
        self.assertContains(
            response,
            '<label class="w-field__label" for="id_first_published_at" id="id_first_published_at-label">First published at</label>',
            html=True,
        )
        self.assertContains(
            response,
            f'<input type="text" name="first_published_at" value="{self.date_str}" autocomplete="off" id="id_first_published_at">',
            html=True,
        )


class TestListFilterWithDict(TestListFilterWithList):
    model = ModeratedModel

    def test_filtered_contains_with_results(self):
        self.create_test_snippets()
        response = self.get({"text__contains": "second one"})
        self.assertContains(response, "A second one after that")
        self.assertContains(response, "There is 1 match")
        self.assertContains(
            response,
            '<label class="w-field__label" for="id_text__contains" id="id_text__contains-label">Text contains</label>',
            html=True,
        )
        self.assertContains(
            response,
            '<input type="text" name="text__contains" value="second one" id="id_text__contains">',
            html=True,
        )


class TestListViewWithCustomColumns(BaseSnippetViewSetTests):
    model = FullFeaturedSnippet

    @classmethod
    def setUpTestData(cls):
        cls.model.objects.create(text="From Indonesia", country_code="ID")
        cls.model.objects.create(text="From the UK", country_code="UK")

    def get(self, params={}):
        return self.client.get(self.get_url("list"), params)

    def test_custom_columns(self):
        response = self.get()
        self.assertContains(response, "Text")
        self.assertContains(response, "Country code")
        self.assertContains(response, "Custom FOO column")
        self.assertContains(response, "Updated")
        self.assertContains(response, "Modulo two")
        self.assertContains(response, "Tristate")

        self.assertContains(response, "Foo UK")

        list_url = self.get_url("list")
        sort_country_code_url = list_url + "?ordering=country_code"

        # One from the country code column, another from the custom foo column
        self.assertContains(response, sort_country_code_url, count=2)

        soup = self.get_soup(response.content)

        headings = soup.select("#listing-results table th")

        # The bulk actions column plus 6 columns defined in FullFeaturedSnippetViewSet
        self.assertEqual(len(headings), 7)

    def test_falsy_value(self):
        # https://github.com/wagtail/wagtail/issues/10765
        response = self.get()
        self.assertContains(response, "<td>0</td>", html=True, count=1)

    def test_boolean_column(self):
        self.model.objects.create(text="Another one")
        response = self.get()
        self.assertContains(
            response,
            """
            <td>
                <svg class="icon icon-check default w-text-positive-100" aria-hidden="true">
                    <use href="#icon-check"></use>
                </svg>
                <span class="w-sr-only">True</span>
            </td>
            """,
            html=True,
            count=1,
        )
        self.assertContains(
            response,
            """
            <td>
                <svg class="icon icon-cross default w-text-text-error" aria-hidden="true">
                    <use href="#icon-cross"></use>
                </svg>
                <span class="w-sr-only">False</span>
            </td>
            """,
            html=True,
            count=1,
        )
        self.assertContains(
            response,
            """
            <td>
                <svg class="icon icon-help default" aria-hidden="true">
                    <use href="#icon-help"></use>
                </svg>
                <span class="w-sr-only">None</span>
            </td>
            """,
            html=True,
            count=1,
        )


class TestRelatedFieldListDisplay(BaseSnippetViewSetTests):
    model = SnippetChooserModel

    def setUp(self):
        super().setUp()
        url = "https://example.com/free_examples"
        self.advert = Advert.objects.create(url=url, text="Free Examples")
        self.ffs = FullFeaturedSnippet.objects.create(text="royale with cheese")

    def test_empty_foreignkey(self):
        self.no_ffs_chooser = self.model.objects.create(advert=self.advert)
        response = self.client.get(self.get_url("list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chosen snippet text")
        self.assertContains(response, "<td></td>", html=True)

    def test_single_level_relation(self):
        self.scm = self.model.objects.create(advert=self.advert, full_featured=self.ffs)
        response = self.client.get(self.get_url("list"))
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)
        headers = [
            header.get_text(strip=True)
            for header in soup.select("#listing-results table th")
        ]
        self.assertIn("Chosen snippet text", headers)
        self.assertContains(response, "<td>royale with cheese</td>", html=True)

    def test_multi_level_relation(self):
        self.scm = self.model.objects.create(advert=self.advert, full_featured=self.ffs)
        dummy_revision = self.ffs.save_revision()
        timestamp = render_timestamp(dummy_revision.created_at)
        response = self.client.get(self.get_url("list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Latest revision created at")
        self.assertContains(response, f"<td>{timestamp}</td>", html=True)


class TestListExport(BaseSnippetViewSetTests):
    model = FullFeaturedSnippet

    @classmethod
    def setUpTestData(cls):
        cls.model.objects.create(text="Pot Noodle", country_code="UK")

        cls.first_published_at = "2023-07-01T13:12:11.100"
        if settings.USE_TZ:
            cls.first_published_at = "2023-07-01T13:12:11.100Z"

        obj = cls.model.objects.create(
            text="Indomie",
            country_code="ID",
            first_published_at=cls.first_published_at,
            some_number=1,
        )
        # Refresh so the first_published_at becomes a datetime object
        obj.refresh_from_db()
        cls.first_published_at = obj.first_published_at
        cls.some_date = obj.some_date

    def test_get_not_export_shows_export_buttons(self):
        response = self.client.get(self.get_url("list"))
        self.assertContains(response, "Download CSV")
        self.assertContains(response, self.get_url("list") + "?export=csv")
        self.assertContains(response, "Download XLSX")
        self.assertContains(response, self.get_url("list") + "?export=xlsx")

    def test_csv_export(self):
        response = self.client.get(self.get_url("list"), {"export": "csv"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get("Content-Disposition"),
            'attachment; filename="all-fullfeatured-snippets.csv"',
        )

        data_lines = response.getvalue().decode().split("\n")
        self.assertEqual(
            data_lines[0],
            "Text,Country code,Custom FOO column,Some date,Some number,First published at\r",
        )
        self.assertEqual(
            data_lines[1],
            f"Indomie,ID,Foo ID,{self.some_date.isoformat()},1,{self.first_published_at.isoformat(sep=' ')}\r",
        )
        self.assertEqual(
            data_lines[2],
            f"Pot Noodle,UK,Foo UK,{self.some_date.isoformat()},0,\r",
        )

    def test_xlsx_export(self):
        response = self.client.get(self.get_url("list"), {"export": "xlsx"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get("Content-Disposition"),
            'attachment; filename="all-fullfeatured-snippets.xlsx"',
        )

        workbook_data = response.getvalue()
        worksheet = load_workbook(filename=BytesIO(workbook_data)).active
        cell_array = [[cell.value for cell in row] for row in worksheet.rows]
        self.assertEqual(
            cell_array[0],
            [
                "Text",
                "Country code",
                "Custom FOO column",
                "Some date",
                "Some number",
                "First published at",
            ],
        )
        self.assertEqual(
            cell_array[1],
            [
                "Indomie",
                "ID",
                "Foo ID",
                self.some_date,
                1,
                datetime(2023, 7, 1, 13, 12, 11, 100000),
            ],
        )
        self.assertEqual(
            cell_array[2],
            ["Pot Noodle", "UK", "Foo UK", self.some_date, 0, None],
        )
        self.assertEqual(len(cell_array), 3)

        self.assertEqual(worksheet["F2"].number_format, ExcelDateFormatter().get())


class TestCustomTemplates(BaseSnippetViewSetTests):
    model = FullFeaturedSnippet

    @classmethod
    def setUpTestData(cls):
        cls.object = cls.model.objects.create(text="Some snippet")

    def test_template_lookups(self):
        pk = quote(self.object.pk)
        cases = {
            "with app label and model name": (
                "add",
                [],
                [
                    "wagtailsnippets/snippets/tests/fullfeaturedsnippet/create.html",
                ],
            ),
            "with app label": (
                "edit",
                [pk],
                [
                    "wagtailsnippets/snippets/tests/edit.html",
                ],
            ),
            "without app label and model name": (
                "delete",
                [pk],
                [
                    "wagtailsnippets/snippets/delete.html",
                ],
            ),
            "override a view that uses a generic template": (
                "unpublish",
                [pk],
                [
                    "wagtailsnippets/snippets/tests/fullfeaturedsnippet/unpublish.html",
                ],
            ),
            "override with index_template_name and index results template with namespaced template": (
                "list",
                [],
                [
                    "tests/fullfeaturedsnippet_index.html",
                    "wagtailsnippets/snippets/tests/fullfeaturedsnippet/index_results.html",
                ],
            ),
            "override index results template with namespaced template": (
                # This is technically the same as the first case, but this ensures that
                # the index results view can be overridden separately from the index view
                "list_results",
                [],
                [
                    "wagtailsnippets/snippets/tests/fullfeaturedsnippet/index_results.html"
                ],
            ),
            "override with get_history_template": (
                "history",
                [pk],
                [
                    "tests/snippet_history.html",
                ],
            ),
        }
        for case, (view_name, args, template_names) in cases.items():
            with self.subTest(case=case):
                response = self.client.get(self.get_url(view_name, args=args))
                for template_name in template_names:
                    self.assertTemplateUsed(response, template_name)
                self.assertContains(response, "<p>An added paragraph</p>", html=True)


class TestCustomQuerySet(BaseSnippetViewSetTests):
    model = FullFeaturedSnippet

    @classmethod
    def setUpTestData(cls):
        default_locale = Locale.get_default()
        objects = [
            cls.model(text="FooSnippet", country_code="ID", locale=default_locale),
            cls.model(text="BarSnippet", country_code="UK", locale=default_locale),
            cls.model(text="[HIDDEN]Snippet", country_code="ID", locale=default_locale),
        ]
        cls.model.objects.bulk_create(objects)

    def test_index_view(self):
        response = self.client.get(self.get_url("list"), {"country_code": "ID"})
        self.assertContains(response, "FooSnippet")
        self.assertNotContains(response, "BarSnippet")
        self.assertNotContains(response, "[HIDDEN]Snippet")


class TestCustomOrdering(BaseSnippetViewSetTests):
    model = FullFeaturedSnippet

    @classmethod
    def setUpTestData(cls):
        default_locale = Locale.get_default()
        objects = [
            cls.model(text="CCCCCCCCCC", locale=default_locale),
            cls.model(text="AAAAAAAAAA", locale=default_locale),
            cls.model(text="DDDDDDDDDD", locale=default_locale),
            cls.model(text="BBBBBBBBBB", locale=default_locale),
        ]
        cls.model.objects.bulk_create(objects)

    def test_index_view_order(self):
        response = self.client.get(self.get_url("list"))
        # Should sort by text in descending order as specified in SnippetViewSet.ordering
        # (not the default ordering of the model)
        self.assertFalse(self.model._meta.ordering)
        self.assertEqual(
            [obj.text for obj in response.context["page_obj"]],
            [
                "AAAAAAAAAA",
                "BBBBBBBBBB",
                "CCCCCCCCCC",
                "DDDDDDDDDD",
            ],
        )


class TestDjangoORMSearchBackend(BaseSnippetViewSetTests):
    model = DraftStateModel

    @classmethod
    def setUpTestData(cls):
        cls.first = cls.model.objects.create(
            text="Wagtail is a Django-based CMS",
        )
        cls.second = cls.model.objects.create(
            text="Django is a Python-based web framework",
        )
        cls.third = cls.model.objects.create(
            text="Python is a programming-bas, uh, language",
        )

    def get(self, params={}, url_name="list"):
        return self.client.get(self.get_url(url_name), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/index.html")

        # All objects should be in items
        self.assertCountEqual(
            list(response.context["page_obj"].object_list),
            [self.first, self.second, self.third],
        )

        # The search box should not raise an error
        self.assertNotContains(response, "This field is required.")

    def test_empty_q(self):
        response = self.get({"q": ""})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/index.html")

        # All objects should be in items
        self.assertCountEqual(
            list(response.context["page_obj"].object_list),
            [self.first, self.second, self.third],
        )

        # The search box should not raise an error
        self.assertNotContains(response, "This field is required.")

    def test_is_searchable(self):
        self.assertIsInstance(self.get().context["search_form"], SearchForm)

    def test_search_index_view(self):
        response = self.get({"q": "Django"})

        # Only objects with "Django" should be in items
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(
            list(response.context["page_obj"].object_list),
            [self.first, self.second],
        )

    def test_search_index_results_view(self):
        response = self.get({"q": "Python"}, url_name="list_results")

        # Only objects with "Python" should be in items
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(
            list(response.context["object_list"]),
            [self.second, self.third],
        )


class TestMenuItemRegistration(BaseSnippetViewSetTests):
    def setUp(self):
        super().setUp()
        self.request = get_dummy_request()
        self.request.user = self.user

    def test_add_to_admin_menu(self):
        self.model = FullFeaturedSnippet
        menu_items = admin_menu.render_component(self.request)
        item = menu_items[-1]
        self.assertEqual(item.name, "fullfeatured")
        self.assertEqual(item.label, "Full-Featured MenuItem")
        self.assertEqual(item.icon_name, "cog")
        self.assertEqual(item.url, self.get_url("list"))

    def test_add_to_settings_menu(self):
        self.model = DraftStateModel
        menu_items = settings_menu.render_component(self.request)
        item = menu_items[0]
        self.assertEqual(item.name, "publishables")
        self.assertEqual(item.label, "Publishables")
        self.assertEqual(item.icon_name, "snippet")
        self.assertEqual(item.url, self.get_url("list"))

    def test_group_registration(self):
        menu_items = admin_menu.render_component(self.request)
        revisables = [item for item in menu_items if item.name == "revisables"]
        self.assertEqual(len(revisables), 1)

        group_item = revisables[0]
        self.assertEqual(group_item.label, "Revisables")
        self.assertEqual(group_item.icon_name, "tasks")
        self.assertEqual(len(group_item.menu_items), 2)

        self.model = RevisableModel
        revisable_item = group_item.menu_items[0]
        self.assertEqual(revisable_item.name, "revisable-models")
        self.assertEqual(revisable_item.label, "Revisable models")
        self.assertEqual(revisable_item.icon_name, "snippet")
        self.assertEqual(revisable_item.url, self.get_url("list"))

        self.model = RevisableChildModel
        revisable_child_item = group_item.menu_items[1]
        self.assertEqual(revisable_child_item.name, "revisable-child-models")
        self.assertEqual(revisable_child_item.label, "Revisable child models")
        self.assertEqual(revisable_child_item.icon_name, "snippet")
        self.assertEqual(revisable_child_item.url, self.get_url("list"))

    def test_limited_permissions(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        menu_items = admin_menu.render_component(self.request)

        # The menu items should not be present
        item = [
            item
            for item in menu_items
            if item.name in {"fullfeatured", "revisables", "publishables"}
        ]
        self.assertEqual(len(item), 0)

    def test_basic_permissions(self):
        self.model = DraftStateModel
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        for action in ("add", "change", "delete"):
            with self.subTest(action=action):
                permission = Permission.objects.get(
                    content_type__app_label=self.model._meta.app_label,
                    codename=get_permission_codename(action, self.model._meta),
                )
                self.user.user_permissions.add(permission)

                menu_items = settings_menu.render_component(self.request)
                item = menu_items[0]
                self.assertEqual(item.name, "publishables")
                self.assertEqual(item.label, "Publishables")
                self.assertEqual(item.icon_name, "snippet")
                self.assertEqual(item.url, self.get_url("list"))

                self.user.user_permissions.remove(permission)

    def test_snippets_menu_item_hidden_when_all_snippets_have_menu_item(self):
        menu_items = admin_menu.menu_items_for_request(self.request)
        snippets = [item for item in menu_items if item.name == "snippets"]
        self.assertEqual(len(snippets), 1)
        item = snippets[0]
        self.assertEqual(item.name, "snippets")
        self.assertEqual(item.label, "Snippets")
        self.assertEqual(item.icon_name, "snippet")
        self.assertEqual(item.url, reverse("wagtailsnippets:index"))

        # Clear cached property
        del item._snippets_in_index_view

        with mock.patch(
            "wagtail.snippets.views.snippets.SnippetViewSet.get_menu_item_is_registered"
        ) as mock_registered:
            mock_registered.return_value = True
            menu_items = admin_menu.render_component(self.request)
            snippets = [item for item in menu_items if item.name == "snippets"]
            self.assertEqual(len(snippets), 0)

    def test_snippets_menu_item_hidden_when_user_lacks_permissions_for_snippets(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        menu_items = admin_menu.render_component(self.request)
        snippets = [item for item in menu_items if item.name == "snippets"]
        self.assertEqual(len(snippets), 0)


class TestCustomFormClass(BaseSnippetViewSetTests):
    model = DraftStateModel

    def test_get_form_class(self):
        add_view = self.client.get(self.get_url("add"))
        self.assertNotContains(add_view, '<input type="text" name="text"')
        self.assertContains(add_view, '<textarea name="text"')

        obj = self.model.objects.create(text="Hello World")

        # The get_form_class has been overridden to replace the widget for the
        # text field with a TextInput, but only for the edit view
        edit_view = self.client.get(self.get_url("edit", args=(quote(obj.pk),)))
        self.assertContains(edit_view, '<input type="text" name="text"')
        self.assertNotContains(edit_view, '<textarea name="text"')


class TestInspectViewConfiguration(BaseSnippetViewSetTests):
    model = FullFeaturedSnippet

    def setUp(self):
        super().setUp()
        self.viewset = self.model.snippet_viewset
        self.object = self.model.objects.create(text="Perkedel", country_code="ID")

    def test_enabled(self):
        self.model = FullFeaturedSnippet
        url = self.get_url("inspect", args=(quote(self.object.pk),))
        response = self.client.get(url)
        self.assertContains(
            response,
            "<dt>Text</dt> <dd>Perkedel</dd>",
            html=True,
        )
        self.assertContains(
            response,
            "<dt>Country code</dt> <dd>Indonesia</dd>",
            html=True,
        )
        self.assertContains(
            response,
            f"<dt>Some date</dt> <dd>{date(self.object.some_date)}</dd>",
            html=True,
        )
        self.assertNotContains(
            response,
            "<dt>Some attribute</dt> <dd>some value</dd>",
            html=True,
        )
        self.assertContains(
            response,
            self.get_url("edit", args=(quote(self.object.pk),)),
        )
        self.assertContains(
            response,
            self.get_url("delete", args=(quote(self.object.pk),)),
        )

    def test_disabled(self):
        self.model = Advert
        object = self.model.objects.create(text="ad")
        with self.assertRaises(NoReverseMatch):
            self.get_url("inspect", args=(quote(object.pk),))

    def test_only_add_permission(self):
        self.model = FullFeaturedSnippet

        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            ),
            Permission.objects.get(
                content_type__app_label=self.model._meta.app_label,
                codename=get_permission_codename("add", self.model._meta),
            ),
        )
        self.user.save()

        url = self.get_url("inspect", args=(quote(self.object.pk),))
        response = self.client.get(url)

        self.assertContains(
            response,
            "<dt>Text</dt> <dd>Perkedel</dd>",
            html=True,
        )
        self.assertContains(
            response,
            "<dt>Country code</dt> <dd>Indonesia</dd>",
            html=True,
        )
        self.assertContains(
            response,
            f"<dt>Some date</dt> <dd>{date(self.object.some_date)}</dd>",
            html=True,
        )
        self.assertNotContains(
            response,
            self.get_url("edit", args=(quote(self.object.pk),)),
        )
        self.assertNotContains(
            response,
            self.get_url("delete", args=(quote(self.object.pk),)),
        )

    def test_custom_fields(self):
        self.model = FullFeaturedSnippet
        url = self.get_url("inspect", args=(quote(self.object.pk),))
        view_func = resolve(url).func

        adverts = [Advert.objects.create(text=f"advertisement {i}") for i in range(3)]
        queryset = Advert.objects.filter(pk=adverts[0].pk)

        mock_manager = mock.patch.object(
            self.model, "adverts", Advert.objects, create=True
        )

        mock_queryset = mock.patch.object(
            self.model, "some_queryset", queryset, create=True
        )

        mock_fields = mock.patch.dict(
            view_func.view_initkwargs,
            {
                "fields": [
                    "country_code",  # Field with choices (thus get_FOO_display method)
                    "some_date",  # DateField
                    "some_attribute",  # Model attribute
                    "adverts",  # Manager
                    "some_queryset",  # QuerySet
                ]
            },
        )

        # We need to mock the view's init kwargs instead of the viewset's
        # attributes, because the viewset's attributes are only used when the
        # view is instantiated, and the view is instantiated once at startup.
        with mock_manager, mock_queryset, mock_fields:
            response = self.client.get(url)

        self.assertNotContains(
            response,
            "<dt>Text</dt> <dd>Perkedel</dd>",
            html=True,
        )
        self.assertContains(
            response,
            "<dt>Country code</dt> <dd>Indonesia</dd>",
            html=True,
        )
        self.assertContains(
            response,
            f"<dt>Some date</dt> <dd>{date(self.object.some_date)}</dd>",
            html=True,
        )
        self.assertContains(
            response,
            "<dt>Some attribute</dt> <dd>some value</dd>",
            html=True,
        )
        self.assertContains(
            response,
            """
            <dt>Adverts</dt>
            <dd>advertisement 0, advertisement 1, advertisement 2</dd>
            """,
            html=True,
        )
        self.assertContains(
            response,
            "<dt>Some queryset</dt> <dd>advertisement 0</dd>",
            html=True,
        )

    def test_exclude_fields(self):
        self.model = FullFeaturedSnippet
        url = self.get_url("inspect", args=(quote(self.object.pk),))
        view_func = resolve(url).func

        # We need to mock the view's init kwargs instead of the viewset's
        # attributes, because the viewset's attributes are only used when the
        # view is instantiated, and the view is instantiated once at startup.
        with mock.patch.dict(
            view_func.view_initkwargs,
            {"fields_exclude": ["some_date"]},
        ):
            response = self.client.get(url)

        self.assertContains(
            response,
            "<dt>Text</dt> <dd>Perkedel</dd>",
            html=True,
        )
        self.assertContains(
            response,
            "<dt>Country code</dt> <dd>Indonesia</dd>",
            html=True,
        )
        self.assertNotContains(
            response,
            f"<dt>Some date</dt> <dd>{date(self.object.some_date)}</dd>",
            html=True,
        )
        self.assertNotContains(
            response,
            "<dt>Some attribute</dt> <dd>some value</dd>",
            html=True,
        )

    def test_image_and_document_fields(self):
        self.model = VariousOnDeleteModel
        image = get_image_model().objects.create(
            title="Test image",
            file=get_test_image_file(),
        )
        document = get_document_model().objects.create(
            title="Test document", file=get_test_document_file()
        )
        object = self.model.objects.create(
            protected_image=image, protected_document=document
        )
        response = self.client.get(self.get_url("inspect", args=(quote(object.pk),)))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f"<dt>Protected image</dt> <dd>{image.get_rendition('max-400x400').img_tag()}</dd>",
            html=True,
        )
        self.assertContains(response, "<dt>Protected document</dt>", html=True)
        self.assertContains(response, f'<a href="{document.url}">')
        self.assertContains(response, "Test document")
        self.assertContains(response, "TXT")
        self.assertContains(response, f"{document.file.size}\xa0bytes")

    def test_image_and_document_fields_none_values(self):
        self.model = VariousOnDeleteModel
        object = self.model.objects.create()
        response = self.client.get(self.get_url("inspect", args=(quote(object.pk),)))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "<dt>Protected image</dt> <dd>None</dd>",
            html=True,
        )
        self.assertContains(
            response,
            "<dt>Protected document</dt> <dd>None</dd>",
            html=True,
        )


class TestBreadcrumbs(AdminTemplateTestUtils, BaseSnippetViewSetTests):
    model = FullFeaturedSnippet

    @classmethod
    def setUpTestData(cls):
        cls.object = cls.model.objects.create(text="Hello World")

    def test_index_view(self):
        response = self.client.get(self.get_url("list"))
        items = [{"url": "", "label": "Full-featured snippets"}]
        self.assertBreadcrumbsItemsRendered(items, response.content)

    def test_add_view(self):
        response = self.client.get(self.get_url("add"))
        items = [
            {
                "url": self.get_url("list"),
                "label": "Full-featured snippets",
            },
            {"url": "", "label": "New: Full-featured snippet"},
        ]
        self.assertBreadcrumbsItemsRendered(items, response.content)

    def test_edit_view(self):
        response = self.client.get(self.get_url("edit", args=(self.object.pk,)))
        items = [
            {
                "url": self.get_url("list"),
                "label": "Full-featured snippets",
            },
            {"url": "", "label": str(self.object)},
        ]
        self.assertBreadcrumbsItemsRendered(items, response.content)

    def test_delete_view(self):
        response = self.client.get(self.get_url("delete", args=(self.object.pk,)))
        self.assertBreadcrumbsNotRendered(response.content)

    def test_history_view(self):
        response = self.client.get(self.get_url("history", args=(self.object.pk,)))
        items = [
            {
                "url": self.get_url("list"),
                "label": "Full-featured snippets",
            },
            {
                "url": self.get_url("edit", args=(self.object.pk,)),
                "label": str(self.object),
            },
            {"url": "", "label": "History", "sublabel": str(self.object)},
        ]
        self.assertBreadcrumbsItemsRendered(items, response.content)

    def test_usage_view(self):
        response = self.client.get(self.get_url("usage", args=(self.object.pk,)))
        items = [
            {
                "url": self.get_url("list"),
                "label": "Full-featured snippets",
            },
            {
                "url": self.get_url("edit", args=(self.object.pk,)),
                "label": str(self.object),
            },
            {"url": "", "label": "Usage", "sublabel": str(self.object)},
        ]
        self.assertBreadcrumbsItemsRendered(items, response.content)

    def test_inspect_view(self):
        response = self.client.get(self.get_url("inspect", args=(self.object.pk,)))
        items = [
            {
                "url": self.get_url("list"),
                "label": "Full-featured snippets",
            },
            {
                "url": self.get_url("edit", args=(self.object.pk,)),
                "label": str(self.object),
            },
            {"url": "", "label": "Inspect", "sublabel": str(self.object)},
        ]
        self.assertBreadcrumbsItemsRendered(items, response.content)

    def test_workflow_history_view(self):
        response = self.client.get(
            self.get_url("workflow_history", args=(self.object.pk,))
        )
        items = [
            {
                "url": self.get_url("list"),
                "label": "Full-featured snippets",
            },
            {
                "url": self.get_url("edit", args=(self.object.pk,)),
                "label": str(self.object),
            },
            {"url": "", "label": "Workflow history", "sublabel": str(self.object)},
        ]
        self.assertBreadcrumbsItemsRendered(items, response.content)


class TestCustomMethods(BaseSnippetViewSetTests):
    model = FullFeaturedSnippet

    def test_index_view_get_add_url_is_respected(self):
        response = self.client.get(self.get_url("list"))
        add_url = self.get_url("add") + "?customised=param"
        soup = self.get_soup(response.content)
        links = soup.find_all("a", attrs={"href": add_url})
        self.assertEqual(len(links), 2)

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_index_view_get_add_url_is_respected_with_i18n(self):
        Locale.objects.create(language_code="fr")
        response = self.client.get(self.get_url("list") + "?locale=fr")
        add_url = self.get_url("add") + "?locale=fr&customised=param"
        soup = self.get_soup(response.content)
        links = soup.find_all("a", attrs={"href": add_url})
        self.assertEqual(len(links), 1)

    def test_index_results_view_get_add_url_teleports_to_header(self):
        response = self.client.get(self.get_url("list_results"))
        add_url = self.get_url("add") + "?customised=param"
        soup = self.get_soup(response.content)
        template = soup.find(
            "template",
            {
                "data-controller": "w-teleport",
                "data-w-teleport-target-value": "#w-slim-header-buttons",
            },
        )
        self.assertIsNotNone(template)
        links = template.find_all("a", attrs={"href": add_url})
        self.assertEqual(len(links), 1)

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_index_results_view_get_add_url_teleports_to_header_with_i18n(self):
        Locale.objects.create(language_code="fr")
        response = self.client.get(self.get_url("list_results") + "?locale=fr")
        add_url = self.get_url("add") + "?locale=fr&customised=param"
        soup = self.get_soup(response.content)
        template = soup.find(
            "template",
            {
                "data-controller": "w-teleport",
                "data-w-teleport-target-value": "#w-slim-header-buttons",
            },
        )
        self.assertIsNotNone(template)
        links = template.find_all("a", attrs={"href": add_url})
        self.assertEqual(len(links), 1)


class TestCustomPermissionPolicy(BaseSnippetViewSetTests):
    model = FullFeaturedSnippet

    @classmethod
    def setUpTestData(cls):
        cls.object = cls.model.objects.create(text="Hello World")

    def test_get_edit_view_not_allowed(self):
        response = self.client.get(self.get_url("edit", args=(quote(self.object.pk),)))
        self.assertEqual(response.status_code, 200)

        # The custom permission policy disallows any user with [FORBIDDEN]
        # in their name, even if they are a superuser
        self.user.first_name = "[FORBIDDEN]"
        self.user.last_name = "Joe"
        self.user.save()
        self.assertTrue(self.user.is_superuser)
        self.assertEqual(self.user.get_full_name(), "[FORBIDDEN] Joe")
        response = self.client.get(self.get_url("edit", args=(quote(self.object.pk),)))
        self.assertRedirects(response, reverse("wagtailadmin_home"))


class TestSnippetIndexViewBreadcrumbs(SimpleTestCase):
    def test_snippet_without_menu_item_breadcrumbs(self):
        self.assertEqual(
            Advert.snippet_viewset.breadcrumbs_items,
            [
                {"url": reverse("wagtailadmin_home"), "label": "Home"},
                {"url": reverse("wagtailsnippets:index"), "label": "Snippets"},
            ],
        )

    def check_snippet_with_menu_item_breadcrumbs(self, expected):
        self.assertEqual(DraftStateModel.snippet_viewset.breadcrumbs_items, expected)

    def test_snippet_with_menu_item_breadcrumbs(self):
        self.check_snippet_with_menu_item_breadcrumbs(
            [
                {"url": reverse("wagtailadmin_home"), "label": "Home"},
            ],
        )

    @override_settings(WAGTAILSNIPPETS_MENU_SHOW_ALL=True)
    def test_snippet_with_menu_item_breadcrumbs_show_all(self):
        self.check_snippet_with_menu_item_breadcrumbs(
            [
                {"url": reverse("wagtailadmin_home"), "label": "Home"},
                {"url": reverse("wagtailsnippets:index"), "label": "Snippets"},
            ]
        )
