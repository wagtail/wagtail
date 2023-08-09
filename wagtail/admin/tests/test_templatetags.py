import json
from datetime import timedelta
from unittest import mock

from django.conf import settings
from django.template import Context, Template, TemplateSyntaxError
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from django.utils.html import format_html
from freezegun import freeze_time

from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.templatetags.wagtailadmin_tags import (
    avatar_url,
    i18n_enabled,
    locale_label_from_id,
    notification_static,
    timesince_last_update,
    timesince_simple,
)
from wagtail.admin.templatetags.wagtailadmin_tags import locales as locales_tag
from wagtail.admin.ui.components import Component
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Locale
from wagtail.test.utils import WagtailTestUtils
from wagtail.users.models import UserProfile
from wagtail.utils.deprecation import RemovedInWagtail60Warning


class TestAvatarTemplateTag(WagtailTestUtils, TestCase):
    def setUp(self):
        # Create a user
        self.test_user = self.create_user(
            username="testuser",
            email="testuser@email.com",
            password="password",
        )

    def test_use_gravatar_by_default(self):
        url = avatar_url(self.test_user)
        self.assertIn("www.gravatar.com", url)

    def test_skip_gravatar_if_no_email(self):
        self.test_user.email = ""
        url = avatar_url(self.test_user)
        self.assertIn("default-user-avatar", url)

    @override_settings(WAGTAIL_GRAVATAR_PROVIDER_URL="https://robohash.org")
    def test_custom_gravatar_provider(self):
        url = avatar_url(self.test_user)
        self.assertIn("robohash.org", url)

    @override_settings(WAGTAIL_GRAVATAR_PROVIDER_URL=None)
    def test_disable_gravatar(self):
        url = avatar_url(self.test_user)
        self.assertIn("default-user-avatar", url)

    def test_uploaded_avatar(self):
        user_profile = UserProfile.get_for_user(self.test_user)
        user_profile.avatar = get_test_image_file(filename="custom-avatar.png")
        user_profile.save()

        url = avatar_url(self.test_user)
        self.assertIn("custom-avatar", url)


class TestNotificationStaticTemplateTag(TestCase):
    @override_settings(STATIC_URL="/static/")
    def test_local_notification_static(self):
        url = notification_static("wagtailadmin/images/email-header.jpg")
        self.assertEqual(
            "{}/static/wagtailadmin/images/email-header.jpg".format(
                settings.WAGTAILADMIN_BASE_URL
            ),
            url,
        )

    @override_settings(
        STATIC_URL="/static/", WAGTAILADMIN_BASE_URL="http://localhost:8000"
    )
    def test_local_notification_static_baseurl(self):
        url = notification_static("wagtailadmin/images/email-header.jpg")
        self.assertEqual(
            "http://localhost:8000/static/wagtailadmin/images/email-header.jpg", url
        )

    @override_settings(
        STATIC_URL="https://s3.amazonaws.com/somebucket/static/",
        WAGTAILADMIN_BASE_URL="http://localhost:8000",
    )
    def test_remote_notification_static(self):
        url = notification_static("wagtailadmin/images/email-header.jpg")
        self.assertEqual(
            "https://s3.amazonaws.com/somebucket/static/wagtailadmin/images/email-header.jpg",
            url,
        )


class TestVersionedStatic(TestCase):
    def test_versioned_static(self):
        result = versioned_static("wagtailadmin/js/core.js")
        self.assertRegex(result, r"^/static/wagtailadmin/js/core.js\?v=(\w+)$")

    @mock.patch("wagtail.admin.staticfiles.static")
    def test_versioned_static_version_string(self, mock_static):
        mock_static.return_value = "/static/wagtailadmin/js/core.js?v=123"
        result = versioned_static("wagtailadmin/js/core.js")
        self.assertEqual(result, "/static/wagtailadmin/js/core.js?v=123")
        mock_static.assert_called_once_with("wagtailadmin/js/core.js")

    def test_versioned_static_absolute_path(self):
        result = versioned_static("/static/wagtailadmin/js/core.js")
        self.assertEqual(result, "/static/wagtailadmin/js/core.js")

    def test_versioned_static_url(self):
        result = versioned_static("http://example.org/static/wagtailadmin/js/core.js")
        self.assertEqual(result, "http://example.org/static/wagtailadmin/js/core.js")


@freeze_time("2020-07-01 12:00:00")
class TestTimesinceTags(TestCase):
    def test_timesince_simple(self):
        now = timezone.now()
        ts = timesince_simple(now)
        self.assertEqual(ts, "just now")

        ts = timesince_simple(now - timedelta(hours=1, minutes=10))
        self.assertEqual(ts, "1\xa0hour ago")

        ts = timesince_simple(now - timedelta(weeks=2, hours=1, minutes=10))
        self.assertEqual(ts, "2\xa0weeks ago")

    def test_timesince_last_update_today_shows_time(self):
        dt = timezone.now() - timedelta(hours=1)
        formatted_time = dt.astimezone(timezone.get_current_timezone()).strftime(
            "%H:%M"
        )

        timesince = timesince_last_update(dt)
        self.assertEqual(timesince, formatted_time)

        # Check prefix output
        timesince = timesince_last_update(dt, show_time_prefix=True)
        self.assertEqual(timesince, f"at {formatted_time}")

        # Check user output
        timesince = timesince_last_update(dt, user_display_name="Gary")
        self.assertEqual(timesince, f"{formatted_time} by Gary")

        # Check user and prefix output
        timesince = timesince_last_update(
            dt, show_time_prefix=True, user_display_name="Gary"
        )
        self.assertEqual(timesince, f"at {formatted_time} by Gary")

    def test_timesince_last_update_before_today_shows_timeago(self):
        dt = timezone.now() - timedelta(weeks=1, days=2)

        # 1) use_shorthand=False

        timesince = timesince_last_update(dt, use_shorthand=False)
        self.assertEqual(timesince, "1\xa0week, 2\xa0days ago")
        # The prefix is not used, if the date is older than the current day.
        self.assertEqual(
            timesince_last_update(dt, use_shorthand=False, show_time_prefix=True),
            timesince,
        )

        # Check user output
        timesince = timesince_last_update(
            dt, use_shorthand=False, user_display_name="Gary"
        )
        self.assertEqual(timesince, "1\xa0week, 2\xa0days ago by Gary")
        self.assertEqual(
            timesince_last_update(
                dt, use_shorthand=False, user_display_name="Gary", show_time_prefix=True
            ),
            timesince,
        )

        # 2) use_shorthand=True

        timesince = timesince_last_update(dt)
        self.assertEqual(timesince, "1\xa0week ago")
        self.assertEqual(timesince_last_update(dt, show_time_prefix=True), timesince)

        timesince = timesince_last_update(dt, user_display_name="Gary")
        self.assertEqual(timesince, "1\xa0week ago by Gary")
        self.assertEqual(
            timesince_last_update(dt, user_display_name="Gary", show_time_prefix=True),
            timesince,
        )

    def test_human_readable_date(self):
        now = timezone.now()
        template = """
            {% load wagtailadmin_tags %}
            {% human_readable_date date %}
        """

        html = Template(template).render(Context({"date": now}))
        self.assertIn("Just now", html)

        html = Template(template).render(
            Context({"date": now - timedelta(hours=1, minutes=10)})
        )
        self.assertIn("1\xa0hour ago", html)


class TestComponentTag(TestCase):
    def test_passing_context_to_component(self):
        class MyComponent(Component):
            def render_html(self, parent_context):
                return format_html(
                    "<h1>{} was here</h1>", parent_context.get("first_name")
                )

        template = Template(
            "{% load wagtailadmin_tags %}{% with first_name='Kilroy' %}{% component my_component %}{% endwith %}"
        )
        html = template.render(Context({"my_component": MyComponent()}))
        self.assertEqual(html, "<h1>Kilroy was here</h1>")

    def test_component_escapes_unsafe_strings(self):
        class MyComponent(Component):
            def render_html(self, parent_context):
                return "Look, I'm running with scissors! 8< 8< 8<"

        template = Template(
            "{% load wagtailadmin_tags %}<h1>{% component my_component %}</h1>"
        )
        html = template.render(Context({"my_component": MyComponent()}))
        self.assertEqual(
            html, "<h1>Look, I&#x27;m running with scissors! 8&lt; 8&lt; 8&lt;</h1>"
        )

    def test_error_on_rendering_non_component(self):
        template = Template(
            "{% load wagtailadmin_tags %}<h1>{% component my_component %}</h1>"
        )

        with self.assertRaises(ValueError) as cm:
            template.render(Context({"my_component": "hello"}))
        self.assertEqual(str(cm.exception), "Cannot render 'hello' as a component")


@override_settings(
    WAGTAIL_CONTENT_LANGUAGES=[
        ("en", "English"),
        ("fr", "French"),
        ("ro", "Romanian"),
        ("ru", "Russian"),
    ]
)
class TestInternationalisationTags(TestCase):
    def setUp(self):
        self.locale_ids = []
        for language_code in ["en", "fr", "ro", "ru"]:
            locale, _ = Locale.objects.get_or_create(language_code=language_code)
            self.locale_ids.append(locale.pk)

    def test_i18n_enabled(self):
        with override_settings(WAGTAIL_I18N_ENABLED=False):
            self.assertFalse(i18n_enabled())

        with override_settings(WAGTAIL_I18N_ENABLED=True):
            self.assertTrue(i18n_enabled())

    def test_locales(self):
        locales_output = locales_tag()
        self.assertIsInstance(locales_output, str)
        self.assertEqual(
            json.loads(locales_output),
            [
                {"code": "en", "display_name": "English"},
                {"code": "fr", "display_name": "French"},
                {"code": "ro", "display_name": "Romanian"},
                {"code": "ru", "display_name": "Russian"},
            ],
        )

    def test_locale_label_from_id(self):
        with self.assertNumQueries(1):
            self.assertEqual(locale_label_from_id(self.locale_ids[0]), "English")

        with self.assertNumQueries(0):
            self.assertEqual(locale_label_from_id(self.locale_ids[1]), "French")

        # check with an invalid id
        with self.assertNumQueries(0):
            self.assertIsNone(locale_label_from_id(self.locale_ids[-1] + 100), None)


class ComponentTest(TestCase):
    def test_render_block_component(self):
        template = """
            {% load wagtailadmin_tags %}
            {% help_block status="info" %}Proceed with caution{% endhelp_block %}
        """

        expected = """
            <div class="help-block help-info">
                <svg aria-hidden="true" class="icon icon icon-help"><use href="#icon-help"></svg>
                Proceed with caution
            </div>
        """

        self.assertHTMLEqual(expected, Template(template).render(Context()))

    def test_render_nested(self):
        template = """
            {% load wagtailadmin_tags %}
            {% help_block status="warning" %}
                {% help_block status="info" %}Proceed with caution{% endhelp_block %}
            {% endhelp_block %}
        """

        expected = """
            <div class="help-block help-warning">
                <svg aria-hidden="true" class="icon icon icon-warning"><use href="#icon-warning"></svg>
                <div class="help-block help-info">
                    <svg aria-hidden="true" class="icon icon icon-help"><use href="#icon-help"></svg>
                    Proceed with caution
                </div>
            </div>
        """

        self.assertHTMLEqual(expected, Template(template).render(Context()))

    def test_kwargs_with_filters(self):
        template = """
            {% load wagtailadmin_tags %}
            {% help_block status="warning"|upper %}Proceed with caution{% endhelp_block %}
        """

        expected = """
            <div class="help-block help-WARNING">
                <svg aria-hidden="true" class="icon icon icon-warning"><use href="#icon-warning"></svg>
                Proceed with caution
            </div>
        """

        self.assertHTMLEqual(expected, Template(template).render(Context()))

    def test_render_as_variable(self):
        template = """
            {% load wagtailadmin_tags %}
            {% help_block status="info" as help %}Proceed with caution{% endhelp_block %}
            <template>{{ help }}</template>
        """

        expected = """
            <template>
                <div class="help-block help-info">
                    <svg aria-hidden="true" class="icon icon icon-help"><use href="#icon-help"></svg>
                    Proceed with caution
                </div>
            </template>
        """

        self.assertHTMLEqual(expected, Template(template).render(Context()))


class FragmentTagTest(TestCase):
    def test_basic(self):
        context = Context({})

        template = """
            {% load wagtailadmin_tags %}
            {% fragment as my_fragment %}
            <p>Hello, World</p>
            {% endfragment %}
            Text coming after:
            {{ my_fragment }}
        """

        expected = """
            Text coming after:
            <p>Hello, World</p>
        """

        self.assertHTMLEqual(expected, Template(template).render(context))

    @override_settings(DEBUG=True)
    def test_syntax_error(self):
        template = """
            {% load wagtailadmin_tags %}
            {% fragment %}
            <p>Hello, World</p>
            {% endfragment %}
        """

        with self.assertRaises(TemplateSyntaxError):
            Template(template).render(Context())

    def test_with_variables(self):
        context = Context({"name": "jonathan wells"})

        template = """
            {% load wagtailadmin_tags %}
            {% fragment as my_fragment %}
                <p>Hello, {{ name|title }}</p>
            {% endfragment %}
            Text coming after:
            {{ my_fragment }}
        """

        expected = """
            Text coming after:
            <p>Hello, Jonathan Wells</p>
        """

        self.assertHTMLEqual(expected, Template(template).render(context))


class ClassnamesTagTest(TestCase):
    def test_with_single_arg(self):
        template = """
            {% load wagtailadmin_tags %}
            <p class="{% classnames "w-header" classname  %}">Hello!</p>
        """

        expected = """
            <p class="w-header">Hello!</p>
        """

        actual = Template(template).render(Context())

        self.assertHTMLEqual(expected, actual)

    def test_with_multiple_args(self):
        template = """
            {% load wagtailadmin_tags %}
            <p class="{% classnames "w-header" classname "w-header--merged" "w-header--hasform" %}">
                Hello!
            </p>
        """

        expected = """
            <p class="w-header w-header--merged w-header--hasform">
                Hello!
            </p>
        """

        actual = Template(template).render(Context())

        self.assertHTMLEqual(expected, actual)

    def test_with_falsy_args(self):
        template = """
            {% load wagtailadmin_tags %}
            <p class="{% classnames "w-header" classname "" %}">Hello!</p>
        """

        expected = """
            <p class="w-header">Hello!</p>
        """

        actual = Template(template).render(Context())

        self.assertEqual(expected.strip(), actual.strip())

    def test_with_args_with_extra_whitespace(self):
        context = Context(
            {
                "merged": "w-header--merged ",
                "search_form": " w-header--hasform",
                "name": " wagtail ",
            }
        )

        template = """
            {% load wagtailadmin_tags %}
            <p class="{% classnames "w-header" classname merged search_form name %}">Hello!</p>
        """

        expected = """
            <p class="w-header w-header--merged w-header--hasform wagtail">Hello!</p>
        """

        actual = Template(template).render(context)

        self.assertEqual(expected.strip(), actual.strip())


class IconTagTest(TestCase):
    def test_basic(self):
        template = """
            {% load wagtailadmin_tags %}
            {% icon name="cogs" %}
        """

        expected = """
            <svg aria-hidden="true" class="icon icon-cogs icon"><use href="#icon-cogs"></svg>
        """

        self.assertHTMLEqual(expected, Template(template).render(Context()))

    def test_with_classes_positional(self):
        template = """
            {% load wagtailadmin_tags %}
            {% icon "cogs" "myclass" %}
        """

        expected = """
            <svg aria-hidden="true" class="icon icon-cogs myclass"><use href="#icon-cogs"></svg>
        """

        self.assertHTMLEqual(expected, Template(template).render(Context()))

    def test_with_classes_keyword(self):
        template = """
            {% load wagtailadmin_tags %}
            {% icon name="warning" classname="myclass" %}
        """

        expected = """
            <svg aria-hidden="true" class="icon icon-warning myclass"><use href="#icon-warning"></svg>
        """

        self.assertHTMLEqual(expected, Template(template).render(Context()))

    def test_with_classes_obsolete_keyword(self):
        template = """
            {% load wagtailadmin_tags %}
            {% icon name="doc-empty" class_name="myclass" %}
        """

        expected = """
            <svg aria-hidden="true" class="icon icon-doc-empty myclass"><use href="#icon-doc-empty"></svg>
        """

        with self.assertWarnsMessage(
            RemovedInWagtail60Warning,
            (
                "Icon template tag `class_name` has been renamed to `classname`, "
                "please adopt the new usage instead. Replace "
                '`{% icon ... class_name="myclass" %}` with '
                '`{% icon ... classname="myclass" %}`'
            ),
        ):
            self.assertHTMLEqual(expected, Template(template).render(Context()))

    def test_with_deprecated_icon(self):
        template = """
            {% load wagtailadmin_tags %}
            {% icon name="reset" %}
        """

        expected = """
            <svg aria-hidden="true" class="icon icon-reset icon"><use href="#icon-reset"></svg>
        """

        with self.assertWarnsMessage(
            RemovedInWagtail60Warning,
            ("Icon `reset` is deprecated and will be removed in a future release."),
        ):
            self.assertHTMLEqual(expected, Template(template).render(Context()))

    def test_with_renamed_icon(self):
        template = """
            {% load wagtailadmin_tags %}
            {% icon name="download-alt" %}
        """

        expected = """
            <svg aria-hidden="true" class="icon icon-download icon"><use href="#icon-download"></svg>
        """

        with self.assertWarnsMessage(
            RemovedInWagtail60Warning,
            (
                "Icon `download-alt` has been renamed to `download`, "
                "please adopt the new usage instead. Replace "
                '`{% icon name="download-alt" ... %}` with '
                '`{% icon name="download" ... %}'
            ),
        ):
            self.assertHTMLEqual(expected, Template(template).render(Context()))


class StatusTagTest(TestCase):
    def test_render_block_component_span_variations(self):
        template = """
            {% load wagtailadmin_tags i18n %}
            {% status "live" classname="w-status--primary" %}
            {% status "live" %}
            {% trans "hidden translated label" as trans_hidden_label %}
            {% status "live" hidden_label=trans_hidden_label classname="w-status--primary" %}
            {% status %}
        """

        expected = """
            <span class="w-status w-status--primary">live</span>
            <span class="w-status">live</span>
            <span class="w-status w-status--primary"><span class="visuallyhidden">hidden translated label</span>live</span>
            <span class="w-status"></span>
        """

        self.assertHTMLEqual(expected, Template(template).render(Context()))

    def test_render_block_component_anchor_variations(self):
        template = """
            {% load wagtailadmin_tags i18n %}
            {% trans "title" as trans_title %}
            {% trans "hidden label" as trans_hidden_label %}
            {% status "live" url="/test-url/" title=trans_title hidden_label=trans_hidden_label classname="w-status--primary" attrs='target="_blank" rel="noreferrer"' %}
            {% status "live" url="/test-url/" title=trans_title classname="w-status--primary" %}
            {% status "live" url="/test-url/" title=trans_title %}
            {% status  url="/test-url/" title=trans_title attrs='id="my-status"' %}
        """

        expected = """
            <a href="/test-url/" class="w-status w-status--primary" title="title" target="_blank" rel="noreferrer">
                <span class="visuallyhidden">hidden label</span>
                live
            </a>
            <a href="/test-url/" class="w-status w-status--primary" title="title">
                live
            </a>
            <a href="/test-url/" class="w-status" title="title">
                live
            </a>
            <a href="/test-url/" class="w-status" title="title" id="my-status">
            </a>
        """

        self.assertHTMLEqual(expected, Template(template).render(Context()))

    def test_render_as_fragment(self):
        template = """
            {% load wagtailadmin_tags i18n %}
            {% fragment as var %}
                {% trans "title" as trans_title %}
                {% trans "hidden label" as trans_hidden_label %}
                {% status "live" url="/test-url/" title=trans_title hidden_label=trans_hidden_label classname="w-status--primary" attrs='target="_blank" rel="noreferrer"' %}
                {% status "live" hidden_label=trans_hidden_label classname="w-status--primary" attrs="data-example='present'" %}
            {% endfragment %}
            {{var}}
        """

        expected = """
            <a href="/test-url/" class="w-status w-status--primary" title="title" target="_blank" rel="noreferrer">
                <span class="visuallyhidden">hidden label</span>
                live
            </a>
            <span class="w-status w-status--primary" data-example='present'>
                <span class="visuallyhidden">hidden label</span>
                live
            </span>
        """

        self.assertHTMLEqual(expected, Template(template).render(Context()))
