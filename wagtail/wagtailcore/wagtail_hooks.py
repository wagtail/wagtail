from django.http import HttpResponse

from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.models import PageViewRestriction

def check_view_restrictions(page, request):
    restrictions = PageViewRestriction.objects.filter(page__in=page.get_ancestors(inclusive=True))
    for restriction in restrictions:
        return HttpResponse("<h1>Blocked due to view restriction</h1>")
hooks.register('before_serve_page', check_view_restrictions)
