from django.core.exceptions import ImproperlyConfigured
from django.forms.models import modelform_factory
from django.urls import path

from wagtail.admin.views import generic
from wagtail.core.permissions import ModelPermissionPolicy

from .base import ViewSet


class ModelViewSet(ViewSet):
    icon = ""

    index_view_class = generic.IndexView
    add_view_class = generic.CreateView
    edit_view_class = generic.EditView
    delete_view_class = generic.DeleteView

    @property
    def permission_policy(self):
        return ModelPermissionPolicy(self.model)

    @property
    def index_view(self):
        return self.index_view_class.as_view(
            model=self.model,
            permission_policy=self.permission_policy,
            index_url_name=self.get_url_name('index'),
            add_url_name=self.get_url_name('add'),
            edit_url_name=self.get_url_name('edit'),
            header_icon=self.icon,
        )

    @property
    def add_view(self):
        return self.add_view_class.as_view(
            model=self.model,
            permission_policy=self.permission_policy,
            form_class=self.get_form_class(),
            index_url_name=self.get_url_name('index'),
            add_url_name=self.get_url_name('add'),
            edit_url_name=self.get_url_name('edit'),
            header_icon=self.icon,
        )

    @property
    def edit_view(self):
        return self.edit_view_class.as_view(
            model=self.model,
            permission_policy=self.permission_policy,
            form_class=self.get_form_class(for_update=True),
            index_url_name=self.get_url_name('index'),
            edit_url_name=self.get_url_name('edit'),
            delete_url_name=self.get_url_name('delete'),
            header_icon=self.icon,
        )

    @property
    def delete_view(self):
        return self.delete_view_class.as_view(
            model=self.model,
            permission_policy=self.permission_policy,
            index_url_name=self.get_url_name('index'),
            delete_url_name=self.get_url_name('delete'),
            header_icon=self.icon,
        )

    def formfield_for_dbfield(self, db_field, **kwargs):
        return db_field.formfield(**kwargs)

    def get_form_class(self, for_update=False):
        fields = getattr(self, 'form_fields', None)
        exclude = getattr(self, 'exclude_form_fields', None)

        if fields is None and exclude is None:
            raise ImproperlyConfigured(
                "Subclasses of ModelViewSet must specify 'get_form_class', 'form_fields' "
                "or 'exclude_form_fields'."
            )

        return modelform_factory(
            self.model,
            formfield_callback=self.formfield_for_dbfield,
            fields=fields,
            exclude=exclude
        )

    def get_urlpatterns(self):
        return super().get_urlpatterns() + [
            path('', self.index_view, name='index'),
            path('new/', self.add_view, name='add'),
            path('<int:pk>/', self.edit_view, name='edit'),
            path('<int:pk>/delete/', self.delete_view, name='delete'),
        ]
