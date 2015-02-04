import json

from taggit.models import Tag

from django.http import HttpResponse


def autocomplete(request):
    term = request.GET.get('term', None)
    if term:
        tags = Tag.objects.filter(name__istartswith=term).order_by('name')
    else:
        tags = Tag.objects.none()

    response = json.dumps([tag.name for tag in tags])

    return HttpResponse(response, content_type='text/javascript')
