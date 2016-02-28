from django.contrib.auth.models import Permission
from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model
from django.forms.widgets import flatatt
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

from wagtail.wagtailcore.models import Page
from wagtail.wagtailimages.models import Filter
from wagtail.wagtailcore import hooks

from .menus import ModelAdminMenuItem, GroupMenuItem, SubMenu
from .helpers import (
    PermissionHelper, PagePermissionHelper, ButtonHelper, PageButtonHelper,
    get_url_pattern, get_object_specific_url_pattern, get_url_name)
from .views import (
    IndexView, CreateView, ChooseParentView, EditView, ConfirmDeleteView,
    CopyRedirectView, UnpublishRedirectView)


class WagtailRegisterable(object):
    """
    Base class, providing a more convenient way for ModelAdmin or
    ModelAdminGroup instances to be registered with Wagtail's admin area.
    """
    add_to_settings_menu = False

    def register_with_wagtail(self):

        @hooks.register('register_permissions')
        def register_permissions():
            return self.get_permissions_for_registration()

        @hooks.register('register_admin_urls')
        def register_admin_urls():
            return self.get_admin_urls_for_registration()

        menu_hook = (
            'register_settings_menu_item' if self.add_to_settings_menu else
            'register_admin_menu_item'
        )

        @hooks.register(menu_hook)
        def register_admin_menu_item():
            return self.get_menu_item()


class ModelAdminThumbMixin(object):
    """
    Mixin class to help display thumbnail images in ModelAdmin listing results.
    `thumb_image_field_name` must be overridden to name a ForeignKey field on
    your model, linking to `wagtailimages.Image`.
    """
    thumb_image_field_name = 'image'
    thumb_image_filter_spec = 'fill-100x100'
    thumb_image_width = 50
    thumb_classname = 'admin-thumb'
    thumb_col_header_text = _('image')
    thumb_default = None

    def admin_thumb(self, obj):
        try:
            image = getattr(obj, self.thumb_image_field_name, None)
        except AttributeError:
            raise ImproperlyConfigured(
                u"The `thumb_image_field_name` attribute on your `%s` class "
                "must name a field on your model." % self.__class__.__name__
            )

        img_attrs = {
            'src': self.thumb_default,
            'width': self.thumb_image_width,
            'class': self.thumb_classname,
        }
        if image:
            fltr, _ = Filter.objects.get_or_create(
                spec=self.thumb_image_filter_spec)
            img_attrs.update({'src': image.get_rendition(fltr).url})
            return mark_safe('<img{}>'.format(flatatt(img_attrs)))
        elif self.thumb_default:
            return mark_safe('<img{}>'.format(flatatt(img_attrs)))
        return ''
    admin_thumb.short_description = thumb_col_header_text


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
    list_display = ('__str__',)
    list_display_add_buttons = None
    empty_value_display = '-'
    list_filter = ()
    list_select_related = False
    list_per_page = 100
    search_fields = None
    ordering = None
    parent = None
    index_view_class = IndexView
    create_view_class = CreateView
    edit_view_class = EditView
    confirm_delete_view_class = ConfirmDeleteView
    choose_parent_view_class = ChooseParentView
    copy_view_class = CopyRedirectView
    unpublish_view_class = UnpublishRedirectView
    index_template_name = ''
    create_template_name = ''
    edit_template_name = ''
    confirm_delete_template_name = ''
    choose_parent_template_name = ''
    permission_helper_class = None
    button_helper_class = None
    index_view_extra_css = []
    index_view_extra_js = []
    form_view_extra_css = []
    form_view_extra_js = []

    def __init__(self, parent=None):
        """
        Don't allow initialisation unless self.model is set to a valid model
        """
        if not self.model or not issubclass(self.model, Model):
            raise ImproperlyConfigured(
                u"The model attribute on your '%s' class must be set, and "
                "must be a valid Django model." % self.__class__.__name__)
        self.opts = self.model._meta
        self.is_pagemodel = issubclass(self.model, Page)
        self.parent = parent
        permission_helper_class = self.get_permission_helper_class()
        self.permission_helper = permission_helper_class(self.model)


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
            return 'doc-full-inverse'
        return 'snippet'

    def get_menu_order(self):
        """
        Returns the 'order' to be applied to the menu item. 000 being first
        place. Where ModelAdminGroup is used, the menu_order value should be
        applied to that, and any ModelAdmin classes added to 'items'
        attribute will be ordered automatically, based on their order in that
        sequence.
        """
        return self.menu_order or 999

    def show_menu_item(self, request):
        """
        Returns a boolean indicating whether the menu item should be visible
        for the user in the supplied request, based on their permissions.
        """
        return self.permission_helper.allow_list_view(request.user)

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
        return self.list_display_add_buttons or self.get_list_display(
            request)[0]

    def get_empty_value_display(self, field_name):
        """
        Return the empty_value_display value defined on ModelAdmin
        """
        return mark_safe(self.empty_value_display)

    def get_list_filter(self, request):
        """
        Returns a sequence containing the fields to be displayed as filters in
        the right sidebar in the list view.
        """
        return self.list_filter

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
        return qs

    def get_search_fields(self, request):
        """
        Returns a sequence defining which fields on a model should be searched
        when a search is initiated from the list view.
        """
        return self.search_fields or ()

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

    def get_index_view_extra_css(self):
        css = ['wagtailmodeladmin/css/index.css']
        css.extend(self.index_view_extra_css)
        return css

    def get_index_view_extra_js(self):
        return self.index_view_extra_js

    def get_form_view_extra_css(self):
        return self.form_view_extra_js

    def get_form_view_extra_js(self):
        return self.form_view_extra_js

    def get_index_url(self):
        return reverse(get_url_name(self.opts))

    def get_choose_parent_url(self):
        return reverse(get_url_name(self.opts, 'choose_parent'))

    def get_create_url(self):
        return reverse(get_url_name(self.opts, 'create'))

    def index_view(self, request):
        """
        Instantiates a class-based view to provide listing functionality for
        the assigned model. The view class used can be overridden by changing
        the 'index_view_class' attribute.
        """
        kwargs = {'modeladmin': self}
        view_class = self.index_view_class
        return view_class.as_view(**kwargs)(request)

    def create_view(self, request):
        """
        Instantiates a class-based view to provide 'creation' functionality for
        the assigned model, or redirect to Wagtail's create view if the
        assigned model extends 'Page'. The view class used can be overridden by
        changing the 'create_view_class' attribute.
        """
        kwargs = {'modeladmin': self}
        view_class = self.create_view_class
        return view_class.as_view(**kwargs)(request)

    def choose_parent_view(self, request):
        """
        Instantiates a class-based view to provide a view that allows a parent
        page to be chosen for a new object, where the assigned model extends
        Wagtail's Page model, and there is more than one potential parent for
        new instances. The view class used can be overridden by changing the
        'choose_parent_view_class' attribute.
        """
        kwargs = {'modeladmin': self}
        view_class = self.choose_parent_view_class
        return view_class.as_view(**kwargs)(request)

    def edit_view(self, request, object_id):
        """
        Instantiates a class-based view to provide 'edit' functionality for the
        assigned model, or redirect to Wagtail's edit view if the assinged
        model extends 'Page'. The view class used can be overridden by changing
        the  'edit_view_class' attribute.
        """
        kwargs = {'modeladmin': self, 'object_id': object_id}
        view_class = self.edit_view_class
        return view_class.as_view(**kwargs)(request)

    def confirm_delete_view(self, request, object_id):
        """
        Instantiates a class-based view to provide 'delete confirmation'
        functionality for the assigned model, or redirect to Wagtail's delete
        confirmation view if the assinged model extends 'Page'. The view class
        used can be overridden by changing the 'confirm_delete_view_class'
        attribute.
        """
        kwargs = {'modeladmin': self, 'object_id': object_id}
        view_class = self.confirm_delete_view_class
        return view_class.as_view(**kwargs)(request)

    def unpublish_view(self, request, object_id):
        """
        Instantiates a class-based view that redirects to Wagtail's 'unpublish'
        view for models that extend 'Page' (if the user has sufficient
        permissions). We do this via our own view so that we can reliably
        control redirection of the user back to the index_view once the action
        is completed. The view class used can be overridden by changing the
        'unpublish_view_class' attribute.
        """
        kwargs = {'modeladmin': self, 'object_id': object_id}
        view_class = self.unpublish_view_class
        return view_class.as_view(**kwargs)(request)

    def copy_view(self, request, object_id):
        """
        Instantiates a class-based view that redirects to Wagtail's 'copy'
        view for models that extend 'Page' (if the user has sufficient
        permissions). We do this via our own view so that we can reliably
        control redirection of the user back to the index_view once the action
        is completed. The view class used can be overridden by changing the
        'copy_view_class' attribute.
        """
        kwargs = {'modeladmin': self, 'object_id': object_id}
        view_class = self.copy_view_class
        return view_class.as_view(**kwargs)(request)

    def get_templates(self, action='index'):
        """
        Utility funtion that provides a list of templates to try for a given
        view, when the template isn't overridden by one of the template
        attributes on the class.
        """
        app = self.opts.app_label
        model_name = self.opts.model_name
        return [
            'modeladmin/%s/%s/%s.html' % (app, model_name, action),
            'modeladmin/%s/%s.html' % (app, action),
            'modeladmin/%s.html' % (action,),
        ]

    def get_index_template(self):
        """
        Returns a template to be used when rendering 'index_view'. If a
        template is specified by the 'index_template_name' attribute, that will
        be used. Otherwise, a list of preferred template names are returned,
        allowing custom templates to be used by simply putting them in a
        sensible location in an app's template directory.
        """
        return self.index_template_name or self.get_templates('index')

    def get_choose_parent_template(self):
        """
        Returns a template to be used when rendering 'choose_parent_view'. If a
        template is specified by the 'choose_parent_template_name' attribute,
        that will be used. Otherwise, a list of preferred template names are
        returned, allowing custom templates to be used by simply putting them
        in a sensible location in an app's template directory.
        """
        return self.choose_parent_template_name or self.get_templates(
            'choose_parent')

    def get_create_template(self):
        """
        Returns a template to be used when rendering 'create_view'. If a
        template is specified by the 'create_template_name' attribute,
        that will be used. Otherwise, a list of preferred template names is
        returned, allowing custom templates to be used by simply putting them
        in a sensible location in an app's template directory.
        """
        return self.create_template_name or self.get_templates('create')

    def get_edit_template(self):
        """
        Returns a template to be used when rendering 'edit_view'. If a template
        is specified by the 'edit_template_name' attribute, that will be used.
        Otherwise, a list of preferred template names is returned, allowing
        custom templates to be used by simply putting them in a sensible
        location in an app's template directory.
        """
        return self.edit_template_name or self.get_templates('edit')

    def get_confirm_delete_template(self):
        """
        Returns a template to be used when rendering 'confirm_delete_view'. If
        a template is specified by the 'confirm_delete_template_name'
        attribute, that will be used. Otherwise, a list of preferred template
        names is returned, allowing custom templates to be used by simply
        putting them in a sensible location in an app's template directory.
        """
        return self.confirm_delete_template_name or self.get_templates(
            'confirm_delete')

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
        from wagtail.wagtailsnippets.models import SNIPPET_MODELS
        if not self.is_pagemodel and self.model not in SNIPPET_MODELS:
            return Permission.objects.filter(
                content_type__app_label=self.opts.app_label,
                content_type__model=self.opts.model_name,
            )
        return Permission.objects.none()

    def get_admin_urls_for_registration(self):
        """
        Utilised by Wagtail's 'register_admin_urls' hook to register urls for
        our the views that class offers.
        """
        return [
            url(get_url_pattern(self.opts),
                self.index_view,
                name=get_url_name(self.opts)),

            url(get_url_pattern(self.opts, 'create'),
                self.create_view,
                name=get_url_name(self.opts, 'create')),

            url(get_url_pattern(self.opts, 'choose_parent'),
                self.choose_parent_view,
                name=get_url_name(self.opts, 'choose_parent')),

            url(get_object_specific_url_pattern(self.opts, 'edit'),
                self.edit_view,
                name=get_url_name(self.opts, 'edit')),

            url(get_object_specific_url_pattern(self.opts, 'confirm_delete'),
                self.confirm_delete_view,
                name=get_url_name(self.opts, 'confirm_delete')),

            url(get_object_specific_url_pattern(self.opts, 'unpublish'),
                self.unpublish_view,
                name=get_url_name(self.opts, 'unpublish')),

            url(get_object_specific_url_pattern(self.opts, 'copy'),
                self.copy_view,
                name=get_url_name(self.opts, 'copy')),
        ]


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
        the instances to a 'modeladmin_instances' attribute for convienient
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
        return ''

    def get_menu_icon(self):
        return self.menu_icon or 'icon-folder-open-inverse'

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
        urls = []
        for instance in self.modeladmin_instances:
            urls.extend(instance.get_admin_urls_for_registration())
        return urls


def modeladmin_register(modeladmin_class):
    """
    Method for registering ModelAdmin or ModelAdminGroup classes with Wagtail.
    """
    instance = modeladmin_class()
    instance.register_with_wagtail()
