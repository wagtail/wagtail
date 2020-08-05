from django import forms
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from wagtail.admin.staticfiles import versioned_static
from wagtail.core.models import Site


class SiteSwitchForm(forms.Form):
    site = forms.ChoiceField(choices=[])

    @property
    def media(self):
        return forms.Media(js=[
            versioned_static('wagtailsettings/js/site-switcher.js'),
        ])

    def __init__(self, current_site, model, **kwargs):
        initial_data = {'site': self.get_change_url(current_site, model)}
        super().__init__(initial=initial_data, **kwargs)
        self.fields["site"].choices = [
            (
                self.get_change_url(site, model),
                (
                    site.hostname + " [{}]".format(_("default"))
                    if site.is_default_site
                    else site.hostname
                ),
            )
            for site in Site.objects.all()
        ]

    @classmethod
    def get_change_url(cls, site, model):
        return reverse('wagtailsettings:edit', args=[
            model._meta.app_label, model._meta.model_name, site.pk])
