# Testing documents

This page covers a few common patterns when writing tests for custom document
models and forms.

## Testing document upload forms

When testing document upload forms, uploaded files need to be passed using the
`files` argument of the form constructor. Passing files inside `data` will not
trigger Django’s file upload handling.

Example:

```python
from django.core.files.uploadedfile import SimpleUploadedFile
from wagtail.documents import models
from wagtail.documents.forms import get_document_form

form_data = {
    "title": "Simple Text Document",
}

file_data = {
    "file": SimpleUploadedFile(
        "simple-document.txt",
        b"hello world",
        content_type="text/plain",
    ),
}

form = get_document_form(models.Document)(form_data, file_data)
assert form.is_valid()
```
