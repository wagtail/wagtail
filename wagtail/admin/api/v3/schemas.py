from ninja import Field

from wagtail.api.v3.schemas import BasePageMetaSchema, BasePageSchema
from wagtail.models import AbstractPage


class AdminPageMetaSchema(BasePageMetaSchema):
    live: bool
    has_unpublished_changes: bool
    status: str

    @staticmethod
    def resolve_status(obj: AbstractPage, context: dict) -> str:
        # Resolve translatable string
        return str(obj.status_string)


class AdminPageSchema(BasePageSchema):
    meta: AdminPageMetaSchema
    admin_display_title: str = Field(..., alias="get_admin_display_title")
