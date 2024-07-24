from django.contrib.contenttypes.models import ContentType
from django.http import Http404, JsonResponse
from taggit.models import Tag, TagBase


def autocomplete(request, app_name=None, model_name=None):
    if app_name and model_name:
        try:
            content_type = ContentType.objects.get_by_natural_key(app_name, model_name)
        except ContentType.DoesNotExist:
            raise Http404

        tag_model = content_type.model_class()
        if not issubclass(tag_model, TagBase):
            raise Http404

    else:
        tag_model = Tag

    term = request.GET.get("term", None)
    if term:
        tags = tag_model.objects.filter(name__istartswith=term).order_by("name")
    else:
        tags = tag_model.objects.none()

    return JsonResponse([tag.name for tag in tags], safe=False)
