from typing import cast

import swapper
from django.conf import settings
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Field, Query, Router
from ninja.pagination import LimitOffsetPagination

from wagtail import hooks
from wagtail.admin.api.v3.schemas import ExplorerSchema
from wagtail.permission_policies.pages import PagePermissionPolicy
from wagtail.permissions import policy_registry
from wagtail.query import PageQuerySet

Page = swapper.load_model("wagtailcore", "Page")
router = Router(tags=["explorer"])

# Match the page size of the admin's page listing view. This is independent of
# WAGTAILAPI_LIMIT_MAX, which is meant for the public API.
EXPLORER_PAGE_SIZE = 50


class ExplorerPagination(LimitOffsetPagination):
    class Input(LimitOffsetPagination.Input):
        limit: int = Field(EXPLORER_PAGE_SIZE, ge=1, le=EXPLORER_PAGE_SIZE)
        offset: int = Field(0, ge=0)


def get_explorer_queryset(queryset: PageQuerySet) -> PageQuerySet:
    queryset = (
        queryset.defer_streamfields()
        .specific()
        .prefetch_related("locale")
        .annotate_approved_schedule()
    )
    if getattr(settings, "WAGTAIL_WORKFLOW_ENABLED", True):
        queryset = queryset.prefetch_workflow_states()
    return queryset


def get_children(
    request: HttpRequest,
    page: Page,
    explorable_pages: PageQuerySet,
) -> PageQuerySet:
    queryset = explorable_pages.child_of(page)

    # Hooks are responsible for queryset modifications that may result in more
    # or fewer pages being included.
    for hook in hooks.get_hooks("construct_explorer_page_queryset"):
        queryset = hook(page, queryset, request)

    return get_explorer_queryset(queryset)


def get_translations(page: Page, explorable_pages: PageQuerySet) -> PageQuerySet:
    if page.is_root() or not getattr(settings, "WAGTAIL_I18N_ENABLED", False):
        return Page.objects.none()

    # Only include translations that have children, as the explorer is used to
    # navigate to the children of the page
    return (
        explorable_pages.translation_of(page)
        .filter(numchild__gt=0)
        .select_related("locale")
    )


@router.get("/{page_id}/", response=ExplorerSchema, url_name="explorer")
def explorer(
    request: HttpRequest,
    page_id: int,
    pagination: ExplorerPagination.Input = Query(...),  # ty: ignore[call-non-callable]
):
    permission_policy = cast(PagePermissionPolicy, policy_registry.get_by_type(Page))
    explorable_pages = permission_policy.explorable_instances(request.user)
    page = get_object_or_404(get_explorer_queryset(explorable_pages), pk=page_id)

    return {
        "page": page,
        "translations": get_translations(page, explorable_pages),
        "children": ExplorerPagination(max_limit=EXPLORER_PAGE_SIZE).paginate_queryset(
            get_children(request, page, explorable_pages),
            pagination=pagination,
            request=request,
        ),
    }
