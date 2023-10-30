from warnings import warn

from django.core.exceptions import ImproperlyConfigured
from django.forms.models import modelform_factory
from django.shortcuts import redirect
from django.urls import path
from django.utils.functional import cached_property

from wagtail.admin.admin_url_finder import (
    ModelAdminURLFinder,
    register_admin_url_finder,
)
from wagtail.admin.views import generic
from wagtail.admin.views.generic import history, usage
from wagtail.models import ReferenceIndex
from wagtail.permissions import ModelPermissionPolicy
from wagtail.utils.deprecation import RemovedInWagtail60Warning

from .base import ViewSet, ViewSetGroup


class ModelViewSet(ViewSet):
    """
    A viewset to allow listing, creating, editing and deleting model instances.

    All attributes and methods from :class:`~wagtail.admin.viewsets.base.ViewSet`
    are available.

    For more information on how to use this class, see :ref:`generic_views`.
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

    #: The view class to use for the history view; must be a subclass of ``wagtail.admin.views.generic.history.HistoryView``.
    history_view_class = history.HistoryView

    #: The view class to use for the usage view; must be a subclass of ``wagtail.admin.views.generic.usage.UsageView``.
    usage_view_class = usage.UsageView

    #: The view class to use for the inspect view; must be a subclass of ``wagtail.admin.views.generic.InspectView``.
    inspect_view_class = generic.InspectView

    # Breadcrumbs can be turned off until we have a design that can be consistently applied
    _show_breadcrumbs = True

    #: The prefix of template names to look for when rendering the admin views.
    template_prefix = ""

    #: The number of items to display per page in the index view. Defaults to 20.
    list_per_page = 20

    #: The default ordering to use for the index view.
    #: Can be a string or a list/tuple in the same format as Django's
    #: :attr:`~django.db.models.Options.ordering`.
    ordering = None

    #: Whether to enable the inspect view. Defaults to ``False``.
    inspect_view_enabled = False

    #: The model fields or attributes to display in the inspect view.
    #:
    #: If the field has a corresponding :meth:`~django.db.models.Model.get_FOO_display`
    #: method on the model, the method's return value will be used instead.
    #:
    #: If you have ``wagtail.images`` installed, and the field's value is an instance of
    #: ``wagtail.images.models.AbstractImage``, a thumbnail of that image will be rendered.
    #:
    #: If you have ``wagtail.documents`` installed, and the field's value is an instance of
    #: ``wagtail.docs.models.AbstractDocument``, a link to that document will be rendered,
    #: along with the document title, file extension and size.
    inspect_view_fields = []

    #: The fields to exclude from the inspect view.
    inspect_view_fields_exclude = []

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

    def get_common_view_kwargs(self, **kwargs):
        view_kwargs = super().get_common_view_kwargs(
            **{
                "model": self.model,
                "permission_policy": self.permission_policy,
                "index_url_name": self.get_url_name("index"),
                "index_results_url_name": self.get_url_name("index_results"),
                "history_url_name": self.get_url_name("history"),
                "usage_url_name": self.get_url_name("usage"),
                "add_url_name": self.get_url_name("add"),
                "edit_url_name": self.get_url_name("edit"),
                "delete_url_name": self.get_url_name("delete"),
                "header_icon": self.icon,
                "_show_breadcrumbs": self._show_breadcrumbs,
                **kwargs,
            }
        )
        if self.inspect_view_enabled:
            view_kwargs["inspect_url_name"] = self.get_url_name("inspect")
        return view_kwargs

    def get_index_view_kwargs(self, **kwargs):
        return {
            "template_name": self.index_template_name,
            "results_template_name": self.index_results_template_name,
            "list_display": self.list_display,
            "list_filter": self.list_filter,
            "list_export": self.list_export,
            "export_headings": self.export_headings,
            "export_filename": self.export_filename,
            "filterset_class": self.filterset_class,
            "search_fields": self.search_fields,
            "search_backend_name": self.search_backend_name,
            "paginate_by": self.list_per_page,
            "default_ordering": self.ordering,
            **kwargs,
        }

    def get_add_view_kwargs(self, **kwargs):
        return {
            "form_class": self.get_form_class(),
            "template_name": self.create_template_name,
            **kwargs,
        }

    def get_edit_view_kwargs(self, **kwargs):
        return {
            "form_class": self.get_form_class(for_update=True),
            "template_name": self.edit_template_name,
            **kwargs,
        }

    def get_delete_view_kwargs(self, **kwargs):
        return {
            "template_name": self.delete_template_name,
            **kwargs,
        }

    def get_history_view_kwargs(self, **kwargs):
        return {
            "template_name": self.history_template_name,
            "header_icon": "history",
            **kwargs,
        }

    def get_usage_view_kwargs(self, **kwargs):
        return {
            "template_name": self.get_templates(
                "usage", fallback=self.usage_view_class.template_name
            ),
            **kwargs,
        }

    def get_inspect_view_kwargs(self, **kwargs):
        return {
            "template_name": self.inspect_template_name,
            "fields": self.inspect_view_fields,
            "fields_exclude": self.inspect_view_fields_exclude,
            **kwargs,
        }

    @property
    def index_view(self):
        return self.construct_view(
            self.index_view_class, **self.get_index_view_kwargs()
        )

    @property
    def index_results_view(self):
        return self.construct_view(
            self.index_view_class, **self.get_index_view_kwargs(), results_only=True
        )

    @property
    def add_view(self):
        return self.construct_view(self.add_view_class, **self.get_add_view_kwargs())

    @property
    def edit_view(self):
        return self.construct_view(self.edit_view_class, **self.get_edit_view_kwargs())

    @property
    def delete_view(self):
        return self.construct_view(
            self.delete_view_class, **self.get_delete_view_kwargs()
        )

    @property
    def redirect_to_edit_view(self):
        def redirect_to_edit(request, pk):
            warn(
                (
                    "%s's `/<pk>/` edit view URL pattern has been "
                    "deprecated in favour of /edit/<pk>/."
                )
                % (self.__class__.__name__),
                category=RemovedInWagtail60Warning,
            )
            return redirect(self.get_url_name("edit"), pk, permanent=True)

        return redirect_to_edit

    @property
    def redirect_to_delete_view(self):
        def redirect_to_delete(request, pk):
            warn(
                (
                    "%s's `/<pk>/delete/` delete view URL pattern has been "
                    "deprecated in favour of /delete/<pk>/."
                )
                % (self.__class__.__name__),
                category=RemovedInWagtail60Warning,
            )
            return redirect(self.get_url_name("delete"), pk, permanent=True)

        return redirect_to_delete

    @property
    def history_view(self):
        return self.construct_view(
            self.history_view_class, **self.get_history_view_kwargs()
        )

    @property
    def usage_view(self):
        return self.construct_view(
            self.usage_view_class, **self.get_usage_view_kwargs()
        )

    @property
    def inspect_view(self):
        return self.construct_view(
            self.inspect_view_class, **self.get_inspect_view_kwargs()
        )

    def get_templates(self, name="index", fallback=""):
        """
        Utility function that provides a list of templates to try for a given
        view, when the template isn't overridden by one of the template
        attributes on the class.
        """
        if not self.template_prefix:
            return [fallback]
        templates = [
            f"{self.template_prefix}{self.app_label}/{self.model_name}/{name}.html",
            f"{self.template_prefix}{self.app_label}/{name}.html",
            f"{self.template_prefix}{name}.html",
        ]
        if fallback:
            templates.append(fallback)
        return templates

    @cached_property
    def index_template_name(self):
        """
        A template to be used when rendering ``index_view``.

        Default: if :attr:`template_prefix` is specified, an ``index.html``
        template in the prefix directory and its ``{app_label}/{model_name}/``
        or ``{app_label}/`` subdirectories will be used. Otherwise, the
        ``index_view_class.template_name`` will be used.
        """
        return self.get_templates(
            "index",
            fallback=self.index_view_class.template_name,
        )

    @cached_property
    def index_results_template_name(self):
        """
        A template to be used when rendering ``index_results_view``.

        Default: if :attr:`template_prefix` is specified, a ``index_results.html``
        template in the prefix directory and its ``{app_label}/{model_name}/``
        or ``{app_label}/`` subdirectories will be used. Otherwise, the
        ``index_view_class.results_template_name`` will be used.
        """
        return self.get_templates(
            "index_results",
            fallback=self.index_view_class.results_template_name,
        )

    @cached_property
    def create_template_name(self):
        """
        A template to be used when rendering ``add_view``.

        Default: if :attr:`template_prefix` is specified, a ``create.html``
        template in the prefix directory and its ``{app_label}/{model_name}/``
        or ``{app_label}/`` subdirectories will be used. Otherwise, the
        ``add_view_class.template_name`` will be used.
        """
        return self.get_templates(
            "create",
            fallback=self.add_view_class.template_name,
        )

    @cached_property
    def edit_template_name(self):
        """
        A template to be used when rendering ``edit_view``.

        Default: if :attr:`template_prefix` is specified, an ``edit.html``
        template in the prefix directory and its ``{app_label}/{model_name}/``
        or ``{app_label}/`` subdirectories will be used. Otherwise, the
        ``edit_view_class.template_name`` will be used.
        """
        return self.get_templates(
            "edit",
            fallback=self.edit_view_class.template_name,
        )

    @cached_property
    def delete_template_name(self):
        """
        A template to be used when rendering ``delete_view``.

        Default: if :attr:`template_prefix` is specified, a ``confirm_delete.html``
        template in the prefix directory and its ``{app_label}/{model_name}/``
        or ``{app_label}/`` subdirectories will be used. Otherwise, the
        ``delete_view_class.template_name`` will be used.
        """
        return self.get_templates(
            "confirm_delete",
            fallback=self.delete_view_class.template_name,
        )

    @cached_property
    def history_template_name(self):
        """
        A template to be used when rendering ``history_view``.

        Default: if :attr:`template_prefix` is specified, a ``history.html``
        template in the prefix directory and its ``{app_label}/{model_name}/``
        or ``{app_label}/`` subdirectories will be used. Otherwise, the
        ``history_view_class.template_name`` will be used.
        """
        return self.get_templates(
            "history",
            fallback=self.history_view_class.template_name,
        )

    @cached_property
    def inspect_template_name(self):
        """
        A template to be used when rendering ``inspect_view``.

        Default: if :attr:`template_prefix` is specified, an ``inspect.html``
        template in the prefix directory and its ``{app_label}/{model_name}/``
        or ``{app_label}/`` subdirectories will be used. Otherwise, the
        ``inspect_view_class.template_name`` will be used.
        """
        return self.get_templates(
            "inspect",
            fallback=self.inspect_view_class.template_name,
        )

    @cached_property
    def list_display(self):
        """
        A list or tuple, where each item is either:

        - The name of a field on the model;
        - The name of a callable or property on the model that accepts a single
          parameter for the model instance; or
        - An instance of the ``wagtail.admin.ui.tables.Column`` class.

        If the name refers to a database field, the ability to sort the listing
        by the database column will be offerred and the field's verbose name
        will be used as the column header.

        If the name refers to a callable or property, an ``admin_order_field``
        attribute can be defined on it to point to the database column for
        sorting. A ``short_description`` attribute can also be defined on the
        callable or property to be used as the column header.

        This list will be passed to the ``list_display`` attribute of the index
        view. If left unset, the ``list_display`` attribute of the index view
        will be used instead, which by default is defined as
        ``["__str__", wagtail.admin.ui.tables.UpdatedAtColumn()]``.
        """
        return self.index_view_class.list_display

    @cached_property
    def list_filter(self):
        """
        A list or tuple, where each item is the name of model fields of type
        ``BooleanField``, ``CharField``, ``DateField``, ``DateTimeField``,
        ``IntegerField`` or ``ForeignKey``.
        Alternatively, it can also be a dictionary that maps a field name to a
        list of lookup expressions.
        This will be passed as django-filter's ``FilterSet.Meta.fields``
        attribute. See
        `its documentation <https://django-filter.readthedocs.io/en/stable/guide/usage.html#generating-filters-with-meta-fields>`_
        for more details.
        If ``filterset_class`` is set, this attribute will be ignored.
        """
        return self.index_view_class.list_filter

    @cached_property
    def filterset_class(self):
        """
        A subclass of ``wagtail.admin.filters.WagtailFilterSet``, which is a
        subclass of `django_filters.FilterSet <https://django-filter.readthedocs.io/en/stable/ref/filterset.html>`_.
        This will be passed to the ``filterset_class`` attribute of the index view.
        """
        return self.index_view_class.filterset_class

    @cached_property
    def search_fields(self):
        """
        The fields to use for the search in the index view.
        If set to ``None`` and :attr:`search_backend_name` is set to use a Wagtail search backend,
        the ``search_fields`` attribute of the model will be used instead.
        """
        return self.index_view_class.search_fields

    @cached_property
    def search_backend_name(self):
        """
        The name of the Wagtail search backend to use for the search in the index view.
        If set to a falsy value, the search will fall back to use Django's QuerySet API.
        """
        return self.index_view_class.search_backend_name

    @cached_property
    def list_export(self):
        """
        A list or tuple, where each item is the name of a field, an attribute,
        or a single-argument callable on the model to be exported.
        """
        return self.index_view_class.list_export

    @cached_property
    def export_headings(self):
        """
        A dictionary of export column heading overrides in the format
        ``{field_name: heading}``.
        """
        return self.index_view_class.export_headings

    @cached_property
    def export_filename(self):
        """
        The base file name for the exported listing, without extensions.
        If unset, the model's :attr:`~django.db.models.Options.db_table` will be
        used instead.
        """
        return self.model._meta.db_table

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
        urlpatterns = [
            path("", self.index_view, name="index"),
            path("results/", self.index_results_view, name="index_results"),
            path("new/", self.add_view, name="add"),
            path("edit/<str:pk>/", self.edit_view, name="edit"),
            path("delete/<str:pk>/", self.delete_view, name="delete"),
            path("history/<str:pk>/", self.history_view, name="history"),
            path("usage/<str:pk>/", self.usage_view, name="usage"),
        ]

        if self.inspect_view_enabled:
            urlpatterns.append(
                path("inspect/<str:pk>/", self.inspect_view, name="inspect")
            )

        # RemovedInWagtail60Warning: Remove legacy URL patterns
        urlpatterns += self._legacy_urlpatterns

        return urlpatterns

    @cached_property
    def _legacy_urlpatterns(self):
        # RemovedInWagtail60Warning: Remove legacy URL patterns
        return [
            path("<int:pk>/", self.redirect_to_edit_view),
            path("<int:pk>/delete/", self.redirect_to_delete_view),
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
