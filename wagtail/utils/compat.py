from __future__ import absolute_import, unicode_literals

import django


# TODO: This compat function is now obsolete
def user_is_authenticated(user):
    return user.is_authenticated


# TODO: This compat function is now obsolete
def user_is_anonymous(user):
    return user.is_anonymous
