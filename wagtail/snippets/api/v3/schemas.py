from typing import ClassVar, Literal

from django.contrib.admin.utils import quote
from django.db.models import Model
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

from wagtail.api.v2.utils import get_full_url
from wagtail.api.v3.schemas.base import (
    BaseCreateMetaSchema,
    BaseCreateSchema,
    BaseMetaSchema,
    BaseSchema,
    BaseUpdateMetaSchema,
    BaseUpdateSchema,
)
from wagtail.api.v3.schemas.params import TypeInjectingBody, TypeInjectingBodyModel


class SnippetMetaSchema(BaseMetaSchema):
    detail_url: str | None = None

    @staticmethod
    def resolve_detail_url(obj: Model, context: dict) -> str | None:
        request = context["request"]
        model = type(obj)

        try:
            path = reverse(
                "wagtailapi_v3:detail_snippet",
                kwargs={"type": model._meta.label, "pk": quote(str(obj.pk))},
            )
            detail_url = get_full_url(request, path)
        except NoReverseMatch:
            detail_url = None

        return detail_url


class BaseSnippetSchema(BaseSchema):
    meta: SnippetMetaSchema


class BaseSnippetCreateMetaSchema(BaseCreateMetaSchema):
    type: str | None = None


class BaseSnippetCreateSchema(BaseCreateSchema):
    meta: BaseSnippetCreateMetaSchema | None = BaseSnippetCreateMetaSchema()


class BaseSnippetUpdateMetaSchema(BaseUpdateMetaSchema):
    pass


class BaseSnippetUpdateSchema(BaseUpdateSchema):
    meta: BaseSnippetUpdateMetaSchema | None = BaseSnippetUpdateMetaSchema()


PUBLISH_ACTION_META_FIELD = {"action": (Literal["publish"] | None, None)}


class ParamTypeInjectingBodyModel(TypeInjectingBodyModel):
    type_param: ClassVar[str] = "type"
    validate = True

    @classmethod
    def get_meta_type(cls, request, api, path_params):
        return path_params.get(cls.type_param)


class ParamTypeInjectingBody(TypeInjectingBody):
    _model = ParamTypeInjectingBodyModel
