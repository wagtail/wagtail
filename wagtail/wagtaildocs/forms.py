from django import forms

from wagtail.wagtaildocs.models import Document


class DocumentForm(forms.ModelForm):
    required_css_class = "required"

    class Meta:
        model = Document
        widgets = {
            'file': forms.FileInput()
        }
        exclude = tuple()
