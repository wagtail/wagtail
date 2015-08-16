from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext as _, ugettext_lazy as __
from django.views.generic.base import View

from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.utils import permission_denied


class PermissionCheckedView(View):
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

        return super(PermissionCheckedView, self).dispatch(request, *args, **kwargs)


class IndexView(PermissionCheckedView):
    def get_queryset(self):
        return self.model.objects.all()

    def get(self, request):
        object_list = self.get_queryset()
        return render(request, self.template, {
            'view': self,
            self.context_object_name: object_list,
            'can_add': self.request.user.has_perm(self.add_permission_name),
        })


class CreateView(PermissionCheckedView):
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
        return render(self.request, self.template, {
            'view': self,
            'form': self.form,
        })


class EditView(PermissionCheckedView):
    page_title = __("Editing")

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
        return render(self.request, self.template, {
            'view': self,
            self.context_object_name: self.instance,
            'form': self.form,
            'can_delete': self.request.user.has_perm(self.delete_permission_name),
        })


class DeleteView(PermissionCheckedView):
    template = 'wagtailadmin/generic/confirm_delete.html'

    def get_page_subtitle(self):
        return str(self.instance)

    def get_delete_url(self):
        return reverse(self.delete_url_name, args=(self.instance.id,))

    def get(self, request, instance_id):
        self.instance = get_object_or_404(self.model, id=instance_id)
        return render(request, self.template, {
            'view': self,
            self.context_object_name: self.instance,
        })

    def post(self, request, instance_id):
        self.instance = get_object_or_404(self.model, id=instance_id)
        self.instance.delete()
        messages.success(request, self.success_message.format(self.instance))
        return redirect(self.index_url_name)
