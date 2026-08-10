from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from wagtail.models import APIToken
from wagtail.models.api import (
    candidate_key_hashes,
    generate_token,
    hash_token,
    validate_token_format,
)

User = get_user_model()


def make_user(username_value, *, superuser=True):
    """Create a user without assuming which field is USERNAME_FIELD."""
    kwargs = {"password": "password"}
    kwargs[User.USERNAME_FIELD] = username_value
    if User.USERNAME_FIELD != "email":
        kwargs["email"] = f"{username_value}@example.com"
    if superuser:
        return User.objects.create_superuser(**kwargs)
    return User.objects.create_user(**kwargs)


class TestTokenFormat(TestCase):
    def test_format(self):
        token = generate_token()
        self.assertTrue(token.startswith("wagtail_"))
        self.assertEqual(len(token), len("wagtail_") + 27 + 6)
        self.assertTrue(validate_token_format(token))

    def test_checksum_detects_tampering(self):
        token = generate_token()
        tampered = token[:-1] + ("0" if token[-1] != "0" else "1")
        self.assertFalse(validate_token_format(tampered))

    def test_uniqueness(self):
        self.assertNotEqual(generate_token(), generate_token())


class TestTokenStorage(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = make_user("tokenuser")

    def test_create_token_stores_digest_not_plaintext(self):
        instance, plaintext = APIToken.create_token(user=self.user, name="deploy")
        self.assertEqual(instance.key_hash, hash_token(plaintext))
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
        token = generate_token()
        with override_settings(SECRET_KEY="new-key", SECRET_KEY_FALLBACKS=["old-key"]):
            candidates = candidate_key_hashes(token)
        self.assertEqual(len(candidates), 2)
        self.assertEqual(candidates[0], hash_token(token, secret_key="new-key"))
        self.assertEqual(candidates[1], hash_token(token, secret_key="old-key"))

    def test_current_secret_key_is_first_candidate(self):
        token = generate_token()
        candidates = candidate_key_hashes(token)
        self.assertEqual(candidates[0], hash_token(token))
        self.assertEqual(
            candidates[0],
            hash_token(token, secret_key=settings.SECRET_KEY),
        )
