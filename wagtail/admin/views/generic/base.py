from collections import namedtuple

from django.contrib.admin.utils import quote, unquote
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.formats import date_format
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic.base import ContextMixin, TemplateResponseMixin
from django.views.generic.list import BaseListView
from django_filters.filters import (
    ChoiceFilter,
    DateFromToRangeFilter,
    ModelChoiceFilter,
    ModelMultipleChoiceFilter,
)

from wagtail.admin import messages
from wagtail.admin.ui.tables import Column, Table
from wagtail.admin.utils import get_valid_next_url_from_request
from wagtail.admin.widgets.button import ButtonWithDropdown


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
    header_buttons = []
    header_more_buttons = []

    def get_page_title(self):
        return self.page_title

    def get_page_subtitle(self):
        return self.page_subtitle

    def get_header_title(self):
        title = self.get_page_title()
        subtitle = self.get_page_subtitle()
        if subtitle:
            title = f"{title}: {subtitle}"
        return title

    def get_header_icon(self):
        return self.header_icon

    def get_breadcrumbs_items(self):
        return self.breadcrumbs_items

    def get_header_buttons(self):
        buttons = sorted(self.header_buttons)

        more_buttons = self.get_header_more_buttons()
        if more_buttons:
            buttons.append(
                ButtonWithDropdown(
                    buttons=more_buttons,
                    icon_name="dots-horizontal",
                    attrs={"aria-label": _("Actions")},
                    classname="w-h-slim-header",
                )
            )
        return buttons

    def get_header_more_buttons(self):
        return sorted(self.header_more_buttons)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # These are only used for legacy header.html
        # and view templates that don't use "wagtailadmin/generic/base.html"
        context["page_title"] = self.get_page_title()
        context["page_subtitle"] = self.get_page_subtitle()
        context["header_icon"] = self.get_header_icon()

        # Once all appropriate views use "wagtailadmin/generic/base.html" and
        # the slim_header.html, _show_breadcrumbs can be removed
        context["header_title"] = self.get_header_title()
        context["breadcrumbs_items"] = None
        if self._show_breadcrumbs:
            context["breadcrumbs_items"] = self.get_breadcrumbs_items()
            context["header_buttons"] = self.get_header_buttons()
            context["header_more_buttons"] = self.get_header_more_buttons()
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


# Represents a django-filters filter that is currently in force on a listing queryset
ActiveFilter = namedtuple(
    "ActiveFilter", ["auto_id", "field_label", "value", "removed_filter_url"]
)


class BaseListingView(WagtailAdminTemplateMixin, BaseListView):
    template_name = "wagtailadmin/generic/listing.html"
    results_template_name = "wagtailadmin/generic/listing_results.html"
    results_only = False  # If true, just render the results as an HTML fragment
    table_class = Table
    table_classname = None
    columns = [Column("__str__", label=_("Title"))]
    index_url_name = None
    index_results_url_name = None
    page_kwarg = "p"
    default_ordering = None
    filterset_class = None

    def get_template_names(self):
        if self.results_only:
            if isinstance(self.results_template_name, (list, tuple)):
                return self.results_template_name
            return [self.results_template_name]
        else:
            return super().get_template_names()

    @cached_property
    def filters(self):
        if self.filterset_class:
            return self.filterset_class(self.request.GET, request=self.request)

    @cached_property
    def is_filtering(self):
        # we are filtering if the filter form has changed from its default state
        return (
            self.filters and self.filters.is_valid() and self.filters.form.has_changed()
        )

    def filter_queryset(self, queryset):
        if self.filters and self.filters.is_valid():
            queryset = self.filters.filter_queryset(queryset)
        return queryset

    def get_url_without_filter_param(self, param):
        """
        Return the index URL with the given filter parameter removed from the query string
        """
        base_url = self.index_results_url.split("?")[0]
        query_dict = self.request.GET.copy()
        query_dict.pop(self.page_kwarg, None)  # reset pagination to first page
        if isinstance(param, (list, tuple)):
            for p in param:
                query_dict.pop(p, None)
        else:
            query_dict.pop(param, None)
        query_dict["_w_filter_fragment"] = 1
        return base_url + "?" + query_dict.urlencode()

    def get_url_without_filter_param_value(self, param, value):
        """
        Return the index URL where the filter parameter with the given value has been removed
        from the query string, preserving all other values for that parameter
        """
        base_url = self.index_results_url.split("?")[0]
        query_dict = self.request.GET.copy()
        query_dict.pop(self.page_kwarg, None)  # reset pagination to first page
        query_dict.setlist(
            param, [v for v in query_dict.getlist(param) if v != str(value)]
        )
        query_dict["_w_filter_fragment"] = 1
        return base_url + "?" + query_dict.urlencode()

    @cached_property
    def active_filters(self):
        filters = []

        if not self.filters:
            return filters

        for field_name in self.filters.form.changed_data:
            filter_def = self.filters.filters[field_name]
            bound_field = self.filters.form[field_name]
            try:
                value = self.filters.form.cleaned_data[field_name]
            except KeyError:
                continue  # invalid filter value

            if isinstance(filter_def, ModelMultipleChoiceFilter):
                field = filter_def.field
                for item in value:
                    filters.append(
                        ActiveFilter(
                            bound_field.auto_id,
                            filter_def.label,
                            field.label_from_instance(item),
                            self.get_url_without_filter_param_value(
                                field_name, item.pk
                            ),
                        )
                    )
            elif isinstance(filter_def, ModelChoiceFilter):
                field = filter_def.field
                filters.append(
                    ActiveFilter(
                        bound_field.auto_id,
                        filter_def.label,
                        field.label_from_instance(value),
                        self.get_url_without_filter_param(field_name),
                    )
                )
            elif isinstance(filter_def, DateFromToRangeFilter):
                start_date_display = date_format(value.start) if value.start else ""
                end_date_display = date_format(value.stop) if value.stop else ""
                filters.append(
                    ActiveFilter(
                        bound_field.auto_id,
                        filter_def.label,
                        "%s - %s" % (start_date_display, end_date_display),
                        self.get_url_without_filter_param(
                            [f"{field_name}_before", f"{field_name}_after"]
                        ),
                    )
                )
            elif isinstance(filter_def, ChoiceFilter):
                choices = {str(id): label for id, label in filter_def.field.choices}
                filters.append(
                    ActiveFilter(
                        bound_field.auto_id,
                        filter_def.label,
                        choices.get(str(value), str(value)),
                        self.get_url_without_filter_param(field_name),
                    )
                )
            else:
                filters.append(
                    ActiveFilter(
                        bound_field.auto_id,
                        filter_def.label,
                        str(value),
                        self.get_url_without_filter_param(field_name),
                    )
                )

        return filters

    def get_valid_orderings(self):
        orderings = []
        for col in self.columns:
            if col.sort_key:
                orderings.append(col.sort_key)
                orderings.append("-%s" % col.sort_key)
        return orderings

    @cached_property
    def is_explicitly_ordered(self):
        return "ordering" in self.request.GET

    def get_ordering(self):
        ordering = self.request.GET.get("ordering", self.default_ordering)
        if ordering not in self.get_valid_orderings():
            ordering = self.default_ordering
        return ordering

    @cached_property
    def ordering(self):
        return self.get_ordering()

    def order_queryset(self, queryset):
        if not self.ordering:
            return queryset

        ordering = self.ordering
        if not isinstance(ordering, (list, tuple)):
            ordering = (ordering,)
        return queryset.order_by(*ordering)

    def get_base_queryset(self):
        if self.queryset is not None:
            queryset = self.queryset
            if isinstance(queryset, models.QuerySet):
                queryset = queryset.all()
        elif self.model is not None:
            queryset = self.model._default_manager.all()
        else:
            raise ImproperlyConfigured(
                "%(cls)s is missing a QuerySet. Define "
                "%(cls)s.model, %(cls)s.queryset, or override "
                "%(cls)s.get_queryset()." % {"cls": self.__class__.__name__}
            )
        return queryset

    def get_queryset(self):
        # Instead of calling super().get_queryset(), we copy the initial logic from Django's
        # MultipleObjectMixin into get_base_queryset(). This allows us to perform additional steps
        # before the ordering step (such as annotations), and funnel the call to get_ordering()
        # through the cached property self.ordering so that we don't have to worry about calling
        # get_ordering() multiple times.
        # https://github.com/django/django/blob/stable/4.1.x/django/views/generic/list.py#L22-L47

        queryset = self.get_base_queryset()
        queryset = self.order_queryset(queryset)
        queryset = self.filter_queryset(queryset)
        return queryset

    def get_table_kwargs(self):
        return {
            "ordering": self.ordering,
            "classname": self.table_classname,
            "base_url": self.index_url,
        }

    def get_table(self, object_list):
        return self.table_class(
            self.columns,
            object_list,
            **self.get_table_kwargs(),
        )

    @cached_property
    def index_url(self):
        return self.get_index_url()

    def get_index_url(self):
        if self.index_url_name:
            return reverse(self.index_url_name)

    @cached_property
    def index_results_url(self):
        return self.get_index_results_url()

    def get_index_results_url(self):
        if self.index_results_url_name:
            return reverse(self.index_results_url_name)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        table = self.get_table(context["object_list"])

        context["index_url"] = self.index_url
        context["index_results_url"] = self.index_results_url
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

        if self.filters:
            context["filters"] = self.filters
            context["is_filtering"] = self.is_filtering
            context["media"] += self.filters.form.media

        # If we're rendering the results as an HTML fragment, the caller can pass a _w_filter_fragment=1
        # URL parameter to indicate that the filters should be rendered as a <template> block so that
        # we can replace the existing filters.
        context["render_filters_fragment"] = (
            self.request.GET.get("_w_filter_fragment")
            and self.filters
            and self.results_only
        )

        return context
