from django.views.generic.base import ContextMixin, TemplateResponseMixin


class WagtailAdminTemplateMixin(TemplateResponseMixin, ContextMixin):
    """
    Mixin for views that render a template response using the standard Wagtail admin
    page furniture.
    Provides accessors for page title, subtitle and header icon.
    """

    page_title = ''
    page_subtitle = ''
    header_icon = ''
    template_name = 'wagtailadmin/generic/base.html'

    def get_page_title(self):
        return self.page_title

    def get_page_subtitle(self):
        return self.page_subtitle

    def get_header_icon(self):
        return self.header_icon

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.get_page_title()
        context['page_subtitle'] = self.get_page_subtitle()
        context['header_icon'] = self.get_header_icon()
        return context
