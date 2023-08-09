from django.core.exceptions import ImproperlyConfigured
from django.forms.models import modelform_factory
from django.urls import path

from wagtail.admin.admin_url_finder import (
    ModelAdminURLFinder,
    register_admin_url_finder,
)
from wagtail.admin.views import generic
from wagtail.permissions import ModelPermissionPolicy

from .base import ViewSet


class ModelViewSet(ViewSet):
    """
    A viewset to allow listing, creating, editing and deleting model instances.
    """

    icon = ""  #: The icon to use to represent the model within this viewset.

    #: The view class to use for the index view; must be a subclass of ``wagtail.admin.views.generic.IndexView``.
    index_view_class = generic.IndexView

    #: The view class to use for the create view; must be a subclass of ``wagtail.admin.views.generic.CreateView``.
    add_view_class = generic.CreateView

    #: The view class to use for the edit view; must be a subclass of ``wagtail.admin.views.generic.EditView``.
    edit_view_class = generic.EditView

    #: The view class to use for the delete view; must be a subclass of ``wagtail.admin.views.generic.DeleteView``.
    delete_view_class = generic.DeleteView

    @property
    def permission_policy(self):
        return ModelPermissionPolicy(self.model)

    def get_index_view_kwargs(self):
        return {
            "model": self.model,
            "permission_policy": self.permission_policy,
            "index_url_name": self.get_url_name("index"),
            "index_results_url_name": self.get_url_name("index_results"),
            "add_url_name": self.get_url_name("add"),
            "edit_url_name": self.get_url_name("edit"),
            "header_icon": self.icon,
        }

    @property
    def index_view(self):
        return self.index_view_class.as_view(
            **self.get_index_view_kwargs(),
        )

    @property
    def index_results_view(self):
        return self.index_view_class.as_view(
            **self.get_index_view_kwargs(),
            results_only=True,
        )

    @property
    def add_view(self):
        return self.add_view_class.as_view(
            model=self.model,
            permission_policy=self.permission_policy,
            form_class=self.get_form_class(),
            index_url_name=self.get_url_name("index"),
            add_url_name=self.get_url_name("add"),
            edit_url_name=self.get_url_name("edit"),
            header_icon=self.icon,
        )

    @property
    def edit_view(self):
        return self.edit_view_class.as_view(
            model=self.model,
            permission_policy=self.permission_policy,
            form_class=self.get_form_class(for_update=True),
            index_url_name=self.get_url_name("index"),
            edit_url_name=self.get_url_name("edit"),
            delete_url_name=self.get_url_name("delete"),
            header_icon=self.icon,
        )

    @property
    def delete_view(self):
        return self.delete_view_class.as_view(
            model=self.model,
            permission_policy=self.permission_policy,
            index_url_name=self.get_url_name("index"),
            delete_url_name=self.get_url_name("delete"),
            header_icon=self.icon,
        )

    def formfield_for_dbfield(self, db_field, **kwargs):
        return db_field.formfield(**kwargs)

    def get_form_class(self, for_update=False):
        """
        Returns the form class to use for the create / edit forms.
        """
        fields = self.get_form_fields()
        exclude = self.get_exclude_form_fields()

        if fields is None and exclude is None:
            raise ImproperlyConfigured(
                "Subclasses of ModelViewSet must specify 'get_form_class', 'form_fields' "
                "or 'exclude_form_fields'."
            )

        return modelform_factory(
            self.model,
            formfield_callback=self.formfield_for_dbfield,
            fields=fields,
            exclude=exclude,
        )

    def get_form_fields(self):
        """
        Returns a list or tuple of field names to be included in the create / edit forms.
        """
        return getattr(self, "form_fields", None)

    def get_exclude_form_fields(self):
        """
        Returns a list or tuple of field names to be excluded from the create / edit forms.
        """
        return getattr(self, "exclude_form_fields", None)

    @property
    def url_finder_class(self):
        return type(
            "_ModelAdminURLFinder",
            (ModelAdminURLFinder,),
            {
                "permission_policy": self.permission_policy,
                "edit_url_name": self.get_url_name("edit"),
            },
        )

    def register_admin_url_finder(self):
        register_admin_url_finder(self.model, self.url_finder_class)

    def get_urlpatterns(self):
        return super().get_urlpatterns() + [
            path("", self.index_view, name="index"),
            path("results/", self.index_results_view, name="index_results"),
            path("new/", self.add_view, name="add"),
            path("<int:pk>/", self.edit_view, name="edit"),
            path("<int:pk>/delete/", self.delete_view, name="delete"),
        ]

    def on_register(self):
        super().on_register()
        self.register_admin_url_finder()
