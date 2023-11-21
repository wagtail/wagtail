from django.conf import settings

from wagtail.permissions import page_permission_policy


def get_site_for_user(user):
    root_page = page_permission_policy.explorable_root_instance(user)
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
