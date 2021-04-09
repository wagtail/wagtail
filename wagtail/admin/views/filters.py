from django.db.models import Q
from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404, redirect

from wagtail.admin.auth import user_has_any_page_permission, user_passes_test
from wagtail.admin.navigation import get_explorable_root_page
from wagtail.core.models import Page, UserPagePermissionsProxy
from wagtail.search.utils import parse_query_string


def apply_filters(filter_query):
    filters_to_be_applied = Q()

    # filter_query should be of the format 'filter1:value1 filter2:value2'
    filter_query = filter_query.strip()
    if not filter_query:
        return filters_to_be_applied
    filter_args = parse_query_string(filter_query)[0]
    filters = {
        'status': {
            'live': Q(live=True),
            'draft': Q(live=False),
        }
    }

    for _arg, filter_value in filter_args.items():
        if _arg not in filters:
            continue
        if filter_value not in filters[_arg]:
            continue
        filters_to_be_applied = filters_to_be_applied & filters[_arg][filter_value]

    return filters_to_be_applied


@user_passes_test(user_has_any_page_permission)
def filter_count(request, parent_page_id=None):
    if parent_page_id:
        parent_page = get_object_or_404(Page, id=parent_page_id)
        # This will always succeed because of the @user_passes_test above.
        root_page = get_explorable_root_page(request.user)

        # If this page isn't a descendant of the user's explorable root page,
        # then redirect to that explorable root page instead.
        if not (
            parent_page.pk == root_page.pk
            or parent_page.is_descendant_of(root_page)
        ):
            return redirect('wagtailadmin_explore', root_page.pk)

        parent_page = parent_page.specific

        user_perms = UserPagePermissionsProxy(request.user)
        pages = (
            parent_page.get_children().prefetch_related(
                "content_type", "sites_rooted_here"
            )
            & user_perms.explorable_pages()
        )
    else:
        pages = Page.objects.all().prefetch_related('content_type').specific()
    filter_query = request.GET.dict().get('filters', '')
    filters_to_be_applied = apply_filters(filter_query)
    return JsonResponse(dict(count=pages.filter(filters_to_be_applied).count()))
