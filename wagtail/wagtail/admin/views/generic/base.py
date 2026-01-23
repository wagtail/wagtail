import warnings

from django.contrib.admin.utils import quote, unquote
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic.base import ContextMixin, TemplateResponseMixin
from django.views.generic.list import BaseListView

from wagtail.admin import messages
from wagtail.admin.active_filters import filter_adapter_class_registry
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.paginator import WagtailPaginator
from wagtail.admin.ui.tables import Column, Table
from wagtail.admin.utils import get_valid_next_url_from_request
from wagtail.admin.widgets.button import ButtonWithDropdown
from wagtail.search.backends import get_search_backend
from wagtail.search.index import class_is_indexed


class WagtailAdminTemplateMixin(TemplateResponseMixin, ContextMixin):
    """
    Mixin for views that render a template response using the standard Wagtail admin
    page furniture.
    Provides accessors for page title, subtitle and header icon.
    """

    page_title = ""
    page_subtitle = ""
    header_icon = ""

    breadcrumbs_items = [{"url": reverse_lazy("wagtailadmin_home"), "label": _("Home")}]
    """
    The base set of breadcrumbs items to be displayed on the page.
    The property can be overridden by subclasses and viewsets to provide
    custom base items, e.g. page tree breadcrumbs or add the "Snippets" item.

    Views should copy and append to this list in :meth:`get_breadcrumbs_items()`
    to define the path to the current view.
    """

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
        """
        Define the current path to the view by copying the base
        :attr:`breadcrumbs_items` and appending the list.

        If breadcrumbs are not required, return an empty list.
        """
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
        context["header_title"] = self.get_header_title()

        # Breadcrumbs are enabled by default.
        context["breadcrumbs_items"] = self.get_breadcrumbs_items()
        context["header_buttons"] = self.get_header_buttons()
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

    def get_base_object_queryset(self):
        return self.model._default_manager.all()

    def get_object(self):
        if not self.model:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.base.BaseObjectMixin must provide a "
                "model attribute or a get_object method"
            )
        return get_object_or_404(self.get_base_object_queryset(), pk=self.pk)


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
    index_results_url_name = None
    page_kwarg = "p"
    is_searchable = None  # Subclasses must explicitly set this to True to enable search
    search_kwarg = "q"
    search_fields = None
    search_backend_name = "default"
    default_ordering = None
    filterset_class = None
    verbose_name_plural = None
    paginator_class = WagtailPaginator

    def get_template_names(self):
        if self.results_only:
            if isinstance(self.results_template_name, (list, tuple)):
                return self.results_template_name
            return [self.results_template_name]
        else:
            return super().get_template_names()

    def get_breadcrumbs_items(self):
        return self.breadcrumbs_items + [
            {
                "url": "",
                "label": self.get_page_title(),
                "sublabel": self.get_page_subtitle(),
            },
        ]

    def get_search_form(self):
        if not self.is_searchable:
            return None

        if self.search_kwarg in self.request.GET:
            return SearchForm(self.request.GET)

        return SearchForm()

    @cached_property
    def search_form(self):
        return self.get_search_form()

    @cached_property
    def search_query(self):
        if self.search_form and self.search_form.is_valid():
            return self.search_form.cleaned_data[self.search_kwarg]
        return ""

    @cached_property
    def is_searching(self):
        return bool(self.search_query)

    def search_queryset(self, queryset):
        if not self.is_searching:
            return queryset

        # Use Wagtail Search if the model is indexed and a search backend is defined.
        # Django ORM can still be used on an indexed model by unsetting
        # search_backend_name and defining search_fields on the view.
        if class_is_indexed(queryset.model) and self.search_backend_name:
            search_backend = get_search_backend(self.search_backend_name)
            if queryset.model.get_autocomplete_search_fields():
                return search_backend.autocomplete(
                    self.search_query,
                    queryset,
                    fields=self.search_fields,
                    order_by_relevance=(not self.is_explicitly_ordered),
                )
            else:
                # fall back on non-autocompleting search
                warnings.warn(
                    f"{queryset.model} is defined as Indexable but does not specify "
                    "any AutocompleteFields. Searches within the admin will only "
                    "respond to complete words.",
                    category=RuntimeWarning,
                )
                return search_backend.search(
                    self.search_query,
                    queryset,
                    fields=self.search_fields,
                    order_by_relevance=(not self.is_explicitly_ordered),
                )

        query = Q()
        for field in self.search_fields or []:
            query |= Q(**{field + "__icontains": self.search_query})
        return queryset.filter(query)

    @cached_property
    def filters(self):
        if self.filterset_class:
            filterset = self.filterset_class(**self.get_filterset_kwargs())
            # Don't use the filterset if it has no fields
            if filterset.form.fields:
                return filterset

    @cached_property
    def is_filtering(self):
        # we are filtering if the filter form has changed from its default state
        return (
            self.filters and self.filters.is_valid() and self.filters.form.has_changed()
        )

    def get_filterset_kwargs(self):
        return {
            "data": self.request.GET,
            "request": self.request,
        }

    def filter_queryset(self, queryset):
        if self.filters and self.filters.is_valid():
            queryset = self.filters.filter_queryset(queryset)
        return queryset

    @cached_property
    def active_filters(self):
        filters = []

        if not self.filters:
            return filters

        base_url = self.index_results_url.split("?")[0]
        query_dict = self.request.GET.copy()
        query_dict.pop(self.page_kwarg, None)  # reset pagination to first page
        query_dict["_w_filter_fragment"] = 1

        for field_name in self.filters.form.changed_data:
            filter_def = self.filters.filters[field_name]
            bound_field = self.filters.form[field_name]
            try:
                value = self.filters.form.cleaned_data[field_name]
            except KeyError:
                continue  # invalid filter value

            if value == bound_field.initial:
                continue  # filter value is the same as the default

            filter_adapter_class = filter_adapter_class_registry.get(filter_def)
            filter_adapter = filter_adapter_class(
                filter_def, bound_field, value, base_url, query_dict
            )
            filters.extend(filter_adapter.get_active_filters())

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
        queryset = self.search_queryset(queryset)
        return queryset

    def paginate_queryset(self, queryset, page_size):
        paginator = self.get_paginator(
            queryset,
            page_size,
            orphans=self.get_paginate_orphans(),
            allow_empty_first_page=self.get_allow_empty(),
        )

        page_number = self.request.GET.get(self.page_kwarg)
        page = paginator.get_page(page_number)
        return (paginator, page, page.object_list, page.has_other_pages())

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

    @cached_property
    def no_results_message(self):
        if not self.verbose_name_plural:
            return _("There are no results.")

        if self.is_searching or self.is_filtering:
            return _("No %(model_name)s match your query.") % {
                "model_name": self.verbose_name_plural
            }

        return _("There are no %(model_name)s to display.") % {
            "model_name": self.verbose_name_plural
        }

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        table = self.get_table(context["object_list"])

        context["index_url"] = self.index_url
        context["index_results_url"] = self.index_results_url
        context["verbose_name_plural"] = self.verbose_name_plural
        context["no_results_message"] = self.no_results_message
        context["ordering"] = self.ordering
        context["table"] = table
        context["media"] = table.media
        # On Django's BaseListView, a listing where pagination is applied, but the results
        # only run to a single page, is considered is_paginated=False. Override this to
        # always consider a listing to be paginated if pagination is applied. This ensures
        # that we output "Page 1 of 1" as is standard in Wagtail.
        context["is_paginated"] = context["page_obj"] is not None

        if context["is_paginated"]:
            context["items_count"] = context["paginator"].count
            context["elided_page_range"] = context["paginator"].get_elided_page_range(
                self.request.GET.get(self.page_kwarg, 1)
            )
        else:
            context["items_count"] = len(context["object_list"])

        if self.filters:
            context["filters"] = self.filters
            context["is_filtering"] = self.is_filtering
            context["media"] += self.filters.form.media

        if self.search_form:
            context["search_form"] = self.search_form
            context["is_searching"] = self.is_searching
            context["query_string"] = self.search_query
            context["media"] += self.search_form.media

        # If we're rendering the results as an HTML fragment, the caller can pass a _w_filter_fragment=1
        # URL parameter to indicate that the filters should be rendered as a <template> block so that
        # we can replace the existing filters.
        context["render_filters_fragment"] = (
            self.request.GET.get("_w_filter_fragment")
            and self.filters
            and self.results_only
        )
        # Ensure that the header buttons get re-rendered for the results-only view,
        # in case they make use of the search/filter state
        context["render_buttons_fragment"] = (
            context.get("header_buttons") and self.results_only
        )

        return context
