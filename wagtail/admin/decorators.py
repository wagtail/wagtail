import l18n
from django.contrib.auth.views import redirect_to_login as auth_redirect_to_login
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.utils.timezone import activate as activate_tz
from django.utils.translation import activate as activate_lang
from django.utils.translation import ugettext as _

from wagtail.admin import messages


def reject_request(request):
    if request.is_ajax():
        raise PermissionDenied

    return auth_redirect_to_login(
        request.get_full_path(), login_url=reverse('wagtailadmin_login'))


def require_admin_access(view_func):
    def decorated_view(request, *args, **kwargs):
        user = request.user

        if user.is_anonymous:
            return reject_request(request)

        if user.has_perms(['wagtailadmin.access_admin']):
            if hasattr(user, 'wagtail_userprofile'):
                language = user.wagtail_userprofile.get_preferred_language()
                l18n.set_language(language)
                activate_lang(language)
                time_zone = user.wagtail_userprofile.get_current_time_zone()
                activate_tz(time_zone)
            return view_func(request, *args, **kwargs)

        if not request.is_ajax():
            messages.error(request, _('You do not have permission to access the admin'))

        return reject_request(request)

    return decorated_view
