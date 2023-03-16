from django.contrib.admin.utils import quote
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.admin.panels import get_edit_handler
from wagtail.coreutils import get_dummy_request
from wagtail.models import Workflow, WorkflowContentType
from wagtail.test.testapp.models import Advert, FullFeaturedSnippet, SnippetChooserModel
from wagtail.test.utils import WagtailTestUtils


class TestCustomIcon(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()
        self.object = FullFeaturedSnippet.objects.create(
            text="test snippet with custom icon"
        )
        self.revision_1 = self.object.save_revision()
        self.revision_1.publish()
        self.object.text = "test snippet with custom icon (updated)"
        self.revision_2 = self.object.save_revision()

    def get_url(self, url_name, args=()):
        return reverse(self.object.snippet_viewset.get_url_name(url_name), args=args)

    def test_get_views(self):
        pk = quote(self.object.pk)
        views = [
            ("list", []),
            ("add", []),
            ("edit", [pk]),
            ("delete", [pk]),
            ("usage", [pk]),
            ("unpublish", [pk]),
            ("workflow_history", [pk]),
            ("revisions_revert", [pk, self.revision_1.id]),
            ("revisions_compare", [pk, self.revision_1.id, self.revision_2.id]),
            ("revisions_unschedule", [pk, self.revision_2.id]),
        ]
        for view_name, args in views:
            with self.subTest(view_name=view_name):
                response = self.client.get(self.get_url(view_name, args))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["header_icon"], "cog")
                self.assertContains(response, "icon icon-cog", count=1)
                # TODO: Make the list view use the shared header template
                if view_name != "list":
                    self.assertTemplateUsed(response, "wagtailadmin/shared/header.html")

    def test_get_history(self):
        response = self.client.get(self.get_url("history", [quote(self.object.pk)]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/shared/header.html")
        # History view icon is not configurable for consistency with pages
        self.assertEqual(response.context["header_icon"], "history")
        self.assertContains(response, "icon icon-history")
        self.assertNotContains(response, "icon icon-cog")

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
        self.assertTemplateUsed(response, "wagtailadmin/shared/header.html")
        # The icon is not displayed in the header,
        # but it is displayed in the main content
        self.assertEqual(response.context["header_icon"], "list-ul")
        self.assertContains(response, "icon icon-list-ul")
        self.assertContains(response, "icon icon-cog")


class TestSnippetChooserPanelWithIcon(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()
        self.request = get_dummy_request()
        self.request.user = self.user
        self.text = "Test full-featured snippet with icon text"
        test_snippet = SnippetChooserModel.objects.create(
            advert=Advert.objects.create(text="foo"),
            full_featured=FullFeaturedSnippet.objects.create(text=self.text),
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


class TestAdminURLs(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()

    def test_default_url_namespace(self):
        snippet = Advert.objects.create(text="foo")
        viewset = snippet.snippet_viewset
        # Accessed via the viewset
        self.assertEqual(
            viewset.get_admin_url_namespace(),
            "wagtailsnippets_tests_advert",
        )
        # Accessed via the model
        self.assertEqual(
            snippet.get_admin_url_namespace(),
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
        # Accessed via the model
        self.assertEqual(snippet.get_admin_base_path(), "snippets/tests/advert")
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
        # Accessed via the model
        self.assertEqual(snippet.get_admin_url_namespace(), "some_namespace")
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
        # Accessed via the model
        self.assertEqual(snippet.get_admin_base_path(), "deep/within/the/admin")
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
