# Testing documents

This page covers a few common patterns when writing tests for custom document
models and forms.

## Testing document upload forms

When testing document upload forms, uploaded files need to be passed using the
`files` argument of the form constructor. Passing files inside `data` will not
trigger Django’s file upload handling.

Example:

```python
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from wagtail.documents import models
from wagtail.documents.forms import get_document_form


class CustomDocumentFormTest(TestCase):
    def test_limit_upload_file_size(self):
        form_data = {
            "title": "Simple Text Document",
            "tags": [],
        }
        file_data = {
            "file": SimpleUploadedFile('simple.txt', b'hello world' * 1024 * 1024, content_type='text/plain'),
        }
        form_cls = get_document_form(models.Document)
        form = form_cls(form_data, file_data)
        self.assertFormError(
            form, 'file', ['The file size exceeds the configured limit (1MB).']
        )
```
