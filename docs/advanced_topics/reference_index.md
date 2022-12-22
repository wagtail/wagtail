
# Managing the Reference Index

Wagtail maintains a reference index, which records cross-references between objects whenever those objects are saved. The index, powered by the `ReferenceIndex` model, allows Wagtail to efficiently report the usage of images, documents and snippets within pages, including within StreamField and rich text fields.

## Configuration

The reference index does not require any configuration. It will by default index every model, unless configured to prevent this. Some of the models within Wagtail (such as revisions) are not indexed, so that object counts remain accurate.

There are two ways to prevent indexing of your own models.

### wagtail_reference_index_ignore

The `wagtail_reference_index_ignore` attribute can be used to prevent indexing with a particular model or model field.

-   set the `wagtail_reference_index_ignore` attribute to `True` within any class where you want to prevent indexing of any fields in the model; or
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

### register_reference_index_ignore hook

For models in third-party apps, the `register_reference_index_ignore` hook can be used to prevent indexing, without needing to change the app code. Simply list the apps and the app models that should not be indexed in a `wagtail_hooks.py` module:

```python
from wagtail import hooks

@hooks.register("register_reference_index_ignore")
def reference_index_ignore(ignore_list):
    ignore_list.extend([
        "my_app",
        "my_second_app.data_entry",
    ])
    return ignore_list
```

In this example, all the models in `my_app` will added to the ignore list, as will the model `data_entry` within the app `my_second_app`.

## Maintenance

The index can be rebuilt with the `rebuild_references_index` management command. This will repopulate the references table and ensure that reference counts are displayed accurately. This should be done if models are manipulated outside of Wagtail.
