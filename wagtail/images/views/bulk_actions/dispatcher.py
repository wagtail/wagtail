from django.http.response import Http404

from wagtail.core import hooks


def index(request, action):
    bulk_actions = hooks.get_hooks('register_image_bulk_action')
    for action_func in bulk_actions:
        _action = action_func(request)
        if _action.action_type != action:
            continue
        return _action.dispatch(request)

    return Http404()
