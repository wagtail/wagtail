from wagtail.core import hooks


class LogFormatter:
    """
    Defines how to format log messages / comments for a particular action type. Messages that depend on
    log entry data should override format_message / format_comment; static messages can just be set as the
    'message' / 'comment' attribute.

    To be registered with log_registry.register_action.
    """
    label = ''
    message = ''
    comment = ''

    def format_message(self, log_entry):
        if callable(self.message):
            # For Wagtail <2.15, a callable passed as 'message' will be called with the log entry's 'data' property.
            # (In 2.14 there was also a takes_log_entry attribute on the callable to specify passing the whole
            # log entry object rather than just data, but this was undocumented)
            return self.message(log_entry.data)
        else:
            return self.message

    def format_comment(self, log_entry):
        return self.comment


class LogActionRegistry:
    """
    A central store for log actions.
    The expected format for registered log actions: Namespaced action, Action label, Action message (or callable)
    """
    def __init__(self, hook_name):
        self.hook_name = hook_name

        # Has the hook been run for this registry?
        self.has_scanned_for_actions = False

        # Holds the formatter objects, keyed by action
        self.formatters = {}

        # Holds a list of action, action label tuples for use in filters
        self.choices = []

    def scan_for_actions(self):
        if not self.has_scanned_for_actions:
            for fn in hooks.get_hooks(self.hook_name):
                fn(self)

            self.has_scanned_for_actions = True

    def register_action(self, action, *args):

        def register_formatter_class(formatter_cls):
            formatter = formatter_cls()
            self.formatters[action] = formatter
            self.choices.append((action, formatter.label))

        if args:
            # register_action has been invoked as register_action(action, label, message); create a LogFormatter
            # subclass and register that
            label, message = args
            formatter_cls = type('_LogFormatter', (LogFormatter, ), {'label': label, 'message': message})
            register_formatter_class(formatter_cls)
        else:
            # register_action has been invoked as a @register_action(action) decorator; return the function that
            # will register the class
            return register_formatter_class

    def get_choices(self):
        self.scan_for_actions()
        return self.choices

    def get_formatter(self, log_entry):
        self.scan_for_actions()
        return self.formatters.get(log_entry.action)

    def action_exists(self, action):
        self.scan_for_actions()
        return action in self.formatters

    def get_action_label(self, action):
        return self.formatters[action].label


# For historical reasons, pages use the 'register_log_actions' hook
page_log_action_registry = LogActionRegistry('register_log_actions')
