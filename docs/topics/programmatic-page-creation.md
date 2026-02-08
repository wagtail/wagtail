# Programmatically creating pages

There are situations where pages need to be created outside of the Wagtail admin interface, such as
during data migrations, import scripts, or management commands. This page describes the canonical
sequence of actions required to create pages programmatically in a way that matches the behavior of
the admin UI.

## When to create pages programmatically

Programmatic page creation is commonly needed when:
- migrating content from an existing CMS into Wagtail
- creating initial or default content during a data migration
- importing large volumes of structured content

In these cases, it is important to follow the same steps that Wagtail performs internally to ensure
that the page tree and revision data remain consistent.

## Creating a page and attaching it to the tree

Pages must be attached to a parent page using the tree APIs rather than being saved directly.

```python
from wagtail.models import Page
```
parent = Page.objects.get(id=1)

page = MyPage(
    title="Example page",
    slug="example-page",
)

parent.add_child(instance=page)


## Creating revisions and publishing
page.save_revision().publish()


## Common mistakes

- Calling `save()` directly on a new page instead of using `add_child()`, which results in an invalid page tree
- Forgetting to create a revision when creating pages programmatically
- Assuming pages are published automatically after creation
- Importing models directly inside migrations instead of using `apps.get_model()`
