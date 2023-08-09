import warnings

from django.conf import settings

from wagtail.permission_policies.pages import PagePermissionPolicy
from wagtail.utils.deprecation import RemovedInWagtail60Warning


def get_pages_with_direct_explore_permission(user):
    warnings.warn(
        "get_pages_with_direct_explore_permission() is deprecated. "
        "Use wagtail.permission_policies.pages.PagePermissionPolicy."
        "instances_with_direct_explore_permission() instead.",
        category=RemovedInWagtail60Warning,
        stacklevel=2,
    )
    return PagePermissionPolicy().instances_with_direct_explore_permission(user)


def get_explorable_root_page(user):
    warnings.warn(
        "get_explorable_root_page() is deprecated. "
        "Use wagtail.permission_policies.pages.PagePermissionPolicy."
        "explorable_root_instance() instead.",
        category=RemovedInWagtail60Warning,
        stacklevel=2,
    )
    return PagePermissionPolicy().explorable_root_instance(user)


def get_site_for_user(user):
    root_page = PagePermissionPolicy().explorable_root_instance(user)
    if root_page:
        root_site = root_page.get_site()
    else:
        root_site = None
    real_site_name = None
    if root_site:
        real_site_name = (
            root_site.site_name if root_site.site_name else root_site.hostname
        )
    return {
        "root_page": root_page,
        "root_site": root_site,
        "site_name": real_site_name if real_site_name else settings.WAGTAIL_SITE_NAME,
    }
