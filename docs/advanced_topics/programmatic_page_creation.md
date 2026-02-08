# Programmatic page creation for content migration

When migrating content into Wagtail from another CMS, it is common to create pages using Python scripts rather than the admin interface.

Unlike creating pages through the admin UI, programmatic page creation requires performing several steps in the correct order to ensure that the page tree, revisions, and publishing state are handled correctly.

This page documents the recommended workflow for creating and publishing pages programmatically so that they behave exactly like pages created through the admin.

## Why this is necessary

When creating pages through the Wagtail admin interface, Wagtail automatically:

- Attaches the page to the correct parent in the page tree
- Creates an initial revision
- Publishes the page when requested

When creating pages programmatically, these steps must be performed explicitly.

Simply calling `save()` on a page model is not sufficient and can lead to pages that do not appear correctly in the page tree or lack revision history.

## Recommended workflow

The correct workflow for programmatic page creation is:

1. Create a page instance
2. Attach the page to a parent using `add_child()`
3. Create a revision
4. Publish the revision

## Example

The following example demonstrates creating and publishing a page using the Django shell or a migration script:

```python
from wagtail.models import Page
from home.models import HomePage

home = Page.objects.get(title="Home")

new_page = HomePage(
    title="Programmatic Test Page",
    slug="programmatic-test-page",
)

home.add_child(instance=new_page)

revision = new_page.save_revision()
revision.publish()
