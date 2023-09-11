import warnings

from django import VERSION as DJANGO_VERSION
from django.contrib.admin.utils import label_for_field, quote, unquote
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import (
    FieldDoesNotExist,
    ImproperlyConfigured,
    PermissionDenied,
)
from django.db import models, transaction
from django.db.models.functions import Cast
from django.forms import Form
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.text import capfirst
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.generic import TemplateView
from django.views.generic.detail import BaseDetailView
from django.views.generic.edit import (
    BaseCreateView,
    BaseUpdateView,
    DeletionMixin,
    FormMixin,
)
from django.views.generic.edit import BaseDeleteView as DjangoBaseDeleteView

from wagtail.actions.unpublish import UnpublishAction
from wagtail.admin import messages
from wagtail.admin.filters import WagtailFilterSet
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.panels import get_edit_handler
from wagtail.admin.ui.components import Component
from wagtail.admin.ui.fields import display_class_registry
from wagtail.admin.ui.tables import Column, TitleColumn, UpdatedAtColumn
from wagtail.admin.utils import get_valid_next_url_from_request
from wagtail.log_actions import log
from wagtail.log_actions import registry as log_registry
from wagtail.models import DraftStateMixin, ReferenceIndex
from wagtail.models.audit_log import ModelLogEntry
from wagtail.search.backends import get_search_backend
from wagtail.search.index import class_is_indexed

from .base import BaseListingView, WagtailAdminTemplateMixin
from .mixins import BeforeAfterHookMixin, HookResponseMixin, LocaleMixin, PanelMixin
from .permissions import PermissionCheckedMixin

if DJANGO_VERSION >= (4, 0):
    BaseDeleteView = DjangoBaseDeleteView
else:
    # As of Django 4.0 BaseDeleteView has switched to a new implementation based on FormMixin
    # where custom deletion logic now lives in form_valid:
    # https://docs.djangoproject.com/en/4.0/releases/4.0/#deleteview-changes
    # Here we define BaseDeleteView to match the Django 4.0 implementation to keep it consistent
    # across all versions.
    class BaseDeleteView(DeletionMixin, FormMixin, BaseDetailView):
        """
        Base view for deleting an object.
        Using this base class requires subclassing to provide a response mixin.
        """

        form_class = Form

        def post(self, request, *args, **kwargs):
            # Set self.object before the usual form processing flow.
            # Inlined because having DeletionMixin as the first base, for
            # get_success_url(), makes leveraging super() with ProcessFormView
            # overly complex.
            self.object = self.get_object()
            form = self.get_form()
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)

        def form_valid(self, form):
            success_url = self.get_success_url()
            self.object.delete()
            return HttpResponseRedirect(success_url)


class IndexView(LocaleMixin, PermissionCheckedMixin, BaseListingView):
    model = None
    template_name = "wagtailadmin/generic/index.html"
    index_results_url_name = None
    add_url_name = None
    add_item_label = gettext_lazy("Add")
    edit_url_name = None
    any_permission_required = ["add", "change", "delete"]
    search_fields = None
    search_backend_name = "default"
    is_searchable = None
    search_kwarg = "q"
    filters = None
    filterset_class = None
    columns = None  # If not explicitly specified, will be derived from list_display
    list_display = ["__str__", UpdatedAtColumn()]
    list_filter = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.columns = self.get_columns()
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

    def get_is_searchable(self):
        if self.model is None:
            return False
        if self.is_searchable is None:
            return class_is_indexed(self.model) or self.search_fields
        return self.is_searchable

    def get_search_url(self):
        if not self.is_searchable:
            return None
        return self.index_url_name

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

    def _annotate_queryset_updated_at(self, queryset):
        # Annotate the objects' updated_at, use _ prefix to avoid name collision
        # with an existing database field.
        # By default, use the latest log entry's timestamp, but subclasses may
        # override this to e.g. use the latest revision's timestamp instead.

        log_model = log_registry.get_log_model_for_model(queryset.model)

        # If the log model is not a subclass of ModelLogEntry, we don't know how
        # to query the logs for the object, so skip the annotation.
        if not log_model or not issubclass(log_model, ModelLogEntry):
            return queryset

        latest_log = (
            log_model.objects.filter(
                content_type=ContentType.objects.get_for_model(
                    queryset.model, for_concrete_model=False
                ),
                object_id=Cast(models.OuterRef("pk"), models.CharField()),
            )
            .order_by("-timestamp", "-pk")
            .values("timestamp")[:1]
        )
        return queryset.annotate(_updated_at=models.Subquery(latest_log))

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
        # Instead of calling super().get_queryset(), we copy the initial logic
        # from Django's MultipleObjectMixin into get_base_queryset(), because
        # we need to annotate the updated_at before using it for ordering.
        # https://github.com/django/django/blob/stable/4.1.x/django/views/generic/list.py#L22-L47

        queryset = self.get_base_queryset()

        self.filters, queryset = self.filter_queryset(queryset)

        if self.locale:
            queryset = queryset.filter(locale=self.locale)

        queryset = self._annotate_queryset_updated_at(queryset)

        ordering = self.get_ordering()
        if ordering:
            # Explicitly handle null values for the updated at column to ensure consistency
            # across database backends and match the behaviour in page explorer
            if ordering == "_updated_at":
                ordering = models.F("_updated_at").asc(nulls_first=True)
            elif ordering == "-_updated_at":
                ordering = models.F("_updated_at").desc(nulls_last=True)
            if not isinstance(ordering, (list, tuple)):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)

        # Preserve the model-level ordering if specified, but fall back on
        # updated_at and PK if not (to ensure pagination is consistent)
        if not queryset.ordered:
            queryset = queryset.order_by(
                models.F("_updated_at").desc(nulls_last=True), "-pk"
            )

        return queryset

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
            if queryset.model.get_autocomplete_search_fields():
                return search_backend.autocomplete(
                    self.search_query, queryset, fields=self.search_fields
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
                    self.search_query, queryset, fields=self.search_fields
                )

        filters = {
            field + "__icontains": self.search_query
            for field in self.search_fields or []
        }
        return queryset.filter(**filters)

    def _get_title_column(self, field_name, column_class=TitleColumn, **kwargs):
        if not self.model:
            return column_class(
                "name",
                label=gettext_lazy("Name"),
                accessor=str,
                get_url=self.get_edit_url,
            )
        return self._get_custom_column(
            field_name, column_class, get_url=self.get_edit_url, **kwargs
        )

    def _get_custom_column(self, field_name, column_class=Column, **kwargs):
        label, attr = label_for_field(field_name, self.model, return_attr=True)
        sort_key = getattr(attr, "admin_order_field", None)

        # attr is None if the field is an actual database field,
        # so it's possible to sort by it
        if attr is None:
            sort_key = field_name

        return column_class(
            field_name,
            label=capfirst(label),
            sort_key=sort_key,
            **kwargs,
        )

    def get_columns(self):
        # Use columns set at the class level, if available
        if self.columns is not None:
            return self.columns

        columns = []
        for i, field in enumerate(self.list_display):
            if isinstance(field, Column):
                column = field
            elif i == 0:
                column = self._get_title_column(field)
            else:
                column = self._get_custom_column(field)
            columns.append(column)

        return columns

    def get_index_results_url(self):
        if self.index_results_url_name:
            return reverse(self.index_results_url_name)

    def get_edit_url(self, instance):
        if self.edit_url_name:
            return reverse(self.edit_url_name, args=(quote(instance.pk),))

    def get_add_url(self):
        if self.add_url_name:
            return reverse(self.add_url_name)

    def get_context_data(self, *args, object_list=None, **kwargs):
        queryset = object_list if object_list is not None else self.object_list
        queryset = self.search_queryset(queryset)

        context = super().get_context_data(*args, object_list=queryset, **kwargs)

        context["can_add"] = (
            self.permission_policy is None
            or self.permission_policy.user_has_permission(self.request.user, "add")
        )
        if context["can_add"]:
            context["add_url"] = context["header_action_url"] = self.get_add_url()
            context["header_action_label"] = self.add_item_label

        if self.filters:
            context["filters"] = self.filters
            context["is_filtering"] = any(
                self.request.GET.get(f) for f in self.filters.filters
            )
            context["media"] += self.filters.form.media

        context["index_results_url"] = self.get_index_results_url()
        context["is_searchable"] = self.is_searchable
        context["search_url"] = self.get_search_url()
        context["search_form"] = self.search_form
        context["is_searching"] = self.is_searching
        context["query_string"] = self.search_query
        context["model_opts"] = self.model and self.model._meta
        return context


class CreateView(
    LocaleMixin,
    PanelMixin,
    PermissionCheckedMixin,
    BeforeAfterHookMixin,
    WagtailAdminTemplateMixin,
    BaseCreateView,
):
    model = None
    form_class = None
    index_url_name = None
    add_url_name = None
    edit_url_name = None
    template_name = "wagtailadmin/generic/create.html"
    permission_required = "add"
    success_message = None
    error_message = None
    submit_button_label = gettext_lazy("Create")
    actions = ["create"]

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.action = self.get_action(request)

    def get_action(self, request):
        for action in self.get_available_actions():
            if request.POST.get(f"action-{action}"):
                return action
        return "create"

    def get_available_actions(self):
        return self.actions

    def get_add_url(self):
        if not self.add_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.CreateView must provide an "
                "add_url_name attribute or a get_add_url method"
            )
        return reverse(self.add_url_name)

    def get_edit_url(self):
        if not self.edit_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.CreateView must provide an "
                "edit_url_name attribute or a get_edit_url method"
            )
        return reverse(self.edit_url_name, args=(quote(self.object.pk),))

    def get_success_url(self):
        if not self.index_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.CreateView must provide an "
                "index_url_name attribute or a get_success_url method"
            )
        return reverse(self.index_url_name)

    def get_success_message(self, instance):
        if self.success_message is None:
            return None
        return self.success_message % {"object": instance}

    def get_success_buttons(self):
        return [messages.button(self.get_edit_url(), _("Edit"))]

    def get_error_message(self):
        if self.error_message is None:
            return None
        return self.error_message

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action_url"] = self.get_add_url()
        context["submit_button_label"] = self.submit_button_label
        return context

    def save_instance(self):
        """
        Called after the form is successfully validated - saves the object to the db
        and returns the new object. Override this to implement custom save logic.
        """
        instance = self.form.save()
        log(instance=instance, action="wagtail.create", content_changed=True)
        return instance

    def save_action(self):
        success_message = self.get_success_message(self.object)
        success_buttons = self.get_success_buttons()
        if success_message is not None:
            messages.success(
                self.request,
                success_message,
                buttons=success_buttons,
            )
        return redirect(self.get_success_url())

    def form_valid(self, form):
        self.form = form
        with transaction.atomic():
            self.object = self.save_instance()

        response = self.save_action()

        hook_response = self.run_after_hook()
        if hook_response is not None:
            return hook_response

        return response

    def form_invalid(self, form):
        self.form = form
        error_message = self.get_error_message()
        if error_message is not None:
            messages.validation_error(self.request, error_message, form)
        return super().form_invalid(form)


class EditView(
    LocaleMixin,
    PanelMixin,
    PermissionCheckedMixin,
    BeforeAfterHookMixin,
    WagtailAdminTemplateMixin,
    BaseUpdateView,
):
    model = None
    form_class = None
    index_url_name = None
    edit_url_name = None
    delete_url_name = None
    page_title = gettext_lazy("Editing")
    context_object_name = None
    template_name = "wagtailadmin/generic/edit.html"
    permission_required = "change"
    delete_item_label = gettext_lazy("Delete")
    success_message = None
    error_message = None
    submit_button_label = gettext_lazy("Save")
    actions = ["edit"]

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.action = self.get_action(request)

    def get_action(self, request):
        for action in self.get_available_actions():
            if request.POST.get(f"action-{action}"):
                return action
        return "edit"

    def get_available_actions(self):
        return self.actions

    def get_object(self, queryset=None):
        if "pk" not in self.kwargs:
            self.kwargs["pk"] = self.args[0]
        self.kwargs["pk"] = unquote(str(self.kwargs["pk"]))
        return super().get_object(queryset)

    def get_page_subtitle(self):
        return str(self.object)

    def get_edit_url(self):
        if not self.edit_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.EditView must provide an "
                "edit_url_name attribute or a get_edit_url method"
            )
        return reverse(self.edit_url_name, args=(quote(self.object.pk),))

    def get_delete_url(self):
        if self.delete_url_name:
            return reverse(self.delete_url_name, args=(quote(self.object.pk),))

    def get_success_url(self):
        if not self.index_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.EditView must provide an "
                "index_url_name attribute or a get_success_url method"
            )
        return reverse(self.index_url_name)

    def save_instance(self):
        """
        Called after the form is successfully validated - saves the object to the db.
        Override this to implement custom save logic.
        """
        instance = self.form.save()

        self.has_content_changes = self.form.has_changed()

        log(
            instance=instance,
            action="wagtail.edit",
            content_changed=self.has_content_changes,
        )

        return instance

    def save_action(self):
        success_message = self.get_success_message()
        success_buttons = self.get_success_buttons()
        if success_message is not None:
            messages.success(
                self.request,
                success_message,
                buttons=success_buttons,
            )
        return redirect(self.get_success_url())

    def get_success_message(self):
        if self.success_message is None:
            return None
        return self.success_message % {"object": self.object}

    def get_success_buttons(self):
        return [
            messages.button(
                reverse(self.edit_url_name, args=(quote(self.object.pk),)), _("Edit")
            )
        ]

    def get_error_message(self):
        if self.error_message is None:
            return None
        return self.error_message

    def form_valid(self, form):
        self.form = form
        with transaction.atomic():
            self.object = self.save_instance()

        response = self.save_action()

        hook_response = self.run_after_hook()
        if hook_response is not None:
            return hook_response

        return response

    def form_invalid(self, form):
        self.form = form
        error_message = self.get_error_message()
        if error_message is not None:
            messages.validation_error(self.request, error_message, form)
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action_url"] = self.get_edit_url()
        context["submit_button_label"] = self.submit_button_label
        context["can_delete"] = (
            self.permission_policy is None
            or self.permission_policy.user_has_permission(self.request.user, "delete")
        )
        if context["can_delete"]:
            context["delete_url"] = self.get_delete_url()
            context["delete_item_label"] = self.delete_item_label
        return context


class DeleteView(
    LocaleMixin,
    PanelMixin,
    PermissionCheckedMixin,
    BeforeAfterHookMixin,
    WagtailAdminTemplateMixin,
    BaseDeleteView,
):
    model = None
    index_url_name = None
    delete_url_name = None
    usage_url_name = None
    template_name = "wagtailadmin/generic/confirm_delete.html"
    context_object_name = None
    permission_required = "delete"
    success_message = None
    page_title = gettext_lazy("Delete")

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.object = self.get_object()
        # Get this here instead of the template so that we do not iterate through
        # the usage and potentially trigger a database query for each item
        self.usage_url = self.get_usage_url()
        self.usage = self.get_usage()

    def get_object(self, queryset=None):
        # If the object has already been loaded, return it to avoid another query
        if getattr(self, "object", None):
            return self.object
        if self.pk_url_kwarg not in self.kwargs:
            self.kwargs[self.pk_url_kwarg] = self.args[0]
        self.kwargs[self.pk_url_kwarg] = unquote(str(self.kwargs[self.pk_url_kwarg]))
        return super().get_object(queryset)

    def get_usage(self):
        if not self.usage_url:
            return None
        return ReferenceIndex.get_grouped_references_to(self.object)

    def get_success_url(self):
        next_url = get_valid_next_url_from_request(self.request)
        if next_url:
            return next_url
        if not self.index_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.DeleteView must provide an "
                "index_url_name attribute or a get_success_url method"
            )
        return reverse(self.index_url_name)

    def get_page_subtitle(self):
        return str(self.object)

    def get_delete_url(self):
        if not self.delete_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.DeleteView must provide a "
                "delete_url_name attribute or a get_delete_url method"
            )
        return reverse(self.delete_url_name, args=(quote(self.object.pk),))

    def get_usage_url(self):
        # Usage URL is optional, allow it to be unset
        if self.usage_url_name:
            return (
                reverse(self.usage_url_name, args=(quote(self.object.pk),))
                + "?describe_on_delete=1"
            )

    @property
    def confirmation_message(self):
        return _("Are you sure you want to delete this %(model_name)s?") % {
            "model_name": self.object._meta.verbose_name
        }

    def get_success_message(self):
        if self.success_message is None:
            return None
        return self.success_message % {"object": self.object}

    def delete_action(self):
        with transaction.atomic():
            log(instance=self.object, action="wagtail.delete")
            self.object.delete()

    def form_valid(self, form):
        if self.usage and self.usage.is_protected:
            raise PermissionDenied
        success_url = self.get_success_url()
        self.delete_action()
        messages.success(self.request, self.get_success_message())
        hook_response = self.run_after_hook()
        if hook_response is not None:
            return hook_response
        return HttpResponseRedirect(success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_opts"] = self.object._meta
        context["next"] = self.get_success_url()
        if self.usage_url:
            context["usage_url"] = self.usage_url
            context["usage_count"] = self.usage.count()
            context["is_protected"] = self.usage.is_protected
        return context


class InspectView(PermissionCheckedMixin, WagtailAdminTemplateMixin, TemplateView):
    template_name = "wagtailadmin/generic/inspect.html"
    page_title = gettext_lazy("Inspecting")
    model = None
    edit_url_name = None
    delete_url_name = None
    fields = []
    fields_exclude = []
    pk_url_kwarg = "pk"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.pk = self.kwargs[self.pk_url_kwarg]
        self.fields = self.get_fields()
        self.object = self.get_object()

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, pk=unquote(self.pk))

    def get_page_subtitle(self):
        return str(self.object)

    def get_fields(self):
        fields = self.fields or [
            f.name
            for f in self.model._meta.get_fields()
            if f.concrete
            and (not f.is_relation or (not f.auto_created and f.related_model))
        ]

        fields = [f for f in fields if f not in self.fields_exclude]
        return fields

    def get_field_label(self, field_name, field):
        return capfirst(label_for_field(field_name, model=self.model))

    def get_field_display_value(self, field_name, field):
        # First we check for a 'get_fieldname_display' property/method on
        # the model, and return the value of that, if present.
        value_func = getattr(self.object, "get_%s_display" % field_name, None)
        if value_func is not None:
            if callable(value_func):
                return value_func()
            return value_func

        # Now let's get the attribute value from the instance itself and see if
        # we can render something useful. Raises AttributeError appropriately.
        value = getattr(self.object, field_name)

        if isinstance(value, models.Manager):
            value = value.all()

        if isinstance(value, models.QuerySet):
            return ", ".join(str(obj) for obj in value) or "-"

        display_class = display_class_registry.get(field)

        if display_class:
            return display_class(value)

        return value

    def get_context_for_field(self, field_name):
        try:
            field = self.model._meta.get_field(field_name)
        except FieldDoesNotExist:
            field = None
        context = {
            "label": self.get_field_label(field_name, field),
            "value": self.get_field_display_value(field_name, field),
            "component": None,
        }
        if isinstance(context["value"], Component):
            context["component"] = context["value"]
        return context

    def get_fields_context(self):
        return [self.get_context_for_field(field_name) for field_name in self.fields]

    def get_edit_url(self):
        if not self.edit_url_name or (
            self.permission_policy
            and not self.permission_policy.user_has_permission(
                self.request.user, "change"
            )
        ):
            return None
        return reverse(self.edit_url_name, args=(quote(self.pk),))

    def get_delete_url(self):
        if not self.delete_url_name or (
            self.permission_policy
            and not self.permission_policy.user_has_permission(
                self.request.user, "delete"
            )
        ):
            return None
        return reverse(self.delete_url_name, args=(quote(self.pk),))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.object
        context["fields"] = self.get_fields_context()
        context["edit_url"] = self.get_edit_url()
        context["delete_url"] = self.get_delete_url()
        return context


class RevisionsCompareView(WagtailAdminTemplateMixin, TemplateView):
    edit_handler = None
    edit_url_name = None
    history_url_name = None
    edit_label = gettext_lazy("Edit")
    history_label = gettext_lazy("History")
    template_name = "wagtailadmin/generic/revisions/compare.html"
    model = None

    def setup(self, request, pk, revision_id_a, revision_id_b, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.pk = pk
        self.revision_id_a = revision_id_a
        self.revision_id_b = revision_id_b
        self.object = self.get_object()

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, pk=unquote(self.pk))

    def get_edit_handler(self):
        if self.edit_handler:
            return self.edit_handler
        return get_edit_handler(self.model)

    def get_page_subtitle(self):
        return str(self.object)

    def get_history_url(self):
        if self.history_url_name:
            return reverse(self.history_url_name, args=(quote(self.object.pk),))

    def get_edit_url(self):
        if self.edit_url_name:
            return reverse(self.edit_url_name, args=(quote(self.object.pk),))

    def _get_revision_and_heading(self, revision_id):
        if revision_id == "live":
            revision = self.object
            revision_heading = _("Live")
            return revision, revision_heading

        if revision_id == "earliest":
            revision = self.object.revisions.order_by("created_at", "id").first()
            revision_heading = _("Earliest")
        elif revision_id == "latest":
            revision = self.object.revisions.order_by("created_at", "id").last()
            revision_heading = _("Latest")
        else:
            revision = get_object_or_404(self.object.revisions, id=revision_id)
            if revision:
                revision_heading = str(revision.created_at)

        if not revision:
            raise Http404

        revision = revision.as_object()

        return revision, revision_heading

    def _get_comparison(self, revision_a, revision_b):
        comparison = (
            self.get_edit_handler()
            .get_bound_panel(instance=self.object, request=self.request, form=None)
            .get_comparison()
        )

        result = []
        for comp in comparison:
            diff = comp(revision_a, revision_b)
            if diff.has_changed():
                result += [diff]

        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        revision_a, revision_a_heading = self._get_revision_and_heading(
            self.revision_id_a
        )
        revision_b, revision_b_heading = self._get_revision_and_heading(
            self.revision_id_b
        )
        comparison = self._get_comparison(revision_a, revision_b)

        context.update(
            {
                "object": self.object,
                "history_label": self.history_label,
                "edit_label": self.edit_label,
                "history_url": self.get_history_url(),
                "edit_url": self.get_edit_url(),
                "revision_a": revision_a,
                "revision_a_heading": revision_a_heading,
                "revision_b": revision_b,
                "revision_b_heading": revision_b_heading,
                "comparison": comparison,
            }
        )

        return context


class UnpublishView(HookResponseMixin, WagtailAdminTemplateMixin, TemplateView):
    model = None
    index_url_name = None
    edit_url_name = None
    unpublish_url_name = None
    usage_url_name = None
    success_message = gettext_lazy("'%(object)s' unpublished.")
    template_name = "wagtailadmin/generic/confirm_unpublish.html"

    def setup(self, request, pk, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.pk = pk
        self.object = self.get_object()

    def dispatch(self, request, *args, **kwargs):
        self.objects_to_unpublish = self.get_objects_to_unpublish()
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if not self.model or not issubclass(self.model, DraftStateMixin):
            raise Http404
        return get_object_or_404(self.model, pk=unquote(self.pk))

    def get_usage(self):
        return ReferenceIndex.get_grouped_references_to(self.object)

    def get_objects_to_unpublish(self):
        # Hook to allow child classes to have more objects to unpublish (e.g. page descendants)
        return [self.object]

    def get_object_display_title(self):
        return str(self.object)

    def get_success_message(self):
        if self.success_message is None:
            return None
        return self.success_message % {"object": str(self.object)}

    def get_success_buttons(self):
        if self.edit_url_name:
            return [
                messages.button(
                    reverse(self.edit_url_name, args=(quote(self.object.pk),)),
                    _("Edit"),
                )
            ]

    def get_next_url(self):
        if not self.index_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.UnpublishView "
                "must provide an index_url_name attribute or a get_next_url method"
            )
        return reverse(self.index_url_name)

    def get_unpublish_url(self):
        if not self.unpublish_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.UnpublishView "
                "must provide an unpublish_url_name attribute or a get_unpublish_url method"
            )
        return reverse(self.unpublish_url_name, args=(quote(self.object.pk),))

    def get_usage_url(self):
        # Usage URL is optional, allow it to be unset
        if self.usage_url_name:
            return reverse(self.usage_url_name, args=(quote(self.object.pk),))

    def unpublish(self):
        hook_response = self.run_hook("before_unpublish", self.request, self.object)
        if hook_response is not None:
            return hook_response

        for object in self.objects_to_unpublish:
            action = UnpublishAction(object, user=self.request.user)
            action.execute(skip_permission_checks=True)

        hook_response = self.run_hook("after_unpublish", self.request, self.object)
        if hook_response is not None:
            return hook_response

    def post(self, request, *args, **kwargs):
        hook_response = self.unpublish()
        if hook_response:
            return hook_response

        success_message = self.get_success_message()
        success_buttons = self.get_success_buttons()
        if success_message is not None:
            messages.success(request, success_message, buttons=success_buttons)

        return redirect(self.get_next_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_opts"] = self.object._meta
        context["object"] = self.object
        context["object_display_title"] = self.get_object_display_title()
        context["unpublish_url"] = self.get_unpublish_url()
        context["next_url"] = self.get_next_url()
        context["usage_url"] = self.get_usage_url()
        if context["usage_url"]:
            usage = self.get_usage()
            context["usage_count"] = usage.count()
        return context


class RevisionsUnscheduleView(WagtailAdminTemplateMixin, TemplateView):
    model = None
    edit_url_name = None
    history_url_name = None
    revisions_unschedule_url_name = None
    success_message = gettext_lazy(
        'Version %(revision_id)s of "%(object)s" unscheduled.'
    )
    template_name = "wagtailadmin/shared/revisions/confirm_unschedule.html"

    def setup(self, request, pk, revision_id, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.pk = pk
        self.revision_id = revision_id
        self.object = self.get_object()
        self.revision = self.get_revision()

    def get_object(self, queryset=None):
        if not self.model or not issubclass(self.model, DraftStateMixin):
            raise Http404
        return get_object_or_404(self.model, pk=unquote(self.pk))

    def get_revision(self):
        return get_object_or_404(self.object.revisions, id=self.revision_id)

    def get_revisions_unschedule_url(self):
        return reverse(
            self.revisions_unschedule_url_name,
            args=(quote(self.object.pk), self.revision.id),
        )

    def get_object_display_title(self):
        return str(self.object)

    def get_success_message(self):
        if self.success_message is None:
            return None
        return self.success_message % {
            "revision_id": self.revision.id,
            "object": self.get_object_display_title(),
        }

    def get_success_buttons(self):
        return [
            messages.button(
                reverse(self.edit_url_name, args=(quote(self.object.pk),)), _("Edit")
            )
        ]

    def get_next_url(self):
        next_url = get_valid_next_url_from_request(self.request)
        if next_url:
            return next_url

        if not self.history_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.RevisionsUnscheduleView "
                " must provide a history_url_name attribute or a get_next_url method"
            )
        return reverse(self.history_url_name, args=(quote(self.object.pk),))

    def get_page_subtitle(self):
        return _('revision %(revision_id)s of "%(object)s"') % {
            "revision_id": self.revision.id,
            "object": self.get_object_display_title(),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "object": self.object,
                "revision": self.revision,
                "subtitle": self.get_page_subtitle(),
                "object_display_title": self.get_object_display_title(),
                "revisions_unschedule_url": self.get_revisions_unschedule_url(),
                "next_url": self.get_next_url(),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        self.revision.approved_go_live_at = None
        self.revision.save(user=request.user, update_fields=["approved_go_live_at"])

        success_message = self.get_success_message()
        success_buttons = self.get_success_buttons()
        if success_message:
            messages.success(
                request,
                success_message,
                buttons=success_buttons,
            )

        return redirect(self.get_next_url())
