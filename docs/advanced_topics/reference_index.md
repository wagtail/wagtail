# Reference index

The reference index in Wagtail tracks where content such as pages, images, documents, and snippets are referenced across the site. It is primarily used to support features like usage reporting and assist with clean-up of unused content.

This document describes how the reference index works, how it can be used in custom code, and its current limitations.

## What the reference index tracks

The reference index records references detected by Wagtail when content is saved. This includes, for example:

- Page-to-page references  
- Images and documents used in StreamField blocks  
- Snippet references in supported fields  

The index is updated automatically when content is created or modified.

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
The reference index may not detect all references. Using it to block deletions can still allow content to be removed if references exist outside of the index’s detection scope.
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

The reference index may fail to detect references stored inside complex or highly customised blocks, such as TypedTableBlock, or blocks that store data in non-standard data structures.

This limitation has been observed in practice when media is referenced inside TypedTableBlock, causing automated clean-up scripts to incorrectly treat those assets as unused.

As a result, automated maintenance scripts that delete "unused" images or documents based solely on reference index results may incorrectly remove content that is still in use.

### Relationships not covered by the reference index

The reference index does not currently track all many-to-many relationships, nor references created outside of Wagtail's standard model fields (for example, identifiers stored in JSON blobs or external systems).

For this reason, the reference index should be treated as advisory rather than authoritative when enforcing deletion or integrity rules.
