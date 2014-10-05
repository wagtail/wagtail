import re
from django.db.models import Model, get_model
from six import string_types


def camelcase_to_underscore(str):
    # http://djangosnippets.org/snippets/585/
    return re.sub('(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', '_\\1', str).lower().strip('_')


def resolve_model_string(model_string, default_app=None):
    """
    Resolve an 'app_label.model_name' string into an actual model class.
    If a model class is passed in, just return that.
    """
    if isinstance(model_string, string_types):
        try:
            app_label, model_name = model_string.split(".")
        except ValueError:
            if default_app is not None:
                # If we can't split, assume a model in current app
                app_label = default_app
                model_name = model_string
            else:
                raise ValueError("Can not resolve {0!r} into a model. Model names "
                                 "should be in the form app_label.model_name".format(
                                     model_string), model_string)

        model = get_model(app_label, model_name)
        if not model:
            raise LookupError("Can not resolve {0!r} into a model".format(model_string), model_string)
        return model

    elif isinstance(model_string, type) and issubclass(model_string, Model):
        return model_string

    else:
        raise LookupError("Can not resolve {0!r} into a model".format(model_string), model_string)
