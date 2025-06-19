from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse
from django.utils.text import capfirst

from wagtail import hooks
from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.admin.panels import FieldPanel, ObjectList, TabbedInterface
from wagtail.contrib.settings.registry import SettingMenuItem
from wagtail.contrib.settings.views import get_setting_edit_handler
from wagtail.test.testapp.models import (
    FileGenericSetting,
    IconGenericSetting,
    PanelGenericSettings,
    TabbedGenericSettings,
    TestGenericSetting,
    TestPermissionedGenericSetting,
)
from wagtail.test.utils import WagtailTestUtils


class TestGenericSettingMenu(WagtailTestUtils, TestCase):
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

        self.assertContains(response, capfirst(TestGenericSetting._meta.verbose_name))
        self.assertContains(
            response,
            reverse("wagtailsettings:edit", args=("tests", "testgenericsetting")),
        )

    def test_menu_item_no_permissions(self):
        self.login_only_admin()
        response = self.client.get(reverse("wagtailadmin_home"))

        self.assertNotContains(response, TestGenericSetting._meta.verbose_name)
        self.assertNotContains(
            response,
            reverse("wagtailsettings:edit", args=("tests", "testgenericsetting")),
        )

    def test_menu_item_icon(self):
        menu_item = SettingMenuItem(
            IconGenericSetting, icon="tag", classname="test-class"
        )
        self.assertEqual(menu_item.icon_name, "tag")
        self.assertEqual(menu_item.classname, "test-class")


class BaseTestGenericSettingView(WagtailTestUtils, TestCase):
    def get(self, params={}, setting=TestGenericSetting):
        url = self.edit_url(setting=setting)
        return self.client.get(url, params)

    def post(self, post_data={}, setting=TestGenericSetting):
        url = self.edit_url(setting=setting)
        return self.client.post(url, post_data)

    def edit_url(self, setting):
        pk = setting._get_or_create().pk
        args = [setting._meta.app_label, setting._meta.model_name, pk]
        return reverse("wagtailsettings:edit", args=args)


class TestGenericSettingCreateView(BaseTestGenericSettingView):
    def setUp(self):
        self.user = self.login()

    def test_get_edit(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)

    def test_edit_invalid(self):
        response = self.post(post_data={"foo": "bar"})
        self.assertContains(response, "The setting could not be saved due to errors.")
        self.assertContains(response, "This field is required", count=2)

    def test_edit(self):
        response = self.post(
            post_data={
                "title": "Edited setting title",
                "email": "edited.email@example.com",
            }
        )
        self.assertEqual(response.status_code, 302)

        setting = TestGenericSetting.objects.first()
        self.assertEqual(setting.title, "Edited setting title")

        url_finder = AdminURLFinder(self.user)
        expected_url = "/admin/settings/tests/testgenericsetting/%d/" % setting.pk
        self.assertEqual(url_finder.get_edit_url(setting), expected_url)

    def test_file_upload_multipart(self):
        response = self.get(setting=FileGenericSetting)
        # Ensure the form supports file uploads
        self.assertContains(response, 'enctype="multipart/form-data"')

    def test_create_restricted_field_without_any_permission(self):
        # User has no permissions over the setting model, only access to the admin
        self.user.is_superuser = False
        self.user.save()
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            ),
        )

        self.assertFalse(TestPermissionedGenericSetting.objects.exists())
        # GET should redirect away with permission denied
        response = self.get(setting=TestPermissionedGenericSetting)
        self.assertRedirects(response, status_code=302, expected_url="/admin/")

        # the GET might create a setting object, depending on when the permission check is done,
        # so remove any created objects prior to testing the POST
        TestPermissionedGenericSetting.objects.all().delete()

        # POST should redirect away with permission denied
        response = self.post(
            post_data={"sensitive_email": "test@example.com", "title": "test"},
            setting=TestPermissionedGenericSetting,
        )
        self.assertRedirects(response, status_code=302, expected_url="/admin/")

        # The retrieved setting should contain none of the submitted data
        setting = TestPermissionedGenericSetting.load()
        self.assertEqual(setting.title, "")
        self.assertEqual(setting.sensitive_email, "")

    def test_create_restricted_field_without_field_permission(self):
        # User has edit permission over the setting model, but not the sensitive_email field
        self.user.is_superuser = False
        self.user.save()
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            ),
            Permission.objects.get(
                content_type__app_label="tests",
                codename="change_testpermissionedgenericsetting",
            ),
        )

        self.assertFalse(TestPermissionedGenericSetting.objects.exists())
        # GET should provide a form with title but not sensitive_email
        response = self.get(setting=TestPermissionedGenericSetting)
        self.assertEqual(response.status_code, 200)
        self.assertIn("title", list(response.context["form"].fields))
        self.assertNotIn("sensitive_email", list(response.context["form"].fields))

        # the GET creates a setting object, so remove any created objects prior to testing the POST
        TestPermissionedGenericSetting.objects.all().delete()

        # POST should allow the title to be set, but not the sensitive_email
        response = self.post(
            post_data={"sensitive_email": "test@example.com", "title": "test"},
            setting=TestPermissionedGenericSetting,
        )
        self.assertEqual(response.status_code, 302)

        settings = TestPermissionedGenericSetting.objects.get()
        self.assertEqual(settings.title, "test")
        self.assertEqual(settings.sensitive_email, "")

    def test_create_restricted_field(self):
        # User has edit permission over the setting model, including the sensitive_email field
        self.user.is_superuser = False
        self.user.save()
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            ),
            Permission.objects.get(
                content_type__app_label="tests",
                codename="change_testpermissionedgenericsetting",
            ),
            Permission.objects.get(codename="can_edit_sensitive_email_generic_setting"),
        )

        self.assertFalse(TestPermissionedGenericSetting.objects.exists())
        # GET should provide a form with title and sensitive_email
        response = self.get(setting=TestPermissionedGenericSetting)
        self.assertEqual(response.status_code, 200)
        self.assertIn("title", list(response.context["form"].fields))
        self.assertIn("sensitive_email", list(response.context["form"].fields))

        # the GET creates a setting object, so remove any created objects prior to testing the POST
        TestPermissionedGenericSetting.objects.all().delete()

        # POST should allow both title and sensitive_email to be set
        self.assertFalse(TestPermissionedGenericSetting.objects.exists())
        response = self.post(
            post_data={"sensitive_email": "test@example.com", "title": "test"},
            setting=TestPermissionedGenericSetting,
        )
        self.assertEqual(response.status_code, 302)

        settings = TestPermissionedGenericSetting.objects.get()
        self.assertEqual(settings.title, "test")
        self.assertEqual(settings.sensitive_email, "test@example.com")


class TestGenericSettingEditView(BaseTestGenericSettingView):
    def setUp(self):
        self.test_setting = TestGenericSetting()
        self.test_setting.title = "Setting title"
        self.test_setting.save()

        self.user = self.login()

    def test_get_edit(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)

    def test_non_existent_model(self):
        response = self.client.get(
            reverse("wagtailsettings:edit", args=["test", "foo", 1])
        )
        self.assertEqual(response.status_code, 404)

    def test_register_with_icon(self):
        edit_url = reverse("wagtailsettings:edit", args=("tests", "IconGenericSetting"))
        edit_response = self.client.get(edit_url, follow=True)
        soup = self.get_soup(edit_response.content)
        self.assertIsNotNone(soup.select_one("h2 svg use[href='#icon-tag']"))

    def test_edit_invalid(self):
        response = self.post(post_data={"foo": "bar"})
        self.assertContains(response, "The setting could not be saved due to errors.")
        self.assertContains(response, "This field is required", count=2)

    def test_edit(self):
        response = self.post(
            post_data={
                "title": "Edited setting title",
                "email": "different.email@example.com",
            }
        )
        self.assertEqual(response.status_code, 302)

        setting = TestGenericSetting.objects.first()
        self.assertEqual(setting.title, "Edited setting title")

    def test_for_request(self):
        url = reverse("wagtailsettings:edit", args=("tests", "testgenericsetting"))

        response = self.client.get(url)
        self.assertRedirects(
            response,
            status_code=302,
            expected_url=f"{url}{TestGenericSetting.objects.first().pk}/",
        )

    def test_edit_restricted_field(self):
        # User has edit permission over the setting model, including the sensitive_email field
        test_setting = TestPermissionedGenericSetting()
        test_setting.sensitive_email = "test@example.com"
        test_setting.title = "Old title"
        test_setting.save()
        self.user.is_superuser = False
        self.user.save()

        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            ),
            Permission.objects.get(
                content_type__app_label="tests",
                codename="change_testpermissionedgenericsetting",
            ),
            Permission.objects.get(codename="can_edit_sensitive_email_generic_setting"),
        )

        # GET should provide a form with title and sensitive_email
        response = self.get(setting=TestPermissionedGenericSetting)
        self.assertEqual(response.status_code, 200)
        self.assertIn("title", list(response.context["form"].fields))
        self.assertIn("sensitive_email", list(response.context["form"].fields))

        # POST should allow both title and sensitive_email to be set
        response = self.post(
            setting=TestPermissionedGenericSetting,
            post_data={
                "sensitive_email": "test-updated@example.com",
                "title": "New title",
            },
        )
        self.assertEqual(response.status_code, 302)

        test_setting.refresh_from_db()
        self.assertEqual(test_setting.sensitive_email, "test-updated@example.com")
        self.assertEqual(test_setting.title, "New title")

    def test_edit_restricted_field_without_field_permission(self):
        # User has edit permission over the setting model, but not the sensitive_email field
        test_setting = TestPermissionedGenericSetting()
        test_setting.sensitive_email = "test@example.com"
        test_setting.title = "Old title"
        test_setting.save()
        self.user.is_superuser = False
        self.user.save()
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            ),
            Permission.objects.get(
                content_type__app_label="tests",
                codename="change_testpermissionedgenericsetting",
            ),
        )

        # GET should provide a form with title but not sensitive_email
        response = self.get(setting=TestPermissionedGenericSetting)
        self.assertEqual(response.status_code, 200)
        self.assertIn("title", list(response.context["form"].fields))
        self.assertNotIn("sensitive_email", list(response.context["form"].fields))

        # POST should allow the title to be set, but not the sensitive_email
        response = self.post(
            setting=TestPermissionedGenericSetting,
            post_data={
                "sensitive_email": "test-updated@example.com",
                "title": "New title",
            },
        )
        self.assertEqual(response.status_code, 302)

        test_setting.refresh_from_db()
        self.assertEqual(test_setting.sensitive_email, "test@example.com")
        self.assertEqual(test_setting.title, "New title")

    def test_edit_restricted_field_without_any_permission(self):
        # User has no permissions over the setting model, only access to the admin
        test_setting = TestPermissionedGenericSetting()
        test_setting.sensitive_email = "test@example.com"
        test_setting.title = "Old title"
        test_setting.save()
        self.user.is_superuser = False
        self.user.save()
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            ),
        )

        # GET should redirect away with permission denied
        response = self.get(setting=TestPermissionedGenericSetting)
        self.assertRedirects(response, status_code=302, expected_url="/admin/")

        # POST should redirect away with permission denied
        response = self.post(
            setting=TestPermissionedGenericSetting,
            post_data={
                "sensitive_email": "test-updated@example.com",
                "title": "new title",
            },
        )
        self.assertRedirects(response, status_code=302, expected_url="/admin/")

        # The retrieved setting should be unchanged
        test_setting.refresh_from_db()
        self.assertEqual(test_setting.sensitive_email, "test@example.com")
        self.assertEqual(test_setting.title, "Old title")


class TestAdminPermission(WagtailTestUtils, TestCase):
    def test_registered_permission(self):
        permission = Permission.objects.get_by_natural_key(
            app_label="tests",
            model="testgenericsetting",
            codename="change_testgenericsetting",
        )
        for fn in hooks.get_hooks("register_permissions"):
            if permission in fn():
                break
        else:
            self.fail("Change permission for tests.TestGenericSetting not registered")


class TestEditHandlers(TestCase):
    def setUp(self):
        get_setting_edit_handler.cache_clear()

    def test_default_model_introspection(self):
        handler = get_setting_edit_handler(TestGenericSetting)
        self.assertIsInstance(handler, ObjectList)
        self.assertEqual(len(handler.children), 2)
        first = handler.children[0]
        self.assertIsInstance(first, FieldPanel)
        self.assertEqual(first.field_name, "title")
        second = handler.children[1]
        self.assertIsInstance(second, FieldPanel)
        self.assertEqual(second.field_name, "email")

    def test_with_custom_panels(self):
        handler = get_setting_edit_handler(PanelGenericSettings)
        self.assertIsInstance(handler, ObjectList)
        self.assertEqual(len(handler.children), 1)
        first = handler.children[0]
        self.assertIsInstance(first, FieldPanel)
        self.assertEqual(first.field_name, "title")

    def test_with_custom_edit_handler(self):
        handler = get_setting_edit_handler(TabbedGenericSettings)
        self.assertIsInstance(handler, TabbedInterface)
        self.assertEqual(len(handler.children), 2)


class TestPermissionConfiguration(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()
        self.group = Group.objects.get(name="Editors")

    def test_get_permissions(self):
        # Generic settings should not get their own section in the group permissions UI
        response = self.client.get(
            reverse("wagtailusers_groups:edit", args=(self.group.id,)),
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Test generic setting permissions")
