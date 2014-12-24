class Module(object):
    def __init__(self, name, **kwargs):
        self.name = name

        for key, value in kwargs.items():
            setattr(self, key, value)

    def has_module_permission(self, request):
        return True

    def get_urls(self):
        return ()

    @property
    def urls(self):
        return self.get_urls(), self.name, self.name


class ModuleViewMixin(object):
    module = None

    def get_context_data(self, *args, **kwargs):
        context = super(ModuleViewMixin, self).get_context_data(*args, **kwargs)

        context['module'] = self.module
        context['has_module_permission'] = self.module.has_module_permission(self.request)
        return context
