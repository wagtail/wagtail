from __future__ import absolute_import, unicode_literals

from django.conf.urls import url
from django.http import Http404
from django.shortcuts import redirect
from django.utils.text import capfirst

from wagtail.contrib.modeladmin.helpers import ButtonHelper, PermissionHelper
from wagtail.contrib.modeladmin.options import WagtailRegisterable
from wagtail.contrib.settings.menu import SettingMenuItem
from wagtail.contrib.settings.views import SettingEditView
from wagtail.wagtailcore.models import Site


class SettingAdmin(WagtailRegisterable):
    """ModelAdmin and Setting things TODO DOCUMENT BETTER WITH WORDS"""
    # The setting model this manages
    model = None

    # Customise these to change how the menu label appears
    menu_label = None
    menu_icon = 'cog'
    menu_order = 999

    # Override these to customise the edit view
    edit_view_class = SettingEditView
    edit_template_name = None

    # Default to adding to the settings menu.
    # This can be changed in the same way as other ModelAdmin classes.
    # If added as part of a ModelAdmin group, this setting is ignored.
    add_to_settings_menu = True

    parent = None
    permission_helper_class = PermissionHelper

    # Some attributes that model admin requires but are not actually used.
    inspect_view_enabled = False
    button_helper_class = ButtonHelper
    url_helper = None
    is_pagemodel = False

    @classmethod
    def for_setting(cls, setting, **attrs):
        """
        A shortcut for making a SettingAdmin subclass for a setting model.
        """
        name = str('{}SettingAdmin'.format(setting.__name__))
        bases = (cls,)
        attrs.update({'model': setting})

        return type(name, bases, attrs)

    def __init__(self, parent=None):
        self.parent = parent
        self.opts = self.model._meta

        self.permission_helper = self.get_permission_helper_class()(
            self.model, self.inspect_view_enabled)

    def edit_current_view(self, request):
        """A shortcut view that edits the setting for the current site"""
        # Redirect the user to the edit page for the current site
        # (or the current request does not correspond to a site, the first site
        # in the list)
        site = request.site or Site.objects.first()
        if site is None:
            raise Http404  # Can't edit settings for a site that don't exist
        return redirect(self.edit_url_name, site_pk=site.pk)

    def edit_view(self, request, site_pk):
        """
        Make a view that provides 'edit' functionality for the setting. The
        view class used can be overridden by changing the
        :attr:`edit_view_class` attribute.
        """
        kwargs = {'model_admin': self, 'site_pk': site_pk}
        view_class = self.edit_view_class
        return view_class.as_view(**kwargs)(request)

    def get_edit_template(self):
        """
        Returns a template to be used when rendering 'edit_view'. If a template
        is specified by the 'edit_template_name' attribute, that will be used.
        Otherwise, a list of preferred template names are returned.
        """
        if self.edit_template_name:
            return self.edit_template_name
        app_label = self.opts.app_label.lower()
        model_name = self.opts.model_name.lower()
        return [
            'wagtailsettings/{}/{}/edit.html'.format(app_label, model_name),
            'wagtailsettings/{}/edit.html'.format(app_label),
            'wagtailsettings/edit.html',
        ]

    def get_menu_icon(self):
        return self.menu_icon

    def get_menu_order(self):
        return self.menu_order

    def get_menu_label(self):
        return self.menu_label or capfirst(self.opts.verbose_name_plural)

    def get_menu_item(self, order=None):
        return SettingMenuItem(self, order=order or self.get_menu_order())

    @property
    def edit_url_name(self):
        return '{}_{}_setting_edit'.format(self.opts.app_label, self.opts.model_name)

    def get_admin_urls_for_registration(self):
        """Register a url named `<app>_<model>_setting_edit`."""
        app_label, model_name = self.opts.app_label, self.opts.model_name
        return (
            url(r'^{}/{}/$'.format(app_label, model_name),
                self.edit_current_view, name=self.edit_url_name),
            url(r'^{}/{}/(?P<site_pk>\d+)/$'.format(app_label, model_name),
                self.edit_view, name=self.edit_url_name),
        )

    def get_permission_helper_class(self):
        return self.permission_helper_class

    # Required by model admin, but not actually used
    def get_form_fields_exclude(self, request):
        return []

    def get_button_helper_class(self):
        """
        Returns a ButtonHelper class to help generate buttons for the given
        model.
        """
        return self.button_helper_class

    def modify_explorer_page_queryset(self, parent_page, queryset, request):
        return queryset
