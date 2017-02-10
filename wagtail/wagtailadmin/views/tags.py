from __future__ import absolute_import, unicode_literals

from django.http import JsonResponse
from taggit.models import Tag


def autocomplete(request):
    term = request.GET.get('term', None)
    if term:
        tags = Tag.objects.filter(name__istartswith=term).order_by('name')
    else:
        tags = Tag.objects.none()

    return JsonResponse([tag.name for tag in tags], safe=False)
