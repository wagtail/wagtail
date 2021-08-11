from django.apps import apps
from django.http.response import Http404

from wagtail.core import hooks

def index(request, app_label, model_name, action):
    model = apps.get_model(app_label, model_name)
    for bulk_action_class in hooks.get_hooks('register_bulk_action'):
        if bulk_action_class.action_type == action and model in bulk_action_class.models:
            return bulk_action_class(request, model).dispatch(request)
    return Http404()
