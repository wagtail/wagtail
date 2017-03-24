from __future__ import absolute_import, unicode_literals

import hashlib
from django.utils.six.moves.urllib.parse import urlencode
from wagtail.wagtailcore.compat import AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME


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


def get_gravatar_url(email, default, size=50):
    gravatar_url = "https://www.gravatar.com/avatar/" + hashlib.md5(email.lower().encode('utf-8')).hexdigest() + "?"
    gravatar_url += urlencode({'d': default, 's': str(size)})
    return gravatar_url
