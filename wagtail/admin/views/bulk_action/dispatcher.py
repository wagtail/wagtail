from wagtail.admin.views.bulk_action.utils import get_bulk_action_class
from django.apps import apps
from django.http.response import Http404

def index(request, app_label, model_name, action):
    model = apps.get_model(app_label, model_name)
    action_class = get_bulk_action_class(app_label, model_name, action)
    if action_class is not None:
        return action_class(request, model).dispatch(request)
    return Http404()
