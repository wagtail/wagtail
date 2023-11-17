from django.contrib.admin.utils import quote, unquote
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic.base import ContextMixin, TemplateResponseMixin
from django.views.generic.list import BaseListView

from wagtail.admin import messages
from wagtail.admin.ui.tables import Column, Table
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
    # Breadcrumbs are opt-in until we have a design that can be consistently applied
    _show_breadcrumbs = False
    breadcrumbs_items = [{"url": reverse_lazy("wagtailadmin_home"), "label": _("Home")}]
    template_name = "wagtailadmin/generic/base.html"

    def get_page_title(self):
        return self.page_title

    def get_page_subtitle(self):
        return self.page_subtitle

    def get_header_icon(self):
        return self.header_icon

    def get_breadcrumbs_items(self):
        return self.breadcrumbs_items

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.get_page_title()
        context["page_subtitle"] = self.get_page_subtitle()
        context["header_icon"] = self.get_header_icon()
        context["breadcrumbs_items"] = None
        if self._show_breadcrumbs:
            context["breadcrumbs_items"] = self.get_breadcrumbs_items()
        return context

    def get_template_names(self):
        # Instead of always wrapping self.template_name in a list like
        # TemplateResponseMixin does, only do so if it's not already a list/tuple.
        # This allows us to use a list of template names in self.template_name.
        if isinstance(self.template_name, (list, tuple)):
            return self.template_name
        return super().get_template_names()


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
        return unquote(str(self.kwargs[self.pk_url_kwarg]))

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


class BaseListingView(WagtailAdminTemplateMixin, BaseListView):
    template_name = "wagtailadmin/generic/listing.html"
    results_template_name = "wagtailadmin/generic/listing_results.html"
    results_only = False  # If true, just render the results as an HTML fragment
    table_class = Table
    table_classname = None
    columns = [Column("__str__", label=_("Title"))]
    index_url_name = None
    page_kwarg = "p"
    default_ordering = None

    def get_template_names(self):
        if self.results_only:
            if isinstance(self.results_template_name, (list, tuple)):
                return self.results_template_name
            return [self.results_template_name]
        else:
            return super().get_template_names()

    def get_valid_orderings(self):
        orderings = []
        for col in self.columns:
            if col.sort_key:
                orderings.append(col.sort_key)
                orderings.append("-%s" % col.sort_key)
        return orderings

    def get_ordering(self):
        ordering = self.request.GET.get("ordering", self.default_ordering)
        if ordering not in self.get_valid_orderings():
            ordering = self.default_ordering
        return ordering

    def get_table_kwargs(self):
        return {
            "ordering": self.get_ordering(),
            "classname": self.table_classname,
            "base_url": self.index_url,
        }

    def get_table(self, object_list):
        return self.table_class(
            self.columns,
            object_list,
            **self.get_table_kwargs(),
        )

    def get_index_url(self):
        if self.index_url_name:
            return reverse(self.index_url_name)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        self.index_url = self.get_index_url()
        table = self.get_table(context["object_list"])

        context["index_url"] = self.index_url
        context["table"] = table
        context["media"] = table.media
        # On Django's BaseListView, a listing where pagination is applied, but the results
        # only run to a single page, is considered is_paginated=False. Override this to
        # always consider a listing to be paginated if pagination is applied. This ensures
        # that we output "Page 1 of 1" as is standard in Wagtail.
        context["is_paginated"] = context["page_obj"] is not None

        if context["is_paginated"]:
            context["items_count"] = context["paginator"].count
        else:
            context["items_count"] = len(context["object_list"])

        return context
