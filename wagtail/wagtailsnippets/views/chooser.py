import json
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.six import text_type

from wagtail.wagtailadmin.modal_workflow import render_modal_workflow

from wagtail.wagtailsnippets.views.snippets import get_content_type_from_url_params, get_snippet_type_name


def choose(request, content_type_app_name, content_type_model_name):
    content_type = get_content_type_from_url_params(content_type_app_name, content_type_model_name)
    model = content_type.model_class()
    snippet_type_name = get_snippet_type_name(content_type)[0]

    items = model.objects.all()

    p = request.GET.get("p", 1)
    paginator = Paginator(items, 25)

    try:
        paginated_items = paginator.page(p)
    except PageNotAnInteger:
        paginated_items = paginator.page(1)
    except EmptyPage:
        paginated_items = paginator.page(paginator.num_pages)

    return render_modal_workflow(
        request,
        'wagtailsnippets/chooser/choose.html', 'wagtailsnippets/chooser/choose.js',
        {
            'content_type': content_type,
            'snippet_type_name': snippet_type_name,
            'items': paginated_items,
        }
    )


def chosen(request, content_type_app_name, content_type_model_name, id):
    content_type = get_content_type_from_url_params(content_type_app_name, content_type_model_name)
    model = content_type.model_class()
    item = get_object_or_404(model, id=id)

    snippet_json = json.dumps({
        'id': item.id,
        'string': text_type(item),
        'edit_link': reverse('wagtailsnippets_edit', args=(content_type_app_name, content_type_model_name, item.id,))
    })

    return render_modal_workflow(
        request,
        None, 'wagtailsnippets/chooser/chosen.js',
        {
            'snippet_json': snippet_json,
        }
    )
