from django.conf.urls import url
from django.utils.translation import ugettext as _, ugettext_lazy as __
from django.forms.models import modelform_factory

from .base import Module

from wagtail.wagtailadmin.views import generic


class ModelModule(Module):
    icon = ""

    index_view_class = generic.IndexView
    add_view_class = generic.CreateView
    edit_view_class = generic.EditView
    delete_view_class = generic.DeleteView

    def get_url_name(self, view_name):
        return self.name + ':' + view_name

    def get_template_name(self, view_name):
        return self.name + '/' + view_name + '.html'

    @property
    def index_view(self):
        return self.index_view_class.as_view(
            model=self.model,
            template_name=self.get_template_name('index'),
            index_url_name=self.get_url_name('index'),
            add_url_name=self.get_url_name('add'),
            edit_url_name=self.get_url_name('edit'),
            header_icon=self.icon,
        )

    @property
    def add_view(self):
        return self.add_view_class.as_view(
            model=self.model,
            form_class=self.get_form_class(),
            template_name=self.get_template_name('create'),
            index_url_name=self.get_url_name('index'),
            add_url_name=self.get_url_name('add'),
            edit_url_name=self.get_url_name('edit'),
            header_icon=self.icon,
        )

    @property
    def edit_view(self):
        return self.edit_view_class.as_view(
            model=self.model,
            form_class=self.get_form_class(for_update=True),
            template_name=self.get_template_name('edit'),
            index_url_name=self.get_url_name('index'),
            edit_url_name=self.get_url_name('edit'),
            delete_url_name=self.get_url_name('delete'),
            header_icon=self.icon,
        )

    @property
    def delete_view(self):
        return self.delete_view_class.as_view(
            model=self.model,
            index_url_name=self.get_url_name('index'),
            delete_url_name=self.get_url_name('delete'),
            header_icon=self.icon,
        )

    def formfield_for_dbfield(self, db_field, **kwargs):
        return db_field.formfield(**kwargs)

    def get_form_class(self, for_update=False):
        return modelform_factory(
            self.model,
            formfield_callback=self.formfield_for_dbfield,
            fields='__all__'
        )

    def get_urlpatterns(self):
        return [
            url(r'^$', self.index_view, name='index'),
            url(r'^new/$', self.add_view, name='add'),
            url(r'^(\d+)/$', self.edit_view, name='edit'),
            url(r'^(\d+)/delete/$', self.delete_view, name='delete'),
        ]
