import re
from django.db.models import Model, get_model
from django.utils.translation import ugettext_lazy as _
from six import string_types


def camelcase_to_underscore(str):
    # http://djangosnippets.org/snippets/585/
    return re.sub('(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', '_\\1', str).lower().strip('_')


def resolve_model_string(model_string, default_app):
    """
    Resolve an 'app_label.model_name' string in to an actual model class.
    If a model class is passed in, just return that.
    """
    if isinstance(model_string, string_types):
        try:
            app_label, model_name = model_string.split(".")
        except ValueError:
            # If we can't split, assume a model in current app
            app_label = default_app
            model_name = model_string

        model = get_model(app_label, model_name)
        if not model:
            raise NameError(_("name '{0}' is not defined.").format(model_string))
        return model

    elif issubclass(model_string, Model):
        return model

    else:
        raise ValueError(_("Can not resolve '{0!r}' in to a model").format(model_string))
