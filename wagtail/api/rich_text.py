from collections.abc import Callable
from typing import Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from wagtail.rich_text import expand_db_html


class RichTextFormatError(Exception):
    pass


class APIRichText:
    """
    Resolves and applies rich text output formats for API responses.

    Built-in formats:

    - ``db_html``: Wagtail database HTML (default)
    - ``html``: display HTML via ``expand_db_html()``

    To add formats (for example ``markdown`` or ``content_state``), extend
    :meth:`_serializers` and add a corresponding ``_serialize_*`` method.
    """

    FORMAT_DB_HTML = "db_html"
    FORMAT_HTML = "html"

    DEFAULT_FORMAT = FORMAT_DB_HTML
    SETTING_NAME = "WAGTAILAPI_RICH_TEXT_FORMAT"

    @classmethod
    def check_setting(cls) -> None:
        """
        Validate ``WAGTAILAPI_RICH_TEXT_FORMAT``.

        Called at app startup; raises ``ImproperlyConfigured`` if invalid.
        """
        rich_text_format = getattr(settings, cls.SETTING_NAME, cls.DEFAULT_FORMAT)
        if rich_text_format in cls._serializers():
            return

        allowed = ", ".join(f"'{name}'" for name in sorted(cls._serializers()))
        raise ImproperlyConfigured(
            f"{cls.SETTING_NAME} must be one of {allowed}, got '{rich_text_format}'"
        )

    @classmethod
    def get_default_format(cls) -> str:
        return getattr(settings, cls.SETTING_NAME, cls.DEFAULT_FORMAT)

    @classmethod
    def resolve_format(cls, rich_text_format: str | None = None) -> str:
        """
        Return the rich text output format for this request.

        When ``rich_text_format`` is provided (e.g. from a query parameter),
        it is validated and takes precedence over
        ``WAGTAILAPI_RICH_TEXT_FORMAT``. When ``None``, falls back to the
        project-wide default.
        """
        if rich_text_format is not None:
            cls._validate_format(rich_text_format)
            return rich_text_format

        return cls.get_default_format()

    @classmethod
    def serialize(cls, value: str | None, *, format: str) -> Any:
        """
        Serialize ``value`` using a previously validated ``format``.

        Callers must resolve the format via :meth:`resolve_format` (or
        :meth:`check_setting` for the project default) before calling this.
        """
        if value is None:
            return None

        return cls._serializers()[format](value)

    @classmethod
    def _serializers(cls) -> dict[str, Callable[[str], Any]]:
        return {
            cls.FORMAT_DB_HTML: cls._serialize_db_html,
            cls.FORMAT_HTML: cls._serialize_html,
        }

    @staticmethod
    def _serialize_db_html(value: str) -> str:
        return value

    @staticmethod
    def _serialize_html(value: str) -> str:
        return expand_db_html(value)

    @classmethod
    def _validate_format(cls, rich_text_format: str) -> None:
        if rich_text_format in cls._serializers():
            return

        allowed = ", ".join(f"'{name}'" for name in sorted(cls._serializers()))
        raise RichTextFormatError(
            f"rich_text_format must be one of {allowed}, got '{rich_text_format}'"
        )
