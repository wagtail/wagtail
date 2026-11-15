"""Field classes for use with :class:`~wagtail.api.APIField` in the API v3."""

from __future__ import annotations

from typing import Any

from django.core.exceptions import ObjectDoesNotExist

__all__ = ["FieldSerializer"]


class FieldSerializer:
    """
    Base class for API v3 field serializers.

    Subclasses must implement :meth:`to_representation`. The value passed to
    it is resolved from the object being serialized via the ``source``
    argument (or the field name if no source is given):

    - ``source="*"`` passes the object itself,
    - dotted sources like ``source="feed_image.id"`` are followed one
      segment at a time.
    """

    def __init__(self, *, source: str | None = None) -> None:
        self.source = source
        self.field_name: str | None = None
        self.source_attrs: list[str] = []

    def bind(self, field_name: str) -> None:
        self.field_name = field_name
        source = self.source or field_name
        self.source_attrs = [] if source == "*" else source.split(".")
        self.source = source

    def get_attribute(self, instance: Any) -> Any:
        obj = instance
        for attr in self.source_attrs:
            try:
                obj = getattr(obj, attr)
            except ObjectDoesNotExist:
                # Nonexistent reverse OneToOneField
                return None
            if obj is None:
                return None
        return obj

    def to_representation(self, value: Any) -> Any:  # pragma: no cover
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement to_representation()"
        )
