from django.apps import apps

from wagtail.admin.views.bulk_action.base_bulk_action import BulkAction
from wagtail.core import hooks


def get_bulk_actions_for_model(app_label, model_name):
    bulk_actions_list = []
    bulk_actions = hooks.get_hooks('register_bulk_action')
    model = apps.get_model(app_label, model_name)

    for action_class in bulk_actions:
        if not issubclass(action_class, BulkAction):
            raise Exception("{} is not a subclass of {}".format(action_class.__name__, BulkAction.__name__))
        if model in action_class.models:
            bulk_actions_list.append(action_class)

    return bulk_actions_list


def get_bulk_action_class(app_label, model_name, action_type):
    model = apps.get_model(app_label, model_name)
    for bulk_action_class in hooks.get_hooks('register_bulk_action'):
        if not issubclass(bulk_action_class, BulkAction):
            raise Exception("{} is not a subclass of {}".format(bulk_action_class.__name__, BulkAction.__name__))
        if bulk_action_class.action_type == action_type and model in bulk_action_class.models:
            return bulk_action_class
