from django.apps import apps

from wagtail.core import hooks


def get_bulk_actions_from_model(app_label, model_name):
    bulk_actions_list = []
    bulk_actions = hooks.get_hooks('register_bulk_action')
    model = apps.get_model(app_label, model_name)

    for action_class in bulk_actions:
        if model in action_class.models:
            bulk_actions_list.append(action_class)

    return bulk_actions_list


def get_bulk_action_class(app_label, model_name, action_type):
    model = apps.get_model(app_label, model_name)
    for bulk_action_class in hooks.get_hooks('register_bulk_action'):
        if bulk_action_class.action_type == action_type and model in bulk_action_class.models:
            return bulk_action_class
