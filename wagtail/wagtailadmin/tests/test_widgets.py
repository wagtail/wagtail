from __future__ import absolute_import, unicode_literals

from django.test import TestCase
from django.test.utils import override_settings

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

    def test_render_js_init_with_can_choose_root(self):
        widget = widgets.AdminPageChooser(can_choose_root=True)

        js_init = widget.render_js_init('test-id', 'test', self.child_page)
        self.assertEqual(
            js_init, "createPageChooser(\"test-id\", [\"wagtailcore.page\"], %d, true);" % self.root_page.id
        )


class TestAdminDateInput(TestCase):

    def test_render_js_init(self):
        widget = widgets.AdminDateInput()

        js_init = widget.render_js_init('test-id', 'test', None)
        self.assertEqual(js_init, 'initDateChooser("test-id", {"dayOfWeekStart": 0});')

    def test_render_js_init_with_format_and_js_format(self):
        widget = widgets.AdminDateInput(format='%d.%m.%Y.', js_format='d.m.Y.')

        js_init = widget.render_js_init('test-id', 'test', None)
        self.assertEqual(
            js_init,
            'initDateChooser("test-id", {"dayOfWeekStart": 0, "format": "d.m.Y."});'
        )

    def test_render_js_init_with_format(self):
        widget = widgets.AdminDateInput(format='%d.%m.%Y.')

        js_init = widget.render_js_init('test-id', 'test', None)
        self.assertEqual(
            js_init,
            'initDateChooser("test-id", {"dayOfWeekStart": 0, "format": "d.m.Y."});'
        )

    @override_settings(WAGTAIL_DATE_FORMAT='%d.%m.%Y.')
    def test_render_js_init_with_format_from_settings(self):
        widget = widgets.AdminDateInput()

        js_init = widget.render_js_init('test-id', 'test', None)
        self.assertEqual(
            js_init,
            'initDateChooser("test-id", {"dayOfWeekStart": 0, "format": "d.m.Y."});'
        )


class TestAdminDateTimeInput(TestCase):

    def test_render_js_init(self):
        widget = widgets.AdminDateTimeInput()

        js_init = widget.render_js_init('test-id', 'test', None)
        self.assertEqual(js_init, 'initDateTimeChooser("test-id", {"dayOfWeekStart": 0});')

    def test_render_js_init_with_format(self):
        widget = widgets.AdminDateTimeInput(format='%d.%m.%Y. %H:%M')

        js_init = widget.render_js_init('test-id', 'test', None)
        self.assertEqual(
            js_init,
            'initDateTimeChooser("test-id", {"dayOfWeekStart": 0, "format": "d.m.Y. H:i"});'
        )

    @override_settings(WAGTAIL_DATETIME_FORMAT='%d.%m.%Y. %H:%M')
    def test_render_js_init_with_format_from_settings(self):
        widget = widgets.AdminDateTimeInput()

        js_init = widget.render_js_init('test-id', 'test', None)
        self.assertEqual(
            js_init,
            'initDateTimeChooser("test-id", {"dayOfWeekStart": 0, "format": "d.m.Y. H:i"});'
        )
