from __future__ import absolute_import, unicode_literals

from django import forms

from .models import Publisher


class PublisherModelAdminForm(forms.ModelForm):
    class Meta:
        model = Publisher
        fields = ["name"]
