from __future__ import absolute_import, unicode_literals

from django.test import TestCase

from wagtail.tests.testapp.models import EventPage, SimplePage
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
        self.assertInHTML("""<input name="test" type="hidden" />""", html)

    def test_render_js_init(self):
        widget = widgets.AdminPageChooser()

        js_init = widget.render_js_init('test-id', 'test', None)
        self.assertEqual(js_init, "createPageChooser(\"test-id\", [\"wagtailcore.page\"], null, false);")

    def test_render_html_with_value(self):
        widget = widgets.AdminPageChooser()

        html = widget.render_html('test', self.child_page, {})
        self.assertInHTML("""<input name="test" type="hidden" value="%d" />""" % self.child_page.id, html)

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

    def test_render_js_init_with_can_choose_root(self):
        widget = widgets.AdminPageChooser(can_choose_root=True)

        js_init = widget.render_js_init('test-id', 'test', self.child_page)
        self.assertEqual(
            js_init, "createPageChooser(\"test-id\", [\"wagtailcore.page\"], %d, true);" % self.root_page.id
        )
