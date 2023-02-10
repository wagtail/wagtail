(managing_the_reference_index)=

# Managing the Reference Index

Wagtail maintains a reference index, which records references between objects whenever those objects are saved. The index allows Wagtail to efficiently report the usage of images, documents and snippets within pages, including within StreamField and rich text fields.

## Configuration

The reference index does not require any configuration. It will by default index every model, unless configured to prevent this. Some of the models within Wagtail (such as revisions) are not indexed, so that object counts remain accurate.

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

The index can be rebuilt with the `rebuild_references_index` management command. This will repopulate the references table and ensure that reference counts are displayed accurately. This should be done if models are manipulated outside of Wagtail.
