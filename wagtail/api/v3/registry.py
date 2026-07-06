"""
Content type registry backing ``/schema/`` discovery.

Registrations run from ``WagtailAPIV3AppConfig.ready()`` so other apps can register types from
their own ``ready()`` hooks.
"""

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from wagtail.api.v3.schemas import ContentTypeSummarySchema


@dataclass
class ContentTypeRegistration:
    """A content type made available to the v3 API.

    Each direction (``read``, ``create``, ``patch``) is backed by an optional
    pydantic schema class; only ``read`` is populated so far.
    """

    name: str
    label: str
    read_schema: type[BaseModel] | None = None
    create_schema: type[BaseModel] | None = None
    patch_schema: type[BaseModel] | None = None


class ContentTypeRegistry:
    """Registry of content types exposed by the v3 API.

    Types are keyed by their ``name`` and discovered through the ``/schema/``
    endpoints. Registrations are populated from
    :meth:`WagtailAPIV3AppConfig.ready` so other apps can register types from
    their own ``ready()`` hooks.
    """

    def __init__(self):
        self._registry: dict[str, ContentTypeRegistration] = {}

    def register(self, registration: ContentTypeRegistration) -> None:
        """Register a content type, keyed by ``registration.name``."""
        self._registry[registration.name] = registration

    def list_content_types(self) -> list[ContentTypeSummarySchema]:
        """Return summary entries for every registered content type."""
        return [
            ContentTypeSummarySchema(name=reg.name, label=reg.label)
            for reg in self._registry.values()
        ]

    def get(self, name: str) -> ContentTypeRegistration | None:
        """Return the registration for ``name``, or ``None`` if unknown."""
        return self._registry.get(name)

    def get_type_schemas(self, name: str) -> dict[str, Any] | None:
        """Return the JSON schemas for each direction of content type ``name``.

        Returns ``None`` when ``name`` is not registered. Directions without a
        schema fall back to a placeholder (``{"description": "Not yet available."}``)
        for ``create`` and ``patch`` so schema discovery keeps advertising the
        planned write directions.
        """
        registration = self.get(name)
        if registration is None:
            return None

        result = {}
        for direction in ("read", "create", "patch"):
            schema = self._schema_for_direction(registration, direction)
            if schema is not None:
                result[direction] = schema
            elif direction in ("create", "patch"):
                # TODO Placeholder until write endpoints land; keeps schema discovery
                # showing that create/patch directions are planned.
                result[direction] = {"description": "Not yet available."}
        return result

    def register_defaults(self) -> None:
        """Register the content types shipped with Wagtail (currently ``pages``)."""
        from wagtail.api.v3.schemas import BasePageSchema, generator
        from wagtail.models import get_page_models

        self.register(
            ContentTypeRegistration(
                name="pages",
                label="Pages",
                read_schema=BasePageSchema,
            )
        )

        for model in get_page_models():
            self.register(
                ContentTypeRegistration(
                    name=model._meta.label,
                    label=str(model._meta.verbose_name),
                    read_schema=generator.generate_schema(
                        model, base_class=BasePageSchema
                    ),
                )
            )

    def _schema_for_direction(
        self, registration: ContentTypeRegistration, direction: str
    ) -> dict[str, Any] | None:
        """Return the JSON schema for ``direction`` of ``registration``.

        ``direction`` is one of ``read``, ``create``, ``patch`` and maps to
        the matching ``<direction>_schema`` attribute. Returns ``None`` when no
        schema is defined for that direction.
        """
        schema_cls = getattr(registration, f"{direction}_schema", None)
        if schema_cls is None:
            return None
        return schema_cls.model_json_schema()


#: Module-level singleton consumed by routers and the app config.
registry = ContentTypeRegistry()
