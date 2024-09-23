# Custom document upload form

Wagtail provides a way to use a custom document form by modifying the [`WAGTAILDOCS_DOCUMENT_FORM_BASE`](wagtaildocs_document_form_base) setting. This setting allows you to extend the default document form with your custom fields and logic.

Here's an example:

```python
# settings.py
WAGTAILDOCS_DOCUMENT_FORM_BASE = 'myapp.forms.CustomDocumentForm'
```

```python
# myapp/forms.py
from django import forms

from wagtail.documents.forms import BaseDocumentForm

class CustomDocumentForm(BaseDocumentForm):
    terms_and_conditions = forms.BooleanField(
        label="I confirm that this document was not created by AI.",
        required=True,
    )

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("terms_and_conditions"):
            raise forms.ValidationError(
                "You must confirm the document was not created by AI."
            )
        return cleaned_data
```

```{note}
Any custom document form should extend the built-in `BaseDocumentForm` class.
```
