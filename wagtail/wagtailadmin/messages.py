from django.contrib import messages
from django.template.loader import render_to_string


def render(message, buttons):
    return render_to_string('wagtailadmin/shared/messages.html', {
        'message': message,
        'buttons': buttons,
    })


def debug(request, message, buttons=None):
    return messages.debug(request, render(message, buttons))


def info(request, message, buttons=None):
    return messages.info(request, render(message, buttons))


def success(request, message, buttons=None):
    return messages.success(request, render(message, buttons))


def warning(request, message, buttons=None):
    return messages.warning(request, render(message, buttons))


def error(request, message, buttons=None):
    return messages.error(request, render(message, buttons))


def button(url, text):
    return url, text
