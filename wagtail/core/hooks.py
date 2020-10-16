from contextlib import ContextDecorator
from operator import itemgetter

from wagtail.utils.apps import get_app_submodules


_hooks = {}


def register(hook_name, fn=None, order=0):
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
            register(hook_name, fn, order=order)
            return fn
        return decorator

    if hook_name not in _hooks:
        _hooks[hook_name] = []
    _hooks[hook_name].append((fn, order))


class TemporaryHook(ContextDecorator):
    def __init__(self, hook_name, fn, order):
        self.hook_name = hook_name
        self.fn = fn
        self.order = order

    def __enter__(self):
        if self.hook_name not in _hooks:
            _hooks[self.hook_name] = []
        _hooks[self.hook_name].append((self.fn, self.order))

    def __exit__(self, exc_type, exc_value, traceback):
        _hooks[self.hook_name].remove((self.fn, self.order))


def register_temporarily(hook_name, fn, order=0):
    """
    Register hook for ``hook_name`` temporarily. This is useful for testing hooks.

    Can be used as a decorator::

        def my_hook(...):
            pass

        class TestMyHook(Testcase):
            @hooks.register_temporarily('hook_name', my_hook)
            def test_my_hook(self):
                pass

    or as a context manager::

        def my_hook(...):
            pass

        with hooks.register_temporarily('hook_name', my_hook):
            # Hook is registered here

        # Hook is unregistered here
    """
    return TemporaryHook(hook_name, fn, order)


_searched_for_hooks = False


def search_for_hooks():
    global _searched_for_hooks
    if not _searched_for_hooks:
        list(get_app_submodules('wagtail_hooks'))
        _searched_for_hooks = True


def get_hooks(hook_name):
    """ Return the hooks function sorted by their order. """
    search_for_hooks()
    hooks = _hooks.get(hook_name, [])
    hooks = sorted(hooks, key=itemgetter(1))
    return [hook[0] for hook in hooks]
