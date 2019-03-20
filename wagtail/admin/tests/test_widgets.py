from django.test import TestCase
from django.test.utils import override_settings

from wagtail.admin import widgets
from wagtail.core.models import Page
from wagtail.tests.testapp.models import EventPage, SimplePage


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
        self.assertIn(">Choose a page<", html)

    def test_render_js_init(self):
        widget = widgets.AdminPageChooser()

        js_init = widget.render_js_init('test-id', 'test', None)
        self.assertEqual(js_init, "createPageChooser(\"test-id\", [\"wagtailcore.page\"], null, false, null);")

    def test_render_js_init_with_user_perm(self):
        widget = widgets.AdminPageChooser(user_perms='copy_to')

        js_init = widget.render_js_init('test-id', 'test', None)
        self.assertEqual(js_init, "createPageChooser(\"test-id\", [\"wagtailcore.page\"], null, false, \"copy_to\");")

    def test_render_html_with_value(self):
        widget = widgets.AdminPageChooser()

        html = widget.render_html('test', self.child_page, {})
        self.assertInHTML("""<input name="test" type="hidden" value="%d" />""" % self.child_page.id, html)

    def test_render_js_init_with_value(self):
        widget = widgets.AdminPageChooser()

        js_init = widget.render_js_init('test-id', 'test', self.child_page)
        self.assertEqual(
            js_init, "createPageChooser(\"test-id\", [\"wagtailcore.page\"], %d, false, null);" % self.root_page.id
        )

    # def test_render_html_init_with_content_type omitted as HTML does not
    # change when selecting a content type

    def test_render_js_init_with_target_model(self):
        widget = widgets.AdminPageChooser(target_models=[SimplePage])

        js_init = widget.render_js_init('test-id', 'test', None)
        self.assertEqual(js_init, "createPageChooser(\"test-id\", [\"tests.simplepage\"], null, false, null);")

        html = widget.render_html('test', self.child_page, {})
        self.assertIn(">Choose a page (Simple Page)<", html)

    def test_render_js_init_with_multiple_target_models(self):
        target_models = [SimplePage, EventPage]
        widget = widgets.AdminPageChooser(target_models=target_models)

        js_init = widget.render_js_init('test-id', 'test', None)
        self.assertEqual(
            js_init, "createPageChooser(\"test-id\", [\"tests.simplepage\", \"tests.eventpage\"], null, false, null);"
        )

        html = widget.render_html('test', self.child_page, {})
        self.assertIn(">Choose a page<", html)

    def test_render_js_init_with_can_choose_root(self):
        widget = widgets.AdminPageChooser(can_choose_root=True)

        js_init = widget.render_js_init('test-id', 'test', self.child_page)
        self.assertEqual(
            js_init, "createPageChooser(\"test-id\", [\"wagtailcore.page\"], %d, true, null);" % self.root_page.id
        )


class TestAdminDateInput(TestCase):

    def test_render_js_init(self):
        widget = widgets.AdminDateInput()

        html = widget.render('test', None, attrs={'id': 'test-id'})

        self.assertInHTML('<input type="text" name="test" autocomplete="new-date" id="test-id" />', html)

        # we should see the JS initialiser code:
        # initDateChooser("test-id", {"dayOfWeekStart": 0, "format": "Y-m-d"});
        # except that we can't predict the order of the config options
        self.assertIn('initDateChooser("test\\u002Did", {', html)
        self.assertIn('"dayOfWeekStart": 0', html)
        self.assertIn('"format": "Y-m-d"', html)

    def test_render_js_init_with_format(self):
        widget = widgets.AdminDateInput(format='%d.%m.%Y.')

        html = widget.render('test', None, attrs={'id': 'test-id'})
        self.assertIn(
            '"format": "d.m.Y."',
            html,
        )

    @override_settings(WAGTAIL_DATE_FORMAT='%d.%m.%Y.')
    def test_render_js_init_with_format_from_settings(self):
        widget = widgets.AdminDateInput()

        html = widget.render('test', None, attrs={'id': 'test-id'})
        self.assertIn(
            '"format": "d.m.Y."',
            html,
        )


class TestAdminDateTimeInput(TestCase):

    def test_render_js_init(self):
        widget = widgets.AdminDateTimeInput()

        html = widget.render('test', None, attrs={'id': 'test-id'})

        self.assertInHTML('<input type="text" name="test" autocomplete="new-date-time" id="test-id" />', html)

        # we should see the JS initialiser code:
        # initDateTimeChooser("test-id", {"dayOfWeekStart": 0, "format": "Y-m-d H:i"});
        # except that we can't predict the order of the config options
        self.assertIn('initDateTimeChooser("test\\u002Did", {', html)
        self.assertIn('"dayOfWeekStart": 0', html)
        self.assertIn('"format": "Y-m-d H:i"', html)

    def test_render_js_init_with_format(self):
        widget = widgets.AdminDateTimeInput(format='%d.%m.%Y. %H:%M')

        html = widget.render('test', None, attrs={'id': 'test-id'})
        self.assertIn(
            '"format": "d.m.Y. H:i"',
            html,
        )

    @override_settings(WAGTAIL_DATETIME_FORMAT='%d.%m.%Y. %H:%M')
    def test_render_js_init_with_format_from_settings(self):
        widget = widgets.AdminDateTimeInput()

        html = widget.render('test', None, attrs={'id': 'test-id'})
        self.assertIn(
            '"format": "d.m.Y. H:i"',
            html,
        )


class TestAdminTagWidget(TestCase):

    def get_js_init_params(self, html):
        """Returns a list of the params passed in to initTagField from the supplied HTML"""
        # Eg. ["'test\\u002Did'", "'/admin/tag\\u002Dautocomplete/'", 'true', 'null']
        start = 'initTagField('
        end = ');'
        items_after_init = html.split(start)[1]
        if items_after_init:
            params_raw = items_after_init.split(end)[0]
            if params_raw:
                return [part.strip() for part in params_raw.split(',')]
        return []


    def test_render_js_init_basic(self):
        """Chekcs that the 'initTagField' is correctly added to the inline script for tag widgets"""
        widget = widgets.AdminTagWidget()

        html = widget.render('tags', None, attrs={'id': 'alpha'})
        params = self.get_js_init_params(html)

        self.assertEqual(len(params), 4)
        self.assertEqual(params[0], "'alpha'")  # id
        self.assertEqual(params[1], "'/admin/tag\\u002Dautocomplete/'")  # autocomplete url
        self.assertEqual(params[2], 'true')  # tag_spaces_allowed
        self.assertEqual(params[3], 'null')  # tag_limit


    @override_settings(TAG_SPACES_ALLOWED=False)
    def test_render_js_init_no_spaces_allowed(self):
        """Chekcs that the 'initTagField' includes the correct value based on TAG_SPACES_ALLOWED in settings"""
        widget = widgets.AdminTagWidget()

        html = widget.render('tags', None, attrs={'id': 'alpha'})
        params = self.get_js_init_params(html)

        self.assertEqual(len(params), 4)
        self.assertEqual(params[2], 'false')  # tag_spaces_allowed
        self.assertEqual(params[3], 'null')  # tag_limit


    @override_settings(TAG_LIMIT=5)
    def test_render_js_init_with_tag_limit(self):
        """Chekcs that the 'initTagField' includes the correct value based on TAG_LIMIT in settings"""
        widget = widgets.AdminTagWidget()

        html = widget.render('tags', None, attrs={'id': 'alpha'})
        params = self.get_js_init_params(html)

        self.assertEqual(len(params), 4)
        self.assertEqual(params[2], 'true')  # tag_spaces_allowed
        self.assertEqual(params[3], '5')  # tag_limit
