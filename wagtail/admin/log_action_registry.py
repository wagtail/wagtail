from django.utils.translation import gettext_lazy as _

from wagtail.core import hooks


class LogActionRegistry:
    """
    A central store for log actions.
    The expected format for registered log actions: Namespaced action, Action label, Action message (or callable)
    """
    def __init__(self):
        # Has the register_log_actions hook been run for this registry?
        self.has_scanned_for_actions = False

        # Holds the actions.
        self.actions = {}

        # Holds a list of action, action label tuples for use in filters
        self.choices = []

        # Holds the action messsages, keyed by action
        self.messages = {}

    def scan_for_actions(self):
        if not self.has_scanned_for_actions:
            for fn in hooks.get_hooks('register_log_actions'):
                fn(self)

            self.has_scanned_for_actions = True

        return self.actions

    def get_actions(self):
        return self.scan_for_actions()

    def register_action(self, action, label, message):
        self.actions[action] = (label, message)
        self.messages[action] = message
        self.choices.append((action, label))

    def get_choices(self):
        self.scan_for_actions()
        return self.choices

    def get_messages(self):
        self.scan_for_actions()
        return self.messages

    def format_message(self, log_entry):
        message = self.get_messages().get(log_entry.action, _('Unkown {action}').format(action=log_entry.action))
        if callable(message):
            message = message(log_entry.data)

        return message

    def get_action_label(self, action):
        return self.get_actions()[action][0]


registry = LogActionRegistry()
