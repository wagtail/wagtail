from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.generic.edit import BaseCreateView, BaseDeleteView, BaseUpdateView
from django.views.generic.list import BaseListView

from wagtail.admin import messages

from .base import WagtailAdminTemplateMixin
from .permissions import PermissionCheckedMixin


class IndexView(PermissionCheckedMixin, WagtailAdminTemplateMixin, BaseListView):
    model = None
    index_url_name = None
    add_url_name = None
    edit_url_name = None
    context_object_name = None
    any_permission_required = ['add', 'change', 'delete']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_add'] = (
            self.permission_policy is None
            or self.permission_policy.user_has_permission(self.request.user, 'add')
        )
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
        self.object = self.save_instance()
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
        self.object = self.save_instance()
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
        response = super().delete(request, *args, **kwargs)
        messages.success(request, self.get_success_message())
        return response
