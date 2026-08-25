from typing import Literal, Optional, TypeAlias, cast

import swapper
from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db.models import Model, Q
from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from ninja import Body, FilterSchema, Query, Router, Schema, Status
from ninja.pagination import paginate
from pydantic import PositiveInt, field_validator, model_validator

from wagtail.actions import action_registry
from wagtail.actions.convert_alias import ConvertAliasPageError
from wagtail.actions.copy_for_translation import ParentNotTranslatedError
from wagtail.actions.copy_page import CopyPageIntegrityError
from wagtail.actions.create_alias import CreatePageAliasIntegrityError
from wagtail.actions.publish_page_revision import PublishPagePermissionError
from wagtail.api.rich_text import RichTextOutputFormat
from wagtail.api.v3.auth import AllowAnonymous, BearerTokenAuth
from wagtail.api.v3.errors import as_validation_error
from wagtail.api.v3.form_data import build_page_form, build_page_update_form
from wagtail.api.v3.pagination import WagtailLimitOffsetPagination
from wagtail.api.v3.permissions import require_any_permission
from wagtail.api.v3.querysets import get_pages_queryset
from wagtail.api.v3.schemas import BasePageSchema
from wagtail.api.v3.schemas.base import build_union_schemas
from wagtail.api.v3.schemas.pages import BASE_PAGE_READ_FIELDS, PageTypeInjectingBody
from wagtail.api.v3.schemas.params import (
    APIFieldFilterSchema,
    OrderingSchema,
    RevisionFilterSchema,
    SearchSchema,
    locale_filter_q,
)
from wagtail.api.v3.schemas.revisions import RevisionDetailSchema, RevisionSchema
from wagtail.api.validators import SiteFilterValidator
from wagtail.coreutils import find_available_slug, resolve_model_string
from wagtail.models import Locale, Site, get_page_models
from wagtail.query import PageQuerySet

Page = swapper.load_model("wagtailcore", "Page")
router = Router(tags=["pages"])
actions_router = Router(auth=BearerTokenAuth())

page_models = get_page_models()
PageTypeLiteral = Literal[tuple(model._meta.label for model in page_models)]  # ty: ignore[invalid-type-form]
_page_schemas = build_union_schemas(page_models)
PageDetailSchema = _page_schemas.detail
PageCreateSchema = _page_schemas.create
PageUpdateSchema = _page_schemas.update


class PageRevisionDetailSchema(RevisionDetailSchema):
    content_object: PageDetailSchema


IntPKFilter: TypeAlias = PositiveInt
RootRelativeFilter: TypeAlias = IntPKFilter | Literal["root"]


# A no-op so that Ninja does not try to do a default exact lookup with the value
def custom_filter(self, value):
    return Q()


class PageFilterSchema(FilterSchema):
    type: list[PageTypeLiteral] = []
    ancestor_of: Optional[IntPKFilter] = None
    child_of: Optional[RootRelativeFilter] = None
    descendant_of: Optional[RootRelativeFilter] = None
    translation_of: Optional[RootRelativeFilter] = None
    locale: Optional[str] = None
    site: Optional[str] = None

    @field_validator("type", mode="after")
    @classmethod
    def parse_type(cls, value: list[PageTypeLiteral]) -> list:
        return [resolve_model_string(model) for model in value]

    def filter_type(self, value: list) -> Q:
        if len(value) <= 1:
            return Q()
        content_types = [
            ct.pk for ct in ContentType.objects.get_for_models(*value).values()
        ]
        return Q(content_type__in=content_types)

    def filter_locale(self, value: str) -> Q:
        if not value:
            return Q()
        return locale_filter_q(value)

    @model_validator(mode="after")
    def validate_child_of_or_descendant_of(self):
        if self.child_of and self.descendant_of:
            raise ValueError(
                "filtering by descendant_of with child_of is not supported."
            )
        return self

    filter_ancestor_of = custom_filter
    filter_child_of = custom_filter
    filter_descendant_of = custom_filter
    filter_translation_of = custom_filter
    filter_site = custom_filter  # Handled via get_pages_queryset

    @staticmethod
    def get_request_root_page(request: HttpRequest) -> Page:
        return Site.find_for_request(request).root_page

    @staticmethod
    def get_public_page(request: HttpRequest, page_id: int, loc: str) -> Page:
        try:
            return get_pages_queryset(request).get(pk=page_id)
        except Page.DoesNotExist as e:
            message = f"No {Page._meta.object_name} matches the given {loc} value."
            raise as_validation_error(e, message, loc=(loc,)) from e

    @staticmethod
    def get_public_page_or_root(
        request: HttpRequest,
        page_id: RootRelativeFilter,
        loc: str,
    ) -> Page:
        if page_id == "root":
            return PageFilterSchema.get_request_root_page(request)
        return PageFilterSchema.get_public_page(request, page_id, loc)

    def apply_ancestor_of(
        self,
        request: HttpRequest,
        queryset: PageQuerySet,
    ) -> PageQuerySet:
        if self.ancestor_of is None:
            return queryset
        relative_to = self.get_public_page(request, self.ancestor_of, "ancestor_of")
        return queryset.ancestor_of(relative_to)

    def apply_descendant_of(
        self,
        request: HttpRequest,
        queryset: PageQuerySet,
    ) -> PageQuerySet:
        relative_to = self.child_of or self.descendant_of
        if relative_to is None:
            return queryset
        loc = "child_of" if self.child_of else "descendant_of"
        relative_to = self.get_public_page_or_root(request, relative_to, loc)
        if self.child_of:
            return queryset.child_of(relative_to)
        return queryset.descendant_of(relative_to)

    def apply_translation_of(
        self,
        request: HttpRequest,
        queryset: PageQuerySet,
    ) -> PageQuerySet:
        if self.translation_of is None:
            return queryset
        relative_to = self.get_public_page_or_root(
            request, self.translation_of, "translation_of"
        )
        return queryset.translation_of(relative_to)

    def apply_custom_filters(
        self,
        request: HttpRequest,
        queryset: PageQuerySet,
    ) -> PageQuerySet:
        queryset = self.apply_ancestor_of(request, queryset)
        queryset = self.apply_descendant_of(request, queryset)
        queryset = self.apply_translation_of(request, queryset)
        return queryset

    def filter(
        self,
        queryset: PageQuerySet,
        request: Optional[HttpRequest] = None,
    ) -> PageQuerySet:
        queryset = super().filter(queryset)
        # request is optional as it's not part of Ninja's FilterSchema API
        if request:
            queryset = self.apply_custom_filters(request, queryset)
        return queryset


@router.get(
    "/",
    response=list[BasePageSchema],
    url_name="list_pages",
    summary="List pages",
    operation_id="pages_list",
    auth=[BearerTokenAuth(), AllowAnonymous()],
)
@paginate(
    WagtailLimitOffsetPagination,
    pass_parameter="pagination_info",  # noqa: S106 not a password
)
def list_pages(
    request: HttpRequest,
    filters: PageFilterSchema = Query(...),  # ty: ignore[call-non-callable]
    ordering: OrderingSchema = Query(...),  # ty: ignore[call-non-callable]
    search: SearchSchema = Query(...),  # ty: ignore[call-non-callable]
    **kwargs,
):
    pagination_info = cast(
        WagtailLimitOffsetPagination.Input,
        kwargs.get("pagination_info"),
    )
    models = cast(list[type[Model]], filters.type)
    model = models[0] if len(models) == 1 else Page
    field_filter = APIFieldFilterSchema.with_exclude_schemas(
        raw_params=request.GET,
        schemas=(PageFilterSchema, OrderingSchema, SearchSchema),
        base_fields=BASE_PAGE_READ_FIELDS,
    )
    queryset = get_pages_queryset(request, model)
    queryset = filters.filter(queryset, request)
    queryset = field_filter.filter_queryset(queryset)
    queryset = ordering.order_queryset(
        queryset,
        pagination_info,
        base_fields=BASE_PAGE_READ_FIELDS,
    )
    queryset = search.search_queryset(request, queryset)
    return queryset


@router.get(
    "/find/",
    response=PageDetailSchema,
    url_name="find_page",
    summary="Find page",
    operation_id="pages_find",
    auth=[BearerTokenAuth(), AllowAnonymous()],
)
def find_page(
    request: HttpRequest,
    id: Optional[PositiveInt] = None,
    html_path: Optional[str] = None,
    site: Optional[str] = None,
    version: Optional[Literal["live", "draft"]] = Query("live"),  # ty: ignore[call-non-callable]
):
    page = None

    if html_path:
        path_components = [component for component in html_path.split("/") if component]
        try:
            site_obj = SiteFilterValidator(site=site, request=request).site_obj
            if site_obj is None:  # No Site records
                raise Http404
            page, _, _ = site_obj.root_page.specific.route(request, path_components)
        except Http404:
            page = None
        else:
            if not get_pages_queryset(request).filter(id=page.id).exists():
                page = None

    if page is None and id:
        # get_pages_queryset() already does site filtering
        page = get_object_or_404(get_pages_queryset(request), pk=id)

    if page is None:
        raise Http404(f"No {Page._meta.object_name} matches the given query.")

    url = reverse("wagtailapi_v3:detail_page", kwargs={"page_id": page.pk})
    query = request.GET.copy()
    query.pop("id", None)
    query.pop("html_path", None)
    return redirect(f"{url}?{query.urlencode()}")


@router.get(
    "/{page_id}/",
    response=PageDetailSchema,
    url_name="detail_page",
    summary="Page detail",
    operation_id="pages_detail",
    auth=[BearerTokenAuth(), AllowAnonymous()],
)
def get_page(
    request: HttpRequest,
    page_id: int,
    version: Optional[Literal["live", "draft"]] = Query("live"),  # ty: ignore[call-non-callable]
    rich_text_format: RichTextOutputFormat | None = Query(None),  # ty: ignore[call-non-callable]
):
    page = get_object_or_404(get_pages_queryset(request), pk=page_id)
    if version == "draft" and request.user.is_authenticated:
        return page.get_latest_revision_as_object()
    return page.specific


@router.post(
    "/",
    response={201: PageDetailSchema},
    url_name="create_page",
    summary="Create page",
    operation_id="pages_create",
    auth=BearerTokenAuth(),
)
@require_any_permission(Page, ("add",))
def create_page(
    request: HttpRequest,
    data: PageCreateSchema = Body(...),  # ty: ignore[call-non-callable]
    rich_text_format: RichTextOutputFormat | None = Query(None),  # ty: ignore[call-non-callable]
):
    model = resolve_model_string(data.meta.type)
    parent = get_object_or_404(Page, id=data.meta.parent_id).specific
    form = build_page_form(model, parent, data, request.user)
    action_class = action_registry.get_action_class(model, "create")
    action = action_class(
        form.instance,
        parent,
        user=request.user,
        form=form,
        publish=data.meta.action == "publish",
    )
    action.execute()
    return Status(201, form.instance)


@router.patch(
    "/{page_id}/",
    response=PageDetailSchema,
    url_name="update_page",
    summary="Update page",
    operation_id="pages_update",
    auth=BearerTokenAuth(),
)
@require_any_permission(Page, ("change",))
def update_page(
    request: HttpRequest,
    page_id: int,
    data: PageUpdateSchema = PageTypeInjectingBody(...),
    rich_text_format: RichTextOutputFormat | None = Query(None),  # ty: ignore[call-non-callable]
):
    model = resolve_model_string(data.meta.type)
    page = get_object_or_404(model, pk=page_id)
    form = build_page_update_form(page, data, request.user)
    action_class = action_registry.get_action_class(model, "edit")
    action = action_class(
        form.instance,
        user=request.user,
        form=form,
        publish=data.meta.action == "publish",
    )
    action.execute()
    return form.instance


def _check_can_view_revisions(request: HttpRequest, page: Page) -> None:
    perms = page.permissions_for_user(request.user)
    if not (perms.can_publish() or perms.can_edit()):
        raise PermissionDenied


@router.get(
    "/{page_id}/revisions/",
    response=list[RevisionSchema],
    url_name="list_page_revisions",
    summary="List page revisions",
    operation_id="pages_revisions_list",
    auth=BearerTokenAuth(),
)
@paginate(WagtailLimitOffsetPagination)
@require_any_permission(Page, ("add", "change", "publish"))
def list_page_revisions(
    request: HttpRequest,
    page_id: int,
    filters: RevisionFilterSchema = Query(...),  # ty: ignore[call-non-callable]
    **kwargs,
):
    page = get_object_or_404(get_pages_queryset(request), pk=page_id).specific
    _check_can_view_revisions(request, page)
    queryset = page.revisions.order_by("-created_at", "-id")
    return filters.filter(queryset)


@router.get(
    "/{page_id}/revisions/{revision_id}/",
    response=PageRevisionDetailSchema,
    url_name="detail_page_revision",
    summary="Page revision detail",
    operation_id="pages_revisions_detail",
    auth=BearerTokenAuth(),
)
@require_any_permission(Page, ("add", "change", "publish"))
def get_page_revision(request: HttpRequest, page_id: int, revision_id: PositiveInt):
    page = get_object_or_404(get_pages_queryset(request), pk=page_id).specific
    _check_can_view_revisions(request, page)
    revisions = page.revisions.select_related("content_type", "base_content_type")
    return get_object_or_404(revisions, pk=revision_id)


@actions_router.post(
    "/{page_id}/actions/publish/",
    response=PageDetailSchema,
    url_name="pages_actions_publish",
    summary="Publish page",
    operation_id="pages_actions_publish",
)
@require_any_permission(Page, ("publish",))
def publish(request: HttpRequest, page_id: PositiveInt):
    page = get_object_or_404(Page, pk=page_id).specific
    revision = page.get_latest_revision()

    # If the page has no revision, create one only if the user has permission.
    if revision is None:
        if not page.permissions_for_user(request.user).can_publish():
            raise PublishPagePermissionError(
                "You do not have permission to publish this page."
            )
        revision = page.save_revision(user=request.user)

    action_class = action_registry.get_action_class(Page, "publish")
    action = action_class(revision, user=request.user)
    action.execute()
    return page.specific_class.objects.get(pk=page.pk)


class PageUnpublishSchema(Schema):
    recursive: bool = False


@actions_router.post(
    "/{page_id}/actions/unpublish/",
    response=PageDetailSchema,
    url_name="pages_actions_unpublish",
    summary="Unpublish page",
    operation_id="pages_actions_unpublish",
)
@require_any_permission(Page, ("publish",))
def unpublish(
    request: HttpRequest,
    page_id: PositiveInt,
    data: PageUnpublishSchema = Body(PageUnpublishSchema()),  # ty: ignore[call-non-callable]
):
    page = get_object_or_404(Page, pk=page_id).specific
    action_class = action_registry.get_action_class(Page, "unpublish")
    action = action_class(page, user=request.user, include_descendants=data.recursive)
    action.execute()
    return page


def _validate_slug(value: Optional[str]) -> Optional[str]:
    """
    Checks for Wagtail’s slug format, respecting unicode on/off settings.
    Replicates ``SlugField`` from ``CopyForm`` in the admin.
    """
    if value is None:
        return None
    allow_unicode = getattr(settings, "WAGTAIL_ALLOW_UNICODE_SLUGS", True)
    field = forms.SlugField(allow_unicode=allow_unicode)
    try:
        field.clean(value)
    except forms.ValidationError as exc:
        raise ValueError(exc.messages[0]) from exc
    return value


class PageCopySchema(Schema):
    destination_id: Optional[PositiveInt] = None
    recursive: bool = False
    keep_live: bool = True
    slug: Optional[str] = None
    title: Optional[str] = None

    @field_validator("slug", mode="after")
    @classmethod
    def validate_slug(cls, value: Optional[str]) -> Optional[str]:
        return _validate_slug(value)

    def get_destination(self) -> Page:
        if self.destination_id is None:
            return None
        return get_object_or_404(Page, pk=self.destination_id)

    def get_update_attrs(self, page: Page, destination: Page | None) -> dict:
        update_attrs = {}
        if self.slug:
            update_attrs["slug"] = self.slug
        else:
            destination = destination or page.get_parent()
            available_slug = find_available_slug(destination, page.slug)
            if available_slug != page.slug:
                update_attrs["slug"] = available_slug
        if self.title:
            update_attrs["title"] = self.title
        return update_attrs


@actions_router.post(
    "/{page_id}/actions/copy/",
    response={201: PageDetailSchema},
    url_name="pages_actions_copy",
    summary="Copy page",
    operation_id="pages_actions_copy",
)
@require_any_permission(Page, ("add",))
def copy(
    request: HttpRequest,
    page_id: PositiveInt,
    data: PageCopySchema = Body(PageCopySchema()),  # ty: ignore[call-non-callable]
):
    page = get_object_or_404(Page, pk=page_id)
    destination = data.get_destination()
    update_attrs = data.get_update_attrs(page, destination)
    action_class = action_registry.get_action_class(Page, "copy")
    action = action_class(
        page=page,
        to=destination,
        recursive=data.recursive,
        keep_live=data.keep_live,
        update_attrs=update_attrs,
        user=request.user,
    )
    try:
        new_page = action.execute()
    except CopyPageIntegrityError as e:
        raise as_validation_error(e) from e
    return Status(201, new_page)


PagePositionLiteral = Literal[
    "first-child",
    "last-child",
    "left",
    "right",
    "first-sibling",
    "last-sibling",
]


class PageMoveSchema(Schema):
    destination_id: PositiveInt
    position: Optional[PagePositionLiteral] = None


@actions_router.post(
    "/{page_id}/actions/move/",
    response=PageDetailSchema,
    url_name="pages_actions_move",
    summary="Move page",
    operation_id="pages_actions_move",
)
@require_any_permission(Page, ("change",))
def move(
    request: HttpRequest,
    page_id: PositiveInt,
    data: PageMoveSchema = Body(...),  # ty: ignore[call-non-callable]
):
    page = get_object_or_404(Page, pk=page_id)
    target = get_object_or_404(Page, pk=data.destination_id)
    action_class = action_registry.get_action_class(Page, "move")
    action = action_class(page, target, pos=data.position, user=request.user)
    action.execute()
    page.refresh_from_db()
    return page.specific


@router.delete(
    "/{page_id}/",
    response={204: None},
    url_name="delete_page",
    summary="Delete page",
    operation_id="pages_delete",
    auth=BearerTokenAuth(),
)
@actions_router.delete(
    "/{page_id}/actions/delete/",
    response={204: None},
    url_name="pages_actions_delete",
    summary="Delete page",
    operation_id="pages_actions_delete",
)
@require_any_permission(Page, ("change",))
def delete(request: HttpRequest, page_id: PositiveInt):
    page = get_object_or_404(Page, pk=page_id).specific
    action_class = action_registry.get_action_class(Page, "delete")
    action = action_class(page, user=request.user)
    action.execute()
    return Status(204, None)


class PageRevertSchema(Schema):
    revision_id: PositiveInt


@actions_router.post(
    "/{page_id}/actions/revert/",
    response=PageDetailSchema,
    url_name="pages_actions_revert",
    summary="Revert page to a previous revision",
    operation_id="pages_actions_revert",
)
@require_any_permission(Page, ("change",))
def revert(
    request: HttpRequest,
    page_id: PositiveInt,
    data: PageRevertSchema = Body(...),  # ty: ignore[call-non-callable]
):
    page = get_object_or_404(Page, pk=page_id).specific
    revision = get_object_or_404(page.revisions, id=data.revision_id)
    action_class = action_registry.get_action_class(Page, "revert")
    action = action_class(instance=page, revision=revision, user=request.user)
    new_revision = action.execute()
    return new_revision.as_object()


@actions_router.post(
    "/{page_id}/actions/convert_alias/",
    response=PageDetailSchema,
    url_name="pages_actions_convert_alias",
    summary="Convert alias page to a regular page",
    operation_id="pages_actions_convert_alias",
)
@require_any_permission(Page, ("change",))
def convert_alias(request: HttpRequest, page_id: PositiveInt):
    page = get_object_or_404(Page, pk=page_id).specific
    action_class = action_registry.get_action_class(Page, "convert_alias")
    action = action_class(page, user=request.user)
    try:
        new_page = action.execute()
    except ConvertAliasPageError as e:
        raise as_validation_error(e) from e
    return new_page


class PageCreateAliasSchema(Schema):
    destination_id: Optional[PositiveInt] = None
    recursive: bool = False
    slug: Optional[str] = None

    @field_validator("slug", mode="after")
    @classmethod
    def validate_slug(cls, value: Optional[str]) -> Optional[str]:
        return _validate_slug(value)

    def get_destination(self) -> Page | None:
        if self.destination_id is None:
            return None
        return get_object_or_404(Page, pk=self.destination_id)

    def get_update_slug(self, page: Page, destination: Page | None) -> str:
        if self.slug:
            return self.slug
        return find_available_slug(destination or page.get_parent(), page.slug)


@actions_router.post(
    "/{page_id}/actions/create_alias/",
    response={201: PageDetailSchema},
    url_name="pages_actions_create_alias",
    summary="Create an alias of a page",
    operation_id="pages_actions_create_alias",
)
@require_any_permission(Page, ("add",))
def create_alias(
    request: HttpRequest,
    page_id: PositiveInt,
    data: PageCreateAliasSchema = Body(PageCreateAliasSchema()),  # ty: ignore[call-non-callable]
):
    page = get_object_or_404(Page, pk=page_id).specific
    destination = data.get_destination()
    action_class = action_registry.get_action_class(Page, "create_alias")
    action = action_class(
        page,
        recursive=data.recursive,
        parent=destination,
        update_slug=data.get_update_slug(page, destination),
        user=request.user,
    )
    try:
        new_page = action.execute()
    except CreatePageAliasIntegrityError as e:
        raise as_validation_error(e) from e
    return Status(201, new_page)


class PageCopyForTranslationSchema(Schema):
    locale: str
    copy_parents: bool = False
    alias: bool = False
    recursive: bool = False


@actions_router.post(
    "/{page_id}/actions/copy_for_translation/",
    response={201: PageDetailSchema},
    url_name="pages_actions_copy_for_translation",
    summary="Copy page for translation",
    operation_id="pages_actions_copy_for_translation",
)
@require_any_permission(Page, ("add",))
def copy_for_translation(
    request: HttpRequest,
    page_id: PositiveInt,
    data: PageCopyForTranslationSchema = Body(...),  # ty: ignore[call-non-callable]
):
    if not getattr(settings, "WAGTAIL_I18N_ENABLED", False):
        raise Http404("Internationalization is not enabled.")

    page = get_object_or_404(Page, pk=page_id).specific
    locale = get_object_or_404(Locale, language_code=data.locale)

    action_class = action_registry.get_action_class(Page, "copy_for_translation")
    action = action_class(
        page=page,
        locale=locale,
        copy_parents=data.copy_parents,
        alias=data.alias,
        user=request.user,
        include_subtree=data.recursive,
    )
    try:
        new_page = action.execute()
    except ParentNotTranslatedError as e:
        raise as_validation_error(e) from e
    return Status(201, new_page)


router.add_router("/", actions_router)
