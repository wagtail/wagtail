from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.text import capfirst

from wagtail import hooks
from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.admin.panels import FieldPanel, ObjectList, TabbedInterface
from wagtail.contrib.settings.registry import SettingMenuItem
from wagtail.contrib.settings.views import get_setting_edit_handler
from wagtail.models import Page, Site
from wagtail.test.testapp.models import (
    FileSiteSetting,
    IconSiteSetting,
    PanelSiteSettings,
    TabbedSiteSettings,
    TestSiteSetting,
)
from wagtail.test.utils import WagtailTestUtils


class TestSiteSettingMenu(WagtailTestUtils, TestCase):
    def login_only_admin(self):
        """Log in with a user that only has permission to access the admin"""
        user = self.create_user(username="test", password="password")
        user.user_permissions.add(
            Permission.objects.get_by_natural_key(
                codename="access_admin", app_label="wagtailadmin", model="admin"
            )
        )
        self.login(username="test", password="password")
        return user

    def test_menu_item_in_admin(self):
        self.login()
        response = self.client.get(reverse("wagtailadmin_home"))

        self.assertContains(response, capfirst(TestSiteSetting._meta.verbose_name))
        self.assertContains(
            response, reverse("wagtailsettings:edit", args=("tests", "testsitesetting"))
        )

    def test_menu_item_no_permissions(self):
        self.login_only_admin()
        response = self.client.get(reverse("wagtailadmin_home"))

        self.assertNotContains(response, TestSiteSetting._meta.verbose_name)
        self.assertNotContains(
            response, reverse("wagtailsettings:edit", args=("tests", "testsitesetting"))
        )

    def test_menu_item_icon(self):
        menu_item = SettingMenuItem(IconSiteSetting, icon="tag", classname="test-class")
        self.assertEqual(menu_item.icon_name, "tag")
        self.assertEqual(menu_item.classname, "test-class")

    def test_menu_item_icon_fontawesome(self):
        menu_item = SettingMenuItem(
            IconSiteSetting, icon="fa-suitcase", classname="test-class"
        )
        self.assertEqual(menu_item.icon_name, "")
        self.assertEqual(
            set(menu_item.classname.split(" ")),
            {"icon", "icon-fa-suitcase", "test-class"},
        )


class BaseTestSiteSettingView(WagtailTestUtils, TestCase):
    def get(self, site_pk=1, params={}, setting=TestSiteSetting):
        url = self.edit_url(setting=setting, site_pk=site_pk)
        return self.client.get(url, params)

    def post(self, site_pk=1, post_data={}, setting=TestSiteSetting):
        url = self.edit_url(setting=setting, site_pk=site_pk)
        return self.client.post(url, post_data)

    def edit_url(self, setting, site_pk=1):
        args = [setting._meta.app_label, setting._meta.model_name, site_pk]
        return reverse("wagtailsettings:edit", args=args)


class TestSiteSettingCreateView(BaseTestSiteSettingView):
    def setUp(self):
        self.user = self.login()

    def test_get_edit(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)

    def test_edit_invalid(self):
        response = self.post(post_data={"foo": "bar"})
        self.assertContains(response, "The setting could not be saved due to errors.")
        self.assertContains(response, "error-message", count=2)
        self.assertContains(response, "This field is required", count=2)

    def test_edit(self):
        response = self.post(
            post_data={"title": "Edited site title", "email": "test@example.com"}
        )
        self.assertEqual(response.status_code, 302)

        default_site = Site.objects.get(is_default_site=True)
        setting = TestSiteSetting.objects.get(site=default_site)
        self.assertEqual(setting.title, "Edited site title")
        self.assertEqual(setting.email, "test@example.com")

        url_finder = AdminURLFinder(self.user)
        expected_url = "/admin/settings/tests/testsitesetting/%d/" % default_site.pk
        self.assertEqual(url_finder.get_edit_url(setting), expected_url)

    def test_file_upload_multipart(self):
        response = self.get(setting=FileSiteSetting)
        # Ensure the form supports file uploads
        self.assertContains(response, 'enctype="multipart/form-data"')


class TestSiteSettingEditView(BaseTestSiteSettingView):
    def setUp(self):
        default_site = Site.objects.get(is_default_site=True)

        self.test_setting = TestSiteSetting()
        self.test_setting.title = "Site title"
        self.test_setting.email = "initial@example.com"
        self.test_setting.site = default_site
        self.test_setting.save()

        self.login()

    def test_get_edit(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)

    def test_non_existant_model(self):
        response = self.client.get(
            reverse("wagtailsettings:edit", args=["test", "foo", 1])
        )
        self.assertEqual(response.status_code, 404)

    def test_edit_invalid(self):
        response = self.post(post_data={"foo": "bar"})
        self.assertContains(response, "The setting could not be saved due to errors.")
        self.assertContains(response, "error-message", count=2)
        self.assertContains(response, "This field is required", count=2)

    def test_edit(self):
        response = self.post(
            post_data={"title": "Edited site title", "email": "test@example.com"}
        )
        self.assertEqual(response.status_code, 302)

        default_site = Site.objects.get(is_default_site=True)
        setting = TestSiteSetting.objects.get(site=default_site)
        self.assertEqual(setting.title, "Edited site title")
        self.assertEqual(setting.email, "test@example.com")

    def test_get_redirect_to_relevant_instance(self):
        url = reverse("wagtailsettings:edit", args=("tests", "testsitesetting"))
        default_site = Site.objects.get(is_default_site=True)

        response = self.client.get(url)
        self.assertRedirects(
            response, status_code=302, expected_url=f"{url}{default_site.pk}/"
        )

    def test_get_redirect_to_relevant_instance_invalid(self):
        Site.objects.all().delete()
        url = reverse("wagtailsettings:edit", args=("tests", "testsitesetting"))
        response = self.client.get(url)
        self.assertRedirects(response, status_code=302, expected_url="/admin/")


@override_settings(
    ALLOWED_HOSTS=["testserver", "example.com", "noneoftheabove.example.com"]
)
class TestMultiSite(BaseTestSiteSettingView):
    def setUp(self):
        self.default_site = Site.objects.get(is_default_site=True)
        self.other_site = Site.objects.create(
            hostname="example.com", root_page=Page.objects.get(pk=2)
        )
        self.login()

    def test_redirect_to_default(self):
        """
        Should redirect to the setting for the default site.
        """
        start_url = reverse("wagtailsettings:edit", args=["tests", "testsitesetting"])
        dest_url = reverse(
            "wagtailsettings:edit",
            args=["tests", "testsitesetting", self.default_site.pk],
        )
        response = self.client.get(start_url, follow=True)
        self.assertRedirects(
            response, dest_url, status_code=302, fetch_redirect_response=False
        )

    def test_redirect_to_current(self):
        """
        Should redirect to the setting for the current site taken from the URL,
        by default
        """
        start_url = reverse("wagtailsettings:edit", args=["tests", "testsitesetting"])
        dest_url = reverse(
            "wagtailsettings:edit",
            args=["tests", "testsitesetting", self.other_site.pk],
        )
        response = self.client.get(
            start_url, follow=True, HTTP_HOST=self.other_site.hostname
        )
        self.assertRedirects(
            response, dest_url, status_code=302, fetch_redirect_response=False
        )

    def test_with_no_current_site(self):
        """
        Redirection should not break if the current request does not correspond to a site
        """
        self.default_site.is_default_site = False
        self.default_site.save()

        start_url = reverse("wagtailsettings:edit", args=["tests", "testsitesetting"])
        response = self.client.get(
            start_url, follow=True, HTTP_HOST="noneoftheabove.example.com"
        )
        self.assertEqual(302, response.redirect_chain[0][1])

    def test_switcher(self):
        """Check that the switcher form exists in the page"""
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="settings-site-switch"')

    def test_unknown_site(self):
        """Check that unknown sites throw a 404"""
        response = self.get(site_pk=3)
        self.assertEqual(response.status_code, 404)

    def test_edit(self):
        """
        Check that editing settings in multi-site mode edits the correct
        setting, and leaves the other ones alone
        """
        TestSiteSetting.objects.create(
            title="default", email="default@example.com", site=self.default_site
        )
        TestSiteSetting.objects.create(
            title="other", email="other@example.com", site=self.other_site
        )
        response = self.post(
            site_pk=self.other_site.pk,
            post_data={"title": "other-new", "email": "other-other@example.com"},
        )
        self.assertEqual(response.status_code, 302)

        # Check that the correct setting was updated
        other_setting = TestSiteSetting.for_site(self.other_site)
        self.assertEqual(other_setting.title, "other-new")
        self.assertEqual(other_setting.email, "other-other@example.com")

        # Check that the other setting was not updated
        default_setting = TestSiteSetting.for_site(self.default_site)
        self.assertEqual(default_setting.title, "default")
        self.assertEqual(default_setting.email, "default@example.com")


class TestAdminPermission(WagtailTestUtils, TestCase):
    def test_registered_permission(self):
        permission = Permission.objects.get_by_natural_key(
            app_label="tests",
            model="testsitesetting",
            codename="change_testsitesetting",
        )
        for fn in hooks.get_hooks("register_permissions"):
            if permission in fn():
                break
        else:
            self.fail("Change permission for tests.TestSiteSetting not registered")


class TestEditHandlers(TestCase):
    def setUp(self):
        get_setting_edit_handler.cache_clear()

    def test_default_model_introspection(self):
        handler = get_setting_edit_handler(TestSiteSetting)
        self.assertIsInstance(handler, ObjectList)
        self.assertEqual(len(handler.children), 2)
        first = handler.children[0]
        self.assertIsInstance(first, FieldPanel)
        self.assertEqual(first.field_name, "title")
        second = handler.children[1]
        self.assertIsInstance(second, FieldPanel)
        self.assertEqual(second.field_name, "email")

    def test_with_custom_panels(self):
        handler = get_setting_edit_handler(PanelSiteSettings)
        self.assertIsInstance(handler, ObjectList)
        self.assertEqual(len(handler.children), 1)
        first = handler.children[0]
        self.assertIsInstance(first, FieldPanel)
        self.assertEqual(first.field_name, "title")

    def test_with_custom_edit_handler(self):
        handler = get_setting_edit_handler(TabbedSiteSettings)
        self.assertIsInstance(handler, TabbedInterface)
        self.assertEqual(len(handler.children), 2)
