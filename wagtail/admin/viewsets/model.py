from django.core.exceptions import ImproperlyConfigured
from django.forms.models import modelform_factory
from django.urls import path
from django.utils.functional import cached_property

from wagtail.admin.admin_url_finder import (
    ModelAdminURLFinder,
    register_admin_url_finder,
)
from wagtail.admin.views import generic
from wagtail.models import ReferenceIndex
from wagtail.permissions import ModelPermissionPolicy

from .base import ViewSet, ViewSetGroup


class ModelViewSet(ViewSet):
    """
    A viewset to allow listing, creating, editing and deleting model instances.

    All attributes and methods from :class:`~wagtail.admin.viewsets.base.ViewSet`
    are available.
    """

    #: Register the model to the reference index to track its usage.
    #: For more details, see :ref:`managing_the_reference_index`.
    add_to_reference_index = True

    #: The view class to use for the index view; must be a subclass of ``wagtail.admin.views.generic.IndexView``.
    index_view_class = generic.IndexView

    #: The view class to use for the create view; must be a subclass of ``wagtail.admin.views.generic.CreateView``.
    add_view_class = generic.CreateView

    #: The view class to use for the edit view; must be a subclass of ``wagtail.admin.views.generic.EditView``.
    edit_view_class = generic.EditView

    #: The view class to use for the delete view; must be a subclass of ``wagtail.admin.views.generic.DeleteView``.
    delete_view_class = generic.DeleteView

    def __init__(self, name=None, **kwargs):
        super().__init__(name=name, **kwargs)
        if not self.model:
            raise ImproperlyConfigured(
                "ModelViewSet %r must define a `model` attribute or pass a `model` argument"
                % self
            )

        self.model_opts = self.model._meta
        self.app_label = self.model_opts.app_label
        self.model_name = self.model_opts.model_name

    @property
    def permission_policy(self):
        return ModelPermissionPolicy(self.model)

    @cached_property
    def name(self):
        """
        Viewset name, to use as the URL prefix and namespace.
        Defaults to the :attr:`~django.db.models.Options.model_name`.
        """
        return self.model_name

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

    @cached_property
    def menu_label(self):
        return self.model_opts.verbose_name_plural.title()

    @cached_property
    def menu_item_class(self):
        from wagtail.admin.menu import MenuItem

        def is_shown(_self, request):
            return self.permission_policy.user_has_any_permission(
                request.user, ("add", "change", "delete")
            )

        return type(
            f"{self.model.__name__}MenuItem",
            (MenuItem,),
            {"is_shown": is_shown},
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

    def register_reference_index(self):
        if self.add_to_reference_index:
            ReferenceIndex.register_model(self.model)

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
        self.register_reference_index()


class ModelViewSetGroup(ViewSetGroup):
    """
    A container for grouping together multiple
    :class:`~wagtail.admin.viewsets.model.ModelViewSet` instances.

    All attributes and methods from
    :class:`~wagtail.admin.viewsets.base.ViewSetGroup` are available.
    """

    def get_app_label_from_subitems(self):
        for instance in self.registerables:
            if app_label := getattr(instance, "app_label", ""):
                return app_label.title()
        return ""

    @cached_property
    def menu_label(self):
        return self.get_app_label_from_subitems()
