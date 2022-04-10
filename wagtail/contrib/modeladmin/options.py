from warnings import warn

from django.conf import settings
from django.contrib.admin import site as default_django_admin_site
from django.contrib.auth.models import Permission
from django.core import checks
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model
from django.urls import re_path
from django.utils.safestring import mark_safe

from wagtail import hooks
from wagtail.admin.admin_url_finder import register_admin_url_finder
from wagtail.admin.checks import check_panels_in_model
from wagtail.admin.panels import ObjectList, extract_panel_definitions_from_model_class
from wagtail.models import Page, TranslatableMixin
from wagtail.utils.deprecation import RemovedInWagtail50Warning

from .helpers import (
    AdminURLHelper,
    ButtonHelper,
    DjangoORMSearchHandler,
    ModelAdminURLFinder,
    PageAdminURLHelper,
    PageButtonHelper,
    PagePermissionHelper,
    PermissionHelper,
)
from .menus import GroupMenuItem, ModelAdminMenuItem, SubMenu
from .mixins import ThumbnailMixin  # NOQA
from .views import (
    ChooseParentView,
    CreateView,
    DeleteView,
    EditView,
    HistoryView,
    IndexView,
    InspectView,
)


class WagtailRegisterable:
    """
    Base class, providing a more convenient way for ModelAdmin or
    ModelAdminGroup instances to be registered with Wagtail's admin area.
    """

    add_to_settings_menu = False
    exclude_from_explorer = False

    def register_with_wagtail(self):
        @hooks.register("register_permissions")
        def register_permissions():
            return self.get_permissions_for_registration()

        @hooks.register("register_admin_urls")
        def register_admin_urls():
            return self.get_admin_urls_for_registration()

        menu_hook = (
            "register_settings_menu_item"
            if self.add_to_settings_menu
            else "register_admin_menu_item"
        )

        @hooks.register(menu_hook)
        def register_admin_menu_item():
            return self.get_menu_item()

        # Overriding the explorer page queryset is a somewhat 'niche' / experimental
        # operation, so only attach that hook if we specifically opt into it
        # by returning True from will_modify_explorer_page_queryset
        if self.will_modify_explorer_page_queryset():

            @hooks.register("construct_explorer_page_queryset")
            def construct_explorer_page_queryset(parent_page, queryset, request):
                return self.modify_explorer_page_queryset(
                    parent_page, queryset, request
                )

        self.register_admin_url_finders()

    def register_admin_url_finders(self):
        pass

    def will_modify_explorer_page_queryset(self):
        return False


class ModelAdmin(WagtailRegisterable):
    """
    The core modeladmin class. It provides an alternative means to
    list and manage instances of a given 'model' within Wagtail's admin area.
    It is essentially comprised of attributes and methods that allow a degree
    of control over how the data is represented, and other methods to make the
    additional functionality available via various Wagtail hooks.
    """

    model = None
    menu_label = None
    menu_icon = None
    menu_order = None
    list_display = ("__str__",)
    list_display_add_buttons = None
    list_export = ()
    inspect_view_fields = []
    inspect_view_fields_exclude = []
    inspect_view_enabled = False
    history_view_enabled = True
    empty_value_display = "-"
    list_filter = ()
    list_select_related = False
    list_per_page = 100
    search_fields = None
    ordering = None
    parent = None
    prepopulated_fields = {}
    index_view_class = IndexView
    create_view_class = CreateView
    edit_view_class = EditView
    inspect_view_class = InspectView
    delete_view_class = DeleteView
    history_view_class = HistoryView
    choose_parent_view_class = ChooseParentView
    index_template_name = ""
    create_template_name = ""
    edit_template_name = ""
    inspect_template_name = ""
    delete_template_name = ""
    history_template_name = ""
    choose_parent_template_name = ""
    search_handler_class = DjangoORMSearchHandler
    extra_search_kwargs = {}
    permission_helper_class = None
    url_helper_class = None
    button_helper_class = None
    index_view_extra_css = []
    index_view_extra_js = []
    inspect_view_extra_css = []
    inspect_view_extra_js = []
    form_view_extra_css = []
    form_view_extra_js = []
    form_fields_exclude = []

    def __init__(self, parent=None):
        """
        Don't allow initialisation unless self.model is set to a valid model
        """
        if not self.model or not issubclass(self.model, Model):
            raise ImproperlyConfigured(
                "The model attribute on your '%s' class must be set, and "
                "must be a valid Django model." % self.__class__.__name__
            )
        self.opts = self.model._meta
        self.is_pagemodel = issubclass(self.model, Page)
        self.parent = parent
        self.permission_helper = self.get_permission_helper_class()(
            self.model, self.inspect_view_enabled
        )
        self.url_helper = self.get_url_helper_class()(self.model)

        # Needed to support RelatedFieldListFilter
        # See: https://github.com/wagtail/wagtail/issues/5105
        self.admin_site = default_django_admin_site

    def get_permission_helper_class(self):
        """
        Returns a permission_helper class to help with permission-based logic
        for the given model.
        """
        if self.permission_helper_class:
            return self.permission_helper_class
        if self.is_pagemodel:
            return PagePermissionHelper
        return PermissionHelper

    def get_url_helper_class(self):
        if self.url_helper_class:
            return self.url_helper_class
        if self.is_pagemodel:
            return PageAdminURLHelper
        return AdminURLHelper

    def get_button_helper_class(self):
        """
        Returns a ButtonHelper class to help generate buttons for the given
        model.
        """
        if self.button_helper_class:
            return self.button_helper_class
        if self.is_pagemodel:
            return PageButtonHelper
        return ButtonHelper

    def get_menu_label(self):
        """
        Returns the label text to be used for the menu item.
        """
        return self.menu_label or self.opts.verbose_name_plural.title()

    def get_menu_icon(self):
        """
        Returns the icon to be used for the menu item. The value is prepended
        with 'icon-' to create the full icon class name. For design
        consistency, the same icon is also applied to the main heading for
        views called by this class.
        """
        if self.menu_icon:
            return self.menu_icon
        if self.is_pagemodel:
            return "doc-full-inverse"
        return "snippet"

    def get_menu_order(self):
        """
        Returns the 'order' to be applied to the menu item. 000 being first
        place. Where ModelAdminGroup is used, the menu_order value should be
        applied to that, and any ModelAdmin classes added to 'items'
        attribute will be ordered automatically, based on their order in that
        sequence.
        """
        return self.menu_order or 999

    def get_list_display(self, request):
        """
        Return a sequence containing the fields/method output to be displayed
        in the list view.
        """
        return self.list_display

    def get_list_display_add_buttons(self, request):
        """
        Return the name of the field/method from list_display where action
        buttons should be added. Defaults to the first item from
        get_list_display()
        """
        return self.list_display_add_buttons or self.get_list_display(request)[0]

    def get_list_export(self, request):
        """
        Return a sequence containing the fields/method output to be displayed
        in spreadsheet exports.
        """
        return self.list_export

    def get_empty_value_display(self, field_name=None):
        """
        Return the empty_value_display value defined on ModelAdmin
        """
        return mark_safe(self.empty_value_display)

    def get_list_filter(self, request):
        """
        Returns a sequence containing the fields to be displayed as filters in
        the right sidebar in the list view.
        """
        list_filter = self.list_filter

        if (
            getattr(settings, "WAGTAIL_I18N_ENABLED", False)
            and issubclass(self.model, TranslatableMixin)
            and "locale" not in list_filter
        ):
            list_filter += ("locale",)

        return list_filter

    def get_ordering(self, request):
        """
        Returns a sequence defining the default ordering for results in the
        list view.
        """
        return self.ordering or ()

    def get_queryset(self, request):
        """
        Returns a QuerySet of all model instances that can be edited by the
        admin site.
        """
        qs = self.model._default_manager.get_queryset()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        if self.is_pagemodel:
            # If we're listing pages, exclude the root page
            qs = qs.exclude(depth=1)
        return qs

    def get_search_fields(self, request):
        """
        Returns a sequence defining which fields on a model should be searched
        when a search is initiated from the list view.
        """
        return self.search_fields or ()

    def get_search_handler(self, request, search_fields=None):
        """
        Returns an instance of ``self.search_handler_class`` that can be used by
        ``IndexView``.
        """
        return self.search_handler_class(
            search_fields or self.get_search_fields(request)
        )

    def get_extra_search_kwargs(self, request, search_term):
        """
        Returns a dictionary of additional kwargs to be sent to
        ``SearchHandler.search_queryset()``.
        """
        return self.extra_search_kwargs

    def get_extra_attrs_for_row(self, obj, context):
        """
        Return a dictionary of HTML attributes to be added to the `<tr>`
        element for the suppled `obj` when rendering the results table in
        `index_view`. `data-object-pk` is already added by default.
        """
        return {}

    def get_extra_class_names_for_field_col(self, obj, field_name):
        """
        Return a list of additional CSS class names to be added to the table
        cell's `class` attribute when rendering the output of `field_name` for
        `obj` in `index_view`.

        Must always return a list.
        """
        return []

    def get_extra_attrs_for_field_col(self, obj, field_name):
        """
        Return a dictionary of additional HTML attributes to be added to a
        table cell when rendering the output of `field_name` for `obj` in
        `index_view`.

        Must always return a dictionary.
        """
        return {}

    def get_prepopulated_fields(self, request):
        """
        Returns a sequence specifying custom prepopulated fields slugs on Create/Edit pages.
        """
        return self.prepopulated_fields or {}

    # RemovedInWagtail50Warning - remove request arg, included here so that old-style super()
    # calls will still work
    def get_form_fields_exclude(self, request=None):
        """
        Returns a list or tuple of fields names to be excluded from Create/Edit pages.
        """
        return self.form_fields_exclude

    def get_index_view_extra_css(self):
        css = ["wagtailmodeladmin/css/index.css"]
        css.extend(self.index_view_extra_css)
        return css

    def get_index_view_extra_js(self):
        return self.index_view_extra_js

    def get_form_view_extra_css(self):
        return self.form_view_extra_css

    def get_form_view_extra_js(self):
        return self.form_view_extra_js

    def get_inspect_view_extra_css(self):
        return self.inspect_view_extra_css

    def get_inspect_view_extra_js(self):
        return self.inspect_view_extra_js

    def get_inspect_view_fields(self):
        """
        Return a list of field names, indicating the model fields that
        should be displayed in the 'inspect' view. Returns the value of the
        'inspect_view_fields' attribute if populated, otherwise a sensible
        list of fields is generated automatically, with any field named in
        'inspect_view_fields_exclude' not being included.
        """
        if not self.inspect_view_fields:
            found_fields = []
            for f in self.model._meta.get_fields():
                if f.name not in self.inspect_view_fields_exclude:
                    if f.concrete and (
                        not f.is_relation or (not f.auto_created and f.related_model)
                    ):
                        found_fields.append(f.name)
            return found_fields
        return self.inspect_view_fields

    def index_view(self, request):
        """
        Instantiates a class-based view to provide listing functionality for
        the assigned model. The view class used can be overridden by changing
        the 'index_view_class' attribute.
        """
        kwargs = {"model_admin": self}
        view_class = self.index_view_class
        return view_class.as_view(**kwargs)(request)

    def create_view(self, request):
        """
        Instantiates a class-based view to provide 'creation' functionality for
        the assigned model, or redirect to Wagtail's create view if the
        assigned model extends 'Page'. The view class used can be overridden by
        changing the 'create_view_class' attribute.
        """
        kwargs = {"model_admin": self}
        view_class = self.create_view_class
        return view_class.as_view(**kwargs)(request)

    def choose_parent_view(self, request):
        """
        Instantiates a class-based view to allows a parent page to be chosen
        for a new object, where the assigned model extends Wagtail's Page
        model, and there is more than one potential parent for new instances.
        The view class used can be overridden by changing the
        'choose_parent_view_class' attribute.
        """
        kwargs = {"model_admin": self}
        view_class = self.choose_parent_view_class
        return view_class.as_view(**kwargs)(request)

    def inspect_view(self, request, instance_pk):
        """
        Instantiates a class-based view to provide 'inspect' functionality for
        the assigned model. The view class used can be overridden by changing
        the 'inspect_view_class' attribute.
        """
        kwargs = {"model_admin": self, "instance_pk": instance_pk}
        view_class = self.inspect_view_class
        return view_class.as_view(**kwargs)(request)

    def edit_view(self, request, instance_pk):
        """
        Instantiates a class-based view to provide 'edit' functionality for the
        assigned model, or redirect to Wagtail's edit view if the assigned
        model extends 'Page'. The view class used can be overridden by changing
        the  'edit_view_class' attribute.
        """
        kwargs = {"model_admin": self, "instance_pk": instance_pk}
        view_class = self.edit_view_class
        return view_class.as_view(**kwargs)(request)

    def delete_view(self, request, instance_pk):
        """
        Instantiates a class-based view to provide 'delete confirmation'
        functionality for the assigned model, or redirect to Wagtail's delete
        confirmation view if the assigned model extends 'Page'. The view class
        used can be overridden by changing the 'delete_view_class'
        attribute.
        """
        kwargs = {"model_admin": self, "instance_pk": instance_pk}
        view_class = self.delete_view_class
        return view_class.as_view(**kwargs)(request)

    def history_view(self, request, instance_pk):
        kwargs = {"model_admin": self, "instance_pk": instance_pk}
        view_class = self.history_view_class
        return view_class.as_view(**kwargs)(request)

    # RemovedInWagtail50Warning - remove instance and request args, included here so that
    # old-style super() calls will still work
    def get_edit_handler(self, instance=None, request=None):
        """
        Returns the appropriate edit_handler for this modeladmin class.
        edit_handlers can be defined either on the model itself or on the
        modeladmin (as property edit_handler or panels). Falls back to
        extracting panel / edit handler definitions from the model class.
        """
        if hasattr(self, "edit_handler"):
            edit_handler = self.edit_handler
        elif hasattr(self, "panels"):
            panels = self.panels
            edit_handler = ObjectList(panels)
        elif hasattr(self.model, "edit_handler"):
            edit_handler = self.model.edit_handler
        elif hasattr(self.model, "panels"):
            panels = self.model.panels
            edit_handler = ObjectList(panels)
        else:
            try:
                fields_to_exclude = self.get_form_fields_exclude()
            except TypeError:
                fields_to_exclude = self.get_form_fields_exclude(request=None)
                warn(
                    "%s.get_form_fields_exclude should not accept a request argument"
                    % type(self).__name__,
                    category=RemovedInWagtail50Warning,
                )

            panels = extract_panel_definitions_from_model_class(
                self.model, exclude=fields_to_exclude
            )
            edit_handler = ObjectList(panels)
        return edit_handler

    def get_templates(self, action="index"):
        """
        Utility function that provides a list of templates to try for a given
        view, when the template isn't overridden by one of the template
        attributes on the class.
        """
        app_label = self.opts.app_label.lower()
        model_name = self.opts.model_name.lower()
        return [
            "modeladmin/%s/%s/%s.html" % (app_label, model_name, action),
            "modeladmin/%s/%s.html" % (app_label, action),
            "modeladmin/%s.html" % (action,),
        ]

    def get_index_template(self):
        """
        Returns a template to be used when rendering 'index_view'. If a
        template is specified by the 'index_template_name' attribute, that will
        be used. Otherwise, a list of preferred template names are returned.
        """
        return self.index_template_name or self.get_templates("index")

    def get_choose_parent_template(self):
        """
        Returns a template to be used when rendering 'choose_parent_view'. If a
        template is specified by the 'choose_parent_template_name' attribute,
        that will be used. Otherwise, a list of preferred template names are
        returned.
        """
        return self.choose_parent_template_name or self.get_templates("choose_parent")

    def get_inspect_template(self):
        """
        Returns a template to be used when rendering 'inspect_view'. If a
        template is specified by the 'inspect_template_name' attribute, that
        will be used. Otherwise, a list of preferred template names are
        returned.
        """
        return self.inspect_template_name or self.get_templates("inspect")

    def get_history_template(self):
        """
        Returns a template to be used when rendering 'history_view'. If a
        template is specified by the 'history_template_name' attribute, that
        will be used. Otherwise, a list of preferred template names are
        returned.
        """
        return self.history_template_name or self.get_templates("history")

    def get_create_template(self):
        """
        Returns a template to be used when rendering 'create_view'. If a
        template is specified by the 'create_template_name' attribute,
        that will be used. Otherwise, a list of preferred template names are
        returned.
        """
        return self.create_template_name or self.get_templates("create")

    def get_edit_template(self):
        """
        Returns a template to be used when rendering 'edit_view'. If a template
        is specified by the 'edit_template_name' attribute, that will be used.
        Otherwise, a list of preferred template names are returned.
        """
        return self.edit_template_name or self.get_templates("edit")

    def get_delete_template(self):
        """
        Returns a template to be used when rendering 'delete_view'. If
        a template is specified by the 'delete_template_name'
        attribute, that will be used. Otherwise, a list of preferred template
        names are returned.
        """
        return self.delete_template_name or self.get_templates("delete")

    def get_menu_item(self, order=None):
        """
        Utilised by Wagtail's 'register_menu_item' hook to create a menu item
        to access the listing view, or can be called by ModelAdminGroup
        to create a SubMenu
        """
        return ModelAdminMenuItem(self, order or self.get_menu_order())

    def get_permissions_for_registration(self):
        """
        Utilised by Wagtail's 'register_permissions' hook to allow permissions
        for a model to be assigned to groups in settings. This is only required
        if the model isn't a Page model, and isn't registered as a Snippet
        """
        from wagtail.snippets.models import SNIPPET_MODELS

        if not self.is_pagemodel and self.model not in SNIPPET_MODELS:
            return self.permission_helper.get_all_model_permissions()
        return Permission.objects.none()

    def get_admin_urls_for_registration(self):
        """
        Utilised by Wagtail's 'register_admin_urls' hook to register urls for
        our the views that class offers.
        """
        urls = (
            re_path(
                self.url_helper.get_action_url_pattern("index"),
                self.index_view,
                name=self.url_helper.get_action_url_name("index"),
            ),
            re_path(
                self.url_helper.get_action_url_pattern("create"),
                self.create_view,
                name=self.url_helper.get_action_url_name("create"),
            ),
            re_path(
                self.url_helper.get_action_url_pattern("edit"),
                self.edit_view,
                name=self.url_helper.get_action_url_name("edit"),
            ),
            re_path(
                self.url_helper.get_action_url_pattern("delete"),
                self.delete_view,
                name=self.url_helper.get_action_url_name("delete"),
            ),
        )
        if self.inspect_view_enabled:
            urls = urls + (
                re_path(
                    self.url_helper.get_action_url_pattern("inspect"),
                    self.inspect_view,
                    name=self.url_helper.get_action_url_name("inspect"),
                ),
            )
        if self.history_view_enabled:
            urls = urls + (
                re_path(
                    self.url_helper.get_action_url_pattern("history"),
                    self.history_view,
                    name=self.url_helper.get_action_url_name("history"),
                ),
            )
        if self.is_pagemodel:
            urls = urls + (
                re_path(
                    self.url_helper.get_action_url_pattern("choose_parent"),
                    self.choose_parent_view,
                    name=self.url_helper.get_action_url_name("choose_parent"),
                ),
            )
        return urls

    def will_modify_explorer_page_queryset(self):
        return self.is_pagemodel and self.exclude_from_explorer

    def modify_explorer_page_queryset(self, parent_page, queryset, request):
        if self.is_pagemodel and self.exclude_from_explorer:
            queryset = queryset.not_type(self.model)
        return queryset

    def register_with_wagtail(self):
        super().register_with_wagtail()

        @checks.register("panels")
        def modeladmin_model_check(app_configs, **kwargs):
            errors = check_panels_in_model(self.model, "modeladmin")
            return errors

    def register_admin_url_finders(self):
        if not self.is_pagemodel:
            finder_class = type(
                "_ModelAdminURLFinder",
                (ModelAdminURLFinder,),
                {
                    "permission_helper": self.permission_helper,
                    "url_helper": self.url_helper,
                },
            )
            register_admin_url_finder(self.model, finder_class)


class ModelAdminGroup(WagtailRegisterable):
    """
    Acts as a container for grouping together mutltiple PageModelAdmin and
    SnippetModelAdmin instances. Creates a menu item with a SubMenu for
    accessing the listing pages of those instances
    """

    items = ()
    menu_label = None
    menu_order = None
    menu_icon = None

    def __init__(self):
        """
        When initialising, instantiate the classes within 'items', and assign
        the instances to a 'modeladmin_instances' attribute for convenient
        access later
        """
        self.modeladmin_instances = []
        for ModelAdminClass in self.items:
            self.modeladmin_instances.append(ModelAdminClass(parent=self))

    def get_menu_label(self):
        return self.menu_label or self.get_app_label_from_subitems()

    def get_app_label_from_subitems(self):
        for instance in self.modeladmin_instances:
            return instance.opts.app_label.title()
        return ""

    def get_menu_icon(self):
        return self.menu_icon or "folder-open-inverse"

    def get_menu_order(self):
        return self.menu_order or 999

    def get_menu_item(self):
        """
        Utilised by Wagtail's 'register_menu_item' hook to create a menu
        for this group with a SubMenu linking to listing pages for any
        associated ModelAdmin instances
        """
        if self.modeladmin_instances:
            submenu = SubMenu(self.get_submenu_items())
            return GroupMenuItem(self, self.get_menu_order(), submenu)

    def get_submenu_items(self):
        menu_items = []
        item_order = 1
        for modeladmin in self.modeladmin_instances:
            menu_items.append(modeladmin.get_menu_item(order=item_order))
            item_order += 1
        return menu_items

    def get_permissions_for_registration(self):
        """
        Utilised by Wagtail's 'register_permissions' hook to allow permissions
        for a all models grouped by this class to be assigned to Groups in
        settings.
        """
        qs = Permission.objects.none()
        for instance in self.modeladmin_instances:
            qs = qs | instance.get_permissions_for_registration()
        return qs

    def get_admin_urls_for_registration(self):
        """
        Utilised by Wagtail's 'register_admin_urls' hook to register urls for
        used by any associated ModelAdmin instances
        """
        urls = ()
        for instance in self.modeladmin_instances:
            urls += instance.get_admin_urls_for_registration()
        return urls

    def will_modify_explorer_page_queryset(self):
        return any(
            instance.will_modify_explorer_page_queryset()
            for instance in self.modeladmin_instances
        )

    def modify_explorer_page_queryset(self, parent_page, queryset, request):
        for instance in self.modeladmin_instances:
            queryset = instance.modify_explorer_page_queryset(
                parent_page, queryset, request
            )
        return queryset

    def register_with_wagtail(self):
        super().register_with_wagtail()

        @checks.register("panels")
        def modeladmin_model_check(app_configs, **kwargs):
            errors = []
            for modeladmin_class in self.items:
                errors.extend(check_panels_in_model(modeladmin_class.model))
            return errors

    def register_admin_url_finders(self):
        for instance in self.modeladmin_instances:
            instance.register_admin_url_finders()


def modeladmin_register(modeladmin_class):
    """
    Method for registering ModelAdmin or ModelAdminGroup classes with Wagtail.
    """
    instance = modeladmin_class()
    instance.register_with_wagtail()
    return modeladmin_class
