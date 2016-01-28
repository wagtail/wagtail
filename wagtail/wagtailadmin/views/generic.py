from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext as _, ugettext_lazy as __
from django.views.generic.base import View

from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.utils import permission_denied


class PermissionCheckedMixin(object):
    """
    Mixin for class-based views to enforce permission checks according to
    a permission policy (see wagtail.wagtailcore.permission_policies).

    To take advantage of this, subclasses should set the class property:
    * permission_policy (a policy object)
    and either of:
    * permission_required (an action name such as 'add', 'change' or 'delete')
    * any_permission_required (a list of action names - the user must have
      one or more of those permissions)
    """
    permission_policy = None
    permission_required = None
    any_permission_required = None

    def dispatch(self, request, *args, **kwargs):
        if self.permission_policy is not None:

            if self.permission_required is not None:
                if not self.permission_policy.user_has_permission(
                    request.user, self.permission_required
                ):
                    return permission_denied(request)

            if self.any_permission_required is not None:
                if not self.permission_policy.user_has_any_permission(
                    request.user, self.any_permission_required
                ):
                    return permission_denied(request)

        return super(PermissionCheckedMixin, self).dispatch(request, *args, **kwargs)


class IndexView(PermissionCheckedMixin, View):
    model = None
    header_icon = ''
    index_url_name = None
    add_url_name = None
    edit_url_name = None
    context_object_name = None
    any_permission_required = ['add', 'change', 'delete']
    template_name = None

    def get_queryset(self):
        return self.model.objects.all()

    def get(self, request):
        object_list = self.get_queryset()

        context = {
            'view': self,
            'object_list': object_list,
            'can_add': (
                self.permission_policy is None or
                self.permission_policy.user_has_permission(self.request.user, 'add')
            ),
        }
        if self.context_object_name:
            context[self.context_object_name] = object_list

        return render(request, self.template_name, context)


class CreateView(PermissionCheckedMixin, View):
    model = None
    form_class = None
    header_icon = ''
    index_url_name = None
    add_url_name = None
    edit_url_name = None
    template_name = 'wagtailadmin/generic/create.html'
    permission_required = 'add'

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
    model = None
    form_class = None
    header_icon = ''
    index_url_name = None
    edit_url_name = None
    delete_url_name = None
    page_title = __("Editing")
    context_object_name = None
    template_name = 'wagtailadmin/generic/edit.html'
    permission_required = 'change'

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
            'can_delete': (
                self.permission_policy is None or
                self.permission_policy.user_has_permission(self.request.user, 'delete')
            ),
        }
        if self.context_object_name:
            context[self.context_object_name] = self.instance

        return render(self.request, self.template_name, context)


class DeleteView(PermissionCheckedMixin, View):
    model = None
    header_icon = ''
    index_url_name = None
    delete_url_name = None
    template_name = 'wagtailadmin/generic/confirm_delete.html'
    context_object_name = None
    permission_required = 'delete'

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
