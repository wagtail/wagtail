from __future__ import absolute_import, unicode_literals

from django.dispatch import Signal

page_published = Signal(providing_args=['instance', 'revision'])
page_unpublished = Signal(providing_args=['instance'])
