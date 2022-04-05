import json
from datetime import timedelta
from unittest import mock

from django.conf import settings
from django.template import Context, Template
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
)
from wagtail.admin.templatetags.wagtailadmin_tags import locales as locales_tag
from wagtail.admin.templatetags.wagtailadmin_tags import (
    notification_static,
    timesince_last_update,
    timesince_simple,
)
from wagtail.admin.ui.components import Component
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Locale
from wagtail.test.utils import WagtailTestUtils
from wagtail.users.models import UserProfile


class TestAvatarTemplateTag(TestCase, WagtailTestUtils):
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
        self.assertEqual(ts, "Just now")

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
        timesince = timesince_last_update(dt, time_prefix="my prefix")
        self.assertEqual(timesince, "my prefix {}".format(formatted_time))

        # Check user output
        timesince = timesince_last_update(dt, user_display_name="Gary")
        self.assertEqual(timesince, "{} by Gary".format(formatted_time))

        # Check user and prefix output
        timesince = timesince_last_update(
            dt, time_prefix="my prefix", user_display_name="Gary"
        )
        self.assertEqual(timesince, "my prefix {} by Gary".format(formatted_time))

    def test_timesince_last_update_before_today_shows_timeago(self):
        dt = timezone.now() - timedelta(weeks=1, days=2)

        timesince = timesince_last_update(dt, use_shorthand=False)
        self.assertEqual(timesince, "1\xa0week, 2\xa0days ago")

        timesince = timesince_last_update(dt)
        self.assertEqual(timesince, "1\xa0week ago")


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
