from wagtail.core.models import Collection, Page


def get_pages_with_direct_explore_permission(user):
    # Get all pages that the user has direct add/edit/publish/lock permission on
    if user.is_superuser:
        # superuser has implicit permission on the root node
        return Page.objects.filter(depth=1)
    else:
        return Page.objects.filter(
            group_permissions__group__in=user.groups.all(),
            group_permissions__permission_type__in=['add', 'edit', 'publish', 'lock']
        )


def get_collections_with_direct_explore_permission(user):
    # Get all collections that the user has permissions for
    if user.is_superuser:
        # superuser has implicit permission on the root node
        return Collection.objects.filter(depth=1)
    else:
        return Collection.objects.filter(
            group_manage_permissions__group__in=user.groups.all(),
            group_manage_permissions__permission_type__in=['add', 'edit']
        ).distinct()


def get_explorable_root_page(user):
    # Get the highest common explorable ancestor for the given user. If the user
    # has no permissions over any pages, this method will return None.
    pages = get_pages_with_direct_explore_permission(user)
    if pages:
        return pages.first_common_ancestor(
            include_self=True,
            strict=True)
    else:
        return None


def get_explorable_root_collection(user):
    # Get the highest common explorable ancestor for the given user. If the user
    # has no permissions over any collections, this method will return None.
    collections = get_collections_with_direct_explore_permission(user)
    if collections:
        return collections.first_common_ancestor(
            include_self=True,
            strict=True
        )
    else:
        return None
