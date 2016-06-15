from __future__ import absolute_import, unicode_literals

import warnings

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from wagtail.tests.testapp.models import EventPage, SimplePage
from wagtail.utils.deprecation import RemovedInWagtail17Warning
from wagtail.wagtailadmin import widgets
from wagtail.wagtailcore.models import Page


class TestAdminPageChooserWidget(TestCase):
    def setUp(self):
        self.root_page = Page.objects.get(id=2)

        # Add child page
        self.child_page = SimplePage(
            title="foobarbaz",
            content="hello",
        )
        self.root_page.add_child(instance=self.child_page)

    def test_not_hidden(self):
        widget = widgets.AdminPageChooser()
        self.assertFalse(widget.is_hidden)

    def test_render_html(self):
        widget = widgets.AdminPageChooser()

        html = widget.render_html('test', None, {})
        self.assertIn("<input name=\"test\" type=\"hidden\" />", html)

    def test_render_js_init(self):
        widget = widgets.AdminPageChooser()

        js_init = widget.render_js_init('test-id', 'test', None)
        self.assertEqual(js_init, "createPageChooser(\"test-id\", [\"wagtailcore.page\"], null, false);")

    def test_render_html_with_value(self):
        widget = widgets.AdminPageChooser()

        html = widget.render_html('test', self.child_page, {})
        self.assertIn("<input name=\"test\" type=\"hidden\" value=\"%d\" />" % self.child_page.id, html)

    def test_render_js_init_with_value(self):
        widget = widgets.AdminPageChooser()

        js_init = widget.render_js_init('test-id', 'test', self.child_page)
        self.assertEqual(
            js_init, "createPageChooser(\"test-id\", [\"wagtailcore.page\"], %d, false);" % self.root_page.id
        )

    # def test_render_html_init_with_content_type omitted as HTML does not
    # change when selecting a content type

    def test_render_js_init_with_target_model(self):
        widget = widgets.AdminPageChooser(target_models=[SimplePage])

        js_init = widget.render_js_init('test-id', 'test', None)
        self.assertEqual(js_init, "createPageChooser(\"test-id\", [\"tests.simplepage\"], null, false);")

    def test_render_js_init_with_multiple_target_models(self):
        target_models = [SimplePage, EventPage]
        widget = widgets.AdminPageChooser(target_models=target_models)

        js_init = widget.render_js_init('test-id', 'test', None)
        self.assertEqual(
            js_init, "createPageChooser(\"test-id\", [\"tests.simplepage\", \"tests.eventpage\"], null, false);"
        )

    def test_render_js_init_with_content_type(self):
        with warnings.catch_warnings(record=True) as ws:
            warnings.simplefilter('always')
            content_type = ContentType.objects.get_for_model(SimplePage)
            widget = widgets.AdminPageChooser(content_type=content_type)

            self.assertEqual(len(ws), 1)
            self.assertIs(ws[0].category, RemovedInWagtail17Warning)
        self.assertEqual(widget.target_models, [SimplePage])

    def test_render_js_init_with_multiple_content_types(self):
        with warnings.catch_warnings(record=True) as ws:
            warnings.simplefilter('always')
            content_types = [
                # Not using get_for_models as we need deterministic ordering
                ContentType.objects.get_for_model(SimplePage),
                ContentType.objects.get_for_model(EventPage),
            ]
            widget = widgets.AdminPageChooser(content_type=content_types)

            self.assertEqual(len(ws), 1)
            self.assertIs(ws[0].category, RemovedInWagtail17Warning)
        self.assertEqual(widget.target_models, [SimplePage, EventPage])

    def test_render_js_init_with_can_choose_root(self):
        widget = widgets.AdminPageChooser(can_choose_root=True)

        js_init = widget.render_js_init('test-id', 'test', self.child_page)
        self.assertEqual(
            js_init, "createPageChooser(\"test-id\", [\"wagtailcore.page\"], %d, true);" % self.root_page.id
        )
