from django.apps import apps
from django.http import Http404

from wagtail.admin.views.bulk_action.registry import bulk_action_registry as registry


def index(request, app_label, model_name, action):
    model = apps.get_model(app_label, model_name)
    action_class = registry.get_bulk_action_class(app_label, model_name, action)
    if action_class is not None:
        return action_class(request, model).dispatch(request)
    raise Http404
