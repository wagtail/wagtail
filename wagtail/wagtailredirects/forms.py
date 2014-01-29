from django import forms

import models


class RedirectForm(forms.ModelForm):
	class Meta:
		model = models.Redirect