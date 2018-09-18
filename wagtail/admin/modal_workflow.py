import json
import warnings

from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string

from wagtail.utils.deprecation import RemovedInWagtail24Warning


def render_modal_workflow(request, html_template, js_template, template_vars=None, json_data=None):
    """"
    Render a response consisting of an HTML chunk and a JS onload chunk
    in the format required by the modal-workflow framework.
    """
    if js_template:
        warnings.warn(
            "Passing a JS template to render_modal_workflow is deprecated. "
            "Use an 'onload' dict on the ModalWorkflow constructor instead",
            category=RemovedInWagtail24Warning
        )
        # construct response as Javascript, including a JS function as the 'onload' field
        response_keyvars = []

        if html_template:
            html = render_to_string(html_template, template_vars or {}, request=request)
            response_keyvars.append('"html": %s' % json.dumps(html))

        js = render_to_string(js_template, template_vars or {}, request=request)
        response_keyvars.append('"onload": %s' % js)

        if json_data:
            for key, val in json_data.items():
                response_keyvars.append("%s: %s" % (json.dumps(key), json.dumps(val)))

        response_text = "{%s}" % ','.join(response_keyvars)

        return HttpResponse(response_text, content_type="text/javascript")

    else:
        # construct response as JSON
        response = {}

        if html_template:
            response['html'] = render_to_string(html_template, template_vars or {}, request=request)

        if json_data:
            response.update(json_data)

        return JsonResponse(response)
