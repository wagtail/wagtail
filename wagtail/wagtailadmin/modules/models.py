from django.conf.urls import url
from django.contrib.auth import get_permission_codename
from django.forms.models import modelform_factory
from django.views.generic.base import TemplateResponseMixin, View
from django.views.generic.list import BaseListView
from django.views.generic.edit import BaseCreateView, BaseUpdateView, BaseDeleteView

from .base import Module, ModuleViewMixin


class ModelModuleViewMixin(ModuleViewMixin):
    def get_context_data(self, *args, **kwargs):
        context = super(ModelModuleViewMixin, self).get_context_data(*args, **kwargs)

        obj = getattr(self, 'object', None)

        context['has_add_permission'] = self.module.has_add_permission(self.request)
        context['has_change_permission'] = self.module.has_change_permission(self.request, obj=obj)
        context['has_delete_permission'] = self.module.has_delete_permission(self.request, obj=obj)
        return context

    @property
    def model(self):
        return self.module.model


class ModelIndexView(ModelModuleViewMixin, TemplateResponseMixin, BaseListView):
    template_name = "wagtailadmin/models/index.html"


class ModelCreateView(ModelModuleViewMixin, TemplateResponseMixin, BaseCreateView):
    template_name = "wagtailadmin/models/create.html"

    def get_form_class(self):
        return self.module.get_create_form_class()


class ModelUpdateView(ModelModuleViewMixin, TemplateResponseMixin, BaseUpdateView):
    template_name = "wagtailadmin/models/update.html"

    def get_form_class(self):
        return self.module.get_edit_form_class()


class ModelDeleteView(ModelModuleViewMixin, TemplateResponseMixin, BaseDeleteView):
    template_name = "wagtailadmin/models/confirm_delete.html"


class ModelModule(Module):
    icon_class = ""

    index_view = ModelIndexView
    create_view = ModelCreateView
    update_view = ModelUpdateView
    delete_view = ModelDeleteView

    @property
    def model_verbose_name(self):
        return self.model._meta.verbose_name

    @property
    def model_verbose_name_plural(self):
        return self.model._meta.verbose_name_plural

    def formfield_for_dbfield(self, db_field, **kwargs):
        return db_field.formfield(**kwargs)

    def get_create_form_class(self):
        return modelform_factory(
            self.model,
            formfield_callback=self.formfield_for_dbfield,
        )

    def get_edit_form_class(self):
        return modelform_factory(
            self.model,
            formfield_callback=self.formfield_for_dbfield,
        )

    # Permissions logic pinched directly from Django
    # https://github.com/django/django/blob/cf1f36bb6eb34fafe6c224003ad585a647f6117b/django/contrib/admin/options.py#L485-L535

    def has_add_permission(self, request):
        """
        Returns True if the given request has permission to add an object.
        Can be overridden by the user in subclasses.
        """
        opts = self.model._meta
        codename = get_permission_codename('add', opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    def has_change_permission(self, request, obj=None):
        """
        Returns True if the given request has permission to change the given
        Django model instance, the default implementation doesn't examine the
        `obj` parameter.

        Can be overridden by the user in subclasses. In such case it should
        return True if the given request has permission to change the `obj`
        model instance. If `obj` is None, this should return True if the given
        request has permission to change *any* object of the given type.
        """
        opts = self.model._meta
        codename = get_permission_codename('change', opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    def has_delete_permission(self, request, obj=None):
        """
        Returns True if the given request has permission to change the given
        Django model instance, the default implementation doesn't examine the
        `obj` parameter.

        Can be overridden by the user in subclasses. In such case it should
        return True if the given request has permission to delete the `obj`
        model instance. If `obj` is None, this should return True if the given
        request has permission to delete *any* object of the given type.
        """
        opts = self.model._meta
        codename = get_permission_codename('delete', opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    def has_module_permission(self, request):
        """
        Returns True if the given request has any permission in the given
        app label.

        Can be overridden by the user in subclasses. In such case it should
        return True if the given request has permission to view the module on
        the admin index page and access the module's index page. Overriding it
        does not restrict access to the add, change or delete views. Use
        `ModelAdmin.has_(add|change|delete)_permission` for that.
        """
        opts = self.model._meta
        return request.user.has_module_perms(opts.app_label)


    def get_urls(self):
        return (
            url(r'^$', self.index_view.as_view(module=self), name='index'),
            url(r'^new/$', self.create_view.as_view(module=self), name='create'),
            url(r'^(?P<pk>\d+)/$', self.update_view.as_view(module=self), name='update'),
            url(r'^(?P<pk>\d+)/delete/$', self.delete_view.as_view(module=self), name='delete'),
        )
