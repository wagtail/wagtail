from django.conf import settings
from imp import find_module
try:
    from importlib import import_module
except ImportError:
    # for Python 2.6, fall back on django.utils.importlib (deprecated as of Django 1.7)
    from django.utils.importlib import import_module

_hooks = {}

# TODO: support 'register' as a decorator:
#    @hooks.register('construct_main_menu')
#    def construct_main_menu(menu_items):
#        ...


def recursive_step(pathname, module):
    """
    Given a pathname and a module name expected at that path, use find_module()
    to return the combined pathname of the input pathname and the module name,
    if it exists and is importable.
    """
    if pathname:
        f, pathname, description = find_module(module, [pathname])
    else:
        f, pathname, description = find_module(module)
    return pathname


def recursively_find_module(app_module, submodule):
    """
    Given a dotted python path and a submodule, check to see whether the
    submodule exists and is importable at that dotted python path.

    This has to happen recursively, as find_module ignores hierarchichal module
    names:
    https://docs.python.org/2.7/library/imp.html?highlight=imp#imp.find_module

    NB find_module raises ImportError if the designated module does not exist,
    but this is distinct from an ImportError raised when importing that module.
    """
    nested_modules = app_module.split('.')

    pathname = None  # initially
    for module in nested_modules:
        pathname = recursive_step(pathname, module)

    try:
        pathname = recursive_step(pathname, submodule)
    except ImportError:
        return False
    else:
        return True


def register(hook_name, fn):
    if hook_name not in _hooks:
        _hooks[hook_name] = []
    _hooks[hook_name].append(fn)

_searched_for_hooks = False


def search_for_hooks():
    global _searched_for_hooks
    if not _searched_for_hooks:
        for app_module in settings.INSTALLED_APPS:
            if recursively_find_module(app_module, 'wagtail_hooks'):
                import_module('%s.wagtail_hooks' % app_module)

        _searched_for_hooks = True


def get_hooks(hook_name):
    search_for_hooks()
    return _hooks.get(hook_name, [])
