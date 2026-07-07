from django.db.models import Model
from ninja import Schema


class BaseMetaSchema(Schema):
    type: str | None = None


class BaseSchema(Schema):
    meta: BaseMetaSchema

    @staticmethod
    def resolve_meta(obj: Model) -> BaseMetaSchema:
        return BaseMetaSchema(type=obj._meta.label)


class ContentTypeSummarySchema(Schema):
    name: str
    label: str
