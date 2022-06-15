from django import VERSION as DJANGO_VERSION
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.forms import Form
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.generic.detail import BaseDetailView
from django.views.generic.edit import BaseCreateView
from django.views.generic.edit import BaseDeleteView as DjangoBaseDeleteView
from django.views.generic.edit import BaseUpdateView, DeletionMixin, FormMixin
from django.views.generic.list import BaseListView

from wagtail.admin import messages
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.ui.tables import Table, TitleColumn
from wagtail.log_actions import log
from wagtail.search.index import class_is_indexed

from .base import WagtailAdminTemplateMixin
from .mixins import BeforeAfterHookMixin, LocaleMixin, PanelMixin
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


class IndexView(
    LocaleMixin, PermissionCheckedMixin, WagtailAdminTemplateMixin, BaseListView
):
    model = None
    index_url_name = None
    add_url_name = None
    add_item_label = _("Add")
    edit_url_name = None
    template_name = "wagtailadmin/generic/index.html"
    context_object_name = None
    any_permission_required = ["add", "change", "delete"]
    page_kwarg = "p"
    default_ordering = None
    is_searchable = None
    search_kwarg = "q"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        if not hasattr(self, "columns"):
            self.columns = self.get_columns()
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
            return class_is_indexed(self.model)
        return self.is_searchable

    def get_search_url(self):
        if not self.is_searchable:
            return None
        return self.get_index_url()

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

    def get_columns(self):
        try:
            return self.columns
        except AttributeError:
            return [
                TitleColumn(
                    "name",
                    label=gettext_lazy("Name"),
                    accessor=str,
                    get_url=lambda obj: self.get_edit_url(obj),
                ),
            ]

    def get_index_url(self):
        if self.index_url_name:
            return reverse(self.index_url_name)

    def get_edit_url(self, instance):
        if self.edit_url_name:
            return reverse(self.edit_url_name, args=(instance.pk,))

    def get_add_url(self):
        if self.add_url_name:
            return reverse(self.add_url_name)

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        index_url = self.get_index_url()
        table = Table(
            self.columns,
            context["object_list"],
            base_url=index_url,
            ordering=self.get_ordering(),
        )

        context["can_add"] = (
            self.permission_policy is None
            or self.permission_policy.user_has_permission(self.request.user, "add")
        )
        if context["can_add"]:
            context["add_url"] = self.get_add_url()
            context["add_item_label"] = self.add_item_label

        context["table"] = table
        context["media"] = table.media
        context["index_url"] = index_url
        context["is_paginated"] = bool(self.paginate_by)
        context["is_searchable"] = self.is_searchable
        context["search_url"] = self.get_search_url()
        context["search_form"] = self.search_form
        context["is_searching"] = self.is_searching
        context["query_string"] = self.search_query
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

    def get_add_url(self):
        if not self.add_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.CreateView must provide an "
                "add_url_name attribute or a get_add_url method"
            )
        return reverse(self.add_url_name)

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
        return self.success_message.format(instance)

    def get_success_buttons(self):
        return [
            messages.button(
                reverse(self.edit_url_name, args=(self.object.id,)), _("Edit")
            )
        ]

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
        return self.form.save()

    def form_valid(self, form):
        self.form = form
        with transaction.atomic():
            self.object = self.save_instance()
            log(instance=self.object, action="wagtail.create")
        success_message = self.get_success_message(self.object)
        success_buttons = self.get_success_buttons()
        if success_message is not None:
            messages.success(self.request, success_message, buttons=success_buttons)
        hook_response = self.run_after_hook()
        if hook_response is not None:
            return hook_response
        return redirect(self.get_success_url())

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

    def get_object(self, queryset=None):
        if "pk" not in self.kwargs:
            self.kwargs["pk"] = self.args[0]
        return super().get_object(queryset)

    def get_page_subtitle(self):
        return str(self.object)

    def get_edit_url(self):
        if not self.edit_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.EditView must provide an "
                "edit_url_name attribute or a get_edit_url method"
            )
        return reverse(self.edit_url_name, args=(self.object.id,))

    def get_delete_url(self):
        if self.delete_url_name:
            return reverse(self.delete_url_name, args=(self.object.id,))

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
        return self.form.save()

    def get_success_message(self):
        if self.success_message is None:
            return None
        return self.success_message.format(self.object)

    def get_success_buttons(self):
        return [
            messages.button(
                reverse(self.edit_url_name, args=(self.object.id,)), _("Edit")
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
            log(instance=self.object, action="wagtail.edit")
        success_message = self.get_success_message()
        success_buttons = self.get_success_buttons()
        if success_message is not None:
            messages.success(
                self.request,
                success_message,
                buttons=success_buttons,
            )
        hook_response = self.run_after_hook()
        if hook_response is not None:
            return hook_response
        return redirect(self.get_success_url())

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
    template_name = "wagtailadmin/generic/confirm_delete.html"
    context_object_name = None
    permission_required = "delete"
    success_message = None

    def get_object(self, queryset=None):
        if "pk" not in self.kwargs:
            self.kwargs["pk"] = self.args[0]
        return super().get_object(queryset)

    def get_success_url(self):
        if not self.index_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.DeleteView must provide an "
                "index_url_name attribute or a get_success_url method"
            )
        return reverse(self.index_url_name)

    def get_page_subtitle(self):
        return str(self.object)

    def get_delete_url(self):
        if not self.index_url_name:
            raise ImproperlyConfigured(
                "Subclasses of wagtail.admin.views.generic.models.DeleteView must provide a "
                "delete_url_name attribute or a get_delete_url method"
            )
        return reverse(self.delete_url_name, args=(self.object.id,))

    def get_success_message(self):
        if self.success_message is None:
            return None
        return self.success_message.format(self.object)

    def delete_action(self):
        with transaction.atomic():
            log(instance=self.object, action="wagtail.delete")
            self.object.delete()

    def form_valid(self, form):
        success_url = self.get_success_url()
        self.delete_action()
        messages.success(self.request, self.get_success_message())
        hook_response = self.run_after_hook()
        if hook_response is not None:
            return hook_response
        return HttpResponseRedirect(success_url)
