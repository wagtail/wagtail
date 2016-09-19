from __future__ import absolute_import, unicode_literals

import json

from django.http import HttpResponse
from django.template.loader import render_to_string


def render_modal_workflow(request, html_template, js_template, template_vars=None):
    """"
    Render a response consisting of an HTML chunk and a JS onload chunk
    in the format required by the modal-workflow framework.
    """
    response_keyvars = {}

    if html_template:
        html = render_to_string(html_template, template_vars or {}, request=request)
        response_keyvars.update({'html': html})

    if js_template:
        js = render_to_string(js_template, template_vars or {}, request=request)
        response_keyvars.update({'onload': js.replace('\n','')})

    return HttpResponse(json.dumps(response_keyvars) , content_type="text/javascript")
