from wagtail.utils.apps import get_app_submodules


_hooks = {}


def register(hook_name, fn=None):
    """
    Register hook for ``hook_name``. Can be used as a decorator::

        @register('hook_name')
        def my_hook(...):
            pass

    or as a function call::

        def my_hook(...):
            pass
        register('hook_name', my_hook)
    """

    # Pretend to be a decorator if fn is not supplied
    if fn is None:
        def decorator(fn):
            register(hook_name, fn)
            return fn
        return decorator

    if hook_name not in _hooks:
        _hooks[hook_name] = []
    _hooks[hook_name].append(fn)

_searched_for_hooks = False


def search_for_hooks():
    global _searched_for_hooks
    if not _searched_for_hooks:
        list(get_app_submodules('wagtail_hooks'))
        _searched_for_hooks = True


def get_hooks(hook_name):
    search_for_hooks()
    return _hooks.get(hook_name, [])
