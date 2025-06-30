import os
import unittest
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone
from unittest import mock

from django.conf import settings
from django.template import Context, Template, TemplateSyntaxError
from django.test import SimpleTestCase, TestCase
from django.test.utils import override_settings
from django.utils import timezone
from freezegun import freeze_time

from wagtail.admin.staticfiles import VERSION_HASH, versioned_static
from wagtail.admin.templatetags.wagtailadmin_tags import (
    absolute_static,
    avatar_url,
    i18n_enabled,
    locale_label_from_id,
    timesince_last_update,
    timesince_simple,
)
from wagtail.coreutils import get_dummy_request
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Locale, Page
from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.template_tests import AdminTemplateTestUtils
from wagtail.users.models import UserProfile


class TestAvatarUrlInterceptTemplateTag(WagtailTestUtils, TestCase):
    def setUp(self):
        self.test_user = self.create_user(
            username="testuser",
            email="testuser@email.com",
            password="password",
        )

    def test_get_avatar_url_undefined(self):
        url = avatar_url(self.test_user)
        self.assertIn("www.gravatar.com", url)

    @mock.patch.dict(os.environ, {"AVATAR_INTERCEPT": "True"}, clear=True)
    def test_get_avatar_url_registered(self):
        url = avatar_url(self.test_user)
        self.assertEqual(url, "/some/avatar/fred.png")


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


class TestAbsoluteStaticTemplateTag(SimpleTestCase):
    @override_settings(STATIC_URL="/static/")
    def test_local_absolute_static(self):
        url = absolute_static("wagtailadmin/images/email-header.jpg")
        expected = (
            rf"^{settings.WAGTAILADMIN_BASE_URL}/static/wagtailadmin/images/"
            r"email-header.jpg\?v=(\w{8})$"
        )
        self.assertRegex(url, expected)

    @override_settings(
        STATIC_URL="/static/", WAGTAILADMIN_BASE_URL="http://localhost:8000"
    )
    def test_local_absolute_static_baseurl(self):
        url = absolute_static("wagtailadmin/images/email-header.jpg")
        expected = (
            r"^http://localhost:8000/static/wagtailadmin/images/"
            r"email-header.jpg\?v=(\w{8})$"
        )
        self.assertRegex(url, expected)

    @override_settings(
        STATIC_URL="https://s3.amazonaws.com/somebucket/static/",
        WAGTAILADMIN_BASE_URL="http://localhost:8000",
    )
    def test_remote_absolute_static(self):
        url = absolute_static("wagtailadmin/images/email-header.jpg")
        expected = (
            r"https://s3.amazonaws.com/somebucket/static/wagtailadmin/images/"
            r"email-header.jpg\?v=(\w{8})$"
        )
        self.assertRegex(url, expected)


class TestVersionedStatic(SimpleTestCase):
    def test_version_hash(self):
        self.assertEqual(len(VERSION_HASH), 8)

    def test_versioned_static(self):
        result = versioned_static("wagtailadmin/js/core.js")
        self.assertRegex(result, r"^/static/wagtailadmin/js/core.js\?v=(\w{8})$")

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


class TestTimesinceTags(SimpleTestCase):
    # timezone matches TIME_ZONE = "Asia/Tokyo" in tests/settings.py
    @freeze_time("2020-07-01 12:00:00+09:00")
    def test_timesince_simple(self):
        now = timezone.make_aware(
            datetime(2020, 7, 1, 12, 0, 0)
        )  # aware date in Asia/Tokyo
        ts = timesince_simple(now)
        self.assertEqual(ts, "just now")

        now = timezone.make_aware(
            datetime(2020, 7, 1, 3, 0, 0), timezone=dt_timezone.utc
        )  # aware date in UTC
        ts = timesince_simple(now)
        self.assertEqual(ts, "just now")

        seventy_minutes_ago = timezone.make_aware(datetime(2020, 7, 1, 10, 50, 0))
        ts = timesince_simple(seventy_minutes_ago)
        self.assertEqual(ts, "1\xa0hour ago")

        two_weeks_ago = timezone.make_aware(datetime(2020, 6, 17, 10, 50, 0))
        ts = timesince_simple(two_weeks_ago)
        self.assertEqual(ts, "2\xa0weeks ago")

    @unittest.skipIf(not settings.USE_TZ, "Test assumes timezone support is active")
    @freeze_time("2020-07-01 06:00:00+09:00")
    def test_timesince_last_update_today_shows_time(self):
        one_hour_ago = timezone.make_aware(
            datetime(2020, 7, 1, 5, 0, 0)
        )  # aware date in Asia/Tokyo
        timesince = timesince_last_update(one_hour_ago)
        self.assertEqual(timesince, "05:00")

        # Check prefix output
        timesince = timesince_last_update(one_hour_ago, show_time_prefix=True)
        self.assertEqual(timesince, "at 05:00")

        # Check user output
        timesince = timesince_last_update(one_hour_ago, user_display_name="Gary")
        self.assertEqual(timesince, "05:00 by Gary")

        # Check user and prefix output
        timesince = timesince_last_update(
            one_hour_ago, show_time_prefix=True, user_display_name="Gary"
        )
        self.assertEqual(timesince, "at 05:00 by Gary")

        one_hour_ago = timezone.make_aware(
            datetime(2020, 6, 30, 20, 0, 0), timezone=dt_timezone.utc
        )  # aware date in UTC
        timesince = timesince_last_update(one_hour_ago)
        self.assertEqual(timesince, "05:00")

    @unittest.skipIf(settings.USE_TZ, "Test assumes timezone support is disabled")
    @freeze_time("2020-07-01 06:00:00")
    def test_timesince_last_update_today_shows_time_without_tz(self):
        one_hour_ago = datetime(2020, 7, 1, 5, 0, 0)
        timesince = timesince_last_update(one_hour_ago)
        self.assertEqual(timesince, "05:00")

        # Check prefix output
        timesince = timesince_last_update(one_hour_ago, show_time_prefix=True)
        self.assertEqual(timesince, "at 05:00")

        # Check user output
        timesince = timesince_last_update(one_hour_ago, user_display_name="Gary")
        self.assertEqual(timesince, "05:00 by Gary")

        # Check user and prefix output
        timesince = timesince_last_update(
            one_hour_ago, show_time_prefix=True, user_display_name="Gary"
        )
        self.assertEqual(timesince, "at 05:00 by Gary")

    @unittest.skipIf(not settings.USE_TZ, "Test assumes timezone support is active")
    @freeze_time("2020-07-01 06:00:00+09:00")
    def test_timesince_last_update_before_midnight_shows_timeago(self):
        """
        If the last update was yesterday in local time, we show "x hours ago" even if it was less
        than 24 hours ago (and even if it matches today's date in UTC)
        """
        eight_hours_ago = timezone.make_aware(
            datetime(2020, 6, 30, 21, 50, 0)
        )  # aware date in Asia/Tokyo
        timesince = timesince_last_update(eight_hours_ago)
        self.assertEqual(timesince, "8\xa0hours ago")

    @unittest.skipIf(settings.USE_TZ, "Test assumes timezone support is disabled")
    @freeze_time("2020-07-01 06:00:00")
    def test_timesince_last_update_before_midnight_shows_timeago_without_tz(self):
        """
        If the last update was yesterday in local time, we show "x hours ago" even if it was less
        than 24 hours ago
        """
        eight_hours_ago = datetime(2020, 6, 30, 21, 50, 0)
        timesince = timesince_last_update(eight_hours_ago)
        self.assertEqual(timesince, "8\xa0hours ago")

    @unittest.skipIf(not settings.USE_TZ, "Test assumes timezone support is active")
    @freeze_time("2020-07-01 12:00:00+09:00")
    def test_timesince_last_update_before_today_shows_timeago(self):
        dt = timezone.make_aware(datetime(2020, 6, 22, 12, 0, 0))

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

    @unittest.skipIf(settings.USE_TZ, "Test assumes timezone support is disabled")
    @freeze_time("2020-07-01 12:00:00")
    def test_timesince_last_update_before_today_shows_timeago_without_tz(self):
        dt = timezone.make_aware(datetime(2020, 6, 22, 12, 0, 0))

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

    @override_settings(USE_TZ=False)
    @freeze_time("2020-07-01 12:00:00")
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
        self.assertIn('data-w-tooltip-placement-value="top"', html)
        self.assertIn('data-w-tooltip-content-value="July 1, 2020, 10:50 a.m."', html)

    @override_settings(USE_TZ=False)
    @freeze_time("2020-07-01 12:00:00")
    def test_human_readable_date_with_date_object(self):
        today = timezone.now().date()
        template = """
            {% load wagtailadmin_tags %}
            {% human_readable_date date %}
        """

        html = Template(template).render(Context({"date": today}))
        self.assertIn("12\xa0hours ago", html)

        html = Template(template).render(
            Context({"date": today - timedelta(days=1, hours=1)})
        )
        self.assertIn("1\xa0day ago", html)
        self.assertIn('data-w-tooltip-placement-value="top"', html)
        self.assertIn('data-w-tooltip-content-value="June 30, 2020"', html)

    @freeze_time("2020-07-01 12:00:00")
    def test_human_readable_date_with_args(self):
        now = timezone.now()
        template = """
            {% load wagtailadmin_tags %}
            {% human_readable_date date "The clock ticked" "bottom" %}
        """

        html = Template(template).render(Context({"date": now}))
        self.assertIn(
            '<span class="w-human-readable-date__description">The clock ticked</span>',
            html,
        )
        self.assertIn('data-w-tooltip-placement-value="bottom"', html)


@override_settings(
    WAGTAIL_CONTENT_LANGUAGES=[
        ("en", "English"),
        ("fr", "French"),
        ("ro", "Romanian"),
        ("ru", "Russian"),
    ],
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
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

    def test_locale_label_from_id(self):
        with self.assertNumQueries(1):
            self.assertEqual(locale_label_from_id(self.locale_ids[0]), "English")

        with self.assertNumQueries(0):
            self.assertEqual(locale_label_from_id(self.locale_ids[1]), "French")

        # check with an invalid id
        with self.assertNumQueries(0):
            self.assertIsNone(locale_label_from_id(self.locale_ids[-1] + 100), None)


class ComponentTest(SimpleTestCase):
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


class FragmentTagTest(SimpleTestCase):
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


class ClassnamesTagTest(SimpleTestCase):
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

    def test_with_nested_lists(self):
        context = Context(
            {
                "nested": ["button-add", "button-base "],
                "has_falsey": ["", False, [], {}],
                "simple": " wagtail ",
            }
        )

        template = """
            {% load wagtailadmin_tags %}
            <button class="{% classnames nested "add-second " has_falsey simple %}">Hello!</button>
        """

        expected = """
            <button class="button-add button-base add-second wagtail">Hello!</button>
        """

        actual = Template(template).render(context)

        self.assertEqual(expected.strip(), actual.strip())


class IconTagTest(SimpleTestCase):
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


class StatusTagTest(SimpleTestCase):
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
            <span class="w-status w-status--primary"><span class="w-sr-only">hidden translated label</span>live</span>
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
                <span class="w-sr-only">hidden label</span>
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
                <span class="w-sr-only">hidden label</span>
                live
            </a>
            <span class="w-status w-status--primary" data-example='present'>
                <span class="w-sr-only">hidden label</span>
                live
            </span>
        """

        self.assertHTMLEqual(expected, Template(template).render(Context()))


class BreadcrumbsTagTest(AdminTemplateTestUtils, WagtailTestUtils, SimpleTestCase):
    base_breadcrumb_items = []
    template = """
        {% load wagtailadmin_tags %}
        {% breadcrumbs items %}
    """

    def test_single_item(self):
        items = [{"label": "Something", "url": "/admin/something/"}]
        rendered = Template(self.template).render(Context({"items": items}))
        self.assertBreadcrumbsItemsRendered(items, rendered)
        # Without specifying is_expanded=False, the breadcrumbs should not be
        # collapsible anyway, so it is not controlled by Stimulus
        soup = self.get_soup(rendered)
        breadcrumbs = soup.select_one(".w-breadcrumbs")
        self.assertIsNotNone(breadcrumbs)
        self.assertIsNone(breadcrumbs.get("data-controller"))

    def test_trailing_no_url(self):
        items = [
            {"label": "Snippets", "url": "/admin/snippets/"},
            {"label": "People", "url": "/admin/snippets/people/"},
            {"label": "New: Person"},
        ]
        rendered = Template(self.template).render(Context({"items": items}))
        self.assertBreadcrumbsItemsRendered(items, rendered)

    def test_not_is_expanded(self):
        items = [
            {"label": "Snippets", "url": "/admin/snippets/"},
            {"label": "People", "url": "/admin/snippets/people/"},
            {"label": "Muddy Waters", "url": "/admin/snippets/people/1/edit/"},
        ]
        rendered = Template(self.template).render(Context({"items": items}))
        self.assertBreadcrumbsItemsRendered(items, rendered)

        soup = self.get_soup(rendered)
        controller = soup.select_one('[data-controller="w-breadcrumbs"]')
        toggle_button = soup.select_one('button[data-w-breadcrumbs-target="toggle"]')
        self.assertIsNotNone(controller)
        self.assertIsNotNone(toggle_button)
        # If is_expanded=False (the default), the breadcrumbs should be
        # collapsible via Stimulus
        soup = self.get_soup(rendered)
        breadcrumbs = soup.select_one(".w-breadcrumbs")
        self.assertIsNotNone(breadcrumbs)
        self.assertEqual(breadcrumbs.get("data-controller"), "w-breadcrumbs")

    def test_is_expanded(self):
        template = """
            {% load wagtailadmin_tags %}
            {% breadcrumbs items is_expanded=True %}
        """
        items = [
            {"label": "Snippets", "url": "/admin/snippets/"},
            {"label": "People", "url": "/admin/snippets/people/"},
            {"label": "Muddy Waters", "url": "/admin/snippets/people/1/edit/"},
        ]
        rendered = Template(template).render(Context({"items": items}))
        self.assertBreadcrumbsItemsRendered(items, rendered)

        soup = self.get_soup(rendered)
        controller = soup.select_one('[data-controller="w-breadcrumbs"]')
        toggle_button = soup.select_one('button[data-w-breadcrumbs-target="toggle"]')
        self.assertIsNone(controller)
        self.assertIsNone(toggle_button)
        # If is_expanded=True, the breadcrumbs should not be collapsible, so it
        # is not controlled by Stimulus
        soup = self.get_soup(rendered)
        breadcrumbs = soup.select_one(".w-breadcrumbs")
        self.assertIsNotNone(breadcrumbs)
        self.assertIsNone(breadcrumbs.get("data-controller"))

    def test_classname(self):
        template = """
            {% load wagtailadmin_tags %}
            {% breadcrumbs items classname="my-class" %}
        """
        items = [{"label": "Home", "url": "/admin/"}]
        rendered = Template(template).render(Context({"items": items}))
        self.assertBreadcrumbsItemsRendered(items, rendered)

        soup = self.get_soup(rendered)
        div = soup.select_one("div.w-breadcrumbs")
        self.assertIsNotNone(div)
        self.assertIn("my-class", div["class"])

    def test_icon_name(self):
        template = """
            {% load wagtailadmin_tags %}
            {% breadcrumbs items icon_name="site" %}
        """
        items = [
            {"label": "Home", "url": "/admin/"},
            {"label": "Something", "url": "/admin/something/"},
        ]
        rendered = Template(template).render(Context({"items": items}))
        self.assertBreadcrumbsItemsRendered(items, rendered)

        soup = self.get_soup(rendered)
        invalid_icons = soup.select("ol li:not(:last-child) svg use[href='#icon-site']")
        self.assertEqual(len(invalid_icons), 0)
        icon = soup.select_one("ol li:last-child svg use[href='#icon-site']")
        self.assertIsNotNone(icon)


class PageBreadcrumbsTagTest(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    fixtures = ["test.json"]
    base_breadcrumb_items = []

    def setUp(self):
        self.request = get_dummy_request()
        self.user = self.login()
        self.request.user = self.user

    def test_root_single_item(self):
        template = """
            {% load wagtailadmin_tags %}
            {% page_breadcrumbs page 'wagtailadmin_explore' url_root_name='wagtailadmin_explore_root' %}
        """
        page = Page.objects.get(id=1)
        items = [{"label": "Root", "url": "/admin/pages/"}]
        rendered = Template(template).render(
            Context({"page": page, "request": self.request})
        )
        self.assertBreadcrumbsItemsRendered(items, rendered)
        # Without specifying is_expanded=False, the breadcrumbs should not be
        # collapsible anyway, so it is not controlled by Stimulus
        soup = self.get_soup(rendered)
        breadcrumbs = soup.select_one(".w-breadcrumbs")
        self.assertIsNotNone(breadcrumbs)
        self.assertIsNone(breadcrumbs.get("data-controller"))

    def test_url_name(self):
        template = """
            {% load wagtailadmin_tags %}
            {% page_breadcrumbs page 'wagtailadmin_choose_page_child' %}
        """
        page = Page.objects.get(id=15)
        items = [
            {
                "label": "Root",
                "url": "/admin/choose-page/1/",
            },
            {
                "label": "Welcome to the Wagtail test site!",
                "url": "/admin/choose-page/2/",
            },
            {
                "label": "Events",
                "url": "/admin/choose-page/3/",
            },
            {
                "label": "Businessy events",
                "url": "/admin/choose-page/15/",
            },
        ]
        rendered = Template(template).render(
            Context({"page": page, "request": self.request})
        )
        self.assertBreadcrumbsItemsRendered(items, rendered)

    def test_not_include_self(self):
        template = """
            {% load wagtailadmin_tags %}
            {% page_breadcrumbs page 'wagtailadmin_explore' url_root_name='wagtailadmin_explore_root' include_self=False %}
        """
        page = Page.objects.get(id=15)
        items = [
            {"label": "Root", "url": "/admin/pages/"},
            {"label": "Welcome to the Wagtail test site!", "url": "/admin/pages/2/"},
            {"label": "Events", "url": "/admin/pages/3/"},
        ]
        rendered = Template(template).render(
            Context({"page": page, "request": self.request})
        )
        self.assertBreadcrumbsItemsRendered(items, rendered)

    def test_not_is_expanded(self):
        template = """
            {% load wagtailadmin_tags %}
            {% page_breadcrumbs page 'wagtailadmin_explore' url_root_name='wagtailadmin_explore_root' %}
        """
        page = Page.objects.get(id=15)
        items = [
            {"label": "Root", "url": "/admin/pages/"},
            {"label": "Welcome to the Wagtail test site!", "url": "/admin/pages/2/"},
            {"label": "Events", "url": "/admin/pages/3/"},
            {"label": "Businessy events", "url": "/admin/pages/15/"},
        ]
        rendered = Template(template).render(
            Context({"page": page, "request": self.request})
        )
        self.assertBreadcrumbsItemsRendered(items, rendered)
        # If is_expanded=False, the breadcrumbs should be collapsible via Stimulus
        soup = self.get_soup(rendered)
        breadcrumbs = soup.select_one(".w-breadcrumbs")
        self.assertIsNotNone(breadcrumbs)
        self.assertEqual(breadcrumbs.get("data-controller"), "w-breadcrumbs")

    def test_is_expanded(self):
        template = """
            {% load wagtailadmin_tags %}
            {% page_breadcrumbs page 'wagtailadmin_explore' url_root_name='wagtailadmin_explore_root' is_expanded=True %}
        """
        page = Page.objects.get(id=15)
        items = [
            {"label": "Root", "url": "/admin/pages/"},
            {"label": "Welcome to the Wagtail test site!", "url": "/admin/pages/2/"},
            {"label": "Events", "url": "/admin/pages/3/"},
            {"label": "Businessy events", "url": "/admin/pages/15/"},
        ]
        rendered = Template(template).render(
            Context({"page": page, "request": self.request})
        )
        self.assertBreadcrumbsItemsRendered(items, rendered)
        # If is_expanded=True, the breadcrumbs should not be collapsible, so it
        # is not controlled by Stimulus
        soup = self.get_soup(rendered)
        breadcrumbs = soup.select_one(".w-breadcrumbs")
        self.assertIsNotNone(breadcrumbs)
        self.assertIsNone(breadcrumbs.get("data-controller"))

    def test_querystring_value(self):
        template = """
            {% load wagtailadmin_tags %}
            {% page_breadcrumbs page 'wagtailadmin_explore' url_root_name='wagtailadmin_explore_root' querystring_value='?site=2&has_child_pages=true' %}
        """
        page = Page.objects.get(id=15)
        params = "?site=2&has_child_pages=true"
        items = [
            {"label": "Root", "url": f"/admin/pages/{params}"},
            {
                "label": "Welcome to the Wagtail test site!",
                "url": f"/admin/pages/2/{params}",
            },
            {"label": "Events", "url": f"/admin/pages/3/{params}"},
            {"label": "Businessy events", "url": f"/admin/pages/15/{params}"},
        ]
        rendered = Template(template).render(
            Context({"page": page, "request": self.request})
        )
        self.assertBreadcrumbsItemsRendered(items, rendered)

    def test_trailing_breadcrumb_title(self):
        template = """
            {% load wagtailadmin_tags %}
            {% page_breadcrumbs page 'wagtailadmin_explore' url_root_name='wagtailadmin_explore_root' trailing_breadcrumb_title='New: Simple Page' %}
        """
        page = Page.objects.get(id=15)
        items = [
            {"label": "Root", "url": "/admin/pages/"},
            {"label": "Welcome to the Wagtail test site!", "url": "/admin/pages/2/"},
            {"label": "Events", "url": "/admin/pages/3/"},
            {"label": "Businessy events", "url": "/admin/pages/15/"},
            {"label": "New: Simple Page"},
        ]
        rendered = Template(template).render(
            Context({"page": page, "request": self.request})
        )
        self.assertBreadcrumbsItemsRendered(items, rendered)

    def test_classname(self):
        template = """
            {% load wagtailadmin_tags %}
            {% page_breadcrumbs page 'wagtailadmin_choose_page_child' classname='my-class' %}
        """
        page = Page.objects.get(id=1)
        items = [{"label": "Root", "url": "/admin/choose-page/1/"}]
        rendered = Template(template).render(
            Context({"page": page, "request": self.request})
        )
        self.assertBreadcrumbsItemsRendered(items, rendered)

        soup = self.get_soup(rendered)
        div = soup.select_one("div.w-breadcrumbs")
        self.assertIsNotNone(div)
        self.assertIn("my-class", div["class"])

    def test_icon_name(self):
        template = """
            {% load wagtailadmin_tags %}
            {% page_breadcrumbs page 'wagtailadmin_explore' icon_name='site' %}
        """
        page = Page.objects.get(id=3)
        items = [
            {"label": "Root", "url": "/admin/pages/1/"},
            {"label": "Welcome to the Wagtail test site!", "url": "/admin/pages/2/"},
            {"label": "Events", "url": "/admin/pages/3/"},
        ]
        rendered = Template(template).render(
            Context({"page": page, "request": self.request})
        )
        self.assertBreadcrumbsItemsRendered(items, rendered)

        soup = self.get_soup(rendered)
        invalid_icons = soup.select("ol li:not(:last-child) svg use[href='#icon-site']")
        self.assertEqual(len(invalid_icons), 0)
        icon = soup.select_one("ol li:last-child svg use[href='#icon-site']")
        self.assertIsNotNone(icon)


class ThemeColorSchemeTest(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    def setUp(self):
        self.request = get_dummy_request()
        self.user = self.login()
        self.request.user = self.user
        self.profile = UserProfile.get_for_user(self.user)

    def test_default_mode(self):
        template = """
            {% load wagtailadmin_tags %}
            <meta name="color-scheme" content="{% admin_theme_color_scheme %}">
        """
        rendered = Template(template).render(Context({"request": self.request}))

        soup = self.get_soup(rendered)
        meta_tag = soup.find("meta", {"name": "color-scheme"})
        self.assertIsNotNone(meta_tag)
        self.assertEqual(meta_tag["content"], "dark light")

    def test_dark_mode(self):
        self.profile.theme = "dark"
        self.profile.save()

        template = """
            {% load wagtailadmin_tags %}
            <meta name="color-scheme" content="{% admin_theme_color_scheme %}">
        """
        rendered = Template(template).render(Context({"request": self.request}))

        soup = self.get_soup(rendered)
        meta_tag = soup.find("meta", {"name": "color-scheme"})
        self.assertIsNotNone(meta_tag)
        self.assertEqual(meta_tag["content"], "dark")

    def test_light_mode(self):
        self.profile.theme = "light"
        self.profile.save()

        template = """
            {% load wagtailadmin_tags %}
            <meta name="color-scheme" content="{% admin_theme_color_scheme %}">
        """
        rendered = Template(template).render(Context({"request": self.request}))

        soup = self.get_soup(rendered)
        meta_tag = soup.find("meta", {"name": "color-scheme"})
        self.assertIsNotNone(meta_tag)
        self.assertEqual(meta_tag["content"], "light")
