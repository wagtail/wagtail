from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages import get_messages
from django.contrib.messages.constants import ERROR
from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail import hooks
from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.models import Locale, Page
from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.template_tests import AdminTemplateTestUtils


class TestLocaleIndexView(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_test_user()
        cls.add_url = reverse("wagtaillocales:add")

    def setUp(self):
        self.login(user=self.user)

    def get(self, params={}):
        return self.client.get(reverse("wagtaillocales:index"), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/index.html")
        self.assertBreadcrumbsItemsRendered(
            [{"url": "", "label": "Locales"}],
            response.content,
        )
        self.assertContains(response, self.add_url)

    @override_settings(WAGTAIL_CONTENT_LANGUAGES=[("en", "English")])
    def test_index_view_doesnt_show_add_locale_button_if_all_locales_created(self):
        self.assertNotContains(self.get(), self.add_url)

    @override_settings(WAGTAIL_CONTENT_LANGUAGES=[("en", "English"), ("fr", "French")])
    def test_index_view_shows_add_locale_button_with_stale_locales(self):
        Locale.objects.create(language_code="de")
        self.assertContains(self.get(), self.add_url)


class TestLocaleCreateView(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()
        self.english = Locale.objects.get()

    def get(self, params={}):
        return self.client.get(reverse("wagtaillocales:add"), params)

    def post(self, post_data={}):
        return self.client.post(reverse("wagtaillocales:add"), post_data)

    def test_default_language(self):
        # we should have loaded with a single locale
        self.assertEqual(self.english.language_code, "en")
        self.assertEqual(self.english.get_display_name(), "English")

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaillocales/create.html")
        self.assertBreadcrumbsItemsRendered(
            [
                {"label": "Locales", "url": "/admin/locales/"},
                {"label": "New: Locale", "url": ""},
            ],
            response.content,
        )

        self.assertEqual(
            response.context["form"].fields["language_code"].choices, [("fr", "French")]
        )

    def test_create(self):
        response = self.post(
            {
                "language_code": "fr",
            }
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtaillocales:index"))

        # Check that the locale was created
        self.assertTrue(Locale.objects.filter(language_code="fr").exists())

    def test_duplicate_not_allowed(self):
        response = self.post(
            {
                "language_code": "en",
            }
        )

        # Should return the form with errors
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "language_code",
            ["Select a valid choice. en is not one of the available choices."],
        )

    def test_language_code_must_be_in_settings(self):
        response = self.post(
            {
                "language_code": "ja",
            }
        )

        # Should return the form with errors
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "language_code",
            ["Select a valid choice. ja is not one of the available choices."],
        )

    @override_settings(WAGTAIL_CONTENT_LANGUAGES=[("en", "English")])
    def test_create_view_no_access_if_all_locales_created(self):
        response = self.get()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.context["message"],
            "Sorry, you do not have permission to access this area.",
        )

    @override_settings(WAGTAIL_CONTENT_LANGUAGES=[("en", "English"), ("fr", "French")])
    def test_create_view_can_access_with_stale_locales(self):
        Locale.objects.create(language_code="de")
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaillocales/create.html")


class TestLocaleEditView(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()
        self.english = Locale.objects.get()

    def get(self, params=None, locale=None):
        locale = locale or self.english
        return self.client.get(
            reverse("wagtaillocales:edit", args=[locale.id]), params or {}
        )

    def post(self, post_data=None, locale=None):
        post_data = post_data or {}
        locale = locale or self.english
        post_data.setdefault("language_code", locale.language_code)
        return self.client.post(
            reverse("wagtaillocales:edit", args=[locale.id]), post_data
        )

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaillocales/edit.html")
        self.assertBreadcrumbsItemsRendered(
            [
                {"url": "/admin/locales/", "label": "Locales"},
                {"url": "", "label": str(self.english)},
            ],
            response.content,
        )

        self.assertEqual(
            response.context["form"].fields["language_code"].choices,
            [
                (
                    "en",
                    "English",
                ),  # Note: Current value is displayed even though it's in use
                ("fr", "French"),
            ],
        )

        url_finder = AdminURLFinder(self.user)
        expected_url = "/admin/locales/edit/%d/" % self.english.id
        self.assertEqual(url_finder.get_edit_url(self.english), expected_url)

    def test_invalid_language(self):
        invalid = Locale.objects.create(language_code="foo")

        response = self.get(locale=invalid)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtaillocales/edit.html")

        self.assertEqual(
            response.context["form"].fields["language_code"].choices,
            [
                (
                    None,
                    "Select a new language",
                ),  # This is shown instead of the current value if invalid
                ("fr", "French"),
            ],
        )

    def test_edit(self):
        response = self.post(
            {
                "language_code": "fr",
            }
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtaillocales:index"))

        # Check that the locale was edited
        self.english.refresh_from_db()
        self.assertEqual(self.english.language_code, "fr")

    def test_edit_duplicate_not_allowed(self):
        french = Locale.objects.create(language_code="fr")

        response = self.post(
            {
                "language_code": "en",
            },
            locale=french,
        )

        # Should return the form with errors
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "language_code",
            ["Select a valid choice. en is not one of the available choices."],
        )

    def test_edit_language_code_must_be_in_settings(self):
        response = self.post(
            {
                "language_code": "ja",
            }
        )

        # Should return the form with errors
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "language_code",
            ["Select a valid choice. ja is not one of the available choices."],
        )


class TestLocaleDeleteView(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()
        self.english = Locale.objects.get()

    def get(self, params={}, locale=None):
        locale = locale or self.english
        return self.client.get(
            reverse("wagtaillocales:delete", args=[locale.id]), params
        )

    def post(self, post_data={}, locale=None):
        locale = locale or self.english
        return self.client.post(
            reverse("wagtaillocales:delete", args=[locale.id]), post_data
        )

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/confirm_delete.html")
        self.assertBreadcrumbsNotRendered(response.content)

    def test_delete_locale(self):
        french = Locale.objects.create(language_code="fr")

        response = self.post(locale=french)

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtaillocales:index"))

        # Check that the locale was deleted
        self.assertFalse(Locale.objects.filter(language_code="fr").exists())

    def test_cannot_delete_locales_with_pages(self):
        # create a French locale so that the deletion is not rejected on grounds of being the only
        # existing locale
        Locale.objects.create(language_code="fr")

        response = self.post()

        self.assertEqual(response.status_code, 200)

        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(messages[0].level, ERROR)
        self.assertEqual(
            messages[0].message,
            "This locale cannot be deleted because there are pages and/or other objects using it.\n\n\n\n\n",
        )

        # Check that the locale was not deleted
        self.assertTrue(Locale.objects.filter(language_code="en").exists())

    @override_settings(
        LANGUAGE_CODE="de-at",
        WAGTAIL_CONTENT_LANGUAGES=[
            ("en", "English"),
            ("fr", "French"),
            ("de", "German"),
            ("pl", "Polish"),
            ("ja", "Japanese"),
        ],
    )
    def test_can_delete_default_locale(self):
        # The presence of the locale on the root page node (if that's the only thing using the
        # locale) should not prevent deleting it

        for lang in ("fr", "de", "pl", "ja"):
            Locale.objects.create(language_code=lang)

        self.assertEqual(Page.get_first_root_node().locale.language_code, "en")
        Page.objects.filter(depth__gt=1).delete()
        response = self.post()

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtaillocales:index"))

        # Check that the locale was deleted
        self.assertFalse(Locale.objects.filter(language_code="en").exists())

        # root node's locale should now have been reassigned to the one matching the current
        # LANGUAGE_CODE
        self.assertEqual(Page.get_first_root_node().locale.language_code, "de")

    @override_settings(
        LANGUAGE_CODE="de-at",
        WAGTAIL_CONTENT_LANGUAGES=[
            ("en", "English"),
            ("fr", "French"),
            ("de", "German"),
            ("pl", "Polish"),
            ("ja", "Japanese"),
        ],
    )
    def test_can_delete_default_locale_when_language_code_has_no_locale(self):
        Locale.objects.create(language_code="fr")

        self.assertEqual(Page.get_first_root_node().locale.language_code, "en")
        Page.objects.filter(depth__gt=1).delete()
        response = self.post()

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtaillocales:index"))

        # Check that the locale was deleted
        self.assertFalse(Locale.objects.filter(language_code="en").exists())

        # root node's locale should now have been reassigned to 'fr' despite that not matching
        # LANGUAGE_CODE (because it's the only remaining Locale record)
        self.assertEqual(Page.get_first_root_node().locale.language_code, "fr")

    def test_cannot_delete_last_remaining_locale(self):
        Page.objects.filter(depth__gt=1).delete()

        response = self.post()

        self.assertEqual(response.status_code, 200)

        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(messages[0].level, ERROR)
        self.assertEqual(
            messages[0].message,
            "This locale cannot be deleted because there are no other locales.\n\n\n\n\n",
        )

        # Check that the locale was not deleted
        self.assertTrue(Locale.objects.filter(language_code="en").exists())


class TestAdminPermissions(WagtailTestUtils, TestCase):
    def test_registered_permissions(self):
        locale_ct = ContentType.objects.get_for_model(Locale)
        qs = Permission.objects.none()
        for fn in hooks.get_hooks("register_permissions"):
            qs |= fn()
        registered_permissions = qs.filter(content_type=locale_ct)
        self.assertEqual(
            set(registered_permissions.values_list("codename", flat=True)),
            {"add_locale", "change_locale", "delete_locale"},
        )
