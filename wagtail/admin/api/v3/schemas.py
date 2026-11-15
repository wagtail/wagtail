from typing import cast

import swapper
from ninja import Schema

from wagtail.models import AbstractPage
from wagtail.permission_policies.pages import PagePermissionPolicy
from wagtail.permissions import policy_registry

Page = swapper.load_model("wagtailcore", "Page")


class AdminSimplePageMetaSchema(Schema):
    type: str

    @staticmethod
    def resolve_type(obj: AbstractPage) -> str:
        return (obj.specific_class or Page)._meta.label


# Used for the parent of the explorer's current page
class AdminSimplePageSchema(Schema):
    id: int
    title: str
    meta: AdminSimplePageMetaSchema

    @staticmethod
    def resolve_meta(obj: AbstractPage) -> AbstractPage:
        # Pass through so resolve_* methods on meta schema works with the model
        return obj


class AdminPageMetaSchema(AdminSimplePageMetaSchema):
    locale: str
    depth: int
    status: str
    live: bool
    has_unpublished_changes: bool
    has_children: bool

    @staticmethod
    def resolve_locale(obj: AbstractPage) -> str:
        return obj.locale.language_code

    @staticmethod
    def resolve_status(obj: AbstractPage) -> str:
        return str(obj.status_string)

    @staticmethod
    def resolve_has_children(obj: AbstractPage) -> bool:
        return obj.numchild > 0


class AdminPageDetailMetaSchema(AdminPageMetaSchema):
    parent: AdminSimplePageSchema | None = None

    @staticmethod
    def resolve_parent(obj: AbstractPage, context: dict) -> AbstractPage | None:
        # Only include the parent if the user can explore it, e.g. the parent
        # of the user's explorable root page is not included
        permission_policy = cast(
            PagePermissionPolicy, policy_registry.get_by_type(Page)
        )
        return (
            permission_policy.explorable_instances(context["request"].user)
            .parent_of(obj)
            .first()
        )


# Used for child pages in the explorer
class AdminPageSchema(AdminSimplePageSchema):
    meta: AdminPageMetaSchema
    admin_display_title: str

    @staticmethod
    def resolve_admin_display_title(obj: AbstractPage) -> str:
        return obj.get_admin_display_title()


# Used for the explorer's current page
class AdminPageDetailSchema(AdminPageSchema):
    meta: AdminPageDetailMetaSchema


class ExplorerTranslationSchema(Schema):
    id: int
    locale: str

    @staticmethod
    def resolve_locale(obj: AbstractPage) -> str:
        return obj.locale.language_code


class ExplorerChildrenSchema(Schema):
    count: int
    items: list[AdminPageSchema]


class ExplorerSchema(Schema):
    page: AdminPageDetailSchema
    translations: list[ExplorerTranslationSchema]
    children: ExplorerChildrenSchema
