import json

from django import forms
from django.test import TestCase
from django.test.utils import override_settings

from wagtail.admin import widgets
from wagtail.admin.forms.tags import TagField
from wagtail.core.models import Page
from wagtail.tests.testapp.forms import AdminStarDateInput
from wagtail.tests.testapp.models import EventPage, RestaurantTag, SimplePage


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
        # SimplePage has a custom get_admin_display_title method which should be reflected here
        self.assertInHTML("foobarbaz (simple page)", html)

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

        self.assertInHTML('<input type="text" name="test" autocomplete="off" id="test-id" />', html)

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

    def test_media_inheritance(self):
        """
        Widgets inheriting from AdminDateInput should have their media definitions merged
        with AdminDateInput's
        """
        widget = AdminStarDateInput()
        media_html = str(widget.media)
        self.assertIn('wagtailadmin/js/date-time-chooser.js', media_html)
        self.assertIn('vendor/star_date.js', media_html)


class TestAdminDateTimeInput(TestCase):

    def test_render_js_init(self):
        widget = widgets.AdminDateTimeInput()

        html = widget.render('test', None, attrs={'id': 'test-id'})

        self.assertInHTML('<input type="text" name="test" autocomplete="off" id="test-id" />', html)

        # we should see the JS initialiser code:
        # initDateTimeChooser("test-id", {"dayOfWeekStart": 0, "format": "Y-m-d H:i"});
        # except that we can't predict the order of the config options
        self.assertIn('initDateTimeChooser("test\\u002Did", {', html)
        self.assertIn('"dayOfWeekStart": 0', html)
        self.assertIn('"format": "Y-m-d H:i"', html)
        self.assertIn('"formatTime": "H:i"', html)

    def test_render_js_init_with_format(self):
        widget = widgets.AdminDateTimeInput(format='%d.%m.%Y. %H:%M', time_format='%H:%M %p')

        html = widget.render('test', None, attrs={'id': 'test-id'})
        self.assertIn(
            '"format": "d.m.Y. H:i"',
            html,
        )
        self.assertIn(
            '"formatTime": "H:i A"',
            html,
        )

    @override_settings(WAGTAIL_DATETIME_FORMAT='%d.%m.%Y. %H:%M', WAGTAIL_TIME_FORMAT='%H:%M %p')
    def test_render_js_init_with_format_from_settings(self):
        widget = widgets.AdminDateTimeInput()

        html = widget.render('test', None, attrs={'id': 'test-id'})
        self.assertIn(
            '"format": "d.m.Y. H:i"',
            html,
        )
        self.assertIn(
            '"formatTime": "H:i A"',
            html,
        )


class TestAdminTagWidget(TestCase):

    def get_js_init_params(self, html):
        """Returns a list of the params passed in to initTagField from the supplied HTML"""
        # Eg. ["test_id", "/admin/tag-autocomplete/", {'allowSpaces': True}]
        start = 'initTagField('
        end = ');'
        items_after_init = html.split(start)[1]
        if items_after_init:
            params_raw = items_after_init.split(end)[0]
            if params_raw:
                # stuff parameter string into an array so that we can unpack it as JSON
                return json.loads('[%s]' % params_raw)
        return []

    def test_render_js_init_basic(self):
        """Checks that the 'initTagField' is correctly added to the inline script for tag widgets"""
        widget = widgets.AdminTagWidget()

        html = widget.render('tags', None, attrs={'id': 'alpha'})
        params = self.get_js_init_params(html)

        self.assertEqual(
            params,
            ['alpha', '/admin/tag-autocomplete/', {'allowSpaces': True, 'tagLimit': None, 'autocompleteOnly': False}]
        )

    @override_settings(TAG_SPACES_ALLOWED=False)
    def test_render_js_init_no_spaces_allowed(self):
        """Checks that the 'initTagField' includes the correct value based on TAG_SPACES_ALLOWED in settings"""
        widget = widgets.AdminTagWidget()

        html = widget.render('tags', None, attrs={'id': 'alpha'})
        params = self.get_js_init_params(html)

        self.assertEqual(
            params,
            ['alpha', '/admin/tag-autocomplete/', {'allowSpaces': False, 'tagLimit': None, 'autocompleteOnly': False}]
        )

    @override_settings(TAG_LIMIT=5)
    def test_render_js_init_with_tag_limit(self):
        """Checks that the 'initTagField' includes the correct value based on TAG_LIMIT in settings"""
        widget = widgets.AdminTagWidget()

        html = widget.render('tags', None, attrs={'id': 'alpha'})
        params = self.get_js_init_params(html)

        self.assertEqual(
            params,
            ['alpha', '/admin/tag-autocomplete/', {'allowSpaces': True, 'tagLimit': 5, 'autocompleteOnly': False}]
        )

    def test_render_js_init_with_tag_model(self):
        """
        Checks that 'initTagField' is passed the correct autocomplete URL for the custom model,
        and sets autocompleteOnly according to that model's free_tagging attribute
        """
        widget = widgets.AdminTagWidget(tag_model=RestaurantTag)

        html = widget.render('tags', None, attrs={'id': 'alpha'})
        params = self.get_js_init_params(html)

        self.assertEqual(
            params,
            ['alpha', '/admin/tag-autocomplete/tests/restauranttag/', {'allowSpaces': True, 'tagLimit': None, 'autocompleteOnly': True}]
        )

    def test_render_with_free_tagging_false(self):
        """Checks that free_tagging=False is passed to the inline script"""
        widget = widgets.AdminTagWidget(free_tagging=False)

        html = widget.render('tags', None, attrs={'id': 'alpha'})
        params = self.get_js_init_params(html)

        self.assertEqual(
            params,
            ['alpha', '/admin/tag-autocomplete/', {'allowSpaces': True, 'tagLimit': None, 'autocompleteOnly': True}]
        )

    def test_render_with_free_tagging_true(self):
        """free_tagging=True on the widget can also override the tag model setting free_tagging=False"""
        widget = widgets.AdminTagWidget(tag_model=RestaurantTag, free_tagging=True)

        html = widget.render('tags', None, attrs={'id': 'alpha'})
        params = self.get_js_init_params(html)

        self.assertEqual(
            params,
            ['alpha', '/admin/tag-autocomplete/tests/restauranttag/', {'allowSpaces': True, 'tagLimit': None, 'autocompleteOnly': False}]
        )


class TestTagField(TestCase):
    def setUp(self):
        RestaurantTag.objects.create(name='Italian', slug='italian')
        RestaurantTag.objects.create(name='Indian', slug='indian')

    def test_tag_whitelisting(self):

        class RestaurantTagForm(forms.Form):
            # RestaurantTag sets free_tagging=False at the model level
            tags = TagField(tag_model=RestaurantTag)

        form = RestaurantTagForm({'tags': "Italian, delicious"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['tags'], ["Italian"])

    def test_override_free_tagging(self):

        class RestaurantTagForm(forms.Form):
            tags = TagField(tag_model=RestaurantTag, free_tagging=True)

        form = RestaurantTagForm({'tags': "Italian, delicious"})
        self.assertTrue(form.is_valid())
        self.assertEqual(set(form.cleaned_data['tags']), {"Italian", "delicious"})


class TestFilteredSelect(TestCase):
    def test_render(self):
        widget = widgets.FilteredSelect(choices=[
            (None, '----'),
            ('FR', 'France', ['EU']),
            ('JP', 'Japan', ['AS']),
            ('RU', 'Russia', ['AS', 'EU']),
        ], filter_field='id_continent')

        html = widget.render('country', 'JP')
        self.assertHTMLEqual(html, '''
            <select name="country" data-widget="filtered-select" data-filter-field="id_continent">
                <option value="">----</option>
                <option value="FR" data-filter-value="EU">France</option>
                <option value="JP" selected data-filter-value="AS">Japan</option>
                <option value="RU" data-filter-value="AS,EU">Russia</option>
            </select>
        ''')

    def test_optgroups(self):
        widget = widgets.FilteredSelect(choices=[
            (None, '----'),
            ('Big countries', [
                ('FR', 'France', ['EU']),
                ('JP', 'Japan', ['AS']),
                ('RU', 'Russia', ['AS', 'EU']),
                ('MOON', 'The moon'),
            ]),
            ('Small countries', [
                ('AZ', 'Azerbaijan', ['AS']),
                ('LI', 'Liechtenstein', ['EU']),
            ]),
            ('SK', 'Slovakia', ['EU'])
        ], filter_field='id_continent')

        html = widget.render('country', 'JP')
        self.assertHTMLEqual(html, '''
            <select name="country" data-widget="filtered-select" data-filter-field="id_continent">
                <option value="">----</option>
                <optgroup label="Big countries">
                    <option value="FR" data-filter-value="EU">France</option>
                    <option value="JP" selected data-filter-value="AS">Japan</option>
                    <option value="RU" data-filter-value="AS,EU">Russia</option>
                    <option value="MOON">The moon</option>
                </optgroup>
                <optgroup label="Small countries">
                    <option value="AZ" data-filter-value="AS">Azerbaijan</option>
                    <option value="LI" data-filter-value="EU">Liechtenstein</option>
                </optgroup>
                <option value="SK" data-filter-value="EU">Slovakia</option>
            </select>
        ''')
