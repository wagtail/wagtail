from bs4 import BeautifulSoup
from django.apps import apps
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
    search_field = request.GET.get('lookup_field', 'title')

    if not hasattr(model, search_field):
        return HttpResponseBadRequest('Invalid lookup field')
    filter_kwargs = {
        search_field + '__icontains': search_query,
    }
    queryset = model.objects.filter(**filter_kwargs).order_by(search_field)

    results = []
    for result in queryset[:limit]:
        label = BeautifulSoup(
            getattr(result, search_field, str(result)).strip(), 'html.parser'
        ).text
        results.append(dict(pk=result.pk, label=label))

    return JsonResponse(dict(items=results))
