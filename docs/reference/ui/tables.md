# Tables

```{eval-rst}
.. module:: wagtail.admin.ui.tables
```

Wagtail provides a set of base table components that can be used to build tables in the Wagtail admin.
For more details on how to use these components, refer to the documentation for customizing [generic listings](modelviewset_listing) and [page listings](custom_page_listings).

## Base table components

These are the basic building blocks for constructing tables in the Wagtail admin.

```{eval-rst}
.. autoclass:: wagtail.admin.ui.tables.BaseColumn
    :members:

.. autoclass:: wagtail.admin.ui.tables.Column
    :members:
    :show-inheritance:

.. autoclass:: wagtail.admin.ui.tables.Table
    :members:
    :exclude-members: Row
    :show-inheritance:
```

## Column types

These are the various column types provided by Wagtail that can be used within tables that list any type of objects.
They are all subclasses of {class}`~wagtail.admin.ui.tables.BaseColumn` and can be used directly or subclassed to create new column types.

```{eval-rst}
.. autoclass:: wagtail.admin.ui.tables.BooleanColumn
    :show-inheritance:

.. autoclass:: wagtail.admin.ui.tables.BulkActionsCheckboxColumn
    :show-inheritance:

.. autoclass:: wagtail.admin.ui.tables.DateColumn
    :show-inheritance:

.. autoclass:: wagtail.admin.ui.tables.DownloadColumn
    :show-inheritance:

.. autoclass:: wagtail.admin.ui.tables.LiveStatusTagColumn
    :show-inheritance:

.. autoclass:: wagtail.admin.ui.tables.LocaleColumn
    :show-inheritance:

.. autoclass:: wagtail.admin.ui.tables.NumberColumn
    :show-inheritance:

.. autoclass:: wagtail.admin.ui.tables.orderable.OrderingColumn
    :show-inheritance:

.. autoclass:: wagtail.admin.ui.tables.ReferencesColumn
    :show-inheritance:

.. autoclass:: wagtail.admin.ui.tables.RelatedObjectsColumn
    :show-inheritance:

.. autoclass:: wagtail.admin.ui.tables.StatusFlagColumn
    :show-inheritance:

.. autoclass:: wagtail.admin.ui.tables.StatusTagColumn
    :show-inheritance:

.. autoclass:: wagtail.admin.ui.tables.TitleColumn
    :show-inheritance:

.. autoclass:: wagtail.admin.ui.tables.UpdatedAtColumn
    :show-inheritance:

.. autoclass:: wagtail.admin.ui.tables.UsageCountColumn
    :show-inheritance:

.. autoclass:: wagtail.admin.ui.tables.UserColumn
    :show-inheritance:
```

## Page-specific table components

These are table components that are specific to page listings in the Wagtail admin.

```{eval-rst}
.. autoclass:: wagtail.admin.ui.tables.pages.PageTitleColumn
    :show-inheritance:

.. autoclass:: wagtail.admin.ui.tables.pages.ParentPageColumn
    :show-inheritance:

.. autoclass:: wagtail.admin.ui.tables.pages.BulkActionsColumn
    :show-inheritance:

.. autoclass:: wagtail.admin.ui.tables.pages.PageTypeColumn
    :show-inheritance:

.. autoclass:: wagtail.admin.ui.tables.pages.NavigateToChildrenColumn
    :show-inheritance:

.. autoclass:: wagtail.admin.ui.tables.pages.PageTable
    :show-inheritance:
```

## Supporting components

These are additional components that can be used to enhance the functionality of tables in the Wagtail admin, such as adding buttons or making tables orderable.

```{eval-rst}
.. autoclass:: wagtail.admin.ui.tables.ButtonsColumnMixin
    :members:
    :show-inheritance:

.. autoclass:: wagtail.admin.ui.tables.orderable.OrderableTableMixin
    :show-inheritance:
```
