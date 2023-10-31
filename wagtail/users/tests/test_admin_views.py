import unittest.mock

from django import forms
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ImproperlyConfigured
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail import hooks
from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.compat import AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME
from wagtail.models import (
    Collection,
    GroupCollectionPermission,
    GroupPagePermission,
    Page,
)
from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.template_tests import AdminTemplateTestUtils
from wagtail.users.forms import UserCreationForm, UserEditForm
from wagtail.users.models import UserProfile
from wagtail.users.permission_order import register as register_permission_order
from wagtail.users.views.groups import GroupViewSet
from wagtail.users.views.users import get_user_creation_form, get_user_edit_form
from wagtail.users.wagtail_hooks import get_group_viewset_cls

delete_user_perm_codename = f"delete_{AUTH_USER_MODEL_NAME.lower()}"
change_user_perm_codename = f"change_{AUTH_USER_MODEL_NAME.lower()}"

User = get_user_model()


def test_avatar_provider(user, default, size=50):
    return "/nonexistent/path/to/avatar.png"


class CustomUserCreationForm(UserCreationForm):
    country = forms.CharField(required=True, label="Country")
    attachment = forms.FileField(required=True, label="Attachment")


class CustomUserEditForm(UserEditForm):
    country = forms.CharField(required=True, label="Country")
    attachment = forms.FileField(required=True, label="Attachment")


class CustomGroupViewSet(GroupViewSet):
    icon = "custom-icon"


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
        user_form = get_user_creation_form()
        self.assertIs(user_form, CustomUserCreationForm)

    @override_settings(WAGTAIL_USER_EDIT_FORM="wagtail.users.tests.CustomUserEditForm")
    def test_get_user_edit_form_with_custom_form(self):
        user_form = get_user_edit_form()
        self.assertIs(user_form, CustomUserEditForm)

    @override_settings(
        WAGTAIL_USER_CREATION_FORM="wagtail.users.tests.CustomUserCreationFormDoesNotExist"
    )
    def test_get_user_creation_form_with_invalid_form(self):
        self.assertRaises(ImproperlyConfigured, get_user_creation_form)

    @override_settings(
        WAGTAIL_USER_EDIT_FORM="wagtail.users.tests.CustomUserEditFormDoesNotExist"
    )
    def test_get_user_edit_form_with_invalid_form(self):
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
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailusers/users/index.html")
        self.assertContains(response, "testuser")
        # response should contain page furniture, including the "Add a user" button
        self.assertContains(response, "Add a user")
        self.assertBreadcrumbsNotRendered(response.content)

    def test_inexisting_group(self):
        response = self.get(group_id=9999)
        self.assertEqual(response.status_code, 404)

    def test_search(self):
        response = self.get({"q": "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["query_string"], "Hello")

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
        # page numbers in range should be accepted
        response = self.get({"p": 1})
        self.assertEqual(response.status_code, 200)
        # page numbers out of range should return 404
        response = self.get({"p": 9999})
        self.assertEqual(response.status_code, 404)


class TestGroupUsersResultsView(WagtailTestUtils, TestCase):
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
                "wagtailusers_groups:users_results",
                args=(group_id or self.test_group.pk,),
            ),
            params,
        )

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailusers/users/results.html")
        self.assertContains(response, "testuser")
        # response should contain not page furniture
        self.assertNotContains(response, "Add a user")


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
        self.login()

    def get(self, params={}):
        return self.client.get(reverse("wagtailusers_users:index"), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailusers/users/index.html")
        self.assertContains(response, "testuser")
        # response should contain page furniture, including the "Add a user" button
        self.assertContains(response, "Add a user")
        self.assertBreadcrumbsNotRendered(response.content)

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
        # page numbers in range should be accepted
        response = self.get({"p": 1})
        self.assertEqual(response.status_code, 200)
        # page numbers out of range should return 404
        response = self.get({"p": 9999})
        self.assertEqual(response.status_code, 404)

    def test_valid_ordering(self):
        # checking that only valid ordering used, in case of `IndexView` the valid
        # ordering fields are "name" and "username".
        response = self.get({"ordering": "email"})
        self.assertNotEqual(response.context_data["ordering"], "email")
        # name is default ordering in `IndexView`.
        self.assertEqual(response.context_data["ordering"], "name")
        response = self.get({"ordering": "username"})
        self.assertEqual(response.context_data["ordering"], "username")

    def test_num_queries(self):
        # Warm up
        self.get()

        num_queries = 9
        with self.assertNumQueries(num_queries):
            self.get()

        # Ensure we don't have any N+1 queries
        self.create_user("test", "test@example.com", "gu@rd14n")
        with self.assertNumQueries(num_queries):
            self.get()


class TestUserIndexResultsView(WagtailTestUtils, TestCase):
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
        self.assertTemplateUsed(response, "wagtailusers/users/results.html")
        self.assertContains(response, "testuser")
        # response should not contain page furniture
        self.assertNotContains(response, "Add a user")


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
        self.assertBreadcrumbsNotRendered(response.content)

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
        WAGTAIL_USER_CUSTOM_FIELDS=["country", "document"],
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
        self.assertBreadcrumbsNotRendered(response.content)

        url_finder = AdminURLFinder(self.current_user)
        expected_url = "/admin/users/%s/" % self.test_user.pk
        self.assertEqual(url_finder.get_edit_url(self.test_user), expected_url)

    def test_nonexistant_redirect(self):
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
        self.assertBreadcrumbsNotRendered(response.content)

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


class TestGroupIndexResultsView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse("wagtailusers_groups:index_results"), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/listing_results.html")
        # response should not contain page furniture
        self.assertNotContains(response, "Add a group")

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
        self.assertBreadcrumbsNotRendered(response.content)

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
            | Q(codename__startswith="publish")
        ).delete()

        response = self.get()

        self.assertInHTML("Custom permissions", response.content.decode(), count=0)

    def test_custom_permissions_shown(self):
        response = self.get()

        self.assertInHTML("Custom permissions", response.content.decode())

    def test_show_publish_permissions(self):
        response = self.get()
        html = response.content.decode()

        # Should show the Publish column
        self.assertInHTML("<th>Publish</th>", html)

        # Should show inputs for publish permissions on models with DraftStateMixin
        self.assertInHTML("Can publish draft state model", html)
        self.assertInHTML("Can publish draft state custom primary key model", html)

        # Should not show inputs for publish permissions on models without DraftStateMixin
        self.assertNotInHTML("Can publish advert", html)

    def test_hide_publish_permissions(self):
        # Remove all `publish` permissions
        Permission.objects.filter(codename__startswith="publish").delete()

        response = self.get()
        html = response.content.decode()

        # Should not show the Publish column
        self.assertNotInHTML("<th>Publish</th>", html)

        # Should not show inputs for publish permissions even on models with DraftStateMixin
        self.assertNotInHTML("Can publish draft state model", html)
        self.assertNotInHTML("Can publish draft state custom primary key model", html)

        # Should not show inputs for publish permissions on models without DraftStateMixin
        self.assertNotInHTML("Can publish advert", html)


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
        self.assertBreadcrumbsNotRendered(response.content)

        url_finder = AdminURLFinder(self.user)
        expected_url = "/admin/groups/edit/%d/" % self.test_group.id
        self.assertEqual(url_finder.get_edit_url(self.test_group), expected_url)

    def test_nonexistant_group_redirect(self):
        self.assertEqual(self.get(group_id=100000).status_code, 404)

    def test_group_edit(self):
        response = self.post({"name": "test group edited"})

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailusers_groups:index"))

        # Check that the group was edited
        group = Group.objects.get(pk=self.test_group.pk)
        self.assertEqual(group.name, "test group edited")

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
        custom_permission = Permission.objects.get(codename="view_person")
        self.test_group.permissions.add(custom_permission)

        response = self.get()

        self.assertTagInHTML(
            '<input type="checkbox" name="permissions" value="%s" checked>'
            % custom_permission.id,
            response.content.decode(),
        )

    def test_show_publish_permissions(self):
        response = self.get()
        html = response.content.decode()

        # Should show the Publish column
        self.assertInHTML("<th>Publish</th>", html)

        # Should show inputs for publish permissions on models with DraftStateMixin
        self.assertInHTML("Can publish draft state model", html)
        self.assertInHTML("Can publish draft state custom primary key model", html)

        # Should not show inputs for publish permissions on models without DraftStateMixin
        self.assertNotInHTML("Can publish advert", html)

    def test_hide_publish_permissions(self):
        # Remove all `publish` permissions
        Permission.objects.filter(codename__startswith="publish").delete()

        response = self.get()
        html = response.content.decode()

        # Should not show the Publish column
        self.assertNotInHTML("<th>Publish</th>", html)

        # Should not show inputs for publish permissions even on models with DraftStateMixin
        self.assertNotInHTML("Can publish draft state model", html)
        self.assertNotInHTML("Can publish draft state custom primary key model", html)

        # Should not show inputs for publish permissions on models without DraftStateMixin
        self.assertNotInHTML("Can publish advert", html)

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
                for perm in [next(v for v in flatten(perm_set) if "perm" in v)["perm"]]
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


class TestGroupViewSet(TestCase):
    def setUp(self):
        self.app_config = apps.get_app_config("wagtailusers")

    def test_get_group_viewset_cls(self):
        self.assertIs(get_group_viewset_cls(self.app_config), GroupViewSet)

    def test_get_group_viewset_cls_with_custom_form(self):
        with unittest.mock.patch.object(
            self.app_config,
            "group_viewset",
            new="wagtail.users.tests.CustomGroupViewSet",
        ):
            group_viewset = get_group_viewset_cls(self.app_config)
        self.assertIs(group_viewset, CustomGroupViewSet)
        self.assertEqual(group_viewset.icon, "custom-icon")

    def test_get_group_viewset_cls_custom_form_invalid_value(self):
        with unittest.mock.patch.object(
            self.app_config, "group_viewset", new="asdfasdf"
        ):
            with self.assertRaises(ImproperlyConfigured) as exc_info:
                get_group_viewset_cls(self.app_config)
            self.assertIn(
                "asdfasdf doesn't look like a module path", str(exc_info.exception)
            )

    def test_get_group_viewset_cls_custom_form_does_not_exist(self):
        with unittest.mock.patch.object(
            self.app_config,
            "group_viewset",
            new="wagtail.users.tests.CustomClassDoesNotExist",
        ):
            with self.assertRaises(ImproperlyConfigured) as exc_info:
                get_group_viewset_cls(self.app_config)
            self.assertIn(
                'Module "wagtail.users.tests" does not define a "CustomClassDoesNotExist" attribute/class',
                str(exc_info.exception),
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
