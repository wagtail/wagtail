from django import forms

import models


class RedirectForm(forms.ModelForm):
    required_css_class = "required"

    class Meta:
        model = models.Redirect
