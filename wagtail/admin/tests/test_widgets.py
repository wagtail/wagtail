import json
import re
from html import unescape

from bs4 import BeautifulSoup
from django import forms
from django.test import TestCase
from django.test.utils import override_settings
from django.utils.html import escape

from wagtail.admin import widgets
from wagtail.admin.forms.tags import TagField
from wagtail.models import Locale, Page
from wagtail.test.testapp.forms import AdminStarDateInput
from wagtail.test.testapp.models import EventPage, RestaurantTag, SimplePage
from wagtail.utils.deprecation import RemovedInWagtail80Warning


class TestAdminPageChooserWidget(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root_page = Page.objects.get(id=2)

        # Add child page
        cls.child_page = SimplePage(
            title="foobarbaz",
            content="hello",
        )
        cls.root_page.add_child(instance=cls.child_page)

    def test_not_hidden(self):
        widget = widgets.AdminPageChooser()
        self.assertFalse(widget.is_hidden)

    def test_adapt(self):
        widget = widgets.AdminPageChooser()

        js_args = widgets.PageChooserAdapter().js_args(widget)
        self.assertInHTML(
            """<input id="__ID__" name="__NAME__" type="hidden" />""", js_args[0]
        )
        self.assertIn("Choose a page", js_args[0])
        self.assertEqual(js_args[1], "__ID__")
        self.assertEqual(
            js_args[2],
            {
                "canChooseRoot": False,
                "modelNames": ["wagtailcore.page"],
                "userPerms": None,
                "modalUrl": "/admin/choose-page/",
            },
        )

    def test_adapt_with_target_model(self):
        widget = widgets.AdminPageChooser(target_models=[SimplePage, EventPage])

        js_args = widgets.PageChooserAdapter().js_args(widget)
        self.assertEqual(
            js_args[2]["modelNames"], ["tests.simplepage", "tests.eventpage"]
        )

    def test_adapt_with_can_choose_root(self):
        widget = widgets.AdminPageChooser(can_choose_root=True)

        js_args = widgets.PageChooserAdapter().js_args(widget)
        self.assertTrue(js_args[2]["canChooseRoot"])

    def test_render_html(self):
        # render_html is mostly an internal API, but we do want to support calling it with None as
        # a value, to render a blank field without the JS initialiser (so that we can call that
        # separately in our own context and hold on to the return value)
        widget = widgets.AdminPageChooser()

        html = widget.render_html("test", None, {})
        self.assertInHTML("""<input name="test" type="hidden" />""", html)
        self.assertIn("Choose a page", html)

    def test_render_js_init(self):
        widget = widgets.AdminPageChooser()

        html = widget.render("test", None, {"id": "test-id"})
        self.assertIn(
            'new PageChooser("test-id", {"modelNames": ["wagtailcore.page"], "canChooseRoot": false, "userPerms": null, "modalUrl": "/admin/choose-page/"});',
            html,
        )

    def test_render_js_init_with_user_perm(self):
        widget = widgets.AdminPageChooser(user_perms="copy_to")

        html = widget.render("test", None, {"id": "test-id"})
        self.assertIn(
            'new PageChooser("test-id", {"modelNames": ["wagtailcore.page"], "canChooseRoot": false, "userPerms": "copy_to", "modalUrl": "/admin/choose-page/"});',
            html,
        )

    def test_render_with_value(self):
        widget = widgets.AdminPageChooser()

        html = widget.render("test", self.child_page, {"id": "test-id"})
        self.assertInHTML(
            """<input id="test-id" name="test" type="hidden" value="%d" />"""
            % self.child_page.id,
            html,
        )
        # SimplePage has a custom get_admin_display_title method which should be reflected here
        self.assertInHTML("foobarbaz (simple page)", html)

        self.assertIn(
            'new PageChooser("test-id", {"modelNames": ["wagtailcore.page"], "canChooseRoot": false, "userPerms": null, "modalUrl": "/admin/choose-page/", "parentId": %d});'
            % self.root_page.id,
            html,
        )

    def test_render_with_target_model(self):
        widget = widgets.AdminPageChooser(target_models=[SimplePage])

        html = widget.render("test", None, {"id": "test-id"})
        self.assertIn(
            'new PageChooser("test-id", {"modelNames": ["tests.simplepage"], "canChooseRoot": false, "userPerms": null, "modalUrl": "/admin/choose-page/"});',
            html,
        )

        html = widget.render("test", self.child_page, {"id": "test-id"})
        self.assertIn("Choose a page (Simple page)", html)

    def test_render_with_target_model_as_single_instance(self):
        widget = widgets.AdminPageChooser(target_models=SimplePage)

        html = widget.render("test", None, {"id": "test-id"})
        self.assertIn(
            'new PageChooser("test-id", {"modelNames": ["tests.simplepage"], "canChooseRoot": false, "userPerms": null, "modalUrl": "/admin/choose-page/"});',
            html,
        )

        html = widget.render("test", self.child_page, {"id": "test-id"})
        self.assertIn("Choose a page (Simple page)", html)

    def test_render_with_target_model_as_single_string(self):
        widget = widgets.AdminPageChooser(target_models="tests.SimplePage")

        html = widget.render("test", None, {"id": "test-id"})
        self.assertIn(
            'new PageChooser("test-id", {"modelNames": ["tests.simplepage"], "canChooseRoot": false, "userPerms": null, "modalUrl": "/admin/choose-page/"});',
            html,
        )

        html = widget.render("test", self.child_page, {"id": "test-id"})
        self.assertIn("Choose a page (Simple page)", html)

    def test_render_with_multiple_target_models(self):
        target_models = [SimplePage, "tests.eventpage"]
        widget = widgets.AdminPageChooser(target_models=target_models)

        html = widget.render("test", None, {"id": "test-id"})
        self.assertIn(
            'new PageChooser("test-id", {"modelNames": ["tests.simplepage", "tests.eventpage"], "canChooseRoot": false, "userPerms": null, "modalUrl": "/admin/choose-page/"});',
            html,
        )

        html = widget.render("test", self.child_page, {"id": "test-id"})
        self.assertIn("Choose a page", html)

    def test_render_js_init_with_can_choose_root(self):
        widget = widgets.AdminPageChooser(can_choose_root=True)

        html = widget.render("test", self.child_page, {"id": "test-id"})
        self.assertIn(
            'new PageChooser("test-id", {"modelNames": ["wagtailcore.page"], "canChooseRoot": true, "userPerms": null, "modalUrl": "/admin/choose-page/", "parentId": %d});'
            % self.root_page.id,
            html,
        )

    def test_get_instance(self):
        widget = widgets.AdminPageChooser(target_models=[SimplePage])
        self.assertIsNone(widget.get_instance(None))
        self.assertIsNone(widget.get_instance(self.root_page.id))
        self.assertIsNone(widget.get_instance(self.child_page.id + 100))
        self.assertEqual(widget.get_instance(self.child_page), self.child_page)
        self.assertEqual(widget.get_instance(self.child_page.id), self.child_page)


class TestAdminDateInput(TestCase):
    def test_adapt(self):
        widget = widgets.AdminDateInput()

        js_args = widgets.AdminDateInputAdapter().js_args(widget)

        self.assertEqual(js_args[0], {"dayOfWeekStart": 0, "format": "Y-m-d"})

    def test_adapt_with_custom_format(self):
        widget = widgets.AdminDateInput(format="%d.%m.%Y")

        js_args = widgets.AdminDateInputAdapter().js_args(widget)

        self.assertEqual(js_args[0], {"dayOfWeekStart": 0, "format": "d.m.Y"})

    def test_render_js_init(self):
        widget = widgets.AdminDateInput()

        html = widget.render("test", None, attrs={"id": "test-id"})

        self.assertInHTML(
            '<input type="text" name="test" autocomplete="off" id="test-id" />', html
        )

        # we should see the JS initialiser code:
        # initDateChooser("test-id", {"dayOfWeekStart": 0, "format": "Y-m-d"});
        # except that we can't predict the order of the config options
        self.assertIn('initDateChooser("test\\u002Did", {', html)
        self.assertIn('"dayOfWeekStart": 0', html)
        self.assertIn('"format": "Y-m-d"', html)

    def test_render_js_init_with_format(self):
        widget = widgets.AdminDateInput(format="%d.%m.%Y.")

        html = widget.render("test", None, attrs={"id": "test-id"})
        self.assertIn(
            '"format": "d.m.Y."',
            html,
        )

    @override_settings(WAGTAIL_DATE_FORMAT="%d.%m.%Y.")
    def test_render_js_init_with_format_from_settings(self):
        widget = widgets.AdminDateInput()

        html = widget.render("test", None, attrs={"id": "test-id"})
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
        self.assertIn("wagtailadmin/js/date-time-chooser.js", media_html)
        self.assertIn("vendor/star_date.js", media_html)


class TestAdminTimeInput(TestCase):
    def test_adapt(self):
        widget = widgets.AdminTimeInput()

        js_args = widgets.AdminTimeInputAdapter().js_args(widget)

        self.assertEqual(js_args[0], {"format": "H:i", "formatTime": "H:i"})

    def test_adapt_with_custom_format(self):
        widget = widgets.AdminTimeInput(format="%H:%M:%S")

        js_args = widgets.AdminTimeInputAdapter().js_args(widget)

        self.assertEqual(js_args[0], {"format": "H:i:s", "formatTime": "H:i:s"})

    def test_render_js_init(self):
        widget = widgets.AdminTimeInput()

        html = widget.render("test", None, attrs={"id": "test-id"})

        self.assertInHTML(
            '<input type="text" name="test" autocomplete="off" id="test-id" />', html
        )

        # we should see the JS initialiser code:
        # initDateChooser("test-id", {"dayOfWeekStart": 0, "format": "Y-m-d"});
        # except that we can't predict the order of the config options
        self.assertIn('initTimeChooser("test\\u002Did", {', html)
        self.assertIn('"format": "H:i"', html)

    def test_render_js_init_with_format(self):
        widget = widgets.AdminTimeInput(format="%H:%M:%S")

        html = widget.render("test", None, attrs={"id": "test-id"})
        self.assertIn(
            '"format": "H:i:s"',
            html,
        )

    @override_settings(WAGTAIL_TIME_FORMAT="%H:%M:%S")
    def test_render_js_init_with_format_from_settings(self):
        widget = widgets.AdminTimeInput()

        html = widget.render("test", None, attrs={"id": "test-id"})
        self.assertIn(
            '"format": "H:i:s"',
            html,
        )


class TestAdminDateTimeInput(TestCase):
    def test_adapt(self):
        widget = widgets.AdminDateTimeInput()

        js_args = widgets.AdminDateTimeInputAdapter().js_args(widget)

        self.assertEqual(
            js_args[0],
            {
                "dayOfWeekStart": 0,
                "format": "Y-m-d H:i",
                "formatTime": "H:i",
                "parentID": "body",
            },
        )

    def test_adapt_with_custom_format(self):
        widget = widgets.AdminDateTimeInput(
            format="%d.%m.%Y. %H:%M", time_format="%H:%M %p"
        )

        js_args = widgets.AdminDateTimeInputAdapter().js_args(widget)

        self.assertEqual(
            js_args[0],
            {
                "dayOfWeekStart": 0,
                "format": "d.m.Y. H:i",
                "formatTime": "H:i A",
                "parentID": "body",
            },
        )

    def test_adapt_with_custom_parent_selector(self):
        widget = widgets.AdminDateTimeInput(
            js_overlay_parent_selector="#test-parent-id"
        )

        js_args = widgets.AdminDateTimeInputAdapter().js_args(widget)

        self.assertEqual(
            js_args[0],
            {
                "dayOfWeekStart": 0,
                "format": "Y-m-d H:i",
                "formatTime": "H:i",
                "parentID": "#test-parent-id",
            },
        )

    def test_render_js_init(self):
        widget = widgets.AdminDateTimeInput()

        html = widget.render("test", None, attrs={"id": "test-id"})

        self.assertInHTML(
            '<input type="text" name="test" autocomplete="off" id="test-id" />', html
        )

        # we should see the JS initialiser code:
        # initDateTimeChooser("test-id", {"dayOfWeekStart": 0, "format": "Y-m-d H:i"});
        # except that we can't predict the order of the config options
        self.assertIn('initDateTimeChooser("test\\u002Did", {', html)
        self.assertIn('"dayOfWeekStart": 0', html)
        self.assertIn('"format": "Y-m-d H:i"', html)
        self.assertIn('"formatTime": "H:i"', html)
        self.assertIn('"parentID": "body"', html)

    def test_render_js_init_with_format(self):
        widget = widgets.AdminDateTimeInput(
            format="%d.%m.%Y. %H:%M", time_format="%H:%M %p"
        )

        html = widget.render("test", None, attrs={"id": "test-id"})
        self.assertIn(
            '"format": "d.m.Y. H:i"',
            html,
        )
        self.assertIn(
            '"formatTime": "H:i A"',
            html,
        )

    @override_settings(
        WAGTAIL_DATETIME_FORMAT="%d.%m.%Y. %H:%M", WAGTAIL_TIME_FORMAT="%H:%M %p"
    )
    def test_render_js_init_with_format_from_settings(self):
        widget = widgets.AdminDateTimeInput()

        html = widget.render("test", None, attrs={"id": "test-id"})
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
        """
        Returns a list of the key parts of data needed for the w-tag controlled element
        An id for the element with the 'w-tag' controller, the autocomplete url & tag options

        example element <input data-controller="w-tag" id="test_id" data-w-tag-url-value="/admin/tag-autocomplete/" data-w-tag-options-value="{...encoded json opts}" />
        example result - ["test_id", "/admin/tag-autocomplete/", {'allowSpaces': True}]
        """

        element_id = re.search(
            r'data-controller=\"w-tag\" id=\"((?:\\.|[^"\\])*)\"\s+', html
        ).group(1)
        autocomplete_url = re.search(
            r'data-w-tag-url-value=\"((?:\\.|[^"\\])*)"', html
        ).group(1)
        options = re.search(
            r'data-w-tag-options-value=\"((?:\\.|[^"\\])*)"', html
        ).group(1)

        return [
            element_id,
            autocomplete_url,
            json.loads(unescape(options)),
        ]

    def test_render_js_init_basic(self):
        """Checks that the 'w-tag' controller attributes are correctly added to the tag widgets"""
        widget = widgets.AdminTagWidget()

        html = widget.render("tags", None, attrs={"id": "alpha"})
        params = self.get_js_init_params(html)

        self.assertEqual(
            params,
            [
                "alpha",
                "/admin/tag-autocomplete/",
                {"allowSpaces": True, "tagLimit": None, "autocompleteOnly": False},
            ],
        )

    @override_settings(WAGTAIL_TAG_SPACES_ALLOWED=False)
    def test_render_js_init_no_spaces_allowed(self):
        """Checks that the 'w-tag' controller attributes are correctly added to the tag widgets based  on WAGTAIL_TAG_SPACES_ALLOWED in settings"""
        widget = widgets.AdminTagWidget()

        html = widget.render("tags", None, attrs={"id": "alpha"})
        params = self.get_js_init_params(html)

        self.assertEqual(
            params,
            [
                "alpha",
                "/admin/tag-autocomplete/",
                {"allowSpaces": False, "tagLimit": None, "autocompleteOnly": False},
            ],
        )

    @override_settings(WAGTAIL_TAG_LIMIT=5)
    def test_render_js_init_with_tag_limit(self):
        """Checks that the 'w-tag' controller attributes are correctly added to the tag widget using options based on WAGTAIL_TAG_LIMIT in settings"""

        widget = widgets.AdminTagWidget()

        html = widget.render("tags", None, attrs={"id": "alpha"})
        params = self.get_js_init_params(html)

        self.assertEqual(
            params,
            [
                "alpha",
                "/admin/tag-autocomplete/",
                {"allowSpaces": True, "tagLimit": 5, "autocompleteOnly": False},
            ],
        )

    def test_render_js_init_with_tag_model(self):
        """
        Checks that the 'w-tag' controller attributes are correctly added to the tag widget using
        the correct autocomplete URL for the custom model,
        and sets autocompleteOnly according to that model's free_tagging attribute
        """
        widget = widgets.AdminTagWidget(tag_model=RestaurantTag)

        html = widget.render("tags", None, attrs={"id": "alpha"})
        params = self.get_js_init_params(html)

        self.assertEqual(
            params,
            [
                "alpha",
                "/admin/tag-autocomplete/tests/restauranttag/",
                {"allowSpaces": True, "tagLimit": None, "autocompleteOnly": True},
            ],
        )

    def test_render_with_free_tagging_false(self):
        """Checks that free_tagging=False is passed to the inline script"""
        widget = widgets.AdminTagWidget(free_tagging=False)

        html = widget.render("tags", None, attrs={"id": "alpha"})
        params = self.get_js_init_params(html)

        self.assertEqual(
            params,
            [
                "alpha",
                "/admin/tag-autocomplete/",
                {"allowSpaces": True, "tagLimit": None, "autocompleteOnly": True},
            ],
        )

    def test_render_with_free_tagging_true(self):
        """free_tagging=True on the widget can also override the tag model setting free_tagging=False"""
        widget = widgets.AdminTagWidget(tag_model=RestaurantTag, free_tagging=True)

        html = widget.render("tags", None, attrs={"id": "alpha"})
        params = self.get_js_init_params(html)

        self.assertEqual(
            params,
            [
                "alpha",
                "/admin/tag-autocomplete/tests/restauranttag/",
                {"allowSpaces": True, "tagLimit": None, "autocompleteOnly": False},
            ],
        )

    @override_settings(WAGTAIL_TAG_SPACES_ALLOWED=True)
    def test_tags_help_text_spaces_allowed(self):
        """Checks that the tags help text html element content is correct when WAGTAIL_TAG_SPACES_ALLOWED is True"""
        widget = widgets.AdminTagWidget()
        help_text = widget.get_context(None, None, {})["widget"]["help_text"]

        html = widget.render("tags", None, {})

        self.assertEqual(
            help_text,
            'Multi-word tags with spaces will automatically be enclosed in double quotes (").',
        )

        self.assertIn(
            """<p class="help">%s</p>""" % escape(help_text),
            html,
        )

    @override_settings(WAGTAIL_TAG_SPACES_ALLOWED=False)
    def test_tags_help_text_no_spaces_allowed(self):
        """Checks that the tags help text html element content is correct when WAGTAIL_TAG_SPACES_ALLOWED is False"""
        widget = widgets.AdminTagWidget()
        help_text = widget.get_context(None, None, {})["widget"]["help_text"]

        html = widget.render("tags", None, {})

        self.assertEqual(
            help_text, "Tags can only consist of a single word, no spaces allowed."
        )

        self.assertIn(
            """<p class="help">%s</p>""" % escape(help_text),
            html,
        )

    @override_settings(TAG_LIMIT=3)
    def test_legacy_tag_limit_setting(self):
        widget = widgets.AdminTagWidget()
        with self.assertWarnsMessage(
            RemovedInWagtail80Warning,
            "The setting 'TAG_LIMIT' is deprecated. "
            "Please use 'WAGTAIL_TAG_LIMIT' instead.",
        ):
            html = widget.render("tags", None, attrs={"id": "alpha"})
        params = self.get_js_init_params(html)
        self.assertEqual(
            params,
            [
                "alpha",
                "/admin/tag-autocomplete/",
                {"allowSpaces": True, "tagLimit": 3, "autocompleteOnly": False},
            ],
        )

    @override_settings(TAG_SPACES_ALLOWED=False)
    def test_legacy_tag_spaces_allowed_setting(self):
        widget = widgets.AdminTagWidget()
        with self.assertWarnsMessage(
            RemovedInWagtail80Warning,
            "The setting 'TAG_SPACES_ALLOWED' is deprecated. "
            "Please use 'WAGTAIL_TAG_SPACES_ALLOWED' instead.",
        ):
            html = widget.render("tags", None, attrs={"id": "alpha"})
        params = self.get_js_init_params(html)
        self.assertEqual(
            params,
            [
                "alpha",
                "/admin/tag-autocomplete/",
                {"allowSpaces": False, "tagLimit": None, "autocompleteOnly": False},
            ],
        )


class TestTagField(TestCase):
    def setUp(self):
        RestaurantTag.objects.create(name="Italian", slug="italian")
        RestaurantTag.objects.create(name="Indian", slug="indian")

    def test_tag_whitelisting(self):
        class RestaurantTagForm(forms.Form):
            # RestaurantTag sets free_tagging=False at the model level
            tags = TagField(tag_model=RestaurantTag)

        form = RestaurantTagForm({"tags": "Italian, delicious"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["tags"], ["Italian"])

    def test_override_free_tagging(self):
        class RestaurantTagForm(forms.Form):
            tags = TagField(tag_model=RestaurantTag, free_tagging=True)

        form = RestaurantTagForm({"tags": "Italian, delicious"})
        self.assertTrue(form.is_valid())
        self.assertEqual(set(form.cleaned_data["tags"]), {"Italian", "delicious"})

    def test_tag_over_one_hundred_characters(self):
        class RestaurantTagForm(forms.Form):
            tags = TagField(tag_model=RestaurantTag)

        tag_name = ""
        for _ in range(101):
            tag_name += "a"
        form = RestaurantTagForm({"tags": tag_name})
        self.assertFalse(form.is_valid())


class TestFilteredSelect(TestCase):
    def test_render(self):
        widget = widgets.FilteredSelect(
            choices=[
                (None, "----"),
                ("FR", "France", ["EU"]),
                ("JP", "Japan", ["AS"]),
                ("RU", "Russia", ["AS", "EU"]),
            ],
            filter_field="id_continent",
        )

        html = widget.render("country", "JP")
        self.assertHTMLEqual(
            html,
            """
            <select name="country" data-widget="filtered-select" data-filter-field="id_continent">
                <option value="">----</option>
                <option value="FR" data-filter-value="EU">France</option>
                <option value="JP" selected data-filter-value="AS">Japan</option>
                <option value="RU" data-filter-value="AS,EU">Russia</option>
            </select>
        """,
        )

    def test_optgroups(self):
        widget = widgets.FilteredSelect(
            choices=[
                (None, "----"),
                (
                    "Big countries",
                    [
                        ("FR", "France", ["EU"]),
                        ("JP", "Japan", ["AS"]),
                        ("RU", "Russia", ["AS", "EU"]),
                        ("MOON", "The moon"),
                    ],
                ),
                (
                    "Small countries",
                    [
                        ("AZ", "Azerbaijan", ["AS"]),
                        ("LI", "Liechtenstein", ["EU"]),
                    ],
                ),
                ("SK", "Slovakia", ["EU"]),
            ],
            filter_field="id_continent",
        )

        html = widget.render("country", "JP")
        self.assertHTMLEqual(
            html,
            """
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
        """,
        )


class TestSlugInput(TestCase):
    def getAttrs(self, *args, **kwargs):
        return (
            BeautifulSoup(
                widgets.SlugInput(*args, **kwargs).render("slug", None),
                "html.parser",
            )
            .find("input")
            .attrs
        )

    def test_has_data_attr(self):
        widget = widgets.SlugInput()

        html = widget.render("test", None, attrs={"id": "test-id"})

        self.assertInHTML(
            '<input type="text" name="test" data-controller="w-slug" data-action="blur-&gt;w-slug#slugify w-sync:check-&gt;w-slug#compare w-sync:apply-&gt;w-slug#urlify:prevent" data-w-slug-allow-unicode-value data-w-slug-compare-as-param="urlify" data-w-slug-trim-value="true" id="test-id">',
            html,
        )

    @override_settings(WAGTAIL_ALLOW_UNICODE_SLUGS=False)
    def test_render_data_attrs_from_settings(self):
        widget = widgets.SlugInput()

        html = widget.render("test", None, attrs={"id": "test-id"})

        self.assertNotIn("data-w-slug-allow-unicode-value", html)

    def test_with_locale_and_formatters_not_provided(self):
        self.assertEqual(
            self.getAttrs(),
            {
                "data-action": "blur->w-slug#slugify w-sync:check->w-slug#compare w-sync:apply->w-slug#urlify:prevent",
                "data-controller": "w-slug",
                "data-w-slug-allow-unicode-value": "",
                "data-w-slug-compare-as-param": "urlify",
                # "data-w-slug-formatters-value":... # not included at all
                # "data-w-slug-locale-value":... # not included at all
                "data-w-slug-trim-value": "true",
                "name": "slug",
                "type": "text",
            },
        )

        self.assertEqual(
            self.getAttrs(formatters=[], locale=None),
            {
                "data-action": "blur->w-slug#slugify w-sync:check->w-slug#compare w-sync:apply->w-slug#urlify:prevent",
                "data-controller": "w-slug",
                "data-w-slug-allow-unicode-value": "",
                "data-w-slug-compare-as-param": "urlify",
                # "data-w-slug-formatters-value":... # not included at all
                # "data-w-slug-locale-value":... # not included at all
                "data-w-slug-trim-value": "true",
                "name": "slug",
                "type": "text",
            },
        )

    # Test formatters argument

    def test_with_formatters_provided_are_escaped(self):
        self.assertEqual(
            self.getAttrs(formatters=[(r"\D\s[']+", "'?'")])[
                "data-w-slug-formatters-value"
            ],
            '[[["\\\\D\\\\s[\']+","gu"],"\'?\'"]]',
        )

    def test_with_formatters_as_string(self):
        self.assertEqual(
            self.getAttrs(formatters=[r"\d"])["data-w-slug-formatters-value"],
            '[[["\\\\d","gu"],""]]',
        )

        # handling of inline flags
        self.assertEqual(
            self.getAttrs(formatters=[r"(?m)^\d+"])["data-w-slug-formatters-value"],
            '[[["^\\\\d+","gmu"],""]]',
        )

    def test_with_formatters_as_pattern(self):
        self.assertEqual(
            self.getAttrs(formatters=[re.compile(r"\d")])[
                "data-w-slug-formatters-value"
            ],
            '[[["\\\\d","gu"],""]]',
        )

        # handling of inline flags
        self.assertEqual(
            self.getAttrs(
                formatters=[re.compile(r"(?i)\b(?:and\|or\|the\|in\|of\|to)\b")]
            )["data-w-slug-formatters-value"],
            '[[["\\\\b(?:and\\\\|or\\\\|the\\\\|in\\\\|of\\\\|to)\\\\b","giu"],""]]',
        )

    def test_with_formatters_as_list_like_with_string(self):
        self.assertEqual(
            self.getAttrs(formatters=[["ABC"]])["data-w-slug-formatters-value"],
            '[[["ABC","gu"],""]]',
        )

        self.assertEqual(
            self.getAttrs(formatters=[(r"\d",)])["data-w-slug-formatters-value"],
            '[[["\\\\d","gu"],""]]',
        )

    def test_with_formatters_as_list_like_with_pattern(self):
        self.assertEqual(
            self.getAttrs(formatters=[[re.compile(r"(?i)!")]])[
                "data-w-slug-formatters-value"
            ],
            '[[["!","giu"],""]]',
        )
        self.assertEqual(
            self.getAttrs(formatters=[(re.compile("(?m)^A"),)])[
                "data-w-slug-formatters-value"
            ],
            '[[["^A","gmu"],""]]',
        )

    def test_with_formatters_with_replace(self):
        self.assertEqual(
            self.getAttrs(formatters=[(r"\d", "X")])["data-w-slug-formatters-value"],
            '[[["\\\\d","gu"],"X"]]',
        )

        self.assertEqual(
            self.getAttrs(formatters=[[re.compile(r"\d{1,3}"), "X"]])[
                "data-w-slug-formatters-value"
            ],
            '[[["\\\\d{1,3}","gu"],"X"]]',
        )

    def test_with_formatters_with_replace_and_flags(self):
        self.assertEqual(
            self.getAttrs(
                formatters=[
                    [re.compile(r"^(?!blog[-\s])", flags=re.MULTILINE), "blog-", "u"]
                ]
            )["data-w-slug-formatters-value"],
            '[[["^(?!blog[-\\\\s])","mu"],"blog-"]]',
        )

        self.assertEqual(
            self.getAttrs(
                formatters=[[re.compile(r"(?i)a*"), "Z", "g"], [r"the", "", "u"]]
            )["data-w-slug-formatters-value"],
            '[[["a*","gi"],"Z"],[["the","u"],""]]',
        )

    def test_with_multiple_formatters(self):
        self.assertEqual(
            self.getAttrs(
                formatters=[
                    r"\d",
                    [r"(?<!\S)Й", "Y"],
                    [re.compile(r"(?<!\S)Є"), "Ye", "u"],
                    (r"(?i)the",),
                ]
            )["data-w-slug-formatters-value"],
            '[[["\\\\d","gu"],""],[["(?<!\\\\S)\\u0419","gu"],"Y"],[["(?<!\\\\S)\\u0404","u"],"Ye"],[["the","giu"],""]]',
        )

    # Test locale argument

    def test_with_locale_provided(self):
        self.assertEqual(
            self.getAttrs(locale="uk-UK"),
            {
                "data-action": "blur->w-slug#slugify w-sync:check->w-slug#compare w-sync:apply->w-slug#urlify:prevent",
                "data-controller": "w-slug",
                "data-w-slug-allow-unicode-value": "",
                "data-w-slug-compare-as-param": "urlify",
                "data-w-slug-locale-value": "uk-UK",  # from provided locale
                "data-w-slug-trim-value": "true",
                "name": "slug",
                "type": "text",
            },
        )

        french = Locale.objects.create(language_code="fr")
        self.assertEqual(
            self.getAttrs(locale=french),
            {
                "data-action": "blur->w-slug#slugify w-sync:check->w-slug#compare w-sync:apply->w-slug#urlify:prevent",
                "data-controller": "w-slug",
                "data-w-slug-allow-unicode-value": "",
                "data-w-slug-compare-as-param": "urlify",
                "data-w-slug-locale-value": "fr",  # from provided locale
                "data-w-slug-trim-value": "true",
                "name": "slug",
                "type": "text",
            },
        )

        self.assertEqual(
            self.getAttrs(locale=False),
            {
                "data-action": "blur->w-slug#slugify w-sync:check->w-slug#compare w-sync:apply->w-slug#urlify:prevent",
                "data-controller": "w-slug",
                "data-w-slug-allow-unicode-value": "",
                "data-w-slug-compare-as-param": "urlify",
                "data-w-slug-locale-value": "und",  # from False (aka 'undetermined')
                "data-w-slug-trim-value": "true",
                "name": "slug",
                "type": "text",
            },
        )

    def test_with_locale_blank_override(self):
        self.assertEqual(
            self.getAttrs(locale=False)["data-w-slug-locale-value"],
            "und",
        )

        self.assertEqual(
            self.getAttrs(locale="")["data-w-slug-locale-value"],
            "und",
        )
