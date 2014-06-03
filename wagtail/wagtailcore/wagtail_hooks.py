from django.http import HttpResponse

from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.models import PageViewRestriction

def check_view_restrictions(page, request):
    ancestors_and_self = list(page.get_ancestors().values_list('id', flat=True)) + [page]
    restrictions = PageViewRestriction.objects.filter(page__in=ancestors_and_self)
    for restriction in restrictions:
        return HttpResponse("<h1>Blocked due to view restriction</h1>")
hooks.register('before_serve_page', check_view_restrictions)
