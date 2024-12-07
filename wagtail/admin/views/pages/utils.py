from django.urls import reverse
from django.utils.functional import cached_property

# Retain backwards compatibility for imports
from wagtail.admin.utils import (  # noqa: F401
    get_latest_str,
    get_valid_next_url_from_request,
)
from wagtail.permissions import page_permission_policy


def get_breadcrumbs_items_for_page(
    page,
    user,
    url_name="wagtailadmin_explore",
    root_url_name="wagtailadmin_explore_root",
    include_self=True,
    querystring_value="",
):
    # find the closest common ancestor of the pages that this user has direct explore permission
    # (i.e. add/edit/publish/lock) over; this will be the root of the breadcrumb
    cca = page_permission_policy.explorable_root_instance(user)
    if not cca:
        return []

    pages = (
        page.get_ancestors(inclusive=include_self)
        .descendant_of(cca, inclusive=True)
        .specific(defer=True)
    )

    items = []
    for page in pages:
        if page.is_root() and root_url_name:
            url = reverse(root_url_name)
        else:
            url = reverse(url_name, args=(page.id,))
        items.append({"url": url + querystring_value, "label": get_latest_str(page)})

    return items


class GenericPageBreadcrumbsMixin:
    """
    A mixin that allows a view for pages that extends a generic view to combine
    the page explorer breadcrumbs with the generic view's breadcrumbs.

    This is done by generating the explorer breadcrumbs items for the page as a
    normalised breadcrumbs items list, and then concatenating that with the last
    item of the generic view's generated breadcrumbs items.
    """

    breadcrumbs_items_to_take = 1

    @cached_property
    def breadcrumbs_items(self):
        return get_breadcrumbs_items_for_page(self.object, self.request.user)

    def get_breadcrumbs_items(self):
        # The generic view tends to generate breadcrumbs with items such as
        # IndexView > EditView > CurrentView,
        # but we don't want that because we want the preceding items to be links
        # to the explore view of the page's ancestors for consistency with how
        # page breadcrumbs have always worked. So we only take the last N items,
        # which in most cases is the final item that links to the current view.
        # However, this can be customised in the case of generic views that are
        # nested inside another generic view.
        return (
            self.breadcrumbs_items
            + super().get_breadcrumbs_items()[-self.breadcrumbs_items_to_take :]
        )
