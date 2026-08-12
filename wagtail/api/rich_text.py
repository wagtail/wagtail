from collections.abc import Callable
from typing import Any, Literal, cast

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from wagtail.rich_text import expand_db_html

RichTextOutputFormat = Literal["db_html", "html"]
RichTextInputFormat = Literal["db_html"]


class RichTextFormatError(Exception):
    pass


class APIRichText:
    """
    Resolves and applies rich text output formats for API responses, and
    converts/sanitises rich text input for API writes.

    Built-in output formats:

    - ``db_html``: Wagtail database HTML (default)
    - ``html``: display HTML via ``expand_db_html()``

    To add output formats (for example ``markdown`` or ``content_state``),
    extend :meth:`_serializers` and add a corresponding ``_serialize_*``
    method.

    On the input side, :meth:`convert_input` accepts a plain string
    (database HTML) or a ``{"format": ..., "content": ...}`` envelope and
    returns sanitised database HTML, enforcing a rich text feature list.
    Input formats are registered separately in :meth:`_input_converters`.
    """

    FORMAT_DB_HTML: Literal["db_html"] = "db_html"
    FORMAT_HTML: Literal["html"] = "html"

    DEFAULT_FORMAT: RichTextOutputFormat = FORMAT_DB_HTML
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
    def get_default_format(cls) -> RichTextOutputFormat:
        return cast(
            RichTextOutputFormat,
            getattr(settings, cls.SETTING_NAME, cls.DEFAULT_FORMAT),
        )

    @classmethod
    def resolve_format(
        cls, rich_text_format: str | None = None
    ) -> RichTextOutputFormat:
        """
        Return the rich text output format for this request.

        When ``rich_text_format`` is provided (e.g. from a query parameter),
        it is validated and takes precedence over
        ``WAGTAILAPI_RICH_TEXT_FORMAT``. When ``None``, falls back to the
        project-wide default.
        """
        if rich_text_format is not None:
            cls._validate_format(rich_text_format)
            return cast(RichTextOutputFormat, rich_text_format)

        return cls.get_default_format()

    @classmethod
    def serialize(cls, value: str | None, *, format: RichTextOutputFormat) -> Any:
        """
        Serialize ``value`` using a previously validated ``format``.

        Callers must resolve the format via :meth:`resolve_format` (or
        :meth:`check_setting` for the project default) before calling this.
        """
        if value is None:
            return None

        return cls._serializers()[format](value)

    @classmethod
    def parse_input(cls, value: str | dict) -> tuple[RichTextInputFormat, str]:
        """
        Normalise a rich text input value to a ``(format, content)`` pair.

        A plain string is database HTML; a dict is the
        ``{"format": ..., "content": ...}`` envelope, where ``format``
        defaults to ``db_html``. Raises :class:`RichTextFormatError` for
        anything else.
        """
        if isinstance(value, str):
            return cls.FORMAT_DB_HTML, value

        if isinstance(value, dict):
            rich_text_format = value.get("format", cls.FORMAT_DB_HTML)
            content = value.get("content")
            if not isinstance(content, str):
                raise RichTextFormatError(
                    "Rich text input objects must provide a string 'content'"
                )
            if rich_text_format not in cls._input_converters():
                allowed = ", ".join(
                    f"'{name}'" for name in sorted(cls._input_converters())
                )
                raise RichTextFormatError(
                    f"Rich text input format must be one of {allowed}, "
                    f"got '{rich_text_format}'"
                )
            return cast(RichTextInputFormat, rich_text_format), content

        raise RichTextFormatError(
            f"Rich text input must be a string or an object, got {type(value).__name__}"
        )

    @classmethod
    def sanitize_db_html(
        cls, content: str, *, features: list[str] | None = None
    ) -> tuple[str, list]:
        """
        Sanitise database-HTML rich text against ``features`` (registry
        defaults when ``None``). Returns ``(cleaned_html, removals)``.
        """
        # Lazy import: wagtail.api must stay importable without wagtail.admin.
        from wagtail.admin.rich_text.converters.db_html import DbHTMLConverter

        return DbHTMLConverter(features).clean(content)

    @classmethod
    def convert_input(
        cls, value: str | dict, *, features: list[str] | None = None
    ) -> tuple[str, list]:
        """
        Convert any accepted rich text input shape to database HTML,
        enforcing ``features``. Returns ``(db_html, removals)``.
        """
        rich_text_format, content = cls.parse_input(value)
        return cls._input_converters()[rich_text_format](content, features=features)

    @classmethod
    def _input_converters(cls) -> dict[RichTextInputFormat, Callable]:
        """
        Input format converters, keyed by format name. Deliberately separate
        from ``_serializers`` — e.g. ``html`` is a valid output format but
        not a valid input format.
        """
        return {cls.FORMAT_DB_HTML: cls.sanitize_db_html}

    @classmethod
    def _serializers(cls) -> dict[RichTextOutputFormat, Callable[[str], Any]]:
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
