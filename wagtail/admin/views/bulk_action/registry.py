from wagtail import hooks
from wagtail.admin.views.bulk_action import BulkAction


class BulkActionRegistry:
    def __init__(self):
        self.actions = {}  # {app_name: {model_name: {action_name: action_class]}}
        self.has_scanned_for_bulk_actions = False

    def _scan_for_bulk_actions(self):
        if not self.has_scanned_for_bulk_actions:
            for action_class in hooks.get_hooks("register_bulk_action"):
                if not issubclass(action_class, BulkAction):
                    raise Exception(
                        "{} is not a subclass of {}".format(
                            action_class.__name__, BulkAction.__name__
                        )
                    )
                for model in action_class.models:
                    self.actions.setdefault(model._meta.app_label, {})
                    self.actions[model._meta.app_label].setdefault(
                        model._meta.model_name, {}
                    )
                    self.actions[model._meta.app_label][model._meta.model_name][
                        action_class.action_type
                    ] = action_class
            self.has_scanned_for_bulk_actions = True

    def get_bulk_actions_for_model(self, app_label, model_name):
        self._scan_for_bulk_actions()
        return self.actions.get(app_label, {}).get(model_name, {}).values()

    def get_bulk_action_class(self, app_label, model_name, action_type):
        self._scan_for_bulk_actions()
        return (
            self.actions.get(app_label, {}).get(model_name, {}).get(action_type, None)
        )


bulk_action_registry = BulkActionRegistry()
