from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext as _, ugettext_lazy as __
from django.views.generic.base import View

from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.utils import permission_denied


class PermissionCheckedMixin(object):
    """
    Mixin for class-based views to enforce permission checks.
    Subclasses should set either of the following class properties:
    * permission_required (a single permission string)
    * any_permission_required (a list of permission strings - the user must have
      one or more of those permissions)
    """
    permission_required = None
    any_permission_required = None

    def dispatch(self, request, *args, **kwargs):
        if self.permission_required is not None:
            if not request.user.has_perm(self.permission_required):
                return permission_denied(request)

        if self.any_permission_required is not None:
            has_permission = False

            for perm in self.any_permission_required:
                if request.user.has_perm(perm):
                    has_permission = True
                    break

            if not has_permission:
                return permission_denied(request)

        return super(PermissionCheckedMixin, self).dispatch(request, *args, **kwargs)


class IndexView(PermissionCheckedMixin, View):
    context_object_name = None

    def get_queryset(self):
        return self.model.objects.all()

    def get(self, request):
        object_list = self.get_queryset()

        context = {
            'view': self,
            'object_list': object_list,
            'can_add': self.request.user.has_perm(self.add_permission_name),
        }
        if self.context_object_name:
            context[self.context_object_name] = object_list

        return render(request, self.template_name, context)


class CreateView(PermissionCheckedMixin, View):
    template_name = 'wagtailadmin/generic/create.html'

    def get_add_url(self):
        return reverse(self.add_url_name)

    def get(self, request):
        self.form = self.form_class()
        return self.render_to_response()

    def post(self, request):
        self.form = self.form_class(request.POST)
        if self.form.is_valid():
            instance = self.form.save()

            messages.success(request, self.success_message.format(instance), buttons=[
                messages.button(reverse(self.edit_url_name, args=(instance.id,)), _('Edit'))
            ])
            return redirect(self.index_url_name)
        else:
            return self.render_to_response()

    def render_to_response(self):
        return render(self.request, self.template_name, {
            'view': self,
            'form': self.form,
        })


class EditView(PermissionCheckedMixin, View):
    page_title = __("Editing")
    context_object_name = None
    template_name = 'wagtailadmin/generic/edit.html'

    def get_page_subtitle(self):
        return str(self.instance)

    def get_edit_url(self):
        return reverse(self.edit_url_name, args=(self.instance.id,))

    def get_delete_url(self):
        return reverse(self.delete_url_name, args=(self.instance.id,))

    def get(self, request, instance_id):
        self.instance = get_object_or_404(self.model, id=instance_id)
        self.form = self.form_class(instance=self.instance)
        return self.render_to_response()

    def post(self, request, instance_id):
        self.instance = get_object_or_404(self.model, id=instance_id)
        self.form = self.form_class(request.POST, instance=self.instance)
        if self.form.is_valid():
            self.form.save()
            messages.success(request, self.success_message.format(self.instance), buttons=[
                messages.button(reverse(self.edit_url_name, args=(self.instance.id,)), _('Edit'))
            ])
            return redirect(self.index_url_name)
        else:
            messages.error(request, self.error_message)

        return self.render_to_response()

    def render_to_response(self):
        context = {
            'view': self,
            'object': self.instance,
            'form': self.form,
            'can_delete': self.request.user.has_perm(self.delete_permission_name),
        }
        if self.context_object_name:
            context[self.context_object_name] = self.instance

        return render(self.request, self.template_name, context)


class DeleteView(PermissionCheckedMixin, View):
    template_name = 'wagtailadmin/generic/confirm_delete.html'
    context_object_name = None

    def get_page_subtitle(self):
        return str(self.instance)

    def get_delete_url(self):
        return reverse(self.delete_url_name, args=(self.instance.id,))

    def get(self, request, instance_id):
        self.instance = get_object_or_404(self.model, id=instance_id)

        context = {
            'view': self,
            'object': self.instance,
        }
        if self.context_object_name:
            context[self.context_object_name] = self.instance

        return render(request, self.template_name, context)

    def post(self, request, instance_id):
        self.instance = get_object_or_404(self.model, id=instance_id)
        self.instance.delete()
        messages.success(request, self.success_message.format(self.instance))
        return redirect(self.index_url_name)
