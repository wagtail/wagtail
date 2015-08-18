from django.test import TestCase
from django.contrib.contenttypes.models import ContentType

from wagtail.wagtailadmin import widgets

from wagtail.wagtailcore.models import Page
from wagtail.tests.testapp.models import SimplePage


class TestAdminPageChooserWidget(TestCase):
    def setUp(self):
        self.root_page = Page.objects.get(id=2)

        # Add child page
        self.child_page = SimplePage(
            title="foobarbaz",
            slug="foobarbaz",
        )
        self.root_page.add_child(instance=self.child_page)

    def test_render_html(self):
        widget = widgets.AdminPageChooser()

        html = widget.render_html('test', None, {})
        self.assertIn("<input name=\"test\" type=\"hidden\" />", html)

    def test_render_js_init(self):
        widget = widgets.AdminPageChooser()

        js_init = widget.render_js_init('test-id', 'test', None)
        self.assertEqual(js_init, "createPageChooser(\"test-id\", \"wagtailcore.page\", null);")

    def test_render_html_with_value(self):
        widget = widgets.AdminPageChooser()

        html = widget.render_html('test', self.child_page, {})
        self.assertIn("<input name=\"test\" type=\"hidden\" value=\"%d\" />" % self.child_page.id, html)

    def test_render_js_init_with_value(self):
        widget = widgets.AdminPageChooser()

        js_init = widget.render_js_init('test-id', 'test', self.child_page)
        self.assertEqual(js_init, "createPageChooser(\"test-id\", \"wagtailcore.page\", %d);" % self.root_page.id)

    # def test_render_html_init_with_content_type omitted as HTML does not
    # change when selecting a content type

    def test_render_js_init_with_content_type(self):
        content_type = ContentType.objects.get_for_model(SimplePage)
        widget = widgets.AdminPageChooser(content_type=content_type)

        js_init = widget.render_js_init('test-id', 'test', None)
        self.assertEqual(js_init, "createPageChooser(\"test-id\", \"tests.simplepage\", null);")
