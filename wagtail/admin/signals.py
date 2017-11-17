from __future__ import absolute_import, unicode_literals

from django.dispatch import Signal

init_new_page = Signal(providing_args=['page', 'parent'])
