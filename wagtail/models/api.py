import math
import secrets
import zlib

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.crypto import salted_hmac
from django.utils.translation import gettext_lazy as _

BASE62_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
BASE62_CHARS = frozenset(BASE62_ALPHABET)
TOKEN_PREFIX = "wagtail_"  # noqa: S105 - not a credential, a public format prefix
KEY_SECRET_BYTES = 20
KEY_SECRET_LENGTH = math.ceil(KEY_SECRET_BYTES * 8 * math.log(2) / math.log(62))
KEY_CHECKSUM_LENGTH = math.ceil(32 * math.log(2) / math.log(62))
KEY_SALT = "wagtail.apitoken"
# Display the prefx and first 4 secret chars, safe to display.
DISPLAY_PREFIX_LENGTH = len(TOKEN_PREFIX) + 4


def _base62_encode(value, length):
    chars = []
    for _i in range(length):
        value, remainder = divmod(value, len(BASE62_ALPHABET))
        chars.append(BASE62_ALPHABET[remainder])
    return "".join(reversed(chars))


def _token_checksum(secret):
    return _base62_encode(
        zlib.crc32(f"{TOKEN_PREFIX}{secret}".encode()), KEY_CHECKSUM_LENGTH
    )


class APIToken(models.Model):
    """
    A bearer token authenticating API requests as a specific user. Only a
    digest of the token is stored; the plaintext is shown once at creation.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="api_tokens",
        verbose_name=_("user"),
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_("name"),
        help_text=_("A human-readable label to identify this token."),
    )
    key_hash = models.CharField(max_length=64, unique=True, editable=False)
    prefix = models.CharField(max_length=16, editable=False)
    created = models.DateTimeField(auto_now_add=True, verbose_name=_("created"))
    revoked_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("revoked at")
    )
    last_used_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("last used at")
    )

    class Meta:
        verbose_name = _("API token")
        verbose_name_plural = _("API tokens")

    def __str__(self):
        return f"{self.name} ({self.prefix}…)"

    @classmethod
    def generate_token(cls):
        """Return a new plaintext API token: ``wagtail_<secret><checksum>``."""
        secret = _base62_encode(
            int.from_bytes(secrets.token_bytes(KEY_SECRET_BYTES), byteorder="big"),
            KEY_SECRET_LENGTH,
        )
        return f"{TOKEN_PREFIX}{secret}{_token_checksum(secret)}"

    @classmethod
    def validate_token_format(cls, token):
        """
        Offline format check (prefix, length, charset, CRC32 checksum). Validation
        failure means the token cannot exist; validity does not imply it does.
        """
        body = token.removeprefix(TOKEN_PREFIX)
        if body == token or len(body) != KEY_SECRET_LENGTH + KEY_CHECKSUM_LENGTH:
            return False
        if not BASE62_CHARS.issuperset(body):
            return False
        secret, checksum = body[:KEY_SECRET_LENGTH], body[KEY_SECRET_LENGTH:]
        return secrets.compare_digest(checksum, _token_checksum(secret))

    @classmethod
    def hash_token(cls, token, secret_key=None):
        """Return the stored digest for a plaintext token (HMAC-SHA-256 hex)."""
        return salted_hmac(
            KEY_SALT, token, secret=secret_key, algorithm="sha256"
        ).hexdigest()

    @classmethod
    def candidate_key_hashes(cls, token):
        """
        Digests to look up for a presented token: one per current secret key and
        configured SECRET_KEY_FALLBACKS, so tokens survive a rotation window.
        """
        keys = [settings.SECRET_KEY, *settings.SECRET_KEY_FALLBACKS]
        return [cls.hash_token(token, secret_key=key) for key in keys]

    @classmethod
    def create_token(cls, *, user, name):
        """Create a token, returning ``(instance, plaintext)``. The plaintext
        is only available from this return value — never stored or logged."""
        plaintext = cls.generate_token()
        instance = cls(
            user=user,
            name=name,
            key_hash=cls.hash_token(plaintext),
            prefix=plaintext[:DISPLAY_PREFIX_LENGTH],
        )
        instance.save()
        return instance, plaintext

    def revoke(self):
        self.revoked_at = timezone.now()
        self.save(update_fields=["revoked_at"])
