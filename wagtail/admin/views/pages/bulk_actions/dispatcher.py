from django.http.response import Http404

from wagtail.core import hooks


def index(request, parent_page_id, action, rest=''):
    bulk_actions = hooks.get_hooks('register_page_bulk_action')
    for action_func in bulk_actions:
        _action = action_func(request, parent_page_id)
        if _action.action_type != action:
            continue
        return _action.dispatch(request, parent_page_id)
        
    return Http404()
