import datetime
import decimal

from django.template import Variable, VariableDoesNotExist
from django.utils import formats, timezone, six
from django.utils.encoding import smart_text
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

action_form_var = Variable('action_form')


def needs_checkboxes(context):
    try:
        return action_form_var.resolve(context) is not None
    except VariableDoesNotExist:
        return False


def display_for_value(value, boolean=False):  # pragma: no cover
    """ Added for compatibility with django 1.4, copied from django trunk.
    """
    from django.contrib.admin.templatetags.admin_list import _boolean_icon
    from django.contrib.admin.views.main import EMPTY_CHANGELIST_VALUE

    if boolean:
        return _boolean_icon(value)
    elif value is None:
        return EMPTY_CHANGELIST_VALUE
    elif isinstance(value, datetime.datetime):
        return formats.localize(timezone.template_localtime(value))
    elif isinstance(value, (datetime.date, datetime.time)):
        return formats.localize(value)
    elif isinstance(value, six.integer_types + (decimal.Decimal, float)):
        return formats.number_format(value)
    else:
        return smart_text(value)


def format_html(format_string, *args, **kwargs):  # pragma: no cover
    """
    Added for compatibility with django 1.4, copied from django trunk.

    Similar to str.format, but passes all arguments through conditional_escape,
    and calls 'mark_safe' on the result. This function should be used instead
    of str.format or % interpolation to build up small HTML fragments.
    """
    args_safe = map(conditional_escape, args)
    kwargs_safe = dict([(k, conditional_escape(v)) for (k, v) in
                        six.iteritems(kwargs)])
    return mark_safe(format_string.format(*args_safe, **kwargs_safe))
