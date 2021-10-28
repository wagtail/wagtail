from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.urls import reverse


def require_wagtail_login(next):
    login_url = getattr(settings, 'WAGTAIL_FRONTEND_LOGIN_URL', reverse('wagtailcore_login'))
    return redirect_to_login(next, login_url)
