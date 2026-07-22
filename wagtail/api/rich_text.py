from collections.abc import Callable
from typing import Any

from django.conf import settings
from django.http import HttpRequest

from wagtail.rich_text import expand_db_html
from wagtail.rich_text.markdown import expand_db_html_to_markdown


class RichTextFormatError(Exception):
    pass


class APIRichText:
    """
    Resolves and applies rich text output formats for API responses.

    Built-in formats:

    - ``db_html``: Wagtail database HTML (default)
    - ``html``: display-ready HTML
    - ``markdown``: display-ready Markdown
    - ``internal_markdown``: Internal/private Markdown with internal references all preserved

    To add formats, extend :meth:`_serializers` and add a corresponding
    ``_serialize_*`` method.
    """

    FORMAT_DB_HTML = "db_html"
    FORMAT_HTML = "html"
    FORMAT_MARKDOWN = "markdown"
    FORMAT_INTERNAL_MARKDOWN = "internal_markdown"

    DEFAULT_FORMAT = FORMAT_DB_HTML
    SETTING_NAME = "WAGTAILAPI_RICH_TEXT_FORMAT"
    QUERY_PARAMETER = "rich_text_format"

    @classmethod
    def formats(cls) -> frozenset[str]:
        return frozenset(cls._serializers())

    @classmethod
    def get_default_format(cls) -> str:
        rich_text_format = getattr(settings, cls.SETTING_NAME, cls.DEFAULT_FORMAT)
        cls._validate_format(rich_text_format, source=cls.SETTING_NAME)
        return rich_text_format

    @classmethod
    def resolve_format(cls, request: HttpRequest | None = None) -> str:
        """
        Return the rich text output format for this request.

        The ``?rich_text_format=`` query parameter takes precedence over
        ``WAGTAILAPI_RICH_TEXT_FORMAT``.
        """
        if request is not None and cls.QUERY_PARAMETER in request.GET:
            rich_text_format = request.GET[cls.QUERY_PARAMETER]
            cls._validate_format(rich_text_format, source=cls.QUERY_PARAMETER)
            return rich_text_format

        return cls.get_default_format()

    @classmethod
    def serialize(cls, value: str | None, *, format: str) -> Any:
        if value is None:
            return None

        cls._validate_format(format, source="format")
        return cls._serializers()[format](value)

    @classmethod
    def _serializers(cls) -> dict[str, Callable[[str], Any]]:
        return {
            cls.FORMAT_DB_HTML: cls._serialize_db_html,
            cls.FORMAT_HTML: cls._serialize_html,
            cls.FORMAT_MARKDOWN: cls._serialize_markdown,
            cls.FORMAT_INTERNAL_MARKDOWN: cls._serialize_internal_markdown,
        }

    @staticmethod
    def _serialize_db_html(value: str) -> str:
        return value

    @staticmethod
    def _serialize_html(value: str) -> str:
        return expand_db_html(value)

    @staticmethod
    def _serialize_markdown(value: str) -> str:
        return expand_db_html_to_markdown(value, internal=False)

    @staticmethod
    def _serialize_internal_markdown(value: str) -> str:
        return expand_db_html_to_markdown(value, internal=True)

    @classmethod
    def _validate_format(cls, rich_text_format: str, *, source: str) -> None:
        if rich_text_format in cls._serializers():
            return

        allowed = ", ".join(f"'{name}'" for name in sorted(cls._serializers()))
        if source == cls.SETTING_NAME:
            message = (
                f"{cls.SETTING_NAME} must be one of {allowed}, got '{rich_text_format}'"
            )
        elif source == cls.QUERY_PARAMETER:
            message = f"{cls.QUERY_PARAMETER} must be one of {allowed}, got '{rich_text_format}'"
        else:
            message = f"Unknown rich text format '{rich_text_format}'"

        raise RichTextFormatError(message)
