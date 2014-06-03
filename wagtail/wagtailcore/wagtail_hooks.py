from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.models import PageViewRestriction

def check_view_restrictions(page, request):
    restrictions = PageViewRestriction.objects.filter(page__in=page.get_ancestors(inclusive=True))
    for restriction in restrictions:
        return page.serve_password_required_response(request, None)
hooks.register('before_serve_page', check_view_restrictions)
