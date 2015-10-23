from __future__ import absolute_import, unicode_literals

from django import forms
from django.core.urlresolvers import reverse

from wagtail.wagtailcore.models import Site


class SiteSwitchForm(forms.Form):
    site = forms.ChoiceField(choices=[])

    class Media:
        js = [
            'wagtailsettings/js/site-switcher.js',
        ]

    def __init__(self, current_site, model, **kwargs):
        initial_data = {'site': self.get_change_url(current_site, model)}
        super(SiteSwitchForm, self).__init__(initial=initial_data, **kwargs)
        sites = [(self.get_change_url(site, model), site)
                 for site in Site.objects.all()]
        self.fields['site'].choices = sites

    @classmethod
    def get_change_url(cls, site, model):
        return reverse('wagtailsettings:edit', args=[
            site.pk, model._meta.app_label, model._meta.model_name])
