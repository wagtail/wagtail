from django.conf import settings
from django.utils.importlib import import_module

_hooks = {}

# TODO: support 'register' as a decorator:
#    @hooks.register('construct_main_menu')
#    def construct_main_menu(menu_items):
#        ...

def register(hook_name, fn):
    if hook_name not in _hooks:
        _hooks[hook_name] = []
    _hooks[hook_name].append(fn)

_searched_for_hooks = False
def search_for_hooks():
    global _searched_for_hooks
    if not _searched_for_hooks:
        for app_module in settings.INSTALLED_APPS:
            try:
                import_module('%s.wagtail_hooks' % app_module)
            except ImportError:
                continue

        _searched_for_hooks = True


def get_hooks(hook_name):
    search_for_hooks()
    return _hooks.get(hook_name, [])
