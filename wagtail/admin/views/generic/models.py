from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.generic.edit import BaseCreateView, BaseDeleteView, BaseUpdateView
from django.views.generic.list import BaseListView

from wagtail.admin import messages
from wagtail.admin.ui.tables import Table, TitleColumn
from wagtail.core.log_actions import log

from .base import WagtailAdminTemplateMixin
from .permissions import PermissionCheckedMixin


class IndexView(PermissionCheckedMixin, WagtailAdminTemplateMixin, BaseListView):
    model = None
    index_url_name = None
    add_url_name = None
    edit_url_name = None
    template_name = 'wagtailadmin/generic/index.html'
    context_object_name = None
    any_permission_required = ['add', 'change', 'delete']
    page_kwarg = 'p'
    default_ordering = None

    def get(self, request, *args, **kwargs):
        if not hasattr(self, 'columns'):
            self.columns = self.get_columns()

        return super().get(request, *args, **kwargs)

    def get_columns(self):
        try:
            return self.columns
        except AttributeError:
            return [
                TitleColumn(
                    'name', label=gettext_lazy("Name"), accessor=str, get_url=lambda obj: self.get_edit_url(obj)
                ),
            ]

    def get_index_url(self):
        if self.index_url_name:
            return reverse(self.index_url_name)

    def get_edit_url(self, instance):
        if self.edit_url_name:
            return reverse(self.edit_url_name, args=(instance.pk,))

    def get_valid_orderings(self):
        orderings = []
        for col in self.columns:
            if col.sort_key:
                orderings.append(col.sort_key)
                orderings.append('-%s' % col.sort_key)
        return orderings

    def get_ordering(self):
        ordering = self.request.GET.get('ordering', self.default_ordering)
        if ordering not in self.get_valid_orderings():
            ordering = self.default_ordering
        return ordering

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        index_url = self.get_index_url()
        table = Table(
            self.columns, context['object_list'], base_url=index_url, ordering=self.get_ordering()
        )

        context['can_add'] = (
            self.permission_policy is None
            or self.permission_policy.user_has_permission(self.request.user, 'add')
        )
        context['table'] = table
        context['media'] = table.media
        context['index_url'] = index_url
        context['is_paginated'] = bool(self.paginate_by)
        return context


class CreateView(PermissionCheckedMixin, WagtailAdminTemplateMixin, BaseCreateView):
    model = None
    form_class = None
    index_url_name = None
    add_url_name = None
    edit_url_name = None
    template_name = 'wagtailadmin/generic/create.html'
    permission_required = 'add'
    success_message = None
    error_message = None

    def get_add_url(self):
        return reverse(self.add_url_name)

    def get_success_url(self):
        return reverse(self.index_url_name)

    def get_success_message(self, instance):
        if self.success_message is None:
            return None
        return self.success_message.format(instance)

    def get_error_message(self):
        if self.error_message is None:
            return None
        return self.error_message

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action_url'] = self.get_add_url()
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
            log(instance=self.object, action='wagtail.create')
        success_message = self.get_success_message(self.object)
        if success_message is not None:
            messages.success(self.request, success_message, buttons=[
                messages.button(reverse(self.edit_url_name, args=(self.object.id,)), _('Edit'))
            ])
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        self.form = form
        error_message = self.get_error_message()
        if error_message is not None:
            messages.error(self.request, error_message)
        return super().form_invalid(form)


class EditView(PermissionCheckedMixin, WagtailAdminTemplateMixin, BaseUpdateView):
    model = None
    form_class = None
    index_url_name = None
    edit_url_name = None
    delete_url_name = None
    page_title = gettext_lazy("Editing")
    context_object_name = None
    template_name = 'wagtailadmin/generic/edit.html'
    permission_required = 'change'
    delete_item_label = gettext_lazy("Delete")
    success_message = None
    error_message = None

    def get_object(self, queryset=None):
        if 'pk' not in self.kwargs:
            self.kwargs['pk'] = self.args[0]
        return super().get_object(queryset)

    def get_page_subtitle(self):
        return str(self.object)

    def get_edit_url(self):
        return reverse(self.edit_url_name, args=(self.object.id,))

    def get_delete_url(self):
        return reverse(self.delete_url_name, args=(self.object.id,))

    def get_success_url(self):
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

    def get_error_message(self):
        if self.error_message is None:
            return None
        return self.error_message

    def form_valid(self, form):
        self.form = form
        with transaction.atomic():
            self.object = self.save_instance()
            log(instance=self.object, action='wagtail.edit')
        success_message = self.get_success_message()
        if success_message is not None:
            messages.success(self.request, success_message, buttons=[
                messages.button(reverse(self.edit_url_name, args=(self.object.id,)), _('Edit'))
            ])
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        self.form = form
        error_message = self.get_error_message()
        if error_message is not None:
            messages.error(self.request, error_message)
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action_url'] = self.get_edit_url()
        context['delete_url'] = self.get_delete_url()
        context['delete_item_label'] = self.delete_item_label
        context['can_delete'] = (
            self.permission_policy is None
            or self.permission_policy.user_has_permission(self.request.user, 'delete')
        )
        return context


class DeleteView(PermissionCheckedMixin, WagtailAdminTemplateMixin, BaseDeleteView):
    model = None
    index_url_name = None
    delete_url_name = None
    template_name = 'wagtailadmin/generic/confirm_delete.html'
    context_object_name = None
    permission_required = 'delete'
    success_message = None

    def get_object(self, queryset=None):
        if 'pk' not in self.kwargs:
            self.kwargs['pk'] = self.args[0]
        return super().get_object(queryset)

    def get_success_url(self):
        return reverse(self.index_url_name)

    def get_page_subtitle(self):
        return str(self.object)

    def get_delete_url(self):
        return reverse(self.delete_url_name, args=(self.object.id,))

    def get_success_message(self):
        if self.success_message is None:
            return None
        return self.success_message.format(self.object)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        with transaction.atomic():
            log(instance=self.object, action='wagtail.delete')
            self.object.delete()
        messages.success(request, self.get_success_message())
        return HttpResponseRedirect(success_url)
