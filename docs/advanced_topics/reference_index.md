(managing_the_reference_index)=

# Manage the reference index

Wagtail maintains a reference index, which records references between objects whenever those objects are saved. The index allows Wagtail to efficiently report the usage of images, documents and snippets within pages, including within StreamField and rich text fields.

## Configuration

By default, the index will store references between objects managed within the Wagtail admin, specifically:

-   all Page types
-   Images
-   Documents
-   models registered as [Snippets](snippets)
-   models registered with [`ModelViewSet`](../extending/generic_views)

The reference index does not require any further configuration. However there are circumstances where it may be necessary to add or remove models from the index.

(registering_a_model_for_indexing)=

### Registering a Model for Indexing

A model can be registered for reference indexing by adding code to `apps.py` in the app where the model is defined:

```python
from django.apps import AppConfig


class SprocketAppConfig(AppConfig):
    ...
    def ready(self):
        from wagtail.models.reference_index import ReferenceIndex

        from .models import SprocketController

        ReferenceIndex.register_model(SprocketController)
```

### Preventing Indexing of models and fields

The `wagtail_reference_index_ignore` attribute can be used to prevent indexing with a particular model or model field.

-   set the `wagtail_reference_index_ignore` attribute to `True` within any model class where you want to prevent indexing of all fields in the model; or
-   set the `wagtail_reference_index_ignore` attribute to `True` within any model field, to prevent that field or the related model field from being indexed:

```python
class CentralPage(Page):
    ...
    reference = models.ForeignKey(
        "doc",
        on_delete=models.SET_NULL,
        related_name="page_ref",
    )
    reference.wagtail_reference_index_ignore = True
    ...
```

## Maintenance

The index can be rebuilt with the `rebuild_references_index` management command. This will repopulate the references table and ensure that reference counts are displayed accurately. This should be done if models are manipulated outside of Wagtail, or after an upgrade.

A summary of the index can be shown with the `show_references_index` management command. This shows the number of objects indexed against each model type, and can be useful to identify which models are being indexed without rebuilding the index itself.
