import warnings
from importlib import import_module


class RemovedInWagtail28Warning(DeprecationWarning):
    pass


removed_in_next_version_warning = RemovedInWagtail28Warning


class RemovedInWagtail29Warning(PendingDeprecationWarning):
    pass


class MovedDefinitionHandler:
    """
    A wrapper for module objects to enable definitions to be moved to a new module, with a
    deprecation path for the old location. Importing the name from the old location will
    raise a deprecation warning (but will still complete successfully).

    To use, place the following code in the old module:

    import sys
    from wagtail.utils.deprecation import MovedDefinitionHandler, RemovedInWagtailXWarning

    MOVED_DEFINITIONS = {
        'SomeClassOrVariableName': 'path.to.new.module',
    }

    sys.modules[__name__] = MovedDefinitionHandler(sys.modules[__name__], MOVED_DEFINITIONS, RemovedInWagtailXWarning)
    """
    def __init__(self, real_module, moved_definitions, warning_class):
        self.real_module = real_module
        self.moved_definitions = moved_definitions
        self.warning_class = warning_class

    def __getattr__(self, name):
        try:
            return getattr(self.real_module, name)
        except AttributeError as e:
            try:
                # is the missing name one of our moved definitions?
                new_module_name = self.moved_definitions[name]
            except KeyError:
                # raise the original AttributeError without including the inner try/catch
                # in the stack trace
                raise e from None

        warnings.warn(
            "%s has been moved from %s to %s" % (name, self.real_module.__name__, new_module_name),
            category=self.warning_class, stacklevel=2
        )

        # load the requested definition from the module named in moved_definitions
        new_module = import_module(new_module_name)
        definition = getattr(new_module, name)

        # stash that definition into the current module so that we don't have to
        # redo this import next time we access it
        setattr(self.real_module, name, definition)

        return definition
