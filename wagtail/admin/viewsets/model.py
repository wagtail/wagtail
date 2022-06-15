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

    @property
    def index_view(self):
        return self.index_view_class.as_view(
            model=self.model,
            permission_policy=self.permission_policy,
            index_url_name=self.get_url_name("index"),
            add_url_name=self.get_url_name("add"),
            edit_url_name=self.get_url_name("edit"),
            header_icon=self.icon,
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
        fields = getattr(self, "form_fields", None)
        exclude = getattr(self, "exclude_form_fields", None)

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

    def get_urlpatterns(self):
        return super().get_urlpatterns() + [
            path("", self.index_view, name="index"),
            path("new/", self.add_view, name="add"),
            path("<int:pk>/", self.edit_view, name="edit"),
            path("<int:pk>/delete/", self.delete_view, name="delete"),
        ]

    def on_register(self):
        super().on_register()
        url_finder_class = type(
            "_ModelAdminURLFinder",
            (ModelAdminURLFinder,),
            {
                "permission_policy": self.permission_policy,
                "edit_url_name": self.get_url_name("edit"),
            },
        )
        register_admin_url_finder(self.model, url_finder_class)
