from __future__ import absolute_import, unicode_literals

from django.http import HttpResponse


def sendfile(request, filename, **kwargs):
    """
    Dummy sendfile backend implementation.
    """
    return HttpResponse('Dummy backend response')
