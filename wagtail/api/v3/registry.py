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
    name: str
    label: str
    read_schema: type[BaseModel] | None = None
    create_schema: type[BaseModel] | None = None
    patch_schema: type[BaseModel] | None = None


# Content types keyed by name.
_registry: dict[str, ContentTypeRegistration] = {}


def register_content_type(registration: ContentTypeRegistration) -> None:
    _registry[registration.name] = registration


def list_content_types() -> list[ContentTypeSummarySchema]:
    return [
        ContentTypeSummarySchema(name=reg.name, label=reg.label)
        for reg in _registry.values()
    ]


def get_content_type(name: str) -> ContentTypeRegistration | None:
    return _registry.get(name)


def _schema_for_direction(
    registration: ContentTypeRegistration, direction: str
) -> dict[str, Any] | None:
    schema_cls = getattr(registration, f"{direction}_schema", None)
    if schema_cls is None:
        return None
    return schema_cls.model_json_schema()


def get_type_schemas(name: str) -> dict[str, Any] | None:
    registration = get_content_type(name)
    if registration is None:
        return None

    result = {}
    for direction in ("read", "create", "patch"):
        schema = _schema_for_direction(registration, direction)
        if schema is not None:
            result[direction] = schema
        elif direction in ("create", "patch"):
            # TODO Placeholder until write endpoints land; keeps schema discovery
            # showing that create/patch directions are planned.
            result[direction] = {"description": "Not yet available."}
    return result


def register_default_content_types() -> None:
    from wagtail.api.v3.schemas import PageListingSchema

    register_content_type(
        ContentTypeRegistration(
            name="pages",
            label="Pages",
            read_schema=PageListingSchema,
        )
    )
