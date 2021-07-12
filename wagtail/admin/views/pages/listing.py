from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch
from django.db.models.expressions import Exists, OuterRef
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse

from wagtail.admin.auth import user_has_any_page_permission, user_passes_test
from wagtail.admin.navigation import get_explorable_root_page
from wagtail.core import hooks
from wagtail.core.models import Page, PageRevision, UserPagePermissionsProxy, WorkflowState
from wagtail.core.models.sites import Site


def prefetch_workflow_states(queryset):
    """
    Performance optimisation for listing pages.
    Prefetches the active workflow states on each page in this queryset.
    """
    workflow_states = WorkflowState.objects.active().select_related(
        "current_task_state__task"
    )

    return queryset.prefetch_related(
        Prefetch(
            "workflow_states",
            queryset=workflow_states,
            to_attr="_current_workflow_states",
        )
    )


def annotate_approved_schedule(queryset):
    """
    Performance optimisation for listing pages.
    Annotates each page with the existence of an approved go live time.
    """
    return queryset.annotate(
        _approved_schedule=Exists(
            PageRevision.objects.exclude(approved_go_live_at__isnull=True).filter(
                page__pk=OuterRef("pk")
            )
        )
    )


def annotate_site_root_state(queryset):
    """
    Performance optimisation for listing pages.
    Annotates each object with whether it is a root page of any site.
    """
    return queryset.annotate(
        _is_site_root=Exists(
            Site.objects.filter(
                root_page__translation_key=OuterRef("translation_key")
            )
        )
    )


@user_passes_test(user_has_any_page_permission)
def index(request, parent_page_id=None):
    if parent_page_id:
        parent_page = get_object_or_404(Page, id=parent_page_id)
    else:
        parent_page = Page.get_first_root_node()

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

    # Get page ordering
    ordering = request.GET.get('ordering', '-latest_revision_created_at')
    if ordering not in [
        'title',
        '-title',
        'content_type',
        '-content_type',
        'live', '-live',
        'latest_revision_created_at',
        '-latest_revision_created_at',
        'ord'
    ]:
        ordering = '-latest_revision_created_at'

    if ordering == 'ord':
        # preserve the native ordering from get_children()
        pass
    elif ordering == 'latest_revision_created_at':
        # order by oldest revision first.
        # Special case NULL entries - these should go at the top of the list.
        # Do this by annotating with Count('latest_revision_created_at'),
        # which returns 0 for these
        pages = pages.annotate(
            null_position=Count('latest_revision_created_at')
        ).order_by('null_position', 'latest_revision_created_at')
    elif ordering == '-latest_revision_created_at':
        # order by oldest revision first.
        # Special case NULL entries - these should go at the end of the list.
        pages = pages.annotate(
            null_position=Count('latest_revision_created_at')
        ).order_by('-null_position', '-latest_revision_created_at')
    else:
        pages = pages.order_by(ordering)

    # Don't paginate if sorting by page order - all pages must be shown to
    # allow drag-and-drop reordering
    do_paginate = ordering != 'ord'

    # We want specific page instances, but do not need streamfield values here
    pages = pages.defer_streamfields().specific()

    # allow hooks defer_streamfieldsyset
    for hook in hooks.get_hooks('construct_explorer_page_queryset'):
        pages = hook(parent_page, pages, request)

    # Annotate queryset with various states to be used later for performance optimisations
    pages = annotate_site_root_state(
        annotate_approved_schedule(
            prefetch_workflow_states(pages)
        )
    )

    # Pagination
    if do_paginate:
        paginator = Paginator(pages, per_page=50)
        pages = paginator.get_page(request.GET.get('p'))

    context = {
        'parent_page': parent_page.specific,
        'ordering': ordering,
        'pagination_query_params': "ordering=%s" % ordering,
        'pages': pages,
        'do_paginate': do_paginate,
        'locale': None,
        'translations': [],
    }

    if getattr(settings, 'WAGTAIL_I18N_ENABLED', False) and not parent_page.is_root():
        context.update({
            'locale': parent_page.locale,
            'translations': [
                {
                    'locale': translation.locale,
                    'url': reverse('wagtailadmin_explore', args=[translation.id]),
                }
                for translation in parent_page.get_translations().only('id', 'locale').select_related('locale')
            ],
        })

    return TemplateResponse(request, 'wagtailadmin/pages/index.html', context)
