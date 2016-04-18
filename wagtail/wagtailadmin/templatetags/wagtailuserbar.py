from django import template
from django.template.loader import render_to_string

from wagtail.wagtailcore.models import Page, PageRevision, PAGE_TEMPLATE_VAR

# from django.contrib.auth.decorators import permission_required

from wagtail.wagtailadmin.userbar import AdminItem, ExplorePageItem, EditPageItem, AddPageItem, \
    ApproveModerationEditPageItem, RejectModerationEditPageItem
from wagtail.wagtailcore import hooks

register = template.Library()


def get_page_instance(context):
    """
    Given a template context, try and find a Page variable in the common
    places. Returns None if a page can not be found.
    """
    possible_names = [PAGE_TEMPLATE_VAR, 'self']
    for name in possible_names:
        if name in context:
            page = context[name]
            if isinstance(page, Page):
                return page


@register.simple_tag(takes_context=True)
def wagtailuserbar(context, position='bottom-right'):
    # Find request object
    try:
        request = context['request']
    except KeyError:
        return ''

    # Don't render if user doesn't have permission to access the admin area
    if not request.user.has_perm('wagtailadmin.access_admin'):
        return ''

    # Only render if the context contains a variable referencing a saved page
    page = get_page_instance(context)
    if page is None:
        return ''

    # Dont render anything if the page has not been saved - i.e. a preview
    if page.pk is None:
        return ''

    try:
        revision_id = request.revision_id
    except AttributeError:
        revision_id = None

    if revision_id is None:
        items = [
            AdminItem(),
            ExplorePageItem(Page.objects.get(id=page.id)),
            EditPageItem(Page.objects.get(id=page.id)),
            AddPageItem(Page.objects.get(id=page.id)),
        ]
    else:
        items = [
            AdminItem(),
            ExplorePageItem(PageRevision.objects.get(id=revision_id).page),
            EditPageItem(PageRevision.objects.get(id=revision_id).page),
            AddPageItem(PageRevision.objects.get(id=revision_id).page),
            ApproveModerationEditPageItem(PageRevision.objects.get(id=revision_id)),
            RejectModerationEditPageItem(PageRevision.objects.get(id=revision_id)),
        ]

    for fn in hooks.get_hooks('construct_wagtail_userbar'):
        fn(request, items)

    # Render the items
    rendered_items = [item.render(request) for item in items]

    # Remove any unrendered items
    rendered_items = [item for item in rendered_items if item]

    # Render the userbar items
    return render_to_string('wagtailadmin/userbar/base.html', {
        'request': request,
        'items': rendered_items,
        'position': position,
        'page': page,
        'revision_id': revision_id
    })
