from wagtail import hooks


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
            if hasattr(result, "status_code"):
                return result


class BeforeAfterHookMixin(HookResponseMixin):
    before_hook_name = None
    after_hook_name = None

    def run_before_hook(self):
        return self.run_hook(self.before_hook_name)

    def run_after_hook(self):
        return self.run_hook(self.after_hook_name)

    def dispatch(self, *args, **kwargs):
        hooks_result = self.run_before_hook()
        if hooks_result is not None:
            return hooks_result

        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)

        hooks_result = self.run_after_hook()
        if hooks_result is not None:
            return hooks_result

        return response
