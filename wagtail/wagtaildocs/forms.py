from django import forms

from wagtail.wagtaildocs.models import Document


class DocumentForm(forms.ModelForm):
    required_css_class = "required"

    class Meta:
        model = Document
        fields = ('title', 'file', 'tags')
        widgets = {
            'file': forms.FileInput()
        }
