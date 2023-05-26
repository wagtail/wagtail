from django.contrib.admin.utils import quote, unquote
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic.base import ContextMixin, TemplateResponseMixin
from django.views.generic.list import BaseListView

from wagtail.admin import messages
from wagtail.admin.filters import WagtailFilterSet
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.ui.tables import Table
from wagtail.admin.utils import get_valid_next_url_from_request
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


class BaseListingView(WagtailAdminTemplateMixin, BaseListView):
    model = None
    index_url_name = None
    template_name = "wagtailadmin/generic/index.html"
    page_kwarg = "p"
    is_searchable = None
    search_kwarg = "q"
    search_fields = None
    default_ordering = None
    list_filter = None
    filters = None
    filterset_class = None
    search_backend_name = "default"
    use_autocomplete = False
    table_class = Table
    context_object_name = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.filterset_class = self.get_filterset_class()
        self.setup_search()

    def setup_search(self):
        self.is_searchable = self.get_is_searchable()
        self.search_url = self.get_search_url()
        self.search_form = self.get_search_form()
        self.is_searching = False
        self.search_query = None

        if self.search_form and self.search_form.is_valid():
            self.search_query = self.search_form.cleaned_data[self.search_kwarg]
            self.is_searching = True

    def get_index_url(self):
        if self.index_url_name:
            return reverse(self.index_url_name)

    def get_search_url(self):
        if not self.is_searchable:
            return None
        return self.index_url_name

    def get_is_searchable(self):
        if self.model is None:
            return False
        if self.is_searchable is None:
            return class_is_indexed(self.model) or self.search_fields
        return self.is_searchable

    def get_search_form(self):
        if self.model is None:
            return None

        if self.is_searchable and self.search_kwarg in self.request.GET:
            return SearchForm(
                self.request.GET,
                placeholder=_("Search %(model_name)s")
                % {"model_name": self.model._meta.verbose_name_plural},
            )

        return SearchForm(
            placeholder=_("Search %(model_name)s")
            % {"model_name": self.model._meta.verbose_name_plural}
        )

    def get_queryset(self):
        queryset = super().get_queryset()

        self.filters, queryset = self.filter_queryset(queryset)

        ordering = self.get_ordering()
        if ordering:
            if not isinstance(ordering, (list, tuple)):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)

        # Preserve the model-level ordering if specified, but fall back on
        # PK if not (to ensure pagination is consistent)
        if not queryset.ordered:
            queryset = queryset.order_by("pk")

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

    def get_filterset_class(self):
        if self.filterset_class:
            return self.filterset_class

        if not self.list_filter or not self.model:
            return None

        class Meta:
            model = self.model
            fields = self.list_filter

        return type(
            f"{self.model.__name__}FilterSet",
            (WagtailFilterSet,),
            {"Meta": Meta},
        )

    def filter_queryset(self, queryset):
        # construct filter instance (self.filters) if not created already
        if self.filterset_class and self.filters is None:
            self.filters = self.filterset_class(
                self.request.GET, queryset=queryset, request=self.request
            )
            queryset = self.filters.qs
        elif self.filters:
            # if filter object was created on a previous filter_queryset call, re-use it
            queryset = self.filters.filter_queryset(queryset)

        return self.filters, queryset

    def search_queryset(self, queryset):
        if not self.search_query:
            return queryset

        if class_is_indexed(queryset.model) and self.search_backend_name:
            search_backend = get_search_backend(self.search_backend_name)
            if self.use_autocomplete:
                return search_backend.autocomplete(
                    self.search_query, queryset, fields=self.search_fields
                )
            return search_backend.search(
                self.search_query, queryset, fields=self.search_fields
            )

        filters = {
            field + "__icontains": self.search_query
            for field in self.search_fields or []
        }
        return queryset.filter(**filters)

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

    def get_table(self, object_list, **kwargs):
        return self.table_class(
            self.columns,
            object_list,
            ordering=self.get_ordering(),
            **kwargs,
        )

    def get_context_data(self, *args, object_list=None, **kwargs):
        queryset = object_list if object_list is not None else self.object_list
        queryset = self.search_queryset(queryset)

        context = super().get_context_data(*args, object_list=queryset, **kwargs)

        index_url = self.get_index_url()
        table = self.get_table(context["object_list"], base_url=index_url)
        context["media"] = table.media

        if self.filters:
            context["filters"] = self.filters
            context["is_filtering"] = any(
                self.request.GET.get(f) for f in self.filters.filters
            )
            context["media"] += self.filters.form.media

        context["table"] = table
        context["index_url"] = index_url
        context["is_paginated"] = bool(self.paginate_by)
        context["is_searchable"] = self.is_searchable
        context["search_url"] = self.get_search_url()
        context["search_form"] = self.search_form
        context["is_searching"] = self.is_searching
        context["query_string"] = self.search_query
        context["model_opts"] = self.model and self.model._meta
        return context
