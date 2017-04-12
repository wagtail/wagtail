from __future__ import absolute_import, unicode_literals

from django import forms
from django.core.urlresolvers import reverse

from wagtail.wagtailcore.models import Site


class SiteSwitchForm(forms.Form):
    site = forms.ChoiceField(choices=[])

    class Media:
        js = ['wagtailsettings/js/site-switcher.js']

    def __init__(self, current_site, model, url_name, **kwargs):
        initial_data = {'site': self.get_change_url(current_site, url_name)}

        super(SiteSwitchForm, self).__init__(initial=initial_data, **kwargs)

        sites = [(self.get_change_url(site, url_name), site)
                 for site in Site.objects.all()]
        self.fields['site'].choices = sites

    @classmethod
    def get_change_url(cls, site, url_name):
        return reverse(url_name, args=[site.pk])
