from datetime import datetime
from typing import ClassVar, Literal, cast

import swapper
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Model
from django.shortcuts import get_object_or_404
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
from wagtail.api.v3.schemas.params import (
    TypeInjectingBody,
    TypeInjectingBodyModel,
)
from wagtail.models import AbstractPage

Page = swapper.load_model("wagtailcore", "Page")

#: Page's own fields that every concrete page type can accept on creation,
#: beyond whatever extra fields a model declares through ``api_fields``.
BASE_PAGE_FIELDS = [
    "title",
    "slug",
]
for field in ["seo_title", "search_description", "show_in_menus"]:
    try:
        Page._meta.get_field(field)
    except FieldDoesNotExist:
        pass
    else:
        BASE_PAGE_FIELDS.append(field)

BASE_PAGE_READ_FIELDS = BASE_PAGE_FIELDS + [
    "pk",
    "first_published_at",
    "locale",
]
BASE_PAGE_READ_FIELDS_SET = set(BASE_PAGE_READ_FIELDS)


class SimpleBasePageMetaSchema(BaseMetaSchema):
    type: str | None = None
    detail_url: str | None = None
    html_url: str | None = None

    @staticmethod
    def resolve_type(obj: Model, context: dict) -> str:
        return (cast(AbstractPage, obj).specific_class or Page)._meta.label

    @staticmethod
    def resolve_detail_url(obj: AbstractPage, context: dict) -> str | None:
        request = context["request"]
        try:
            path = reverse("wagtailapi_v3:detail_page", kwargs={"page_id": obj.pk})
            return get_full_url(request, path)
        except NoReverseMatch:
            return None

    @staticmethod
    def resolve_html_url(obj: AbstractPage, context: dict) -> str | None:
        request = context["request"]
        try:
            return obj.get_full_url(request)
        except NoReverseMatch:
            return None


# Used for nested schemas e.g. alias_of and parent
class SimpleBasePageSchema(BaseSchema):
    id: int
    title: str
    meta: SimpleBasePageMetaSchema


class BasePageMetaSchema(SimpleBasePageMetaSchema):
    locale: str | None = None
    slug: str
    first_published_at: datetime | None = None

    @staticmethod
    def resolve_locale(obj: AbstractPage, context: dict) -> str | None:
        return obj.locale.language_code if obj.locale else None


# Used for listing view
class BasePageSchema(SimpleBasePageSchema):
    meta: BasePageMetaSchema


class PageMetaSchema(BasePageMetaSchema):
    if "show_in_menus" in BASE_PAGE_READ_FIELDS_SET:
        show_in_menus: bool | None = None

    if "seo_title" in BASE_PAGE_READ_FIELDS_SET:
        seo_title: str | None = None

    if "search_description" in BASE_PAGE_READ_FIELDS_SET:
        search_description: str | None = None

    alias_of: SimpleBasePageSchema | None = None
    parent: SimpleBasePageSchema | None = None

    @staticmethod
    def resolve_parent(obj: AbstractPage, context: dict) -> AbstractPage | None:
        return obj.get_parent()


# Used for detail view
class PageSchema(BasePageSchema):
    meta: PageMetaSchema


class PageCreateMetaSchema(BaseCreateMetaSchema):
    parent_id: int
    action: Literal["publish"] | None = None


class PageCreateBaseSchema(BaseCreateSchema):
    meta: PageCreateMetaSchema


class PageUpdateMetaSchema(BaseUpdateMetaSchema):
    action: Literal["publish"] | None = None


class PageUpdateBaseSchema(BaseUpdateSchema):
    meta: PageUpdateMetaSchema | None = PageUpdateMetaSchema()


class PageTypeInjectingBodyModel(TypeInjectingBodyModel):
    page_id_param: ClassVar[str] = "page_id"

    @classmethod
    def get_meta_type(cls, request, api, path_params) -> str:
        page_id = path_params.get(cls.page_id_param)
        ct_ids = Page.objects.values_list("content_type_id", flat=True)
        content_type_id = get_object_or_404(ct_ids, pk=page_id)
        content_type = ContentType.objects.get_for_id(content_type_id)
        return (content_type.model_class() or Page)._meta.label


class PageTypeInjectingBody(TypeInjectingBody):
    _model = PageTypeInjectingBodyModel
