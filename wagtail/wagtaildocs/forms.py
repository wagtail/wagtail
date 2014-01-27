from django import forms

from wagtail.wagtaildocs.models import Document


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        widgets = {
            'file': forms.FileInput()
        }
