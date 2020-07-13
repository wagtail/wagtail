from django.apps import apps
from django.db.models import Q
from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def lookup(request):
    target_model = request.GET.get('type')
    search_query = request.GET.get('query', '')

    try:
        model = apps.get_model(target_model)
    except Exception:
        return HttpResponseBadRequest("Invalid model")

    limit = int(request.GET.get('limit', 10))

    q = Q()
    search_fields = []
    for search_field in request.GET.get('lookup_fields', 'title').split(','):
        search_field = search_field.strip()
        if hasattr(model, search_field):
            q |= Q(**{search_field + '__icontains': search_query})
            search_fields.append(search_field)

    if not search_fields:
        return HttpResponseBadRequest("Invalid lookup field(s)")
    queryset = model.objects.filter(q).order_by(*search_fields)

    results = []
    for result in queryset[:limit]:
        results.append(dict(pk=result.pk, label=str(result)))

    return JsonResponse(dict(items=results))
