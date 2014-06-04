from django.core.urlresolvers import reverse

from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.models import PageViewRestriction
from wagtail.wagtailcore.forms import PasswordPageViewRestrictionForm

def check_view_restrictions(page, request):
    restrictions = PageViewRestriction.objects.filter(page__in=page.get_ancestors(inclusive=True))

    for restriction in restrictions:
        form = PasswordPageViewRestrictionForm(instance=restriction,
            initial={'return_url': request.get_full_path()})
        action_url = reverse('wagtailcore_authenticate_with_password', args=[restriction.id, page.id])
        return page.serve_password_required_response(request, form, action_url)

hooks.register('before_serve_page', check_view_restrictions)
