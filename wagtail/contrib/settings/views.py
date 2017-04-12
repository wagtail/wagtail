from __future__ import absolute_import, unicode_literals

from django.contrib.admin.utils import quote, unquote
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from django.utils.text import capfirst
from django.utils.translation import ugettext as _

from wagtail.contrib.modeladmin.views import ModelFormView
from wagtail.wagtailcore.models import Site

from .forms import SiteSwitchForm


class SettingEditView(ModelFormView):
    site_pk = None

    def __init__(self, model_admin, site_pk):
        super(ModelFormView, self).__init__(model_admin)
        self.site_pk = unquote(site_pk)
        self.pk_quoted = quote(self.site_pk)

        # Get the site from the URL, and then find a setting for it
        self.site = get_object_or_404(Site, pk=self.site_pk)
        try:
            self.instance = self.model.objects.get(site=self.site)
        except self.model.DoesNotExist:
            self.instance = self.model(site=self.site)

    def get_page_subtitle(self):
        """
        Subtitle for setting edit view. If there are multiple sites, the site
        name is used as the subtitle, otherwise it is blank.
        """
        if Site.objects.count() > 1:
            return self.site.site_name or self.site.hostname
        return ''

    def get_context_data(self, **kwargs):
        """
        Context data for the setting edit view. Extends
        :meth:`ModelFormView.get_context_data` with a SiteSwitcher form if
        there is more than one site
        """
        site_switcher = None
        if Site.objects.count() > 1:
            site_switcher = SiteSwitchForm(
                self.site, self.model, self.model_admin.edit_url_name)

        context = {
            'site_switcher': site_switcher,
            'edit_url': reverse(self.model_admin.edit_url_name,
                                kwargs={'site_pk': self.site.pk})
        }
        context.update(kwargs)

        return super(SettingEditView, self).get_context_data(**context)

    def get_success_message_buttons(self, instance):
        # No buttons in the message, as the user stays on the page on success.
        return []

    def get_success_message(self, instance):
        return _("{setting_type} updated.").format(
            setting_type=capfirst(self.verbose_name))

    def get_success_url(self):
        """
        Redirect the user back to this view when they hit save.
        """
        return reverse(self.model_admin.edit_url_name, kwargs={
            'site_pk': self.get_instance().site.pk})

    def get_instance(self):
        return self.instance

    def get_template_names(self):
        return self.model_admin.get_edit_template()

    @cached_property
    def header_icon(self):
        return self.menu_icon
