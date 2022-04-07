(custom_document_model)=

# Custom document model

An alternate `Document` model can be used to add custom behaviour and
additional fields.

You need to complete the following steps in your project to do this:

-   Create a new document model that inherits from `wagtail.documents.models.AbstractDocument`. This is where you would add additional fields.
-   Point `WAGTAILDOCS_DOCUMENT_MODEL` to the new model.

Here's an example:

```python
# models.py
from django.db import models

from wagtail.documents.models import Document, AbstractDocument

class CustomDocument(AbstractDocument):
    # Custom field example:
    source = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    admin_form_fields = Document.admin_form_fields + (
        # Add all custom fields names to make them appear in the form:
        'source',
    )
```

Then in your settings module:

```python
# Ensure that you replace app_label with the app you placed your custom
# model in.
WAGTAILDOCS_DOCUMENT_MODEL = 'app_label.CustomDocument'
```

```{note}
Migrating from the builtin document model

When changing an existing site to use a custom document model, no documents
will be copied to the new model automatically. Copying old documents to the
new model would need to be done manually with a
{ref}`data migration <django:data-migrations>`.

Any templates that reference the builtin document model will still continue
to work as before.
```

## Referring to the document model

```{eval-rst}
.. module:: wagtail.documents
```

```{eval-rst}
.. autofunction:: get_document_model
```

```{eval-rst}
.. autofunction:: get_document_model_string
```
