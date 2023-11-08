from typing import Any, Dict, Optional
from unittest import mock

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.http import Http404
from django.test import TestCase
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.text import slugify

from wagtail.coreutils import get_dummy_request
from wagtail.models import Page

from .form_data import querydict_from_html
from .wagtail_tests import WagtailTestUtils

AUTH_BACKEND = settings.AUTHENTICATION_BACKENDS[0]


class WagtailPageTestCase(WagtailTestUtils, TestCase):
    """
    A set of assertions to help write tests for custom Wagtail page types
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dummy_request = get_dummy_request()

    def _testCanCreateAt(self, parent_model, child_model):
        return child_model in parent_model.allowed_subpage_models()

    def assertCanCreateAt(self, parent_model, child_model, msg=None):
        """
        Assert a particular child Page type can be created under a parent
        Page type. ``parent_model`` and ``child_model`` should be the Page
        classes being tested.
        """
        if not self._testCanCreateAt(parent_model, child_model):
            msg = self._formatMessage(
                msg,
                "Can not create a %s.%s under a %s.%s"
                % (
                    child_model._meta.app_label,
                    child_model._meta.model_name,
                    parent_model._meta.app_label,
                    parent_model._meta.model_name,
                ),
            )
            raise self.failureException(msg)

    def assertCanNotCreateAt(self, parent_model, child_model, msg=None):
        """
        Assert a particular child Page type can not be created under a parent
        Page type. ``parent_model`` and ``child_model`` should be the Page
        classes being tested.
        """
        if self._testCanCreateAt(parent_model, child_model):
            msg = self._formatMessage(
                msg,
                "Can create a %s.%s under a %s.%s"
                % (
                    child_model._meta.app_label,
                    child_model._meta.model_name,
                    parent_model._meta.app_label,
                    parent_model._meta.model_name,
                ),
            )
            raise self.failureException(msg)

    def assertCanCreate(self, parent, child_model, data, msg=None, publish=True):
        """
        Assert that a child of the given Page type can be created under the
        parent, using the supplied POST data.

        ``parent`` should be a Page instance, and ``child_model`` should be a
        Page subclass. ``data`` should be a dict that will be POSTed at the
        Wagtail admin Page creation method.
        """
        self.assertCanCreateAt(parent.specific_class, child_model)

        if "slug" not in data and "title" in data:
            data["slug"] = slugify(data["title"])
        if publish:
            data["action-publish"] = "action-publish"

        add_url = reverse(
            "wagtailadmin_pages:add",
            args=[child_model._meta.app_label, child_model._meta.model_name, parent.pk],
        )
        response = self.client.post(add_url, data, follow=True)

        if response.status_code != 200:
            msg = self._formatMessage(
                msg,
                "Creating a %s.%s returned a %d"
                % (
                    child_model._meta.app_label,
                    child_model._meta.model_name,
                    response.status_code,
                ),
            )
            raise self.failureException(msg)

        if response.redirect_chain == []:
            if "form" not in response.context:
                msg = self._formatMessage(msg, "Creating a page failed unusually")
                raise self.failureException(msg)
            form = response.context["form"]
            if not form.errors:
                msg = self._formatMessage(
                    msg, "Creating a page failed for an unknown reason"
                )
                raise self.failureException(msg)

            errors = "\n".join(
                "  {}:\n    {}".format(field, "\n    ".join(errors))
                for field, errors in sorted(form.errors.items())
            )
            msg = self._formatMessage(
                msg,
                "Validation errors found when creating a %s.%s:\n%s"
                % (child_model._meta.app_label, child_model._meta.model_name, errors),
            )
            raise self.failureException(msg)

        if publish:
            expected_url = reverse("wagtailadmin_explore", args=[parent.pk])
        else:
            expected_url = reverse(
                "wagtailadmin_pages:edit", args=[Page.objects.order_by("pk").last().pk]
            )

        if response.redirect_chain != [(expected_url, 302)]:
            msg = self._formatMessage(
                msg,
                "Creating a page %s.%s didn't redirect the user to the expected page %s, but to %s"
                % (
                    child_model._meta.app_label,
                    child_model._meta.model_name,
                    expected_url,
                    response.redirect_chain,
                ),
            )
            raise self.failureException(msg)

    def assertAllowedSubpageTypes(self, parent_model, child_models, msg=None):
        """
        Test that the only page types that can be created under
        ``parent_model`` are ``child_models``.

        The list of allowed child models may differ from those set in
        ``Page.subpage_types``, if the child models have set
        ``Page.parent_page_types``.
        """
        self.assertEqual(
            set(parent_model.allowed_subpage_models()), set(child_models), msg=msg
        )

    def assertAllowedParentPageTypes(self, child_model, parent_models, msg=None):
        """
        Test that the only page types that ``child_model`` can be created under
        are ``parent_models``.

        The list of allowed parent models may differ from those set in
        ``Page.parent_page_types``, if the parent models have set
        ``Page.subpage_types``.
        """
        self.assertEqual(
            set(child_model.allowed_parent_page_models()), set(parent_models), msg=msg
        )

    def assertPageIsRoutable(
        self,
        page: Page,
        route_path: Optional[str] = "/",
        msg: Optional[str] = None,
    ):
        """
        Asserts that ``page`` can be routed to without raising a ``Http404`` error.

        For page types with multiple routes, you can use ``route_path`` to specify an alternate route to test.
        """
        path = page.get_url(self.dummy_request)
        if route_path != "/":
            path = path.rstrip("/") + "/" + route_path.lstrip("/")

        site = page.get_site()
        if site is None:
            msg = self._formatMessage(
                msg,
                'Failed to route to "%s" for %s "%s". The page does not belong to any sites.'
                % (type(page).__name__, route_path, page),
            )
            raise self.failureException(msg)

        path_components = [component for component in path.split("/") if component]
        try:
            page, args, kwargs = site.root_page.localized.specific.route(
                self.dummy_request, path_components
            )
        except Http404:
            msg = self._formatMessage(
                msg,
                'Failed to route to "%(route_path)s" for %(page_type)s "%(page)s". A Http404 was raised for path: "%(full_path)s".'
                % {
                    "route_path": route_path,
                    "page_type": type(page).__name__,
                    "page": page,
                    "full_path": path,
                },
            )
            raise self.failureException(msg)

    def assertPageIsRenderable(
        self,
        page: Page,
        route_path: Optional[str] = "/",
        query_data: Optional[Dict[str, Any]] = None,
        post_data: Optional[Dict[str, Any]] = None,
        user: Optional[AbstractBaseUser] = None,
        accept_404: Optional[bool] = False,
        accept_redirect: Optional[bool] = False,
        msg: Optional[str] = None,
    ):
        """
        Asserts that ``page`` can be rendered without raising a fatal error.

        For page types with multiple routes, you can use ``route_path`` to specify an alternate route to test.

        When ``post_data`` is provided, the test makes a ``POST`` request with ``post_data`` in the request body. Otherwise, a ``GET`` request is made.

        When supplied, ``query_data`` is converted to a querystring and added to the request URL (regardless of whether ``post_data`` is provided).

        When ``user`` is provided, the test is conducted with them as the active user.

        By default, the assertion will fail if the request to the page URL results in a 301, 302 or 404 HTTP response. If you are testing a page/route
        where a 404 response is expected, you can use ``accept_404=True`` to indicate this, and the assertion will pass when encountering a 404. Likewise,
        if you are testing a page/route where a redirect response is expected, you can use `accept_redirect=True` to indicate this, and the assertion will
        pass when encountering 301 or 302.
        """
        if user:
            self.client.force_login(user, AUTH_BACKEND)

        path = page.get_url(self.dummy_request)
        if route_path != "/":
            path = path.rstrip("/") + "/" + route_path.lstrip("/")

        post_kwargs = {}
        if post_data is not None:
            post_kwargs = {"data": post_data}
            if query_data:
                post_kwargs["QUERYSTRING"] = urlencode(query_data, doseq=True)
        try:
            if post_data is None:
                resp = self.client.get(path, data=query_data)
            else:
                resp = self.client.post(path, **post_kwargs)
        except Exception as e:  # noqa: BLE001
            msg = self._formatMessage(
                msg,
                'Failed to render route "%(route_path)s" for %(page_type)s "%(page)s":\n%(exc)s'
                % {
                    "route_path": route_path,
                    "page_type": type(page).__name__,
                    "page": page,
                    "exc": e,
                },
            )
            raise self.failureException(msg)
        finally:
            if user:
                self.client.logout()

        if (
            resp.status_code == 200
            or (accept_404 and resp.status_code == 404)
            or (accept_redirect and resp.status_code in (301, 302))
            or isinstance(resp, mock.MagicMock)
        ):
            return

        msg = self._formatMessage(
            msg,
            'Failed to render route "%(route_path)s" for %(page_type)s "%(page)s":\nA HTTP %(code)s response was received for path: "%(full_path)s".'
            % {
                "route_path": route_path,
                "page_type": type(page).__name__,
                "page": page,
                "code": resp.status_code,
                "full_path": path,
            },
        )
        raise self.failureException(msg)

    def assertPageIsEditable(
        self,
        page: Page,
        post_data: Optional[Dict[str, Any]] = None,
        user: Optional[AbstractBaseUser] = None,
        msg: Optional[str] = None,
    ):
        """
        Asserts that the page edit view works for ``page`` without raising a fatal error.

        When ``user`` is provided, the test is conducted with them as the active user. Otherwise, a superuser is created and used for the test.

        After a successful ``GET`` request, a ``POST`` request is made with field data in the request body. If ``post_data`` is provided, that will be used for this purpose. If not, this data will be extracted from the ``GET`` response HTML.
        """
        if user:
            # rule out permission issues early on
            if not page.permissions_for_user(user).can_edit():
                self._formatMessage(
                    msg,
                    'Failed to load edit view for %(page_type)s "%(page)s":\nUser "%(user)s" have insufficient permissions.'
                    % {
                        "page_type": type(page).__name__,
                        "page": page,
                        "user": user,
                    },
                )
                raise self.failureException(msg)
        else:
            if not hasattr(self, "_pageiseditable_superuser"):
                self._pageiseditable_superuser = self.create_superuser(
                    "assertpageiseditable"
                )
            user = self._pageiseditable_superuser

        self.client.force_login(user, AUTH_BACKEND)

        path = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.id})
        try:
            response = self.client.get(path)
        except Exception as e:  # noqa: BLE001
            self.client.logout()
            msg = self._formatMessage(
                msg,
                'Failed to load edit view via GET for %(page_type)s "%(page)s":\n%(exc)s'
                % {"page_type": type(page).__name__, "page": page, "exc": e},
            )
            raise self.failureException(msg)
        if response.status_code != 200:
            self.client.logout()
            msg = self._formatMessage(
                msg,
                'Failed to load edit view via GET for %(page_type)s "%(page)s":\nReceived response with HTTP status code: %(code)s.'
                % {
                    "page_type": type(page).__name__,
                    "page": page,
                    "code": response.status_code,
                },
            )
            raise self.failureException(msg)

        if post_data is not None:
            data_to_post = post_data
        else:
            data_to_post = querydict_from_html(
                response.content.decode(), form_id="page-edit-form"
            )
            data_to_post["action-publish"] = ""

        try:
            self.client.post(path, data_to_post)
        except Exception as e:  # noqa: BLE001
            msg = self._formatMessage(
                msg,
                'Failed to load edit view via POST for %(page_type)s "%(page)s":\n%(exc)s'
                % {"page_type": type(page).__name__, "page": page, "exc": e},
            )
            raise self.failureException(msg)
        finally:
            page.save()  # undo any changes to page
            self.client.logout()

    def assertPageIsPreviewable(
        self,
        page: Page,
        mode: Optional[str] = "",
        post_data: Optional[Dict[str, Any]] = None,
        user: Optional[AbstractBaseUser] = None,
        msg: Optional[str] = None,
    ):
        """
        Asserts that the page preview view can be loaded for ``page`` without raising a fatal error.

        For page types that support multiple preview modes, ``mode`` can be used to specify the preview mode to be tested.

        When ``user`` is provided, the test is conducted with them as the active user. Otherwise, a superuser is created and used for the test.

        To load the preview, the test client needs to make a ``POST`` request including all required field data in the request body.
        If ``post_data`` is provided, that will be used for this purpose. If not, the method will attempt to extract this data from the page edit view.
        """
        if not user:
            if not hasattr(self, "_pageispreviewable_superuser"):
                self._pageispreviewable_superuser = self.create_superuser(
                    "assertpageispreviewable"
                )
            user = self._pageispreviewable_superuser

        self.client.force_login(user, AUTH_BACKEND)

        if post_data is None:
            edit_path = reverse("wagtailadmin_pages:edit", kwargs={"page_id": page.id})
            html = self.client.get(edit_path).content.decode()
            post_data = querydict_from_html(html, form_id="page-edit-form")

        preview_path = reverse(
            "wagtailadmin_pages:preview_on_edit", kwargs={"page_id": page.id}
        )
        try:
            response = self.client.post(
                preview_path, data=post_data, QUERYSTRING=f"mode={mode}"
            )
            self.assertEqual(response.status_code, 200)
            self.assertJSONEqual(
                response.content.decode(),
                {"is_valid": True, "is_available": True},
            )
        except Exception as e:  # noqa: BLE001
            self.client.logout()
            msg = self._formatMessage(
                msg,
                'Failed to load preview for %(page_type)s "%(page)s" with mode="%(mode)s":\n%(exc)s'
                % {
                    "page_type": type(page).__name__,
                    "page": page,
                    "mode": mode,
                    "exc": e,
                },
            )
            raise self.failureException(msg)

        try:
            self.client.get(preview_path, data={"mode": mode})
        except Exception as e:  # noqa: BLE001
            msg = self._formatMessage(
                msg,
                'Failed to load preview for %(page_type)s "%(page)s" with mode="%(mode)s":\n%(exc)s'
                % {
                    "page_type": type(page).__name__,
                    "page": page,
                    "mode": mode,
                    "exc": e,
                },
            )
            raise self.failureException(msg)
        finally:
            self.client.logout()


class WagtailPageTests(WagtailPageTestCase):
    def setUp(self):
        super().setUp()
        self.login()
