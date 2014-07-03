import json

from six import text_type

from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import permission_required

from wagtail.wagtailadmin.modal_workflow import render_modal_workflow

from wagtail.wagtailsnippets.views.snippets import get_content_type_from_url_params, get_snippet_type_name


@permission_required('wagtailadmin.access_admin')
def choose(request, content_type_app_name, content_type_model_name):
    content_type = get_content_type_from_url_params(content_type_app_name, content_type_model_name)
    model = content_type.model_class()
    snippet_type_name = get_snippet_type_name(content_type)[0]

    items = model.objects.all()

    return render_modal_workflow(
        request,
        'wagtailsnippets/chooser/choose.html', 'wagtailsnippets/chooser/choose.js',
        {
            'content_type': content_type,
            'snippet_type_name': snippet_type_name,
            'items': items,
        }
    )


@permission_required('wagtailadmin.access_admin')
def chosen(request, content_type_app_name, content_type_model_name, id):
    content_type = get_content_type_from_url_params(content_type_app_name, content_type_model_name)
    model = content_type.model_class()
    item = get_object_or_404(model, id=id)

    snippet_json = json.dumps({
        'id': item.id,
        'string': text_type(item),
    })

    return render_modal_workflow(
        request,
        None, 'wagtailsnippets/chooser/chosen.js',
        {
            'snippet_json': snippet_json,
        }
    )
