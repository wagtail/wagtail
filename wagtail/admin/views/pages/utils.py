from django.urls import reverse

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
        .specific()
    )

    items = []
    for page in pages:
        if page.is_root() and root_url_name:
            url = reverse(root_url_name)
        else:
            url = reverse(url_name, args=(page.id,))
        items.append({"url": url + querystring_value, "label": get_latest_str(page)})

    return items
