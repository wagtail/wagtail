from django.contrib import messages
from django.core.exceptions import NON_FIELD_ERRORS
from django.template.loader import render_to_string
from django.utils.html import format_html, format_html_join


def render(message, buttons, detail=''):
    return render_to_string('wagtailadmin/shared/messages.html', {
        'message': message,
        'buttons': buttons,
        'detail': detail,
    })


def debug(request, message, buttons=None, extra_tags=''):
    return messages.debug(request, render(message, buttons), extra_tags=extra_tags)


def info(request, message, buttons=None, extra_tags=''):
    return messages.info(request, render(message, buttons), extra_tags=extra_tags)


def success(request, message, buttons=None, extra_tags=''):
    return messages.success(request, render(message, buttons), extra_tags=extra_tags)


def warning(request, message, buttons=None, extra_tags=''):
    return messages.warning(request, render(message, buttons), extra_tags=extra_tags)


def error(request, message, buttons=None, extra_tags=''):
    return messages.error(request, render(message, buttons), extra_tags=extra_tags)


def validation_error(request, message, form, buttons=None):
    if not form.non_field_errors():
        # just output the generic "there were validation errors" message, and leave
        # the per-field highlighting to do the rest
        detail = ''
    else:
        # display the full list of field and non-field validation errors
        all_errors = []
        for field_name, errors in form.errors.items():
            if field_name == NON_FIELD_ERRORS:
                prefix = ''
            else:
                try:
                    field_label = form[field_name].label
                except KeyError:
                    field_label = field_name
                prefix = "%s: " % field_label

            for error in errors:
                all_errors.append(prefix + error)

        errors_html = format_html_join('\n', '<li>{}</li>', ((e,) for e in all_errors))
        detail = format_html("""<ul class="errorlist">{}</ul>""", errors_html)

    return messages.error(request, render(message, buttons, detail=detail))


def button(url, text, new_window=False):
    if url is None:
        raise ValueError("Button URLs must not be None")
    return url, text, new_window
