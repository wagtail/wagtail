from django.shortcuts import render

from wagtail.wagtailadmin.userbar import EditPageItem, AddPageItem, ApproveModerationEditPageItem, RejectModerationEditPageItem
from wagtail.wagtailadmin import hooks
from wagtail.wagtailcore.models import Page, PageRevision

def index(request):
    # Render the edit bird
    return render(request, 'wagtailadmin/styleguide/base.html', {})
