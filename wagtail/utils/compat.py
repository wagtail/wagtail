from __future__ import absolute_import, unicode_literals

import django


def user_is_authenticated(user):
    if django.VERSION >= (1, 10):
        return user.is_authenticated
    else:
        return user.is_authenticated()


def user_is_anonymous(user):
    if django.VERSION >= (1, 10):
        return user.is_anonymous
    else:
        return user.is_anonymous()
