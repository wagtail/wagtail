from wagtail.core.compat import AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME
import hashlib
from django.utils.http import urlencode

delete_user_perm = "{0}.delete_{1}".format(AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower())


def user_can_delete_user(current_user, user_to_delete):
    if not current_user.has_perm(delete_user_perm):
        return False

    if current_user == user_to_delete:
        # users may not delete themselves
        return False

    if user_to_delete.is_superuser and not current_user.is_superuser:
        # ordinary users may not delete superusers
        return False

    return True


def get_gravatar_url(email, default=None, size=50):
    params = {'s': str(size)}
    if default is not None:
        params['default'] = default
    gravatar_url = "https://www.gravatar.com/avatar/" + hashlib.md5(email.lower().encode('utf-8')).hexdigest() + "?"
    gravatar_url += urlencode(params)
    return gravatar_url
