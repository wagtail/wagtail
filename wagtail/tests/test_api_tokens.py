import json
from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase, override_settings

from wagtail.models import APIToken
from wagtail.models.api import KEY_CHECKSUM_LENGTH, KEY_SECRET_LENGTH, TOKEN_PREFIX
from wagtail.test.utils import WagtailTestUtils


class TestTokenFormat(SimpleTestCase):
    def test_format(self):
        token = APIToken.generate_token()
        self.assertTrue(token.startswith(TOKEN_PREFIX))
        self.assertEqual(
            len(token), len(TOKEN_PREFIX) + KEY_SECRET_LENGTH + KEY_CHECKSUM_LENGTH
        )
        self.assertTrue(APIToken.validate_token_format(token))

    def test_checksum_detects_tampering(self):
        token = APIToken.generate_token()
        tampered = token[:-1] + ("0" if token[-1] != "0" else "1")
        self.assertFalse(APIToken.validate_token_format(tampered))

    def test_uniqueness(self):
        self.assertNotEqual(APIToken.generate_token(), APIToken.generate_token())


class TestTokenStorage(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = WagtailTestUtils.create_superuser("tokenuser")

    def test_create_token_stores_digest_not_plaintext(self):
        instance, plaintext = APIToken.create_token(user=self.user, name="deploy")
        self.assertEqual(instance.key_hash, APIToken.hash_token(plaintext))
        self.assertNotEqual(instance.key_hash, plaintext)
        self.assertNotIn(plaintext, str(instance))
        self.assertEqual(instance.prefix, plaintext[:12])
        self.assertIsNone(instance.revoked_at)

    def test_revoke_sets_timestamp(self):
        instance, _ = APIToken.create_token(user=self.user, name="deploy")
        instance.revoke()
        instance.refresh_from_db()
        self.assertIsNotNone(instance.revoked_at)

    def test_candidate_hashes_include_fallback_keys(self):
        token = APIToken.generate_token()
        with override_settings(SECRET_KEY="new-key", SECRET_KEY_FALLBACKS=["old-key"]):
            candidates = APIToken.candidate_key_hashes(token)
        self.assertEqual(len(candidates), 2)
        self.assertEqual(
            candidates[0], APIToken.hash_token(token, secret_key="new-key")
        )
        self.assertEqual(
            candidates[1], APIToken.hash_token(token, secret_key="old-key")
        )

    def test_current_secret_key_is_first_candidate(self):
        token = APIToken.generate_token()
        candidates = APIToken.candidate_key_hashes(token)
        self.assertEqual(candidates[0], APIToken.hash_token(token))
        self.assertEqual(
            candidates[0],
            APIToken.hash_token(token, secret_key=settings.SECRET_KEY),
        )


class TestApiTokensCommand(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = WagtailTestUtils.create_superuser("cliuser")
        cls.username = cls.user.get_username()

    def call_command(self, *args, **kwargs):
        out, err = StringIO(), StringIO()
        call_command("api_tokens", *args, stdout=out, stderr=err, **kwargs)
        return out.getvalue(), err.getvalue()

    def test_create_prints_bare_token(self):
        out, _ = self.call_command("create", "--user", self.username, "--name", "ci")
        token = out.strip()
        self.assertTrue(APIToken.validate_token_format(token))
        self.assertEqual(APIToken.objects.get().key_hash, APIToken.hash_token(token))

    def test_create_json(self):
        out, _ = self.call_command(
            "create", "--user", self.username, "--name", "ci", "--json"
        )
        payload = json.loads(out)
        self.assertTrue(APIToken.validate_token_format(payload["token"]))
        self.assertEqual(payload["name"], "ci")
        self.assertEqual(payload["user"], self.username)

    def test_create_unknown_user_errors(self):
        with self.assertRaises(CommandError):
            self.call_command("create", "--user", "ghost", "--name", "ci")

    def test_list_and_revoke(self):
        instance, plaintext = APIToken.create_token(user=self.user, name="old")
        out, _ = self.call_command("list", "--user", self.username)
        self.assertIn("old", out)
        self.assertIn(instance.prefix, out)
        self.assertNotIn(instance.key_hash, out)
        self.assertNotIn(plaintext, out)

        out, _ = self.call_command("revoke", "--id", str(instance.pk))
        instance.refresh_from_db()
        self.assertIsNotNone(instance.revoked_at)

        out, _ = self.call_command("list", "--user", self.username)
        self.assertNotIn("old", out)
        out, _ = self.call_command("list", "--user", self.username, "--include-revoked")
        self.assertIn("old", out)

    def test_revoke_by_user_and_prefix(self):
        instance, _ = APIToken.create_token(user=self.user, name="mine")
        self.call_command(
            "revoke", "--user", self.username, "--prefix", instance.prefix
        )
        instance.refresh_from_db()
        self.assertIsNotNone(instance.revoked_at)

    def test_revoke_ambiguous_prefix_errors(self):
        APIToken.create_token(user=self.user, name="a")
        APIToken.create_token(user=self.user, name="b")
        with self.assertRaises(CommandError):
            self.call_command("revoke", "--user", self.username, "--prefix", "wagtail_")

    def test_revoke_requires_identifier(self):
        with self.assertRaises(CommandError):
            self.call_command("revoke")
