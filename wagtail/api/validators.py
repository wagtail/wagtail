from functools import cached_property
from typing import Any, Optional

from django.db.models import Model
from django.shortcuts import get_object_or_404
from pydantic import BaseModel, TypeAdapter, computed_field, model_validator

from wagtail.api import APIField
from wagtail.models import Site


class APIFieldValidator(BaseModel):
    model: type[Model]
    fields: list[str]
    base_fields: list[str] = []
    db_fields_only: bool = False
    skip_invalid: bool = False

    @computed_field
    @cached_property
    def allowed_fields(self) -> set[str]:
        declared_fields = APIField.get_fields_for_model(
            self.model,
            db_fields_only=self.db_fields_only,
        )
        allowed_fields = set(self.base_fields) | {f.name for f in declared_fields}

        if "pk" in allowed_fields:
            allowed_fields.add(self.model._meta.pk.attname)

        return allowed_fields

    @computed_field
    @cached_property
    def valid_fields(self) -> list[str]:
        return [field for field in self.fields if field in self.allowed_fields]

    @computed_field
    @cached_property
    def invalid_fields(self) -> list[str]:
        return [field for field in self.fields if field not in self.allowed_fields]

    @model_validator(mode="after")
    def validate_fields(self):
        if self.skip_invalid:
            self.fields = self.valid_fields
            return self
        if self.invalid_fields:
            raise ValueError(
                f"invalid fields for model {self.model._meta.object_name}: "
                f"{list(self.invalid_fields)}."
            )
        return self


class OrderingValidator(APIFieldValidator):
    has_offset: bool = False

    @computed_field
    @cached_property
    def allowed_fields(self) -> set[str]:
        allowed_fields = super().allowed_fields
        allowed_fields |= {f"-{field}" for field in allowed_fields} | {"random"}
        return allowed_fields

    @model_validator(mode="after")
    def validate_random(self):
        if "random" in self.fields:
            if len(self.fields) > 1:
                raise ValueError(
                    "random ordering cannot be combined with other fields."
                )
            if self.has_offset:
                raise ValueError("random ordering with offset is not supported.")
            self.fields = ["?"]
        return self


class SiteFilterValidator(BaseModel, arbitrary_types_allowed=True):
    site: Optional[str] = None
    request: Any  # DRF Request or Django HttpRequest

    @computed_field
    @cached_property
    def query(self) -> dict[str, str] | None:
        if not self.site:
            return None
        # Optionally allow querying by port
        if ":" in self.site:
            (hostname, port) = self.site.split(":", 1)
            return {"hostname": hostname, "port": port}
        return {"hostname": self.site}

    @computed_field
    @cached_property
    def site_obj(self) -> Site:
        if not self.query:
            return Site.find_for_request(self.request)
        try:
            return get_object_or_404(Site, **self.query)
        except Site.MultipleObjectsReturned as e:
            raise ValueError(
                "Your query returned multiple sites. "
                "Try adding a port number to your site filter."
            ) from e


bool_adapter = TypeAdapter(bool)
