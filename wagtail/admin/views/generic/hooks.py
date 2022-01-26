from wagtail.core import hooks


class HookResponseMixin:
    """
    A mixin for class-based views to support hooks like `before_edit_page`, which are triggered
    during execution of some operation and can return a response to halt that operation.
    """

    def run_hook(self, hook_name, *args, **kwargs):
        """
        Run the named hook, passing args and kwargs to each function registered under that hook name.
        If any return an HttpResponse, stop processing and return that response
        """
        for fn in hooks.get_hooks(hook_name):
            result = fn(*args, **kwargs)
            if hasattr(result, 'status_code'):
                return result
