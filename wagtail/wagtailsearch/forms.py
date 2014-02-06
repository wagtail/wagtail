from django import forms
from django.forms.models import inlineformset_factory

import models


class QueryForm(forms.Form):
    query_string = forms.CharField(label='Search term(s)/phrase', help_text="Enter the full search string to match. An exact match is required for your Editors Picks to be displayed, wildcards are NOT allowed.", required=True)


class EditorsPickForm(forms.ModelForm):
    sort_order = forms.IntegerField(required=False)

    def __init__(self, *args, **kwargs):
        super(EditorsPickForm, self).__init__(*args, **kwargs)
        self.fields['page'].widget = forms.HiddenInput()

    class Meta:
        model = models.EditorsPick

        widgets = {
            'description': forms.Textarea(attrs=dict(rows=3)),
        }


EditorsPickFormSetBase = inlineformset_factory(models.Query, models.EditorsPick, form=EditorsPickForm, can_order=True, can_delete=True, extra=0)


class EditorsPickFormSet(EditorsPickFormSetBase):
    def add_fields(self, form, *args, **kwargs):
        super(EditorsPickFormSet, self).add_fields(form, *args, **kwargs)

        # Hide delete and order fields
        form.fields['DELETE'].widget = forms.HiddenInput()
        form.fields['ORDER'].widget = forms.HiddenInput()

        # Remove query field
        del form.fields['query']
