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

## Guarantees and non-guarantees

The reference index is a **best-effort tracking system**, not a strict referential integrity mechanism.

It aims to detect common references created through Wagtail’s built-in models, fields, and blocks, but it does **not** guarantee that all references between content objects will be detected or enforced.

## Using the ReferenceIndex API

The `ReferenceIndex` model exposes APIs for querying references between content objects.

The most commonly used method is:

- `ReferenceIndex.get_references_for_object(obj)`

This returns a queryset of reference records representing objects that reference the given object. The queryset may be empty even if references exist outside of what the reference index is able to detect.

## Enforcing stricter deletion rules

The reference index does **not** automatically prevent content from being deleted. Projects that require stronger guarantees (for example, required StreamField relationships) must enforce those rules in application code.

A common approach is to block deletion of pages that are still referenced elsewhere, **based on the reference index results**.

```{warning}
The reference index may not detect all references. Using it to block deletions can still allow content to be removed if references exist outside of the index's detection scope.
```

### Example: blocking deletion of referenced pages

```python
from django.core.exceptions import PermissionDenied
from wagtail.hooks import register
from wagtail.models import ReferenceIndex


@register("before_delete_page")
def prevent_deleting_referenced_pages(request, page):
    references = ReferenceIndex.get_references_for_object(page)

    if references.exists():
        raise PermissionDenied(
            "This page is referenced by other content and cannot be deleted."
        )
```

## Known limitations

### References inside complex or custom blocks

The reference index may fail to detect references stored inside complex or highly customised blocks, such as `TypedTableBlock`, or blocks that store data in non-standard data structures.

This limitation has been observed in practice when media is referenced inside `TypedTableBlock`, causing automated clean-up scripts to incorrectly treat those assets as unused.

As a result, automated maintenance scripts that delete "unused" images or documents based solely on reference index results may incorrectly remove content that is still in use.

### Relationships not covered by the reference index

The reference index does not currently track all many-to-many relationships, nor references created outside of Wagtail's standard model fields (for example, identifiers stored in JSON blobs or external systems).

For this reason, the reference index should be treated as advisory rather than authoritative when enforcing deletion or integrity rules.
