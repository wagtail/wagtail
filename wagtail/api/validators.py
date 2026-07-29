from django.db.models import Model
from pydantic import BaseModel, model_validator

from wagtail.api import APIField


class APIFieldValidator(BaseModel):
    model: type[Model]
    fields: list[str]
    base_fields: list[str] = []
    db_fields_only: bool = False

    def get_allowed_fields(self) -> set[str]:
        declared_fields = APIField.get_fields_for_model(
            self.model,
            db_fields_only=self.db_fields_only,
        )
        allowed_fields = set(self.base_fields) | {f.name for f in declared_fields}

        if "pk" in allowed_fields:
            allowed_fields.add(self.model._meta.pk.attname)

        return allowed_fields

    def get_invalid_fields(self) -> set[str]:
        allowed_fields = self.get_allowed_fields()
        return {field for field in self.fields if field not in allowed_fields}

    @model_validator(mode="after")
    def validate_fields(self):
        if invalid_fields := self.get_invalid_fields():
            raise ValueError(
                f"invalid fields for model {self.model._meta.object_name}: "
                f"{list(invalid_fields)}."
            )
        return self


class OrderingValidator(APIFieldValidator):
    has_offset: bool = False

    def get_allowed_fields(self):
        allowed_fields = super().get_allowed_fields()
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
