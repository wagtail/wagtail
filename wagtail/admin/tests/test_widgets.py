import json

from django import forms
from django.test import TestCase
from django.test.utils import override_settings

from wagtail.admin import widgets
from wagtail.admin.forms.tags import TagField
from wagtail.models import Page
from wagtail.test.testapp.forms import AdminStarDateInput
from wagtail.test.testapp.models import EventPage, RestaurantTag, SimplePage


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

    def test_adapt(self):
        widget = widgets.AdminPageChooser()

        js_args = widgets.PageChooserAdapter().js_args(widget)
        self.assertInHTML(
            """<input id="__ID__" name="__NAME__" type="hidden" />""", js_args[0]
        )
        self.assertIn(">Choose a page<", js_args[0])
        self.assertEqual(js_args[1], "__ID__")
        self.assertEqual(
            js_args[2],
            {
                "can_choose_root": False,
                "model_names": ["wagtailcore.page"],
                "user_perms": None,
            },
        )

    def test_adapt_with_target_model(self):
        widget = widgets.AdminPageChooser(target_models=[SimplePage, EventPage])

        js_args = widgets.PageChooserAdapter().js_args(widget)
        self.assertEqual(
            js_args[2]["model_names"], ["tests.simplepage", "tests.eventpage"]
        )

    def test_adapt_with_can_choose_root(self):
        widget = widgets.AdminPageChooser(can_choose_root=True)

        js_args = widgets.PageChooserAdapter().js_args(widget)
        self.assertTrue(js_args[2]["can_choose_root"])

    def test_render_html(self):
        # render_html is mostly an internal API, but we do want to support calling it with None as
        # a value, to render a blank field without the JS initialiser (so that we can call that
        # separately in our own context and hold on to the return value)
        widget = widgets.AdminPageChooser()

        html = widget.render_html("test", None, {})
        self.assertInHTML("""<input name="test" type="hidden" />""", html)
        self.assertIn(">Choose a page<", html)

    def test_render_js_init(self):
        widget = widgets.AdminPageChooser()

        html = widget.render("test", None, {"id": "test-id"})
        self.assertIn(
            'new PageChooser("test-id", null, {"model_names": ["wagtailcore.page"], "can_choose_root": false, "user_perms": null});',
            html,
        )

    def test_render_js_init_with_user_perm(self):
        widget = widgets.AdminPageChooser(user_perms="copy_to")

        html = widget.render("test", None, {"id": "test-id"})
        self.assertIn(
            'new PageChooser("test-id", null, {"model_names": ["wagtailcore.page"], "can_choose_root": false, "user_perms": "copy_to"});',
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
            'new PageChooser("test-id", %d, {"model_names": ["wagtailcore.page"], "can_choose_root": false, "user_perms": null});'
            % self.root_page.id,
            html,
        )

    def test_render_with_target_model(self):
        widget = widgets.AdminPageChooser(target_models=[SimplePage])

        html = widget.render("test", None, {"id": "test-id"})
        self.assertIn(
            'new PageChooser("test-id", null, {"model_names": ["tests.simplepage"], "can_choose_root": false, "user_perms": null});',
            html,
        )

        html = widget.render("test", self.child_page, {"id": "test-id"})
        self.assertIn(">Choose a page (Simple Page)<", html)

    def test_render_with_target_model_as_single_instance(self):
        widget = widgets.AdminPageChooser(target_models=SimplePage)

        html = widget.render("test", None, {"id": "test-id"})
        self.assertIn(
            'new PageChooser("test-id", null, {"model_names": ["tests.simplepage"], "can_choose_root": false, "user_perms": null});',
            html,
        )

        html = widget.render("test", self.child_page, {"id": "test-id"})
        self.assertIn(">Choose a page (Simple Page)<", html)

    def test_render_with_target_model_as_single_string(self):
        widget = widgets.AdminPageChooser(target_models="tests.SimplePage")

        html = widget.render("test", None, {"id": "test-id"})
        self.assertIn(
            'new PageChooser("test-id", null, {"model_names": ["tests.simplepage"], "can_choose_root": false, "user_perms": null});',
            html,
        )

        html = widget.render("test", self.child_page, {"id": "test-id"})
        self.assertIn(">Choose a page (Simple Page)<", html)

    def test_render_with_multiple_target_models(self):
        target_models = [SimplePage, "tests.eventpage"]
        widget = widgets.AdminPageChooser(target_models=target_models)

        html = widget.render("test", None, {"id": "test-id"})
        self.assertIn(
            'new PageChooser("test-id", null, {"model_names": ["tests.simplepage", "tests.eventpage"], "can_choose_root": false, "user_perms": null});',
            html,
        )

        html = widget.render("test", self.child_page, {"id": "test-id"})
        self.assertIn(">Choose a page<", html)

    def test_render_js_init_with_can_choose_root(self):
        widget = widgets.AdminPageChooser(can_choose_root=True)

        html = widget.render("test", self.child_page, {"id": "test-id"})
        self.assertIn(
            'new PageChooser("test-id", %d, {"model_names": ["wagtailcore.page"], "can_choose_root": true, "user_perms": null});'
            % self.root_page.id,
            html,
        )


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
            {"dayOfWeekStart": 0, "format": "Y-m-d H:i", "formatTime": "H:i"},
        )

    def test_adapt_with_custom_format(self):
        widget = widgets.AdminDateTimeInput(
            format="%d.%m.%Y. %H:%M", time_format="%H:%M %p"
        )

        js_args = widgets.AdminDateTimeInputAdapter().js_args(widget)

        self.assertEqual(
            js_args[0],
            {"dayOfWeekStart": 0, "format": "d.m.Y. H:i", "formatTime": "H:i A"},
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
        """Returns a list of the params passed in to initTagField from the supplied HTML"""
        # example - ["test_id", "/admin/tag-autocomplete/", {'allowSpaces': True}]
        start = "initTagField("
        end = ");"
        items_after_init = html.split(start)[1]
        if items_after_init:
            params_raw = items_after_init.split(end)[0]
            if params_raw:
                # stuff parameter string into an array so that we can unpack it as JSON
                return json.loads("[%s]" % params_raw)
        return []

    def get_help_text_html_element(self, html):
        """Return a help text html element with content as string"""
        start = """<input type="text" name="tags">"""
        end = "<script>"
        items_after_input_tag = html.split(start)[1]
        if items_after_input_tag:
            help_text_element = items_after_input_tag.split(end)[0].strip()
            return help_text_element
        return []

    def test_render_js_init_basic(self):
        """Checks that the 'initTagField' is correctly added to the inline script for tag widgets"""
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

    @override_settings(TAG_SPACES_ALLOWED=False)
    def test_render_js_init_no_spaces_allowed(self):
        """Checks that the 'initTagField' includes the correct value based on TAG_SPACES_ALLOWED in settings"""
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

    @override_settings(TAG_LIMIT=5)
    def test_render_js_init_with_tag_limit(self):
        """Checks that the 'initTagField' includes the correct value based on TAG_LIMIT in settings"""
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
        Checks that 'initTagField' is passed the correct autocomplete URL for the custom model,
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

    @override_settings(TAG_SPACES_ALLOWED=True)
    def test_tags_help_text_spaces_allowed(self):
        """Checks that the tags help text html element content is correct when TAG_SPACES_ALLOWED is True"""
        widget = widgets.AdminTagWidget()
        help_text = widget.get_context(None, None, {})["widget"]["help_text"]

        html = widget.render("tags", None, {})
        help_text_html_element = self.get_help_text_html_element(html)

        self.assertEqual(
            help_text,
            'Multi-word tags with spaces will automatically be enclosed in double quotes (").',
        )

        self.assertHTMLEqual(
            help_text_html_element,
            """<p class="help">%s</p>""" % help_text,
        )

    @override_settings(TAG_SPACES_ALLOWED=False)
    def test_tags_help_text_no_spaces_allowed(self):
        """Checks that the tags help text html element content is correct when TAG_SPACES_ALLOWED is False"""
        widget = widgets.AdminTagWidget()
        help_text = widget.get_context(None, None, {})["widget"]["help_text"]

        html = widget.render("tags", None, {})
        help_text_html_element = self.get_help_text_html_element(html)

        self.assertEqual(
            help_text, "Tags can only consist of a single word, no spaces allowed."
        )

        self.assertHTMLEqual(
            help_text_html_element,
            """<p class="help">%s</p>""" % help_text,
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
