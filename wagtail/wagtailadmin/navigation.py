from __future__ import absolute_import, unicode_literals

from django.db.models import Q

from wagtail.wagtailcore.models import Page


def get_navigation_menu_items(user):
    # Get all pages that the user has direct add/edit/publish/lock permission on
    if user.is_superuser:
        # superuser has implicit permission on the root node
        pages_with_direct_permission = Page.objects.filter(depth=1)
    else:
        pages_with_direct_permission = Page.objects.filter(
            group_permissions__group__in=user.groups.all(),
            group_permissions__permission_type__in=['add', 'edit', 'publish', 'lock']
        )

    if not(pages_with_direct_permission):
        return []

    # Find the closest common ancestor of the pages the user has permission for;
    # this (or its children) will be the root menu level for this user.
    cca_path = pages_with_direct_permission[0].path
    for page in pages_with_direct_permission[1:]:
        # repeatedly try shorter prefixes of page.path until we find one that cca_path starts with;
        # this becomes the new cca_path
        for path_len in range(len(page.path), 0, -Page.steplen):
            path_to_test = page.path[0:path_len]
            if cca_path.startswith(path_to_test):
                cca_path = path_to_test
                break

    # Determine the depth (within the overall page tree) at which this user's menu starts:
    # * if CCA is the root node, start at depth 2 (immediate children of root - because we
    #   never want to show root in the navigation);
    # * else if CCA is a node they have direct permission for, start at that depth
    #   (so that they can edit that root node)
    # * else start one level deeper (because the root node is only needed to provide navigation
    #   to deeper levels, and one level deeper is the first point where there's a choice to make)

    if len(cca_path) == Page.steplen:
        # CCA is the root node
        menu_root_depth = 2
    elif any(page.path == cca_path for page in pages_with_direct_permission):
        # user has direct permission on the CCA node
        menu_root_depth = int(len(cca_path) / Page.steplen)
    else:
        menu_root_depth = int(len(cca_path) / Page.steplen) + 1

    # Run the query to fetch all pages to be shown in the navigation. This consists of the following
    # set of pages, for each page in pages_with_direct_permission:
    #  * all ancestors (plus self) from menu_root_depth down
    #  * all descendants that have children
    #  * all descendants at the top level (depth=2), regardless of whether they have children.
    #    (this ensures that a freshly built site with no child pages won't result in an empty menu)

    # construct a filter clause for the ancestors of all pages with direct permission
    ancestor_paths = [
        page.path[0:path_len]
        for page in pages_with_direct_permission
        for path_len in range(menu_root_depth * Page.steplen, len(page.path) + Page.steplen, Page.steplen)
    ]

    criteria = Q(path__in=ancestor_paths)

    # add on the descendants for each page with direct permission
    for page in pages_with_direct_permission:
        criteria = criteria | (
            Q(path__startswith=page.path) & (
                Q(depth=2) | Q(numchild__gt=0)
            )
        )

    pages = Page.objects.filter(criteria).order_by('path')

    # Turn this into a tree structure:
    #     tree_node = (page, children)
    #     where 'children' is a list of tree_nodes.
    # Algorithm:
    # Maintain a list that tells us, for each depth level, the last page we saw at that depth level.
    # Since our page list is ordered by path, we know that whenever we see a page
    # at depth d, its parent must be the last page we saw at depth (d-1), and so we can
    # find it in that list.

    # create dummy entries for pages at a lower depth than menu_root_depth
    # as these won't be covered by the 'pages' queryset
    depth_list = [(None, []) for i in range(0, menu_root_depth)]

    for page in pages:
        # create a node for this page
        node = (page, [])
        # retrieve the parent from depth_list
        parent_page, parent_childlist = depth_list[page.depth - 1]
        # insert this new node in the parent's child list
        parent_childlist.append(node)

        # add the new node to depth_list
        try:
            depth_list[page.depth] = node
        except IndexError:
            # an exception here means that this node is one level deeper than any we've seen so far
            depth_list.append(node)

    return depth_list[menu_root_depth - 1][1]
