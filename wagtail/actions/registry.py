from django.core.exceptions import ImproperlyConfigured

from wagtail import hooks
from wagtail.actions.base import BaseAction


class ActionRegistry:
    """
    A registry mapping model classes to the actions available for them.

    Registration is opt-in: a model only gets the actions that are explicitly
    registered for it, either directly via :meth:`register` or through the
    ``register_actions`` hook.

    Lookups walk the model's inheritance chain (MRO), so an action registered
    against a base class is inherited by its subclasses, and a subclass may add
    further actions on top.
    """

    def __init__(self):
        # {model_class: {action_name: action_class}}
        self.actions = {}
        self.has_scanned_for_actions = False

    def register(self, model, action_class):
        """
        Register ``action_class`` as available for ``model``.
        """
        if not (
            isinstance(action_class, type) and issubclass(action_class, BaseAction)
        ):
            raise TypeError(
                f"{action_class!r} is not a subclass of {BaseAction.__name__}"
            )
        if not action_class.action_name:
            raise ImproperlyConfigured(
                f"{action_class.__name__} must define an 'action_name' to be registered"
            )
        self.actions.setdefault(model, {})[action_class.action_name] = action_class
        return action_class

    def _scan_for_actions(self):
        if not self.has_scanned_for_actions:
            for fn in hooks.get_hooks("register_actions"):
                fn(self)
            self.has_scanned_for_actions = True

    def get_actions_for_model(self, model):
        """
        Return a dict of ``{action_name: action_class}`` for the given model,
        merging actions registered against every class in its MRO. More specific
        (subclass) registrations take precedence over those on base classes.
        """
        self._scan_for_actions()
        actions = {}
        # Walk the MRO from the most generic to the most specific class, so that
        # more specific registrations override less specific ones.
        for klass in reversed(model.mro()):
            actions.update(self.actions.get(klass, {}))
        return actions

    def get_action_class(self, model, action_name):
        """
        Return the action class registered under ``action_name`` for ``model``,
        or ``None`` if there is no such action.
        """
        return self.get_actions_for_model(model).get(action_name)


action_registry = ActionRegistry()
