from __future__ import absolute_import, unicode_literals

from django.contrib.auth.views import redirect_to_login as auth_redirect_to_login
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from wagtail.wagtailadmin import messages


def redirect_to_login(request):
    return auth_redirect_to_login(
        request.get_full_path(), login_url=reverse('wagtailadmin_login'))


def require_admin_access(view_func):
    def decorated_view(request, *args, **kwargs):
        user = request.user

        if user.is_anonymous():
            return redirect_to_login(request)

        if user.has_perms(['wagtailadmin.access_admin']):
            return view_func(request, *args, **kwargs)

        messages.error(request, _('You do not have permission to access the admin'))
        return redirect_to_login(request)
    return decorated_view
