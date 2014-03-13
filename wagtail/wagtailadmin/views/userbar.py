from django.conf import settings
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.decorators import permission_required
from django.utils.translation import ugettext as _ 

from wagtail.wagtailadmin.userbar import EditPageItem, ApproveModerationEditPageItem, RejectModerationEditPageItem
from wagtail.wagtailadmin import hooks
from wagtail.wagtailcore.models import Page

def render_edit_frame(request, context):
    # Render the frame to contain the userbar items
    return render_to_string('wagtailadmin/userbar/frame.html', {
        'page': context
    })

@permission_required('wagtailadmin.access_admin')
def userbar(request, page_id):
    items = [
        EditPageItem(Page.objects.get(id=page_id)),
        ApproveModerationEditPageItem(Page.objects.get(id=page_id)),
        RejectModerationEditPageItem(Page.objects.get(id=page_id)),
    ]

    for fn in hooks.get_hooks('construct_wagtail_edit_bird'):
        fn(request, items)


    for item in items:
        print item.render(request)

    # Render the items
    rendered_items = [item.render(request) for item in items]

    # Remove any unrendered items
    rendered_items = [item for item in rendered_items if item]

    # Quit if no items rendered
    if not rendered_items:
        return

    # Render the edit bird
    return render(request, 'wagtailadmin/userbar/edit_bird.html', {
        'items': [item.render(request) for item in items],
    })