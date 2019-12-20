from django import forms

from .models import Publisher


class PublisherModelAdminForm(forms.ModelForm):
    class Meta:
        model = Publisher
        fields = ["name"]
