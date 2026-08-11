from django.conf import settings
from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.urls import reverse
from ninja.constants import NOT_SET

from wagtail.api.v3.auth import AllowAnonymous, BearerTokenAuth
from wagtail.api.v3.tests.base import TestV3Base
from wagtail.models import APIToken
from wagtail.test.utils import WagtailTestUtils


class TestBearerTokenAuth(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = WagtailTestUtils.create_superuser("apiuser")
        cls.token, cls.plaintext = APIToken.create_token(user=cls.user, name="t")

    def authenticate(self, header):
        request = RequestFactory().get("/", HTTP_AUTHORIZATION=header)
        return request, BearerTokenAuth()(request)

    def test_valid_token_resolves(self):
        request, result = self.authenticate(f"Bearer {self.plaintext}")
        self.assertEqual(result, self.token)
        self.assertEqual(request.user, self.user)

    def test_no_header(self):
        request = RequestFactory().get("/")
        self.assertIsNone(BearerTokenAuth()(request))

    def test_garbage_token(self):
        _, result = self.authenticate("Bearer not-a-token")
        self.assertIsNone(result)

    def test_malformed_header(self):
        _, result = self.authenticate(f"Token {self.plaintext}")
        self.assertIsNone(result)

    def test_revoked_token_rejected(self):
        self.token.revoke()
        _, result = self.authenticate(f"Bearer {self.plaintext}")
        self.assertIsNone(result)

    def test_inactive_user_rejected(self):
        self.user.is_active = False
        self.user.save()
        _, result = self.authenticate(f"Bearer {self.plaintext}")
        self.assertIsNone(result)

    def test_fallback_secret_key_accepted(self):
        original_key = settings.SECRET_KEY
        with override_settings(SECRET_KEY="rotated", SECRET_KEY_FALLBACKS=[]):
            # tokens hashed with the old key no longer match
            _, result = self.authenticate(f"Bearer {self.plaintext}")
            self.assertIsNone(result)
        with override_settings(
            SECRET_KEY="rotated", SECRET_KEY_FALLBACKS=[original_key]
        ):
            _, result = self.authenticate(f"Bearer {self.plaintext}")
            self.assertIsNotNone(result)

    def test_last_used_at_throttled(self):
        request = RequestFactory().get(
            "/", HTTP_AUTHORIZATION=f"Bearer {self.plaintext}"
        )
        BearerTokenAuth()(request)
        self.token.refresh_from_db()
        first = self.token.last_used_at
        self.assertIsNotNone(first)
        BearerTokenAuth()(request)  # within the interval: no update
        self.token.refresh_from_db()
        self.assertEqual(self.token.last_used_at, first)

    @override_settings(WAGTAILAPI_TOKEN_LAST_USED_INTERVAL=None)
    def test_last_used_at_disabled(self):
        request = RequestFactory().get(
            "/", HTTP_AUTHORIZATION=f"Bearer {self.plaintext}"
        )
        BearerTokenAuth()(request)
        self.token.refresh_from_db()
        self.assertIsNone(self.token.last_used_at)

    def test_allow_anonymous_always_truthy(self):
        self.assertTrue(AllowAnonymous()(RequestFactory().get("/")))

    def test_allow_anonymous_clears_session_user(self):
        request = RequestFactory().get("/")
        request.user = self.user  # as session middleware would set it
        result = AllowAnonymous()(request)
        self.assertTrue(result)
        self.assertFalse(request.user.is_authenticated)


class TestAuthWiring(TestV3Base, TestCase):
    def test_every_operation_declares_auth_explicitly(self):

        from wagtail.api.v3.api import api

        for _prefix, router in api._routers:
            for path_view in router.path_operations.values():
                for operation in path_view.operations:
                    declared = (
                        operation.auth_param
                        if operation.auth_param is not NOT_SET
                        else router.auth
                    )
                    if declared is NOT_SET:
                        callbacks = []
                    elif isinstance(declared, (list, tuple)):
                        callbacks = declared
                    else:
                        callbacks = [declared]
                    self.assertTrue(
                        any(isinstance(cb, BearerTokenAuth) for cb in callbacks),
                        f"{operation.operation_id} must declare bearer auth "
                        "explicitly (BearerTokenAuth() for protected endpoints, "
                        "[BearerTokenAuth(), AllowAnonymous()] for public reads; "
                        "router-level auth counts for fully-protected routers)",
                    )

    def test_every_served_operation_has_bearer_security(self):
        # The internals-based test above misses operations from nested
        # routers (flattened at api.urls build time); the built OpenAPI
        # schema is the comprehensive source of truth for what is served.
        from wagtail.api.v3.api import api

        schema = api.get_openapi_schema()
        for path, operations in schema["paths"].items():
            for method, operation in operations.items():
                security = operation.get("security") or []
                schemes = [scheme for entry in security for scheme in entry]
                self.assertIn(
                    "BearerTokenAuth",
                    schemes,
                    f"{method.upper()} {path} has no bearer security scheme",
                )

    def test_session_cookies_do_not_authenticate(self):
        user = WagtailTestUtils.create_superuser("sessionuser")
        self.client.force_login(user)  # session only, no token
        response = self.client.get(reverse("wagtailapi_v3:list_sites"))
        self.assert_problem_response(response, status_code=401)
