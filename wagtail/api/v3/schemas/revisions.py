from datetime import datetime
from typing import Optional
from uuid import UUID

from django.contrib.contenttypes.models import ContentType
from pydantic import PositiveInt

from .base import BaseSchema


class ContentTypeSchema(BaseSchema):
    id: int
    name: str
    label: str

    @staticmethod
    def resolve_name(obj: ContentType) -> str:
        model = obj.model_class()
        return model._meta.label if model else f"{obj.app_label}.{obj.model}"

    @staticmethod
    def resolve_label(obj: ContentType) -> str:
        model = obj.model_class()
        return str(model._meta.verbose_name) if model else obj.model


class RevisionSchema(BaseSchema):
    id: PositiveInt
    object_id: str
    created_at: datetime
    user_id: Optional[int | str | UUID] = None
    object_str: str
    approved_go_live_at: Optional[datetime] = None


class RevisionDetailSchema(RevisionSchema):
    content_type: ContentTypeSchema
    base_content_type: ContentTypeSchema
    # Subclasses must define the type of content_object, which is a schema of
    # the model instance that the revision is for.

    @staticmethod
    def resolve_content_object(obj):
        return obj.as_object()
