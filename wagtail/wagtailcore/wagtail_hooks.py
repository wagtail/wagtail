from django.core.urlresolvers import reverse

from wagtail.wagtailcore import hooks


@hooks.register('before_serve_page')
def check_view_restrictions(page, request, serve_args, serve_kwargs):
    """
    Check whether there are any view restrictions on this page which are
    not fulfilled by the given request object. If there are, return an
    HttpResponse that will notify the user of that restriction (and possibly
    include a password / login form that will allow them to proceed). If
    there are no such restrictions, return None
    """
    restrictions = page.get_view_restrictions()

    if restrictions:
        passed_restrictions = request.session.get('passed_page_view_restrictions', [])
        for restriction in restrictions:
            if restriction.id not in passed_restrictions:
                from wagtail.wagtailcore.forms import PasswordPageViewRestrictionForm
                form = PasswordPageViewRestrictionForm(instance=restriction,
                                                       initial={'return_url': request.get_full_path()})
                action_url = reverse('wagtailcore_authenticate_with_password', args=[restriction.id, page.id])
                return page.serve_password_required_response(request, form, action_url)
