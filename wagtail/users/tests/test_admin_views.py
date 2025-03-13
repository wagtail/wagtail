import unittest.mock

from django import forms
from django.apps import apps
from django.conf import settings
from django.contrib.admin.utils import quote
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.template import RequestContext, Template
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.text import capfirst

from wagtail import hooks
from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.admin.models import Admin
from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.widgets.button import ButtonWithDropdown
from wagtail.compat import AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME
from wagtail.coreutils import get_dummy_request
from wagtail.log_actions import log
from wagtail.models import (
    Collection,
    DraftStateMixin,
    GroupCollectionPermission,
    GroupPagePermission,
    LockableMixin,
    Page,
)
from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.template_tests import AdminTemplateTestUtils
from wagtail.users.forms import GroupForm, UserCreationForm, UserEditForm
from wagtail.users.models import UserProfile
from wagtail.users.permission_order import register as register_permission_order
from wagtail.users.views.groups import GroupViewSet
from wagtail.users.views.users import (
    UserViewSet,
    get_user_creation_form,
    get_user_edit_form,
)
from wagtail.users.wagtail_hooks import get_viewset_cls
from wagtail.users.widgets import UserListingButton
from wagtail.utils.deprecation import RemovedInWagtail70Warning

add_user_perm_codename = f"add_{AUTH_USER_MODEL_NAME.lower()}"
delete_user_perm_codename = f"delete_{AUTH_USER_MODEL_NAME.lower()}"
change_user_perm_codename = f"change_{AUTH_USER_MODEL_NAME.lower()}"

User = get_user_model()


def test_avatar_provider(user, default, size=50):
    return "/nonexistent/path/to/avatar.png"


class CustomGroupForm(GroupForm):
    pass


class CustomUserCreationForm(UserCreationForm):
    country = forms.CharField(required=True, label="Country")
    attachment = forms.FileField(required=True, label="Attachment")


class CustomUserEditForm(UserEditForm):
    country = forms.CharField(required=True, label="Country")
    attachment = forms.FileField(required=True, label="Attachment")


class CustomGroupViewSet(GroupViewSet):
    icon = "custom-icon"

    def get_form_class(self, for_update=False):
        return CustomGroupForm


class CustomUserViewSet(UserViewSet):
    icon = "custom-icon"

    def get_form_class(self, for_update=False):
        if for_update:
            return CustomUserEditForm
        return CustomUserCreationForm


class TestUserFormHelpers(TestCase):
    def test_get_user_edit_form_with_default_form(self):
        user_form = get_user_edit_form()
        self.assertIs(user_form, UserEditForm)

    def test_get_user_creation_form_with_default_form(self):
        user_form = get_user_creation_form()
        self.assertIs(user_form, UserCreationForm)

    @override_settings(
        WAGTAIL_USER_CREATION_FORM="wagtail.users.tests.CustomUserCreationForm"
    )
    def test_get_user_creation_form_with_custom_form(self):
        with self.assertWarnsMessage(
            RemovedInWagtail70Warning,
            "The `WAGTAIL_USER_CREATION_FORM` setting is deprecated. Use a custom "
            "`UserViewSet` subclass and override `get_form_class()` instead.",
        ):
            user_form = get_user_creation_form()
        self.assertIs(user_form, CustomUserCreationForm)

    @override_settings(WAGTAIL_USER_EDIT_FORM="wagtail.users.tests.CustomUserEditForm")
    def test_get_user_edit_form_with_custom_form(self):
        with self.assertWarnsMessage(
            RemovedInWagtail70Warning,
            "The `WAGTAIL_USER_EDIT_FORM` setting is deprecated. Use a custom "
            "`UserViewSet` subclass and override `get_form_class()` instead.",
        ):
            user_form = get_user_edit_form()
        self.assertIs(user_form, CustomUserEditForm)

    @override_settings(
        WAGTAIL_USER_CREATION_FORM="wagtail.users.tests.CustomUserCreationFormDoesNotExist"
    )
    def test_get_user_creation_form_with_invalid_form(self):
        with self.assertWarnsMessage(
            RemovedInWagtail70Warning,
            "The `WAGTAIL_USER_CREATION_FORM` setting is deprecated. Use a custom "
            "`UserViewSet` subclass and override `get_form_class()` instead.",
        ):
            self.assertRaises(ImproperlyConfigured, get_user_creation_form)

    @override_settings(
        WAGTAIL_USER_EDIT_FORM="wagtail.users.tests.CustomUserEditFormDoesNotExist"
    )
    def test_get_user_edit_form_with_invalid_form(self):
        with self.assertWarnsMessage(
            RemovedInWagtail70Warning,
            "The `WAGTAIL_USER_EDIT_FORM` setting is deprecated. Use a custom "
            "`UserViewSet` subclass and override `get_form_class()` instead.",
        ):
            self.assertRaises(ImproperlyConfigured, get_user_edit_form)


class TestGroupUsersView(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    def setUp(self):
        # create a user that should be visible in the listing
        self.test_user = self.create_user(
            username="testuser",
            email="testuser@email.com",
            password="password",
            first_name="First Name",
            last_name="Last Name",
        )
        self.test_group = Group.objects.create(name="Test Group")
        self.test_user.groups.add(self.test_group)
        self.login()

    def get(self, params={}, group_id=None):
        return self.client.get(
            reverse(
                "wagtailusers_groups:users", args=(group_id or self.test_group.pk,)
            ),
            params,
        )

    def test_simple(self):
        with self.assertWarnsMessage(
            RemovedInWagtail70Warning,
            "Accessing the list of users in a group via "
            f"/admin/groups/{self.test_group.pk}/users/ is deprecated, use "
            f"/admin/users/?group={self.test_group.pk} instead.",
        ):
            response = self.get()

        self.assertRedirects(
            response,
            reverse("wagtailusers_users:index") + f"?group={self.test_group.pk}",
        )

    def test_inexisting_group(self):
        response = self.get(group_id=9999)
        self.assertEqual(response.status_code, 404)


class TestUserIndexView(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    def setUp(self):
        # create a user that should be visible in the listing
        self.test_user = self.create_user(
            username="testuser",
            email="testuser@email.com",
            password="password",
            first_name="First Name",
            last_name="Last Name",
        )
        self.user = self.login()

    def get(self, params={}):
        return self.client.get(reverse("wagtailusers_users:index"), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailusers/users/index.html")
        self.assertContains(response, "testuser")
        # response should contain page furniture, including the "Add a user" button
        self.assertContains(response, "Add a user")
        self.assertBreadcrumbsItemsRendered(
            [{"url": "", "label": "Users"}],
            response.content,
        )

    @unittest.skipIf(
        settings.AUTH_USER_MODEL == "emailuser.EmailUser", "Negative UUID not possible"
    )
    def test_allows_negative_ids(self):
        # see https://github.com/wagtail/wagtail/issues/565
        self.create_user("guardian", "guardian@example.com", "gu@rd14n", pk=-1)
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "testuser")
        self.assertContains(response, "guardian")

    def test_search(self):
        response = self.get({"q": "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["query_string"], "Hello")
        soup = self.get_soup(response.content)
        filter_options = soup.select(".filter-options a")
        self.assertIn(
            ("Users", reverse("wagtailusers_users:index") + "?q=Hello"),
            [(a.text.strip(), a.get("href")) for a in filter_options],
        )

    def test_search_query_one_field(self):
        response = self.get({"q": "first name"})
        self.assertEqual(response.status_code, 200)
        results = response.context["users"]
        self.assertIn(self.test_user, results)

    def test_search_query_multiple_fields(self):
        response = self.get({"q": "first name last name"})
        self.assertEqual(response.status_code, 200)
        results = response.context["users"]
        self.assertIn(self.test_user, results)

    def test_pagination(self):
        pages = ["0", "1", "-1", "9999", "Not a page"]
        for page in pages:
            response = self.get({"p": page})
            self.assertEqual(response.status_code, 200)

    def test_ordering(self):
        # checking that only valid ordering used, in case of `IndexView` the valid
        # ordering fields are:
        # - `name`: maps to `User.last_name` and `User.first_name` fields if available
        # - `User.USERNAME_FIELD`: dynamically maps to User.USERNAME_FIELD
        # - `is_superuser`: maps to User.is_superuser (from PermissionsMixin)
        # - `is_active`: maps to User.is_active if available
        # - `last_login`: maps to User.last_login (from AbstractBaseUser)
        cases = {
            "name": ("last_name", "first_name"),
            "-name": ("-last_name", "-first_name"),
            User.USERNAME_FIELD: (User.USERNAME_FIELD,),
            f"-{User.USERNAME_FIELD}": (f"-{User.USERNAME_FIELD}",),
            "is_superuser": ("is_superuser",),
            "-is_superuser": ("-is_superuser",),
            "is_active": ("is_active",),
            "-is_active": ("-is_active",),
            "last_login": ("last_login",),
            "-last_login": ("-last_login",),
        }
        for param, order_by in cases.items():
            with self.subTest(param=param):
                response = self.get({"ordering": param})
                self.assertEqual(
                    response.context_data["object_list"].query.order_by,
                    order_by,
                )

    def test_filters(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(
            response.context["object_list"],
            [self.test_user, self.user],
        )

        response = self.get({"is_superuser": True})
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response.context["object_list"], [self.user])

        response = self.get({"is_superuser": False})
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response.context["object_list"], [self.test_user])

        self.test_user.is_active = False
        self.test_user.save()

        response = self.get({"is_active": True})
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response.context["object_list"], [self.user])

        response = self.get({"is_active": False})
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response.context["object_list"], [self.test_user])

        now = timezone.now()
        if timezone.is_aware(now):
            today = timezone.localtime(now).date()
        else:
            today = now.date()
        tomorrow = today + timezone.timedelta(days=1)
        yesterday = today - timezone.timedelta(days=1)

        response = self.get({"last_login_from": str(today)})
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response.context["object_list"], [self.user])

        response = self.get({"last_login_from": str(tomorrow)})
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response.context["object_list"], [])

        response = self.get({"last_login_to": str(today)})
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response.context["object_list"], [self.user])

        response = self.get({"last_login_to": str(yesterday)})
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response.context["object_list"], [])

        musicians = Group.objects.create(name="Musicians")
        songwriters = Group.objects.create(name="Songwriters")
        self.test_user.groups.add(musicians)
        self.user.groups.add(songwriters)

        response = self.get({"group": musicians.pk})
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response.context["object_list"], [self.test_user])

        response = self.get({"group": [musicians.pk, songwriters.pk]})
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(
            response.context["object_list"],
            [self.test_user, self.user],
        )

    def test_num_queries(self):
        # Warm up
        self.get()

        num_queries = 10
        with self.assertNumQueries(num_queries):
            self.get()

        # Ensure we don't have any N+1 queries
        self.create_user("test", "test@example.com", "gu@rd14n")
        with self.assertNumQueries(num_queries):
            self.get()

    def test_default_buttons(self):
        response = self.get()
        soup = self.get_soup(response.content)
        dropdown_buttons = soup.select("li [data-controller='w-dropdown'] a")
        expected_urls = [
            reverse("wagtailusers_users:edit", args=(self.user.pk,)),
            reverse("wagtailusers_users:copy", args=(self.user.pk,)),
            # Should not link to delete page for the current user
            reverse("wagtailusers_users:edit", args=(self.test_user.pk,)),
            reverse("wagtailusers_users:copy", args=(self.test_user.pk,)),
            reverse("wagtailusers_users:delete", args=(self.test_user.pk,)),
        ]
        urls = [button.attrs.get("href") for button in dropdown_buttons]
        self.assertSequenceEqual(urls, expected_urls)

    def test_buttons_hook(self):
        def hook(user, request_user):
            self.assertEqual(request_user, self.user)
            yield UserListingButton(
                "Show profile",
                f"/goes/to/a/url/{user.pk}",
                priority=30,
            )
            yield ButtonWithDropdown(
                label="Moar pls!",
                buttons=[UserListingButton("Alrighty", "/cheers", priority=10)],
            )

        with self.register_hook("register_user_listing_buttons", hook):
            response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/shared/buttons.html")

        soup = self.get_soup(response.content)
        row = soup.select_one(f"tbody tr:has([data-object-id='{self.test_user.pk}'])")
        self.assertIsNotNone(row)

        profile_url = f"/goes/to/a/url/{self.test_user.pk}"
        actions = row.select_one("td ul.actions")
        top_level_custom_button = actions.select_one(f"li > a[href='{profile_url}']")
        self.assertIsNone(top_level_custom_button)
        custom_button = actions.select_one(
            f"li [data-controller='w-dropdown'] a[href='{profile_url}']"
        )
        self.assertIsNotNone(custom_button)
        self.assertEqual(
            custom_button.text.strip(),
            "Show profile",
        )

        nested_dropdown = actions.select_one(
            "li [data-controller='w-dropdown'] [data-controller='w-dropdown']"
        )
        self.assertIsNone(nested_dropdown)
        dropdown_buttons = actions.select("li > [data-controller='w-dropdown']")
        # Default "More" button and the custom "Moar pls!" button
        self.assertEqual(len(dropdown_buttons), 2)
        custom_dropdown = None
        for button in dropdown_buttons:
            if "Moar pls!" in button.text.strip():
                custom_dropdown = button
        self.assertIsNotNone(custom_dropdown)
        self.assertEqual(custom_dropdown.select_one("button").text.strip(), "Moar pls!")
        # Should contain the custom button inside the custom dropdown
        custom_button = custom_dropdown.find("a", attrs={"href": "/cheers"})
        self.assertIsNotNone(custom_button)
        self.assertEqual(custom_button.text.strip(), "Alrighty")


class TestUserIndexResultsView(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    def setUp(self):
        # create a user that should be visible in the listing
        self.test_user = self.create_user(
            username="testuser",
            email="testuser@email.com",
            password="password",
            first_name="First Name",
            last_name="Last Name",
        )
        self.login()

    def get(self, params={}):
        return self.client.get(reverse("wagtailusers_users:index_results"), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailusers/users/index_results.html")
        self.assertContains(response, "testuser")
        # response should not contain page furniture
        self.assertBreadcrumbsNotRendered(response.content)


class TestUserCreateView(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse("wagtailusers_users:add"), params)

    def post(self, post_data={}, follow=False):
        return self.client.post(
            reverse("wagtailusers_users:add"), post_data, follow=follow
        )

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailusers/users/create.html")
        self.assertContains(response, "Password")
        self.assertContains(response, "Password confirmation")
        self.assertBreadcrumbsItemsRendered(
            [
                {
                    "url": "/admin/users/",
                    "label": capfirst(User._meta.verbose_name_plural),
                },
                {"url": "", "label": f"New: {capfirst(User._meta.verbose_name)}"},
            ],
            response.content,
        )

    def test_create(self):
        response = self.post(
            {
                "username": "testuser",
                "email": "test@user.com",
                "first_name": "Test",
                "last_name": "User",
                "password1": "password",
                "password2": "password",
            },
            follow=True,
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailusers_users:index"))

        # Check that the user was created
        users = get_user_model().objects.filter(email="test@user.com")
        self.assertEqual(users.count(), 1)
        if settings.AUTH_USER_MODEL == "emailuser.EmailUser":
            self.assertContains(response, "User &#x27;test@user.com&#x27; created.")
        else:
            self.assertContains(response, "User &#x27;testuser&#x27; created.")

    @unittest.skipUnless(
        settings.AUTH_USER_MODEL == "customuser.CustomUser",
        "Only applicable to CustomUser",
    )
    @override_settings(
        WAGTAIL_USER_CREATION_FORM="wagtail.users.tests.CustomUserCreationForm",
    )
    def test_create_with_custom_form(self):
        response = self.post(
            {
                "username": "testuser",
                "email": "test@user.com",
                "first_name": "Test",
                "last_name": "User",
                "password1": "password",
                "password2": "password",
                "country": "testcountry",
                "attachment": SimpleUploadedFile("test.txt", b"Uploaded file"),
            }
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailusers_users:index"))

        # Check that the user was created
        users = get_user_model().objects.filter(email="test@user.com")
        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first().country, "testcountry")
        self.assertEqual(users.first().attachment.read(), b"Uploaded file")

    def test_create_with_whitespaced_password(self):
        """Password should not be stripped"""
        self.post(
            {
                "username": "testuser2",
                "email": "test@user2.com",
                "first_name": "Test",
                "last_name": "User",
                "password1": "  whitespaced_password  ",
                "password2": "  whitespaced_password  ",
            },
            follow=True,
        )
        # Try to login with the password
        self.client.logout()
        username = "testuser2"
        if settings.AUTH_USER_MODEL == "emailuser.EmailUser":
            username = "test@user2.com"
        self.login(username=username, password="  whitespaced_password  ")

    def test_create_with_password_mismatch(self):
        response = self.post(
            {
                "username": "testuser",
                "email": "test@user.com",
                "first_name": "Test",
                "last_name": "User",
                "password1": "password1",
                "password2": "password2",
            }
        )

        # Should remain on page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailusers/users/create.html")

        self.assertTrue(response.context["form"].errors["password2"])

        # Check that the user was not created
        users = get_user_model().objects.filter(email="test@user.com")
        self.assertEqual(users.count(), 0)

    @override_settings(
        AUTH_PASSWORD_VALIDATORS=[
            {
                "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
            },
        ],
    )
    def test_create_with_password_validation(self):
        """
        Test that the Django password validators are run when creating a user.
        Specifically test that the UserAttributeSimilarityValidator works,
        which requires a full-populated user model before the validation works.
        """
        # Create a user with a password the same as their name
        response = self.post(
            {
                "username": "testuser",
                "email": "test@user.com",
                "first_name": "Example",
                "last_name": "Name",
                "password1": "example name",
                "password2": "example name",
            }
        )

        # Should remain on page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailusers/users/create.html")

        # Password field should have an error
        errors = response.context["form"].errors.as_data()
        self.assertIn("password2", errors)
        self.assertEqual(errors["password2"][0].code, "password_too_similar")

        # Check that the user was not created
        users = get_user_model().objects.filter(email="test@user.com")
        self.assertEqual(users.count(), 0)

    def test_create_with_missing_password(self):
        """Password should be required by default"""
        response = self.post(
            {
                "username": "testuser",
                "email": "test@user.com",
                "first_name": "Test",
                "last_name": "User",
                "password1": "",
                "password2": "",
            }
        )

        # Should remain on page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailusers/users/create.html")

        self.assertTrue(response.context["form"].errors["password1"])

        # Check that the user was not created
        users = get_user_model().objects.filter(email="test@user.com")
        self.assertEqual(users.count(), 0)

    @override_settings(WAGTAILUSERS_PASSWORD_REQUIRED=False)
    def test_password_fields_exist_when_not_required(self):
        """Password fields should still be shown if WAGTAILUSERS_PASSWORD_REQUIRED is False"""
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailusers/users/create.html")
        self.assertContains(response, "Password")
        self.assertContains(response, "Password confirmation")

    @override_settings(WAGTAILUSERS_PASSWORD_REQUIRED=False)
    def test_create_with_password_not_required(self):
        """Password should not be required if WAGTAILUSERS_PASSWORD_REQUIRED is False"""
        response = self.post(
            {
                "username": "testuser",
                "email": "test@user.com",
                "first_name": "Test",
                "last_name": "User",
                "password1": "",
                "password2": "",
            }
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailusers_users:index"))

        # Check that the user was created
        users = get_user_model().objects.filter(email="test@user.com")
        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first().password, "")

    @override_settings(WAGTAILUSERS_PASSWORD_REQUIRED=False)
    def test_optional_password_is_still_validated(self):
        """When WAGTAILUSERS_PASSWORD_REQUIRED is False, password validation should still apply if a password _is_ supplied"""
        response = self.post(
            {
                "username": "testuser",
                "email": "test@user.com",
                "first_name": "Test",
                "last_name": "User",
                "password1": "banana",
                "password2": "kumquat",
            }
        )

        # Should remain on page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailusers/users/create.html")

        self.assertTrue(response.context["form"].errors["password2"])

        # Check that the user was not created
        users = get_user_model().objects.filter(email="test@user.com")
        self.assertEqual(users.count(), 0)

    @override_settings(WAGTAILUSERS_PASSWORD_REQUIRED=False)
    def test_password_still_accepted_when_optional(self):
        """When WAGTAILUSERS_PASSWORD_REQUIRED is False, we should still allow a password to be set"""
        response = self.post(
            {
                "username": "testuser",
                "email": "test@user.com",
                "first_name": "Test",
                "last_name": "User",
                "password1": "banana",
                "password2": "banana",
            }
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailusers_users:index"))

        # Check that the user was created
        users = get_user_model().objects.filter(email="test@user.com")
        self.assertEqual(users.count(), 1)
        self.assertTrue(users.first().check_password("banana"))

    @override_settings(WAGTAILUSERS_PASSWORD_ENABLED=False)
    def test_password_fields_not_shown_when_disabled(self):
        """WAGTAILUSERS_PASSWORD_ENABLED=False should cause password fields to be removed"""
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailusers/users/create.html")
        self.assertNotContains(response, "Password")
        self.assertNotContains(response, "Password confirmation")

    @override_settings(WAGTAILUSERS_PASSWORD_ENABLED=False)
    def test_password_fields_ignored_when_disabled(self):
        """When WAGTAILUSERS_PASSWORD_ENABLED is False, users should always be created without a usable password"""
        response = self.post(
            {
                "username": "testuser",
                "email": "test@user.com",
                "first_name": "Test",
                "last_name": "User",
                "password1": "banana",  # not part of the form - should be ignored
                "password2": "kumquat",  # not part of the form - should be ignored
            }
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailusers_users:index"))

        # Check that the user was created
        users = get_user_model().objects.filter(email="test@user.com")
        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first().password, "")

    def test_before_create_user_hook(self):
        def hook_func(request):
            self.assertIsInstance(request, HttpRequest)
            return HttpResponse("Overridden!")

        with self.register_hook("before_create_user", hook_func):
            response = self.client.get(reverse("wagtailusers_users:add"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

    def test_before_create_user_hook_post(self):
        def hook_func(request):
            self.assertIsInstance(request, HttpRequest)
            return HttpResponse("Overridden!")

        with self.register_hook("before_create_user", hook_func):
            post_data = {
                "username": "testuser",
                "email": "testuser@test.com",
                "password1": "password12",
                "password2": "password12",
                "first_name": "test",
                "last_name": "user",
            }
            response = self.client.post(reverse("wagtailusers_users:add"), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

    def test_after_create_user_hook(self):
        def hook_func(request, user):
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(user, get_user_model())
            return HttpResponse("Overridden!")

        with self.register_hook("after_create_user", hook_func):
            post_data = {
                "username": "testuser",
                "email": "testuser@test.com",
                "password1": "password12",
                "password2": "password12",
                "first_name": "test",
                "last_name": "user",
            }
            response = self.client.post(reverse("wagtailusers_users:add"), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")


class TestUserDeleteView(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    def setUp(self):
        # create a user that should be visible in the listing
        self.test_user = self.create_user(
            username="testuser", email="testuser@email.com", password="password"
        )
        # also create a superuser to delete
        self.superuser = self.create_superuser(
            username="testsuperuser",
            email="testsuperuser@email.com",
            password="password",
        )
        self.current_user = self.login()

    def get(self, params={}):
        return self.client.get(
            reverse("wagtailusers_users:delete", args=(self.test_user.pk,)), params
        )

    def post(self, post_data={}, follow=False):
        return self.client.post(
            reverse("wagtailusers_users:delete", args=(self.test_user.pk,)),
            post_data,
            follow=follow,
        )

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailusers/users/confirm_delete.html")
        self.assertBreadcrumbsNotRendered(response.content)

        # Should render the form with the correct action URL
        soup = self.get_soup(response.content)
        delete_url = reverse("wagtailusers_users:delete", args=(self.test_user.pk,))
        form_action = soup.select_one("form").attrs["action"]
        self.assertEqual(form_action, delete_url)

    def test_delete(self):
        response = self.post(follow=True)

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailusers_users:index"))

        # Check that the user was deleted
        users = get_user_model().objects.filter(email="testuser@email.com")
        self.assertEqual(users.count(), 0)
        if settings.AUTH_USER_MODEL == "emailuser.EmailUser":
            self.assertContains(
                response, "User &#x27;testuser@email.com&#x27; deleted."
            )
        else:
            self.assertContains(response, "User &#x27;testuser&#x27; deleted.")

    def test_user_cannot_delete_self(self):
        response = self.client.get(
            reverse("wagtailusers_users:delete", args=(self.current_user.pk,))
        )

        # Should redirect to admin index (permission denied)
        self.assertRedirects(response, reverse("wagtailadmin_home"))
        # Check user was not deleted
        self.assertTrue(
            get_user_model().objects.filter(pk=self.current_user.pk).exists()
        )

    def test_user_can_delete_other_superuser(self):
        response = self.client.get(
            reverse("wagtailusers_users:delete", args=(self.superuser.pk,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailusers/users/confirm_delete.html")

        response = self.client.post(
            reverse("wagtailusers_users:delete", args=(self.superuser.pk,))
        )
        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailusers_users:index"))

        # Check that the user was deleted
        users = get_user_model().objects.filter(email="testsuperuser@email.com")
        self.assertEqual(users.count(), 0)

    def test_before_delete_user_hook(self):
        def hook_func(request, user):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(user.pk, self.test_user.pk)

            return HttpResponse("Overridden!")

        with self.register_hook("before_delete_user", hook_func):
            response = self.client.get(
                reverse("wagtailusers_users:delete", args=(self.test_user.pk,))
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

    def test_before_delete_user_hook_post(self):
        def hook_func(request, user):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(user.pk, self.test_user.pk)

            return HttpResponse("Overridden!")

        with self.register_hook("before_delete_user", hook_func):
            response = self.client.post(
                reverse("wagtailusers_users:delete", args=(self.test_user.pk,))
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

    def test_after_delete_user_hook(self):
        def hook_func(request, user):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(user.email, self.test_user.email)

            return HttpResponse("Overridden!")

        with self.register_hook("after_delete_user", hook_func):
            response = self.client.post(
                reverse("wagtailusers_users:delete", args=(self.test_user.pk,))
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")


class TestUserDeleteViewForNonSuperuser(
    AdminTemplateTestUtils, WagtailTestUtils, TestCase
):
    def setUp(self):
        # create a user that should be visible in the listing
        self.test_user = self.create_user(
            username="testuser", email="testuser@email.com", password="password"
        )
        # create a user with delete permission
        self.deleter_user = self.create_user(username="deleter", password="password")
        deleters_group = Group.objects.create(name="User deleters")
        deleters_group.permissions.add(Permission.objects.get(codename="access_admin"))
        deleters_group.permissions.add(
            Permission.objects.get(
                content_type__app_label=AUTH_USER_APP_LABEL,
                codename=delete_user_perm_codename,
            )
        )
        self.deleter_user.groups.add(deleters_group)

        self.superuser = self.create_test_user()

        self.login(username="deleter", password="password")

    def test_simple(self):
        response = self.client.get(
            reverse("wagtailusers_users:delete", args=(self.test_user.pk,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailusers/users/confirm_delete.html")
        self.assertBreadcrumbsNotRendered(response.content)

    def test_delete(self):
        response = self.client.post(
            reverse("wagtailusers_users:delete", args=(self.test_user.pk,))
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailusers_users:index"))

        # Check that the user was deleted
        users = get_user_model().objects.filter(email="testuser@email.com")
        self.assertEqual(users.count(), 0)

    def test_user_cannot_delete_self(self):
        response = self.client.post(
            reverse("wagtailusers_users:delete", args=(self.deleter_user.pk,))
        )

        # Should redirect to admin index (permission denied)
        self.assertRedirects(response, reverse("wagtailadmin_home"))
        # Check user was not deleted
        self.assertTrue(
            get_user_model().objects.filter(pk=self.deleter_user.pk).exists()
        )

    def test_user_cannot_delete_superuser(self):
        response = self.client.post(
            reverse("wagtailusers_users:delete", args=(self.superuser.pk,))
        )

        # Should redirect to admin index (permission denied)
        self.assertRedirects(response, reverse("wagtailadmin_home"))
        # Check user was not deleted
        self.assertTrue(get_user_model().objects.filter(pk=self.superuser.pk).exists())


class TestUserEditView(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    def setUp(self):
        # Create a user to edit
        self.test_user = self.create_user(
            username="testuser",
            email="testuser@email.com",
            first_name="Original",
            last_name="User",
            password="password",
        )

        # Login
        self.current_user = self.login()

    def get(self, params={}, user_id=None):
        return self.client.get(
            reverse("wagtailusers_users:edit", args=(user_id or self.test_user.pk,)),
            params,
        )

    def post(self, post_data={}, user_id=None, follow=False):
        return self.client.post(
            reverse("wagtailusers_users:edit", args=(user_id or self.test_user.pk,)),
            post_data,
            follow=follow,
        )

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailusers/users/edit.html")
        self.assertContains(response, "Password")
        self.assertContains(response, "Password confirmation")
        self.assertBreadcrumbsItemsRendered(
            [
                {
                    "url": "/admin/users/",
                    "label": capfirst(User._meta.verbose_name_plural),
                },
                {"url": "", "label": "Original User"},
            ],
            response.content,
        )

        soup = self.get_soup(response.content)
        header = soup.select_one(".w-slim-header")
        history_url = reverse("wagtailusers_users:history", args=(self.test_user.pk,))
        history_link = header.find("a", attrs={"href": history_url})
        self.assertIsNotNone(history_link)

        # Should render the form with the correct action URL
        edit_url = reverse("wagtailusers_users:edit", args=(self.test_user.pk,))
        form_action = soup.select_one("form").attrs["action"]
        self.assertEqual(form_action, edit_url)

        url_finder = AdminURLFinder(self.current_user)
        self.assertEqual(url_finder.get_edit_url(self.test_user), edit_url)

    def test_legacy_url_redirect(self):
        with self.assertWarnsMessage(
            RemovedInWagtail70Warning,
            (
                "UserViewSet's `/<pk>/` edit view URL pattern has been "
                "deprecated in favour of /edit/<pk>/."
            ),
        ):
            response = self.client.get(f"/admin/users/{self.test_user.pk}/")

        self.assertRedirects(
            response,
            f"/admin/users/edit/{self.test_user.pk}/",
            status_code=301,
        )

    def test_nonexistent_redirect(self):
        invalid_id = (
            "99999999-9999-9999-9999-999999999999"
            if settings.AUTH_USER_MODEL == "emailuser.EmailUser"
            else 100000
        )
        self.assertEqual(self.get(user_id=invalid_id).status_code, 404)

    def test_simple_post(self):
        response = self.post(
            {
                "username": "testuser",
                "email": "test@user.com",
                "first_name": "Edited",
                "last_name": "User",
                "password1": "newpassword",
                "password2": "newpassword",
                "is_active": "on",
            },
            follow=True,
        )
        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailusers_users:index"))

        # Check that the user was edited
        user = get_user_model().objects.get(pk=self.test_user.pk)
        self.assertEqual(user.first_name, "Edited")
        self.assertTrue(user.check_password("newpassword"))
        if settings.AUTH_USER_MODEL == "emailuser.EmailUser":
            self.assertContains(response, "User &#x27;test@user.com&#x27; updated.")
        else:
            self.assertContains(response, "User &#x27;testuser&#x27; updated.")

        # On next load of the edit view,
        # should render the status panel with the last updated time
        response = self.get()
        self.assertContains(response, "Edited User")
        soup = self.get_soup(response.content)
        status_panel = soup.select_one('[data-side-panel="status"]')
        self.assertIsNotNone(status_panel)
        last_updated = status_panel.select_one(".w-help-text")
        self.assertIsNotNone(last_updated)
        self.assertRegex(
            last_updated.get_text(strip=True),
            f"[0-9][0-9]:[0-9][0-9] by {self.current_user.get_username()}",
        )
        history_url = reverse("wagtailusers_users:history", args=(self.test_user.pk,))
        history_link = status_panel.select_one(f'a[href="{history_url}"]')
        self.assertIsNotNone(history_link)

    def test_password_optional(self):
        """Leaving password fields blank should leave it unchanged"""
        response = self.post(
            {
                "username": "testuser",
                "email": "test@user.com",
                "first_name": "Edited",
                "last_name": "User",
                "password1": "",
                "password2": "",
                "is_active": "on",
            }
        )
        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailusers_users:index"))

        # Check that the user was edited but password is unchanged
        user = get_user_model().objects.get(pk=self.test_user.pk)
        self.assertEqual(user.first_name, "Edited")
        self.assertTrue(user.check_password("password"))

    def test_passwords_match(self):
        """Password fields should be validated if supplied"""
        response = self.post(
            {
                "username": "testuser",
                "email": "test@user.com",
                "first_name": "Edited",
                "last_name": "User",
                "password1": "banana",
                "password2": "kumquat",
                "is_active": "on",
            }
        )
        # Should remain on page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailusers/users/edit.html")

        self.assertTrue(response.context["form"].errors["password2"])

        # Check that the user was not edited
        user = get_user_model().objects.get(pk=self.test_user.pk)
        self.assertEqual(user.first_name, "Original")
        self.assertTrue(user.check_password("password"))

    @override_settings(
        AUTH_PASSWORD_VALIDATORS=[
            {
                "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
            },
        ],
    )
    def test_edit_with_password_validation(self):
        """
        Test that the Django password validators are run when editing a user.
        Specifically test that the UserAttributeSimilarityValidator works,
        which requires a full-populated user model before the validation works.
        """
        # Create a user with a password the same as their name
        response = self.post(
            {
                "username": "testuser",
                "email": "test@user.com",
                "first_name": "Edited",
                "last_name": "Name",
                "password1": "edited name",
                "password2": "edited name",
            }
        )

        # Should remain on page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailusers/users/edit.html")

        # Password field should have an error
        errors = response.context["form"].errors.as_data()
        self.assertIn("password2", errors)
        self.assertEqual(errors["password2"][0].code, "password_too_similar")

        # Check that the user was not edited
        user = get_user_model().objects.get(pk=self.test_user.pk)
        self.assertEqual(user.first_name, "Original")
        self.assertTrue(user.check_password("password"))

    def test_edit_and_deactivate(self):
        response = self.post(
            {
                "username": "testuser",
                "email": "test@user.com",
                "first_name": "Edited",
                "last_name": "User",
                "password1": "password",
                "password2": "password",
                # Leaving out these fields, thus setting them to False:
                # 'is_active': 'on'
                # 'is_superuser': 'on',
            }
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailusers_users:index"))

        # Check that the user was edited
        user = get_user_model().objects.get(pk=self.test_user.pk)
        self.assertEqual(user.first_name, "Edited")
        # Check that the user is no longer superuser
        self.assertIs(user.is_superuser, False)
        # Check that the user is no longer active
        self.assertIs(user.is_active, False)

    def test_edit_and_make_superuser(self):
        response = self.post(
            {
                "username": "testuser",
                "email": "test@user.com",
                "first_name": "Edited",
                "last_name": "User",
                "password1": "password",
                "password2": "password",
                "is_active": "on",
                "is_superuser": "on",
            }
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailusers_users:index"))

        # Check that the user was edited
        user = get_user_model().objects.get(pk=self.test_user.pk)

        # Check that the user is now superuser
        self.assertIs(user.is_superuser, True)
        # Check that the user is now active
        self.assertIs(user.is_active, True)

    def test_edit_self(self):
        response = self.post(
            {
                "username": "test@email.com",
                "email": "test@email.com",
                "first_name": "Edited Myself",
                "last_name": "User",
                # 'password1': "password",
                # 'password2': "password",
                "is_active": "on",
                "is_superuser": "on",
            },
            self.current_user.pk,
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailusers_users:index"))

        # Check that the user was edited
        user = get_user_model().objects.get(pk=self.current_user.pk)
        self.assertEqual(user.first_name, "Edited Myself")

        # Check that the user is still superuser
        self.assertIs(user.is_superuser, True)
        # Check that the user is still active
        self.assertIs(user.is_active, True)

    def test_editing_own_password_does_not_log_out(self):
        response = self.post(
            {
                "username": "test@email.com",
                "email": "test@email.com",
                "first_name": "Edited Myself",
                "last_name": "User",
                "password1": "c0rrecth0rse",
                "password2": "c0rrecth0rse",
                "is_active": "on",
                "is_superuser": "on",
            },
            self.current_user.pk,
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailusers_users:index"))

        # Check that the user was edited
        user = get_user_model().objects.get(pk=self.current_user.pk)
        self.assertEqual(user.first_name, "Edited Myself")

        # Check user is not logged out
        response = self.client.get(reverse("wagtailusers_users:index"))
        self.assertEqual(response.status_code, 200)

    def test_cannot_demote_self(self):
        """
        check that unsetting a user's own is_active or is_superuser flag has no effect
        """
        response = self.post(
            {
                "username": "test@email.com",
                "email": "test@email.com",
                "first_name": "Edited Myself",
                "last_name": "User",
                # 'password1': "password",
                # 'password2': "password",
                # failing to submit is_active or is_superuser would unset those flags,
                # if we didn't explicitly prevent that when editing self
                # 'is_active': 'on',
                # 'is_superuser': 'on',
            },
            self.current_user.pk,
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailusers_users:index"))

        # Check that the user was edited
        user = get_user_model().objects.get(pk=self.current_user.pk)
        self.assertEqual(user.first_name, "Edited Myself")

        # Check that the user is still superuser
        self.assertIs(user.is_superuser, True)
        # Check that the user is still active
        self.assertIs(user.is_active, True)

    @unittest.skipUnless(
        settings.AUTH_USER_MODEL == "customuser.CustomUser",
        "Only applicable to CustomUser",
    )
    @override_settings(
        WAGTAIL_USER_EDIT_FORM="wagtail.users.tests.CustomUserEditForm",
    )
    def test_edit_with_custom_form(self):
        response = self.post(
            {
                "username": "testuser",
                "email": "test@user.com",
                "first_name": "Edited",
                "last_name": "User",
                "password1": "password",
                "password2": "password",
                "country": "testcountry",
                "attachment": SimpleUploadedFile("test.txt", b"Uploaded file"),
            }
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailusers_users:index"))

        # Check that the user was edited
        user = get_user_model().objects.get(pk=self.test_user.pk)
        self.assertEqual(user.first_name, "Edited")
        self.assertEqual(user.country, "testcountry")
        self.assertEqual(user.attachment.read(), b"Uploaded file")

    @unittest.skipIf(
        settings.AUTH_USER_MODEL == "emailuser.EmailUser", "Not applicable to EmailUser"
    )
    def test_edit_validation_error(self):
        # Leave "username" field blank. This should give a validation error
        response = self.post(
            {
                "username": "",
                "email": "test@user.com",
                "first_name": "Teset",
                "last_name": "User",
                "password1": "password",
                "password2": "password",
            }
        )

        # Should not redirect to index
        self.assertEqual(response.status_code, 200)

    @override_settings(WAGTAILUSERS_PASSWORD_ENABLED=False)
    def test_password_fields_not_shown_when_disabled(self):
        """WAGTAILUSERS_PASSWORD_ENABLED=False should cause password fields to be removed"""
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailusers/users/edit.html")
        self.assertNotContains(response, "Password")
        self.assertNotContains(response, "Password confirmation")

    @override_settings(WAGTAILUSERS_PASSWORD_ENABLED=False)
    def test_password_fields_ignored_when_disabled(self):
        """When WAGTAILUSERS_PASSWORD_REQUIRED is False, existing password should be left unchanged"""
        response = self.post(
            {
                "username": "testuser",
                "email": "test@user.com",
                "first_name": "Edited",
                "last_name": "User",
                "is_active": "on",
                "password1": "banana",  # not part of the form - should be ignored
                "password2": "kumquat",  # not part of the form - should be ignored
            }
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailusers_users:index"))

        # Check that the user was edited but password is unchanged
        user = get_user_model().objects.get(pk=self.test_user.pk)
        self.assertEqual(user.first_name, "Edited")
        self.assertTrue(user.check_password("password"))

    def test_before_edit_user_hook(self):
        def hook_func(request, user):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(user.pk, self.test_user.pk)

            return HttpResponse("Overridden!")

        with self.register_hook("before_edit_user", hook_func):
            response = self.client.get(
                reverse("wagtailusers_users:edit", args=(self.test_user.pk,))
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

    def test_before_edit_user_hook_post(self):
        def hook_func(request, user):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(user.pk, self.test_user.pk)

            return HttpResponse("Overridden!")

        with self.register_hook("before_edit_user", hook_func):
            post_data = {
                "username": "testuser",
                "email": "test@user.com",
                "first_name": "Edited",
                "last_name": "User",
                "password1": "password",
                "password2": "password",
            }
            response = self.client.post(
                reverse("wagtailusers_users:edit", args=(self.test_user.pk,)), post_data
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

    def test_after_edit_user_hook_post(self):
        def hook_func(request, user):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(user.pk, self.test_user.pk)

            return HttpResponse("Overridden!")

        with self.register_hook("after_edit_user", hook_func):
            post_data = {
                "username": "testuser",
                "email": "test@user.com",
                "first_name": "Edited",
                "last_name": "User",
                "password1": "password",
                "password2": "password",
            }
            response = self.client.post(
                reverse("wagtailusers_users:edit", args=(self.test_user.pk,)), post_data
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")


class TestUserCopyView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()

    @classmethod
    def setUpTestData(cls):
        cls.test_user = cls.create_user(
            username="testuser",
            email="testuser@email.com",
            first_name="Original",
            last_name="User",
            password="password",
        )
        cls.url = reverse("wagtailusers_users:copy", args=[quote(cls.test_user.pk)])

    def test_without_permission(self):
        self.user.is_superuser = False
        self.user.save()
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        self.user.user_permissions.add(admin_permission)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_with_minimal_permission(self):
        self.user.is_superuser = False
        self.user.save()
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            ),
            Permission.objects.get(
                content_type__app_label=AUTH_USER_APP_LABEL,
                codename=add_user_perm_codename,
            ),
        )

        # Form should be prefilled
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)
        first_name = soup.select_one('input[name="first_name"]')
        self.assertEqual(first_name.attrs.get("value"), "Original")
        last_name = soup.select_one('input[name="last_name"]')
        self.assertEqual(last_name.attrs.get("value"), "User")
        # Password fields should be empty
        password1 = soup.select_one('input[name="password1"]')
        password2 = soup.select_one('input[name="password2"]')
        self.assertIsNone(password1.attrs.get("value"))
        self.assertIsNone(password2.attrs.get("value"))


class TestUserProfileCreation(WagtailTestUtils, TestCase):
    def setUp(self):
        # Create a user
        self.test_user = self.create_user(
            username="testuser",
            password="password",
        )

    def test_user_created_without_profile(self):
        self.assertEqual(UserProfile.objects.filter(user=self.test_user).count(), 0)
        with self.assertRaises(UserProfile.DoesNotExist):
            self.test_user.wagtail_userprofile

    def test_user_profile_created_when_method_called(self):
        self.assertIsInstance(UserProfile.get_for_user(self.test_user), UserProfile)
        # and get it from the db too
        self.assertEqual(UserProfile.objects.filter(user=self.test_user).count(), 1)

    def test_avatar_empty_on_profile_creation(self):
        user_profile = UserProfile.get_for_user(self.test_user)
        self.assertFalse(user_profile.avatar)


class TestUserEditViewForNonSuperuser(WagtailTestUtils, TestCase):
    def setUp(self):
        # create a user with edit permission
        self.editor_user = self.create_user(username="editor", password="password")
        editors_group = Group.objects.create(name="User editors")
        editors_group.permissions.add(Permission.objects.get(codename="access_admin"))
        editors_group.permissions.add(
            Permission.objects.get(
                content_type__app_label=AUTH_USER_APP_LABEL,
                codename=change_user_perm_codename,
            )
        )
        self.editor_user.groups.add(editors_group)

        self.login(username="editor", password="password")

    def test_user_cannot_escalate_privileges(self):
        """
        Check that a non-superuser cannot edit their own is_active or is_superuser flag.
        (note: this doesn't necessarily guard against other routes to escalating privileges, such
        as creating a new user with is_superuser=True or adding oneself to a group with additional
        privileges - the latter will be dealt with by #537)
        """
        editors_group = Group.objects.get(name="User editors")
        post_data = {
            "username": "editor",
            "email": "editor@email.com",
            "first_name": "Escalating",
            "last_name": "User",
            "password1": "",
            "password2": "",
            "groups": [
                editors_group.id,
            ],
            # These should not be possible without manipulating the form in the DOM:
            "is_superuser": "on",
            "is_active": "on",
        }
        response = self.client.post(
            reverse("wagtailusers_users:edit", args=(self.editor_user.pk,)), post_data
        )
        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailusers_users:index"))

        user = get_user_model().objects.get(pk=self.editor_user.pk)
        # check if user is still in the editors group
        self.assertTrue(user.groups.filter(name="User editors").exists())

        # check that non-permission-related edits went ahead
        self.assertEqual(user.first_name, "Escalating")

        # Check that the user did not escalate its is_superuser status
        self.assertIs(user.is_superuser, False)


class TestUserHistoryView(WagtailTestUtils, TestCase):
    # More thorough tests are in test_model_viewset

    @classmethod
    def setUpTestData(cls):
        cls.test_user = cls.create_user(
            username="testuser",
            email="testuser@email.com",
            first_name="Original",
            last_name="User",
            password="password",
        )
        cls.url = reverse("wagtailusers_users:history", args=(cls.test_user.pk,))

    def setUp(self):
        self.user = self.login()

    def test_simple(self):
        log(self.test_user, "wagtail.create", user=self.user)
        log(self.test_user, "wagtail.edit", user=self.user)
        response = self.client.get(self.url)
        self.assertTemplateUsed("wagtailadmin/generic/listing.html")
        self.assertContains(response, "Created")
        self.assertContains(response, "Edited")


class TestGroupIndexView(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse("wagtailusers_groups:index"), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailusers/groups/index.html")
        self.assertTemplateUsed(response, "wagtailadmin/generic/index.html")
        # response should contain page furniture, including the "Add a group" button
        self.assertContains(response, "Add a group")
        self.assertBreadcrumbsItemsRendered(
            [{"url": "", "label": "Groups"}], response.content
        )

    def test_search(self):
        response = self.get({"q": "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["search_form"]["q"].value(), "Hello")

    def test_default_ordering(self):
        # This group should display after the default groups but will display
        # before them if default_ordering is lost.
        Group.objects.create(name="Photographers")
        response = self.get()
        # groups should be returned in alpha order by name
        names = [group.name for group in response.context_data["object_list"]]
        self.assertEqual(names, ["Editors", "Moderators", "Photographers"])


class TestGroupIndexResultsView(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse("wagtailusers_groups:index_results"), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/listing_results.html")
        # response should not contain page furniture
        self.assertBreadcrumbsNotRendered(response.content)

    def test_search(self):
        response = self.get({"q": "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["search_form"]["q"].value(), "Hello")


class TestGroupCreateView(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()
        self.add_doc_permission = Permission.objects.get(
            content_type__app_label="wagtaildocs", codename="add_document"
        )
        self.change_doc_permission = Permission.objects.get(
            content_type__app_label="wagtaildocs", codename="change_document"
        )

    def get(self, params={}):
        return self.client.get(reverse("wagtailusers_groups:add"), params)

    def post(self, post_data={}):
        post_defaults = {
            "page_permissions-TOTAL_FORMS": ["0"],
            "page_permissions-MAX_NUM_FORMS": ["1000"],
            "page_permissions-INITIAL_FORMS": ["0"],
            "collection_permissions-TOTAL_FORMS": ["0"],
            "collection_permissions-MAX_NUM_FORMS": ["1000"],
            "collection_permissions-INITIAL_FORMS": ["0"],
            "document_permissions-TOTAL_FORMS": ["0"],
            "document_permissions-MAX_NUM_FORMS": ["1000"],
            "document_permissions-INITIAL_FORMS": ["0"],
            "image_permissions-TOTAL_FORMS": ["0"],
            "image_permissions-MAX_NUM_FORMS": ["1000"],
            "image_permissions-INITIAL_FORMS": ["0"],
        }
        for k, v in post_defaults.items():
            post_data[k] = post_data.get(k, v)
        return self.client.post(reverse("wagtailusers_groups:add"), post_data)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailusers/groups/create.html")
        self.assertBreadcrumbsItemsRendered(
            [
                {"url": "/admin/groups/", "label": "Groups"},
                {"url": "", "label": "New: Group"},
            ],
            response.content,
        )
        # Should contain the JS from the form and the template include
        page_chooser_js = versioned_static("wagtailadmin/js/page-chooser.js")
        self.assertContains(response, page_chooser_js)

    def test_num_queries(self):
        # Warm up the cache
        self.get()
        with self.assertNumQueries(20):
            self.get()

    def test_create_group(self):
        response = self.post({"name": "test group"})

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailusers_groups:index"))

        # Check that the user was created
        groups = Group.objects.filter(name="test group")
        self.assertEqual(groups.count(), 1)

    def test_group_create_adding_permissions(self):
        response = self.post(
            {
                "name": "test group",
                "page_permissions-0-page": ["1"],
                "page_permissions-0-permissions": ["change_page", "publish_page"],
                "page_permissions-TOTAL_FORMS": ["1"],
                "document_permissions-0-collection": [
                    Collection.get_first_root_node().pk
                ],
                "document_permissions-0-permissions": [self.add_doc_permission.pk],
                "document_permissions-TOTAL_FORMS": ["1"],
            }
        )

        self.assertRedirects(response, reverse("wagtailusers_groups:index"))
        # The test group now exists, with two page permissions
        # and one 'add document' collection permission
        new_group = Group.objects.get(name="test group")
        self.assertEqual(new_group.page_permissions.all().count(), 2)
        self.assertEqual(
            new_group.collection_permissions.filter(
                permission=self.add_doc_permission
            ).count(),
            1,
        )

    def test_duplicate_page_permissions_error(self):
        # Try to submit multiple page permission entries for the same page
        response = self.post(
            {
                "name": "test group",
                "page_permissions-0-page": ["1"],
                "page_permissions-0-permissions": ["publish_page"],
                "page_permissions-1-page": ["1"],
                "page_permissions-1-permissions": ["change_page"],
                "page_permissions-TOTAL_FORMS": ["2"],
            }
        )

        self.assertEqual(response.status_code, 200)
        # formset should have a non-form error about the duplication
        self.assertTrue(response.context["permission_panels"][0].non_form_errors)

    def test_duplicate_document_permissions_error(self):
        # Try to submit multiple document permission entries for the same collection
        root_collection = Collection.get_first_root_node()
        response = self.post(
            {
                "name": "test group",
                "document_permissions-0-collection": [root_collection.pk],
                "document_permissions-0-permissions": [self.add_doc_permission.pk],
                "document_permissions-1-collection": [root_collection.pk],
                "document_permissions-1-permissions": [self.change_doc_permission.pk],
                "document_permissions-TOTAL_FORMS": ["2"],
            }
        )

        self.assertEqual(response.status_code, 200)
        # formset should have a non-form error about the duplication
        # (we don't know what index in permission_panels the formset will be,
        # so just assert that it happens on at least one permission_panel)
        self.assertTrue(
            any(
                hasattr(panel, "non_form_errors") and panel.non_form_errors
                for panel in response.context["permission_panels"]
            )
        )

    def test_can_submit_blank_permission_form(self):
        # the formsets for page / collection permissions should gracefully
        # handle (and ignore) forms that have been left entirely blank
        response = self.post(
            {
                "name": "test group",
                "page_permissions-0-page": [""],
                "page_permissions-TOTAL_FORMS": ["1"],
                "document_permissions-0-collection": [""],
                "document_permissions-TOTAL_FORMS": ["1"],
            }
        )

        self.assertRedirects(response, reverse("wagtailusers_groups:index"))
        # The test group now exists, with no page / document permissions
        new_group = Group.objects.get(name="test group")
        self.assertEqual(new_group.page_permissions.all().count(), 0)
        self.assertEqual(
            new_group.collection_permissions.filter(
                permission=self.add_doc_permission
            ).count(),
            0,
        )

    def test_custom_permissions_hidden(self):
        # Remove all permissions that show up in the 'custom permissions' column
        Permission.objects.exclude(
            Q(codename__startswith="add")
            | Q(codename__startswith="change")
            | Q(codename__startswith="delete")
        ).delete()

        # A custom permission that happens to also start with "change"
        Permission.objects.filter(
            codename="change_text",
            content_type__app_label="tests",
            content_type__model="custompermissionmodel",
        ).delete()

        response = self.get()

        self.assertInHTML("Custom permissions", response.content.decode(), count=0)

    def test_custom_permissions_shown(self):
        response = self.get()

        self.assertInHTML("Custom permissions", response.content.decode())

    def test_show_mixin_permissions(self):
        response = self.get()
        soup = self.get_soup(response.content)
        object_permissions = soup.select_one("#object-permissions-section")
        self.assertIsNotNone(object_permissions)

        # Should not show separate Publish, Lock, or Unlock columns
        # (i.e. the checkboxes should be in the "Custom permissions" column)
        self.assertFalse(
            {th.text.strip() for th in object_permissions.select("th")}
            & {"Publish", "Lock", "Unlock"}
        )

        mixin_permissions = (
            ("publish", DraftStateMixin),
            ("lock", LockableMixin),
            ("unlock", LockableMixin),
        )
        for action, mixin in mixin_permissions:
            with self.subTest(action=action):
                permissions = Permission.objects.filter(
                    codename__startswith=action,
                    content_type__app_label="tests",
                ).select_related("content_type")
                self.assertGreater(len(permissions), 0)

                for permission in permissions:
                    # Should show a checkbox for each permission in the
                    # "Custom permissions" column (thus inside a fieldset), with a
                    # simple "Can {action}" label (without the model name)
                    checkbox = object_permissions.select_one(
                        f'td > fieldset input[value="{permission.pk}"]'
                    )
                    self.assertIsNotNone(checkbox)
                    label = checkbox.parent
                    self.assertEqual(label.name, "label")
                    self.assertEqual(label.text.strip(), f"Can {action}")
                    # Should only show the permission for models with the mixin applied
                    content_type = permission.content_type
                    self.assertTrue(issubclass(content_type.model_class(), mixin))

    def test_strip_model_name_from_custom_permissions(self):
        """
        https://github.com/wagtail/wagtail/issues/10982
        Ensure model name or verbose name is stripped from permissions' labels
        for consistency with built-in permissions.
        """
        response = self.get()

        self.assertContains(response, "Can bulk update")
        self.assertContains(response, "Can start trouble")
        self.assertContains(response, "Cause chaos for")
        self.assertContains(response, "Change text")
        self.assertContains(response, "Manage")
        self.assertNotContains(response, "Can bulk_update")
        self.assertNotContains(response, "Can bulk update ADVANCED permission model")
        self.assertNotContains(response, "Cause chaos for advanced permission model")
        self.assertNotContains(response, "Manage custom permission model")

    def test_permission_with_same_action(self):
        """
        https://github.com/wagtail/wagtail/issues/11650
        Ensure that permissions with the same action (part before the first _ in
        the codename) are not hidden.
        """
        response = self.get()
        soup = self.get_soup(response.content)
        main_change_permission = Permission.objects.get(
            codename="change_custompermissionmodel",
            content_type__app_label="tests",
            content_type__model="custompermissionmodel",
        )
        custom_change_permission = Permission.objects.get(
            codename="change_text",
            content_type__app_label="tests",
            content_type__model="custompermissionmodel",
        )

        # Main change permission is in the dedicated column, so it's directly
        # inside a <td>, not inside a <fieldset>"
        self.assertIsNotNone(
            soup.select_one(f'td > input[value="{main_change_permission.pk}"]')
        )
        self.assertIsNone(
            soup.select_one(f'td > fieldset input[value="{main_change_permission.pk}"]')
        )

        # Custom "change_text" permission is in the custom permissions column,
        # so it's inside a <fieldset> and not directly inside a <td>
        self.assertIsNone(
            soup.select_one(f'td > input[value="{custom_change_permission.pk}"]')
        )
        self.assertIsNotNone(
            soup.select_one(
                f'td > fieldset input[value="{custom_change_permission.pk}"]'
            )
        )

    def test_custom_other_permissions_with_wagtail_admin_content_type(self):
        """
        https://github.com/wagtail/wagtail/issues/8086
        Allow custom permissions using Wagtail's Admin content type to be
        displayed in the "Other permissions" section.
        """
        admin_ct = ContentType.objects.get_for_model(Admin)
        custom_permission = Permission.objects.create(
            codename="roadmap_sync",
            name="Can sync roadmap items from GitHub",
            content_type=admin_ct,
        )

        with self.register_hook(
            "register_permissions",
            lambda: Permission.objects.filter(
                codename="roadmap_sync", content_type=admin_ct
            ),
        ):
            response = self.get()

        soup = self.get_soup(response.content)

        other_permissions = soup.select_one("#other-permissions-section")
        self.assertIsNotNone(other_permissions)

        custom_checkbox = other_permissions.select_one(
            f'input[value="{custom_permission.pk}"]'
        )
        self.assertIsNotNone(custom_checkbox)

        custom_label = other_permissions.select_one(
            f'label[for="{custom_checkbox.attrs.get("id")}"]'
        )
        self.assertIsNotNone(custom_label)
        self.assertEqual(
            custom_label.get_text(strip=True), "Can sync roadmap items from GitHub"
        )

    def test_formset_data_attributes(self):
        response = self.get()
        soup = self.get_soup(response.content)

        panel = soup.find(id="page-permissions-section")
        self.assertIn("w-formset", panel.attrs["data-controller"])
        self.assertEqual(
            "totalFormsInput",
            panel.find(id="id_page_permissions-TOTAL_FORMS").attrs[
                "data-w-formset-target"
            ],
        )
        self.assertEqual(
            "template",
            panel.find("template").attrs["data-w-formset-target"],
        )

        self.assertEqual(
            "forms",
            panel.find("table").find("tbody").attrs["data-w-formset-target"],
        )

        # Other panels are rendered with different formset classes, test one of them

        panel = soup.find(id="collection-management-permissions-section")
        self.assertIn("w-formset", panel.attrs["data-controller"])

        self.assertEqual(
            "totalFormsInput",
            panel.find(id="id_collection_permissions-TOTAL_FORMS").attrs[
                "data-w-formset-target"
            ],
        )
        self.assertEqual(
            "template",
            panel.find("template").attrs["data-w-formset-target"],
        )

        self.assertEqual(
            "forms",
            panel.find("table").find("tbody").attrs["data-w-formset-target"],
        )


class TestGroupEditView(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    def setUp(self):
        # Create a group to edit
        self.test_group = Group.objects.create(name="test group")
        self.root_page = Page.objects.get(pk=1)
        self.root_add_permission = GroupPagePermission.objects.create(
            page=self.root_page, permission_type="add", group=self.test_group
        )
        self.home_page = Page.objects.get(pk=2)

        # Get the hook-registered permissions, and add one to this group
        self.registered_permissions = Permission.objects.none()
        for fn in hooks.get_hooks("register_permissions"):
            self.registered_permissions = self.registered_permissions | fn()
        self.existing_permission = self.registered_permissions.order_by("pk")[0]
        self.another_permission = self.registered_permissions.order_by("pk")[1]

        self.test_group.permissions.add(self.existing_permission)

        # set up collections to test document permissions
        self.root_collection = Collection.get_first_root_node()
        self.evil_plans_collection = self.root_collection.add_child(name="Evil plans")
        self.add_doc_permission = Permission.objects.get(
            content_type__app_label="wagtaildocs", codename="add_document"
        )
        self.change_doc_permission = Permission.objects.get(
            content_type__app_label="wagtaildocs", codename="change_document"
        )
        GroupCollectionPermission.objects.create(
            group=self.test_group,
            collection=self.evil_plans_collection,
            permission=self.add_doc_permission,
        )

        # Login
        self.user = self.login()

    def get(self, params={}, group_id=None):
        return self.client.get(
            reverse("wagtailusers_groups:edit", args=(group_id or self.test_group.pk,)),
            params,
        )

    def post(self, post_data={}, group_id=None):
        post_defaults = {
            "name": "test group",
            "permissions": [self.existing_permission.pk],
            "page_permissions-TOTAL_FORMS": ["1"],
            "page_permissions-MAX_NUM_FORMS": ["1000"],
            "page_permissions-INITIAL_FORMS": ["1"],
            "page_permissions-0-page": [self.root_page.pk],
            "page_permissions-0-permissions": ["add_page"],
            "document_permissions-TOTAL_FORMS": ["1"],
            "document_permissions-MAX_NUM_FORMS": ["1000"],
            "document_permissions-INITIAL_FORMS": ["1"],
            "document_permissions-0-collection": [self.evil_plans_collection.pk],
            "document_permissions-0-permissions": [self.add_doc_permission.pk],
            "image_permissions-TOTAL_FORMS": ["0"],
            "image_permissions-MAX_NUM_FORMS": ["1000"],
            "image_permissions-INITIAL_FORMS": ["0"],
            "collection_permissions-TOTAL_FORMS": ["0"],
            "collection_permissions-MAX_NUM_FORMS": ["1000"],
            "collection_permissions-INITIAL_FORMS": ["0"],
        }
        for k, v in post_defaults.items():
            post_data[k] = post_data.get(k, v)
        return self.client.post(
            reverse("wagtailusers_groups:edit", args=(group_id or self.test_group.pk,)),
            post_data,
        )

    def add_non_registered_perm(self):
        # Some groups may have django permissions assigned that are not
        # hook-registered as part of the wagtail interface. We need to ensure
        # that these permissions are not overwritten by our views.
        # Tests that use this method are testing the aforementioned
        # functionality.
        self.non_registered_perms = Permission.objects.exclude(
            pk__in=self.registered_permissions
        )
        self.non_registered_perm = self.non_registered_perms[0]
        self.test_group.permissions.add(self.non_registered_perm)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailusers/groups/edit.html")
        self.assertBreadcrumbsItemsRendered(
            [
                {
                    "url": "/admin/groups/",
                    "label": "Groups",
                },
                {"url": "", "label": str(self.test_group)},
            ],
            response.content,
        )
        # Should contain the JS from the form and the template include
        page_chooser_js = versioned_static("wagtailadmin/js/page-chooser.js")
        self.assertContains(response, page_chooser_js)

        soup = self.get_soup(response.content)
        header = soup.select_one(".w-slim-header")
        history_url = reverse("wagtailusers_groups:history", args=(self.test_group.pk,))
        history_link = header.find("a", attrs={"href": history_url})
        self.assertIsNotNone(history_link)

        url_finder = AdminURLFinder(self.user)
        expected_url = "/admin/groups/edit/%d/" % self.test_group.id
        self.assertEqual(url_finder.get_edit_url(self.test_group), expected_url)

    def test_num_queries(self):
        # Warm up the cache
        self.get()
        with self.assertNumQueries(32):
            self.get()

    def test_nonexistent_group_redirect(self):
        self.assertEqual(self.get(group_id=100000).status_code, 404)

    def test_group_edit(self):
        response = self.post({"name": "test group edited"})

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailusers_groups:index"))

        # Check that the group was edited
        group = Group.objects.get(pk=self.test_group.pk)
        self.assertEqual(group.name, "test group edited")

        # On next load of the edit view,
        # should render the status panel with the last updated time
        response = self.get()
        self.assertContains(response, "test group edited")
        soup = self.get_soup(response.content)
        status_panel = soup.select_one('[data-side-panel="status"]')
        self.assertIsNotNone(status_panel)
        last_updated = status_panel.select_one(".w-help-text")
        self.assertIsNotNone(last_updated)
        self.assertRegex(
            last_updated.get_text(strip=True),
            f"[0-9][0-9]:[0-9][0-9] by {self.user.get_username()}",
        )
        history_url = reverse("wagtailusers_groups:history", args=(self.test_group.pk,))
        history_link = status_panel.select_one(f'a[href="{history_url}"]')
        self.assertIsNotNone(history_link)

    def test_group_edit_validation_error(self):
        # Leave "name" field blank. This should give a validation error
        response = self.post({"name": ""})

        # Should not redirect to index
        self.assertEqual(response.status_code, 200)

    def test_group_edit_adding_page_permissions_same_page(self):
        # The test group has one page permission to begin with - 'add' permission on root.
        # Add two additional permission types on the root page
        self.assertEqual(self.test_group.page_permissions.count(), 1)
        response = self.post(
            {
                "page_permissions-0-permissions": [
                    "add_page",
                    "publish_page",
                    "change_page",
                ],
            }
        )

        self.assertRedirects(response, reverse("wagtailusers_groups:index"))
        # The test group now has three page permissions
        self.assertEqual(self.test_group.page_permissions.count(), 3)

    def test_group_edit_adding_document_permissions_same_collection(self):
        # The test group has one document permission to begin with -
        # 'add' permission on evil_plans.
        # Add 'change' permission on evil_plans
        self.assertEqual(
            self.test_group.collection_permissions.filter(
                permission__content_type__app_label="wagtaildocs"
            ).count(),
            1,
        )
        response = self.post(
            {
                "document_permissions-0-permissions": [
                    self.add_doc_permission.pk,
                    self.change_doc_permission.pk,
                ],
            }
        )

        self.assertRedirects(response, reverse("wagtailusers_groups:index"))
        # The test group now has two document permissions
        self.assertEqual(
            self.test_group.collection_permissions.filter(
                permission__content_type__app_label="wagtaildocs"
            ).count(),
            2,
        )

    def test_group_edit_adding_document_permissions_different_collection(self):
        # The test group has one document permission to begin with -
        # 'add' permission on evil_plans.
        # Add 'add' and 'change' permission on the root collection
        self.assertEqual(
            self.test_group.collection_permissions.filter(
                permission__content_type__app_label="wagtaildocs"
            ).count(),
            1,
        )
        response = self.post(
            {
                "document_permissions-TOTAL_FORMS": ["2"],
                "document_permissions-1-collection": [self.root_collection.pk],
                "document_permissions-1-permissions": [
                    self.add_doc_permission.pk,
                    self.change_doc_permission.pk,
                ],
            }
        )

        self.assertRedirects(response, reverse("wagtailusers_groups:index"))
        # The test group now has three document permissions
        self.assertEqual(
            self.test_group.collection_permissions.filter(
                permission__content_type__app_label="wagtaildocs"
            ).count(),
            3,
        )

    def test_group_edit_deleting_page_permissions(self):
        # The test group has one page permission to begin with
        self.assertEqual(self.test_group.page_permissions.count(), 1)

        response = self.post(
            {
                "page_permissions-0-DELETE": ["1"],
            }
        )

        self.assertRedirects(response, reverse("wagtailusers_groups:index"))
        # The test group now has zero page permissions
        self.assertEqual(self.test_group.page_permissions.count(), 0)

    def test_group_edit_deleting_document_permissions(self):
        # The test group has one document permission to begin with
        self.assertEqual(
            self.test_group.collection_permissions.filter(
                permission__content_type__app_label="wagtaildocs"
            ).count(),
            1,
        )

        response = self.post(
            {
                "document_permissions-0-DELETE": ["1"],
            }
        )

        self.assertRedirects(response, reverse("wagtailusers_groups:index"))
        # The test group now has zero document permissions
        self.assertEqual(
            self.test_group.collection_permissions.filter(
                permission__content_type__app_label="wagtaildocs"
            ).count(),
            0,
        )

    def test_group_edit_loads_with_django_permissions_shown(self):
        # the checkbox for self.existing_permission should be ticked
        response = self.get()

        # use allow_extra_attrs because the input will also have an id (with an unpredictable value)
        self.assertTagInHTML(
            '<input name="permissions" type="checkbox" checked value="%s">'
            % self.existing_permission.id,
            response.content.decode(),
            allow_extra_attrs=True,
        )

    def test_group_edit_displays_collection_nesting(self):
        # Add a child collection to Evil Plans.
        self.evil_plans_collection.add_child(instance=Collection(name="Eviler Plans"))
        response = self.get()

        # "Eviler Plans" should be prefixed with &#x21b3 (↳) and exactly 4 non-breaking spaces
        # after the <option> tag.
        # There are 4 instances because we have one document permission + 3 in the form template javascript.
        self.assertContains(
            response, ">&nbsp;&nbsp;&nbsp;&nbsp;&#x21b3 Eviler Plans", count=4
        )

    def test_group_edit_loads_with_page_permissions_shown(self):
        # The test group has one page permission to begin with
        self.assertEqual(self.test_group.page_permissions.count(), 1)

        response = self.get()

        page_permissions_formset = response.context["permission_panels"][0]
        self.assertEqual(
            page_permissions_formset.management_form["INITIAL_FORMS"].value(), 1
        )
        self.assertEqual(
            page_permissions_formset.forms[0]["page"].value(), self.root_page.pk
        )
        self.assertEqual(
            page_permissions_formset.forms[0]["permissions"].value(), ["add_page"]
        )

        # add edit permission on root
        GroupPagePermission.objects.create(
            page=self.root_page, permission_type="change", group=self.test_group
        )

        # The test group now has two page permissions on root (but only one form covering both)
        self.assertEqual(self.test_group.page_permissions.count(), 2)

        # Reload the page and check the form instances
        response = self.get()
        page_permissions_formset = response.context["permission_panels"][0]
        self.assertEqual(
            page_permissions_formset.management_form["INITIAL_FORMS"].value(), 1
        )
        self.assertEqual(len(page_permissions_formset.forms), 1)
        self.assertEqual(
            page_permissions_formset.forms[0]["page"].value(), self.root_page.pk
        )
        self.assertEqual(
            set(page_permissions_formset.forms[0]["permissions"].value()),
            {"add_page", "change_page"},
        )

        # add edit permission on home
        GroupPagePermission.objects.create(
            page=self.home_page, permission_type="change", group=self.test_group
        )

        # The test group now has three page permissions, over two forms
        self.assertEqual(self.test_group.page_permissions.count(), 3)

        # Reload the page and check the form instances
        response = self.get()
        page_permissions_formset = response.context["permission_panels"][0]
        self.assertEqual(
            page_permissions_formset.management_form["INITIAL_FORMS"].value(), 2
        )
        self.assertEqual(
            page_permissions_formset.forms[0]["page"].value(), self.root_page.pk
        )
        self.assertEqual(
            set(page_permissions_formset.forms[0]["permissions"].value()),
            {"add_page", "change_page"},
        )
        self.assertEqual(
            page_permissions_formset.forms[1]["page"].value(), self.home_page.pk
        )
        self.assertEqual(
            page_permissions_formset.forms[1]["permissions"].value(), ["change_page"]
        )

    def test_duplicate_page_permissions_error(self):
        # Try to submit multiple page permission entries for the same page
        response = self.post(
            {
                "page_permissions-1-page": [self.root_page.pk],
                "page_permissions-1-permissions": ["change_page"],
                "page_permissions-TOTAL_FORMS": ["2"],
            }
        )

        self.assertEqual(response.status_code, 200)
        # the formset should have a non-form error
        self.assertTrue(response.context["permission_panels"][0].non_form_errors)

    def test_duplicate_document_permissions_error(self):
        # Try to submit multiple document permission entries for the same collection
        response = self.post(
            {
                "document_permissions-1-page": [self.evil_plans_collection.pk],
                "document_permissions-1-permissions": [self.change_doc_permission],
                "document_permissions-TOTAL_FORMS": ["2"],
            }
        )

        self.assertEqual(response.status_code, 200)
        # the formset should have a non-form error
        self.assertTrue(
            any(
                hasattr(panel, "non_form_errors") and panel.non_form_errors
                for panel in response.context["permission_panels"]
            )
        )

    def test_group_add_registered_django_permissions(self):
        # The test group has one django permission to begin with
        self.assertEqual(self.test_group.permissions.count(), 1)
        response = self.post(
            {"permissions": [self.existing_permission.pk, self.another_permission.pk]}
        )
        self.assertRedirects(response, reverse("wagtailusers_groups:index"))
        self.assertEqual(self.test_group.permissions.count(), 2)

    def test_group_retains_non_registered_permissions_when_editing(self):
        self.add_non_registered_perm()
        original_permissions = list(
            self.test_group.permissions.all()
        )  # list() to force evaluation

        # submit the form with no changes (only submitting the existing
        # permission, as in the self.post function definition)
        self.post()

        # See that the group has the same permissions as before
        self.assertEqual(list(self.test_group.permissions.all()), original_permissions)
        self.assertEqual(self.test_group.permissions.count(), 2)

    def test_group_retains_non_registered_permissions_when_adding(self):
        self.add_non_registered_perm()
        # Add a second registered permission
        self.post(
            {"permissions": [self.existing_permission.pk, self.another_permission.pk]}
        )

        # See that there are now three permissions in total
        self.assertEqual(self.test_group.permissions.count(), 3)
        # ...including the non-registered one
        self.assertIn(self.non_registered_perm, self.test_group.permissions.all())

    def test_group_retains_non_registered_permissions_when_deleting(self):
        self.add_non_registered_perm()
        # Delete all registered permissions
        self.post({"permissions": []})

        # See that the non-registered permission is still there
        self.assertEqual(self.test_group.permissions.count(), 1)
        self.assertEqual(self.test_group.permissions.all()[0], self.non_registered_perm)

    def test_is_custom_permission_checked(self):
        # Add a permission from the 'custom permission' column to the user's group
        custom_permission = Permission.objects.get(codename="view_fullfeaturedsnippet")
        self.test_group.permissions.add(custom_permission)

        response = self.get()

        soup = self.get_soup(response.content)
        checkbox = soup.find_all(
            "input",
            attrs={
                "name": "permissions",
                "checked": True,
                "value": custom_permission.id,
                "data-action": "w-bulk#toggle",
                "data-w-bulk-group-param": "custom",
                "data-w-bulk-target": "item",
            },
        )

        self.assertEqual(len(checkbox), 1)

    def test_show_mixin_permissions(self):
        response = self.get()
        soup = self.get_soup(response.content)
        object_permissions = soup.select_one("#object-permissions-section")
        self.assertIsNotNone(object_permissions)

        # Should not show separate Publish, Lock, or Unlock columns
        # (i.e. the checkboxes should be in the "Custom permissions" column)
        self.assertFalse(
            {th.text.strip() for th in object_permissions.select("th")}
            & {"Publish", "Lock", "Unlock"}
        )

        mixin_permissions = (
            ("publish", DraftStateMixin),
            ("lock", LockableMixin),
            ("unlock", LockableMixin),
        )
        for action, mixin in mixin_permissions:
            with self.subTest(action=action):
                permissions = Permission.objects.filter(
                    codename__startswith=action,
                    content_type__app_label="tests",
                ).select_related("content_type")
                self.assertGreater(len(permissions), 0)

                for permission in permissions:
                    # Should show a checkbox for each permission in the
                    # "Custom permissions" column (thus inside a fieldset), with a
                    # simple "Can {action}" label (without the model name)
                    checkbox = object_permissions.select_one(
                        f'td > fieldset input[value="{permission.pk}"]'
                    )
                    self.assertIsNotNone(checkbox)
                    label = checkbox.parent
                    self.assertEqual(label.name, "label")
                    self.assertEqual(label.text.strip(), f"Can {action}")
                    # Should only show the permission for models with the mixin applied
                    content_type = permission.content_type
                    self.assertTrue(issubclass(content_type.model_class(), mixin))

    def test_group_edit_loads_with_django_permissions_in_order(self):
        # ensure objects are ordered as registered, followed by the default ordering

        def object_position(object_perms):
            # returns the list of objects in the object permsissions
            # as provided by the format_permissions tag

            def flatten(perm_set):
                # iterates through perm_set dict, flattens the list if present
                for v in perm_set.values():
                    if isinstance(v, list):
                        yield from v
                    else:
                        yield v

            return [
                (
                    perm.content_type.app_label,
                    perm.content_type.model,
                )
                for perm_set in object_perms
                for perm in [
                    next(
                        v
                        for v in flatten(perm_set)
                        if isinstance(v, dict) and "perm" in v
                    )["perm"]
                ]
            ]

        # Set order on two objects, should appear first and second
        register_permission_order("snippetstests.fancysnippet", order=100)
        register_permission_order("snippetstests.standardsnippet", order=110)

        response = self.get()
        object_positions = object_position(response.context["object_perms"])
        self.assertEqual(
            object_positions[0],
            ("snippetstests", "fancysnippet"),
            msg="Configured object permission order is incorrect",
        )
        self.assertEqual(
            object_positions[1],
            ("snippetstests", "standardsnippet"),
            msg="Configured object permission order is incorrect",
        )

        # Swap order of the objects
        register_permission_order("snippetstests.standardsnippet", order=90)
        response = self.get()
        object_positions = object_position(response.context["object_perms"])

        self.assertEqual(
            object_positions[0],
            ("snippetstests", "standardsnippet"),
            msg="Configured object permission order is incorrect",
        )
        self.assertEqual(
            object_positions[1],
            ("snippetstests", "fancysnippet"),
            msg="Configured object permission order is incorrect",
        )

        # Test remainder of objects are sorted
        self.assertEqual(
            object_positions[2:],
            sorted(object_positions[2:]),
            msg="Default object permission order is incorrect",
        )

    def test_data_attributes_for_bulk_selection(self):
        response = self.get()
        soup = self.get_soup(response.content)

        table = soup.find("table", "listing")
        self.assertIn(table["data-controller"], "w-bulk")

        # confirm there is a single select all checkbox for all items
        toggle_all = table.select('tfoot th input[data-w-bulk-target="all"]')
        self.assertEqual(len(toggle_all), 1)
        self.assertEqual(toggle_all[0]["data-action"], "w-bulk#toggleAll")

        # confirm there is one 'add' select all checkbox
        toggle_all_add = table.select(
            'tfoot td input[data-w-bulk-target="all"][data-w-bulk-group-param="add"]'
        )
        self.assertEqual(len(toggle_all_add), 1)
        self.assertEqual(toggle_all_add[0]["data-action"], "w-bulk#toggleAll")

        # confirm that the individual object permissions have the correct attributes
        toggle_add_items = table.select(
            'tbody td input[data-w-bulk-target="item"][data-w-bulk-group-param="add"]'
        )
        self.assertGreaterEqual(len(toggle_add_items), 30)
        self.assertEqual(toggle_add_items[0]["data-action"], "w-bulk#toggle")

    def test_formset_data_attributes(self):
        response = self.get()
        soup = self.get_soup(response.content)

        panel = soup.find(id="page-permissions-section")
        self.assertIn("w-formset", panel.attrs["data-controller"])
        self.assertEqual(
            "totalFormsInput",
            panel.find(id="id_page_permissions-TOTAL_FORMS").attrs[
                "data-w-formset-target"
            ],
        )
        self.assertEqual(
            "template",
            panel.find("template").attrs["data-w-formset-target"],
        )

        tbody = panel.find("table").find("tbody")
        self.assertEqual(
            "forms",
            tbody.attrs["data-w-formset-target"],
        )

        row = tbody.find("tr")
        self.assertEqual(
            "child",
            row.attrs["data-w-formset-target"],
        )
        self.assertEqual(
            "deleteInput",
            row.find(id="id_page_permissions-0-DELETE").attrs["data-w-formset-target"],
        )

        # Other panels are rendered with different formset classes, test one of them

        panel = soup.find(id="collection-management-permissions-section")
        self.assertIn("w-formset", panel.attrs["data-controller"])

        self.assertEqual(
            "totalFormsInput",
            panel.find(id="id_collection_permissions-TOTAL_FORMS").attrs[
                "data-w-formset-target"
            ],
        )
        self.assertEqual(
            "template",
            panel.find("template").attrs["data-w-formset-target"],
        )
        self.assertEqual(
            "forms",
            panel.find("table").find("tbody").attrs["data-w-formset-target"],
        )


class TestGroupHistoryView(WagtailTestUtils, TestCase):
    # More thorough tests are in test_model_viewset

    @classmethod
    def setUpTestData(cls):
        cls.test_group = Group.objects.create(name="test group")
        cls.url = reverse("wagtailusers_groups:history", args=(cls.test_group.pk,))

    def setUp(self):
        self.user = self.login()

    def test_simple(self):
        log(self.test_group, "wagtail.create", user=self.user)
        log(self.test_group, "wagtail.edit", user=self.user)
        response = self.client.get(self.url)
        self.assertTemplateUsed("wagtailadmin/generic/listing.html")
        self.assertContains(response, "Created")
        self.assertContains(response, "Edited")


class TestGroupViewSet(TestCase):
    app_config_attr = "group_viewset"
    default_viewset_cls = GroupViewSet
    custom_viewset_cls = CustomGroupViewSet
    create_form_cls = CustomGroupForm
    edit_form_cls = CustomGroupForm

    def setUp(self):
        self.app_config = apps.get_app_config("wagtailusers")

    def test_get_viewset_cls(self):
        self.assertIs(
            get_viewset_cls(self.app_config, self.app_config_attr),
            self.default_viewset_cls,
        )

    def test_get_viewset_cls_with_custom_form(self):
        with unittest.mock.patch.object(
            self.app_config,
            self.app_config_attr,
            new=f"wagtail.users.tests.{self.custom_viewset_cls.__name__}",
        ):
            group_viewset = get_viewset_cls(self.app_config, self.app_config_attr)
        self.assertIs(group_viewset, self.custom_viewset_cls)
        self.assertEqual(group_viewset.icon, "custom-icon")
        viewset = group_viewset()
        self.assertIs(viewset.get_form_class(for_update=False), self.create_form_cls)
        self.assertIs(viewset.get_form_class(for_update=True), self.edit_form_cls)

    def test_get_viewset_cls_custom_form_invalid_value(self):
        with unittest.mock.patch.object(
            self.app_config, self.app_config_attr, new="asdfasdf"
        ):
            with self.assertRaisesMessage(
                ImproperlyConfigured,
                f"Invalid setting for WagtailUsersAppConfig.{self.app_config_attr}: "
                "asdfasdf doesn't look like a module path",
            ):
                get_viewset_cls(self.app_config, self.app_config_attr)

    def test_get_viewset_cls_custom_form_does_not_exist(self):
        with unittest.mock.patch.object(
            self.app_config,
            self.app_config_attr,
            new="wagtail.users.tests.CustomClassDoesNotExist",
        ):
            with self.assertRaisesMessage(
                ImproperlyConfigured,
                f"Invalid setting for WagtailUsersAppConfig.{self.app_config_attr}: "
                'Module "wagtail.users.tests" does not define a "CustomClassDoesNotExist" attribute/class',
            ):
                get_viewset_cls(self.app_config, self.app_config_attr)


class TestUserViewSet(TestGroupViewSet):
    app_config_attr = "user_viewset"
    default_viewset_cls = UserViewSet
    custom_viewset_cls = CustomUserViewSet
    create_form_cls = CustomUserCreationForm
    edit_form_cls = CustomUserEditForm

    def test_registered_permissions(self):
        group_ct = ContentType.objects.get_for_model(Group)
        qs = Permission.objects.none()
        for fn in hooks.get_hooks("register_permissions"):
            qs |= fn()
        registered_user_permissions = qs.filter(content_type=group_ct)
        self.assertEqual(
            set(registered_user_permissions.values_list("codename", flat=True)),
            {"add_group", "change_group", "delete_group"},
        )


class TestAuthorisationIndexView(WagtailTestUtils, TestCase):
    def setUp(self):
        self._user = self.create_user(username="auth_user", password="password")
        self._user.user_permissions.add(Permission.objects.get(codename="access_admin"))
        self.login(username="auth_user", password="password")

    def get(self, params={}):
        return self.client.get(reverse("wagtailusers_users:index"))

    def test_simple(self):
        response = self.get()
        # Should redirect to admin index (permission denied)
        self.assertRedirects(response, reverse("wagtailadmin_home"))
        self.assertEqual(
            response.context["message"],
            "Sorry, you do not have permission to access this area.",
        )

    def test_authorised(self):
        for permission in ("add", "change", "delete"):
            permission_name = f"{permission}_{AUTH_USER_MODEL_NAME.lower()}"
            permission_object = Permission.objects.get(codename=permission_name)
            self._user.user_permissions.add(permission_object)

            response = self.get()
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "wagtailusers/users/index.html")
            self.assertContains(response, "auth_user")

            self._user.user_permissions.remove(permission_object)


class TestAuthorisationCreateView(WagtailTestUtils, TestCase):
    def setUp(self):
        self._user = self.create_user(username="auth_user", password="password")
        self._user.user_permissions.add(Permission.objects.get(codename="access_admin"))
        self.login(username="auth_user", password="password")

    def get(self, params={}):
        return self.client.get(reverse("wagtailusers_users:add"), params)

    def post(self, post_data={}):
        return self.client.post(reverse("wagtailusers_users:add"), post_data)

    def gain_permissions(self):
        self._user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label=AUTH_USER_APP_LABEL,
                codename=f"add_{AUTH_USER_MODEL_NAME.lower()}",
            )
        )

    def test_simple(self):
        response = self.get()
        # Should redirect to admin index (permission denied)
        self.assertRedirects(response, reverse("wagtailadmin_home"))
        self.assertEqual(
            response.context["message"],
            "Sorry, you do not have permission to access this area.",
        )

    def test_authorised(self):
        self.gain_permissions()
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailusers/users/create.html")

    def test_unauthorised_post(self):
        response = self.post(
            {
                "username": "testuser",
                "email": "test@user.com",
                "first_name": "Test",
                "last_name": "User",
                "password1": "password",
                "password2": "password",
            }
        )
        # Should redirect to admin index (permission denied)
        self.assertRedirects(response, reverse("wagtailadmin_home"))
        self.assertEqual(
            response.context["message"],
            "Sorry, you do not have permission to access this area.",
        )
        user = get_user_model().objects.filter(email="test@user.com")
        self.assertFalse(user.exists())

    def test_authorised_post(self):
        self.gain_permissions()
        response = self.post(
            {
                "username": "testuser",
                "email": "test@user.com",
                "first_name": "Test",
                "last_name": "User",
                "password1": "password",
                "password2": "password",
            }
        )
        self.assertRedirects(response, reverse("wagtailusers_users:index"))
        user = get_user_model().objects.filter(email="test@user.com")
        self.assertTrue(user.exists())


class TestAuthorisationEditView(WagtailTestUtils, TestCase):
    def setUp(self):
        self._user = self.create_user(username="auth_user", password="password")
        self._user.user_permissions.add(Permission.objects.get(codename="access_admin"))
        self.login(username="auth_user", password="password")
        self.test_user = self.create_user(
            username="testuser",
            email="testuser@email.com",
            first_name="Original",
            last_name="User",
            password="password",
        )

    def get(self, params={}, user_id=None):
        return self.client.get(
            reverse("wagtailusers_users:edit", args=(user_id or self.test_user.pk,)),
            params,
        )

    def post(self, post_data={}, user_id=None):
        return self.client.post(
            reverse("wagtailusers_users:edit", args=(user_id or self.test_user.pk,)),
            post_data,
        )

    def gain_permissions(self):
        self._user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label=AUTH_USER_APP_LABEL,
                codename=f"change_{AUTH_USER_MODEL_NAME.lower()}",
            )
        )

    def test_simple(self):
        response = self.get()
        # Should redirect to admin index (permission denied)
        self.assertRedirects(response, reverse("wagtailadmin_home"))
        self.assertEqual(
            response.context["message"],
            "Sorry, you do not have permission to access this area.",
        )

    def test_authorised_get(self):
        self.gain_permissions()
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailusers/users/edit.html")

    def test_unauthorised_post(self):
        response = self.post(
            {
                "username": "testuser",
                "email": "test@user.com",
                "first_name": "Edited",
                "last_name": "User",
                "password1": "newpassword",
                "password2": "newpassword",
                "is_active": "on",
            }
        )
        # Should redirect to admin index (permission denied)
        self.assertRedirects(response, reverse("wagtailadmin_home"))
        self.assertEqual(
            response.context["message"],
            "Sorry, you do not have permission to access this area.",
        )
        user = get_user_model().objects.get(pk=self.test_user.pk)
        self.assertNotEqual(user.first_name, "Edited")
        self.assertFalse(user.check_password("newpassword"))

    def test_authorised_post(self):
        self.gain_permissions()
        response = self.post(
            {
                "username": "testuser",
                "email": "test@user.com",
                "first_name": "Edited",
                "last_name": "User",
                "password1": "newpassword",
                "password2": "newpassword",
                "is_active": "on",
            }
        )
        self.assertRedirects(response, reverse("wagtailusers_users:index"))
        user = get_user_model().objects.get(pk=self.test_user.pk)
        self.assertEqual(user.first_name, "Edited")
        self.assertTrue(user.check_password("newpassword"))


class TestAuthorisationDeleteView(WagtailTestUtils, TestCase):
    def setUp(self):
        self._user = self.create_user(username="auth_user", password="password")
        self._user.user_permissions.add(Permission.objects.get(codename="access_admin"))
        self.login(username="auth_user", password="password")
        self.test_user = self.create_user(
            username="test_user",
            email="test_user@email.com",
            password="password",
        )

    def get(self, params={}):
        return self.client.get(
            reverse("wagtailusers_users:delete", args=(self.test_user.pk,)), params
        )

    def post(self, post_data={}):
        return self.client.post(
            reverse("wagtailusers_users:delete", args=(self.test_user.pk,)), post_data
        )

    def gain_permissions(self):
        self._user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label=AUTH_USER_APP_LABEL,
                codename=f"delete_{AUTH_USER_MODEL_NAME.lower()}",
            )
        )

    def test_simple(self):
        response = self.get()
        # Should redirect to admin index (permission denied)
        self.assertRedirects(response, reverse("wagtailadmin_home"))
        self.assertEqual(
            response.context["message"],
            "Sorry, you do not have permission to access this area.",
        )

    def test_authorised_get(self):
        self.gain_permissions()
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailusers/users/confirm_delete.html")

    def test_unauthorised_post(self):
        response = self.post()
        # Should redirect to admin index (permission denied)
        self.assertRedirects(response, reverse("wagtailadmin_home"))
        self.assertEqual(
            response.context["message"],
            "Sorry, you do not have permission to access this area.",
        )
        user = get_user_model().objects.filter(email="test_user@email.com")
        self.assertTrue(user.exists())

    def test_authorised_post(self):
        self.gain_permissions()
        response = self.post()
        self.assertRedirects(response, reverse("wagtailusers_users:index"))
        user = get_user_model().objects.filter(email="test_user@email.com")
        self.assertFalse(user.exists())


class TestTemplateTags(WagtailTestUtils, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = cls.create_superuser("admin")
        cls.request = get_dummy_request()
        cls.request.user = cls.user
        cls.test_user = cls.create_user(
            username="testuser",
            email="testuser@email.com",
            password="password",
        )

    def test_user_listing_buttons(self):
        template = """
            {% load wagtailusers_tags %}
            {% for user in users %}
                <ul class="actions">
                    {% user_listing_buttons user %}
                </ul>
            {% endfor %}
        """

        def hook(user, request_user):
            self.assertEqual(user, self.test_user)
            self.assertEqual(request_user, self.user)
            yield UserListingButton(
                "Show profile",
                f"/goes/to/a/url/{user.pk}",
                priority=30,
            )

        with self.register_hook("register_user_listing_buttons", hook):
            with self.assertWarnsMessage(
                RemovedInWagtail70Warning,
                "`user_listing_buttons` template tag is deprecated.",
            ):
                html = Template(template).render(
                    RequestContext(self.request, {"users": [self.test_user]})
                )

        soup = self.get_soup(html)

        profile_url = f"/goes/to/a/url/{self.test_user.pk}"
        top_level_custom_button = soup.select_one(f"li > a[href='{profile_url}']")
        self.assertIsNotNone(top_level_custom_button)
        self.assertEqual(
            top_level_custom_button.text.strip(),
            "Show profile",
        )

    def test_user_listing_buttons_with_deprecated_hook(self):
        template = """
            {% load wagtailusers_tags %}
            {% for user in users %}
                <ul class="actions">
                    {% user_listing_buttons user %}
                </ul>
            {% endfor %}
        """

        def deprecated_hook(context, user):
            self.assertEqual(user, self.test_user)
            self.assertEqual(context.request.user, self.user)
            yield UserListingButton(
                "Show profile",
                f"/goes/to/a/url/{user.pk}",
                priority=30,
            )

        with self.register_hook("register_user_listing_buttons", deprecated_hook):
            with self.assertWarns(RemovedInWagtail70Warning) as warning_manager:
                html = Template(template).render(
                    RequestContext(self.request, {"users": [self.test_user]})
                )

        self.assertEqual(
            [str(w.message) for w in warning_manager.warnings],
            [
                # Deprecation of the template tag
                "`user_listing_buttons` template tag is deprecated.",
                # Deprecation of the hook signature
                "`register_user_listing_buttons` hook functions should accept a "
                "`request_user` argument instead of `context` - "
                "wagtail.users.tests.test_admin_views.deprecated_hook needs to be updated",
            ],
        )

        soup = self.get_soup(html)
        profile_url = f"/goes/to/a/url/{self.test_user.pk}"
        top_level_custom_button = soup.select_one(f"li > a[href='{profile_url}']")
        self.assertIsNotNone(top_level_custom_button)
        self.assertEqual(
            top_level_custom_button.text.strip(),
            "Show profile",
        )


class TestAdminPermissions(WagtailTestUtils, TestCase):
    def test_registered_user_permissions(self):
        user_ct = ContentType.objects.get_for_model(User)
        model_name = User._meta.model_name
        qs = Permission.objects.none()
        for fn in hooks.get_hooks("register_permissions"):
            qs |= fn()
        registered_user_permissions = qs.filter(content_type=user_ct)
        self.assertEqual(
            set(registered_user_permissions.values_list("codename", flat=True)),
            {f"add_{model_name}", f"change_{model_name}", f"delete_{model_name}"},
        )
