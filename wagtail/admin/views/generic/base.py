from django.contrib.admin.utils import quote, unquote
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic.base import ContextMixin, TemplateResponseMixin

from wagtail.admin import messages
from wagtail.admin.utils import get_valid_next_url_from_request


class WagtailAdminTemplateMixin(TemplateResponseMixin, ContextMixin):
    """
    Mixin for views that render a template response using the standard Wagtail admin
    page furniture.
    Provides accessors for page title, subtitle and header icon.
    """

    page_title = ""
    page_subtitle = ""
    header_icon = ""
    template_name = "wagtailadmin/generic/base.html"

    def get_page_title(self):
        return self.page_title

    def get_page_subtitle(self):
        return self.page_subtitle

    def get_header_icon(self):
        return self.header_icon

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.get_page_title()
        context["page_subtitle"] = self.get_page_subtitle()
        context["header_icon"] = self.get_header_icon()
        return context


class BaseObjectMixin:
    """Mixin for views that make use of a model instance."""

    model = None
    pk_url_kwarg = "pk"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.pk = self.get_pk()
        self.object = self.get_object()
        self.model_opts = self.object._meta

    def get_pk(self):
        pk = self.kwargs[self.pk_url_kwarg]
        if isinstance(pk, str):
            return unquote(pk)
        return pk

    def get_object(self):
        if not self.model:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.base.BaseObjectMixin must provide a "
                "model attribute or a get_object method"
            )
        return get_object_or_404(self.model, pk=self.pk)


class BaseOperationView(BaseObjectMixin, View):
    """Base view to perform an operation on a model instance using a POST request."""

    success_message = None
    success_message_extra_tags = ""
    success_url_name = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.next_url = get_valid_next_url_from_request(request)

    def perform_operation(self):
        raise NotImplementedError

    def get_success_message(self):
        return self.success_message

    def add_success_message(self):
        success_message = self.get_success_message()
        if success_message:
            messages.success(
                self.request,
                success_message,
                extra_tags=self.success_message_extra_tags,
            )

    def get_success_url(self):
        if not self.success_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.base.BaseOperationView must provide a "
                "success_url_name attribute or a get_success_url method"
            )
        if self.next_url:
            return self.next_url
        return reverse(self.success_url_name, args=[quote(self.object.pk)])

    def post(self, request, *args, **kwargs):
        self.perform_operation()
        self.add_success_message()
        return redirect(self.get_success_url())
