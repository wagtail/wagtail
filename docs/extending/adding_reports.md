(adding_reports)=

# Adding reports

Reports are views with listings of pages or any non-page model (such as snippets) matching a specific query. Reports can also export these listings in spreadsheet format.
They are found in the _Reports_ submenu: by default, the _Locked pages_ report is provided, allowing an overview of locked pages on the site.

It is possible to create your own custom reports in the Wagtail admin with two base classes provided:

-   `wagtail.admin.views.reports.ReportView` - Provides the basic listing (with a single column) and spreadsheet export functionality.
-   `wagtail.admin.views.reports.PageReportView` - Extends the `ReportView` and provides a default set of fields suitable for page listings.

## Reporting reference

### `get_queryset`

The most important attributes and methods to customize to define your report are:

```{eval-rst}
.. method:: get_queryset(self)
```

This retrieves the queryset of pages or other models for your report, two examples below.

```python
# <project>/views.py

from wagtail.admin.views.reports import ReportView, PageReportView
from wagtail.models import Page

from .models import MySnippetModel


class UnpublishedChangesReportView(PageReportView):
    # includes common page fields by default

    def get_queryset(self):
        return Page.objects.filter(has_unpublished_changes=True)


class CustomModelReport(ReportView):
    # includes string representation as a single column only

    def get_queryset(self):
        return MySnippetModel.objects.all()

```

### Other attributes

```{eval-rst}

.. attribute:: template_name

(string)

The template used to render your report view, defaults to ``"wagtailadmin/reports/base_report.html"``.
Note that this template only provides the skeleton of the view, not the listing table itself.
The listing table should be implemented in a separate template specified by ``results_template_name`` (see below), to then be rendered via ``{% include %}``.
Unless you want to customize the overall view, you will rarely need to change this template.
To customize the listing, change the ``results_template_name`` instead.

.. attribute:: results_template_name

(string)

The template used to render the listing table.
For ``ReportView``, this defaults to ``"wagtailadmin/reports/base_report_results.html"``,
which provides support for using the ``wagtail.admin.ui.tables`` framework.
For ``PageReportView``, this defaults to ``"wagtailadmin/reports/base_page_report_results.html"``,
which provides a default table layout based on the explorer views,
displaying action buttons, as well as the title, time of the last update, status, and specific type of any pages.
In this example, we'll change this to a new template in a later section.

.. attribute:: page_title

(string)

The name of your report, which will be displayed in the header. For our example, we'll set it to
``"Pages with unpublished changes"``.

.. attribute:: header_icon

(string)

The name of the icon, using the standard Wagtail icon names. For example, the locked pages view uses ``"locked"``,
and for our example report, we'll set it to ``'doc-empty-inverse'``.

.. attribute:: index_url_name

(string)

The name of the URL pattern registered for the report view.

.. attribute:: index_results_url_name

(string)

The name of the URL pattern registered for the results view (the report view with ``.as_view(results_only=True)``).

```

### Spreadsheet exports

```{eval-rst}

.. attribute:: list_export

(list)

A list of the fields/attributes for each model which are exported as columns in the spreadsheet view. For ``ReportView``, this
is empty by default, and for ``PageReportView``, it corresponds to the listing fields: the title, time of the last update, status,
and specific type of any pages. For our example, we might want to know when the page was last published, so we'll set
``list_export`` as follows:

``list_export = PageReportView.list_export + ['last_published_at']``

.. attribute:: export_headings

(dictionary)

A dictionary of any fields/attributes in ``list_export`` for which you wish to manually specify a heading for the spreadsheet
column and their headings. If unspecified, the heading will be taken from the field ``verbose_name`` if applicable, and the
attribute string otherwise. For our example, ``last_published_at`` will automatically get a heading of ``"Last Published At"``,
but a simple "Last Published" looks neater. We'll add that by setting ``export_headings``:

``export_headings = dict(last_published_at='Last Published', **PageReportView.export_headings)``

.. attribute:: custom_value_preprocess

(dictionary)

A dictionary of ``(value_class_1, value_class_2, ...)`` tuples mapping to ``{export_format: preprocessing_function}`` dictionaries,
allowing custom preprocessing functions to be applied when exporting field values of specific classes (or their subclasses). If
unspecified (and ``ReportView.custom_field_preprocess`` also does not specify a function), ``force_str`` will be used. To prevent
preprocessing, set the preprocessing_function to ``None``.

.. attribute:: custom_field_preprocess

(dictionary)

A dictionary of ``field_name`` strings mapping to ``{export_format: preprocessing_function}`` dictionaries,
allowing custom preprocessing functions to be applied when exporting field values of specific classes (or their subclasses). This
will take priority over functions specified in ``ReportView.custom_value_preprocess``. If unspecified (and
``ReportView.custom_value_preprocess`` also does not specify a function), ``force_str`` will be used. To prevent
preprocessing, set the preprocessing_function to ``None``.

```

## Example report for pages with unpublished changes

For this example, we'll add a report which shows any pages with unpublished changes.
We will register this view using the `unpublished_changes_report` name for the URL pattern.

```python
# <project>/views.py
from wagtail.admin.views.reports import PageReportView

class UnpublishedChangesReportView(PageReportView):
    index_url_name = "unpublished_changes_report"
    index_results_url_name = "unpublished_changes_report_results"
```

### Customizing templates

For this example \"pages with unpublished changes\" report, we'll add an extra column to the listing template, showing the last publication date for each page. To do this, we'll extend two templates: `wagtailadmin/reports/base_page_report_results.html`, and `wagtailadmin/reports/listing/_list_page_report.html`.

```html+django
{# <project>/templates/reports/unpublished_changes_report_results.html #}

{% extends 'wagtailadmin/reports/base_page_report_results.html' %}

{% block results %}
    {% include 'reports/include/_list_unpublished_changes.html' %}
{% endblock %}

{% block no_results_message %}
    <p>No pages with unpublished changes.</p>
{% endblock %}
```

```html+django
{# <project>/templates/reports/include/_list_unpublished_changes.html #}

{% extends 'wagtailadmin/reports/listing/_list_page_report.html' %}

{% block extra_columns %}
    <th>Last Published</th>
{% endblock %}

{% block extra_page_data %}
    <td valign="top">
        {{ page.last_published_at }}
    </td>
{% endblock %}
```

Finally, we'll set `UnpublishedChangesReportView.results_template_name` to this new template: `'reports/unpublished_changes_report_results.html'`.

### Adding a menu item and admin URL

To add a menu item for your new report to the _Reports_ submenu, you will need to use the `register_reports_menu_item` hook (see: [Register Reports Menu Item](register_reports_menu_item)). To add an admin url for the report, you will need to use the `register_admin_urls` hook (see: [Register Admin URLs](register_admin_urls)). This can be done as follows:

```python
# <project>/wagtail_hooks.py

from django.urls import path, reverse

from wagtail.admin.menu import AdminOnlyMenuItem
from wagtail import hooks

from .views import UnpublishedChangesReportView

@hooks.register('register_reports_menu_item')
def register_unpublished_changes_report_menu_item():
    return AdminOnlyMenuItem("Pages with unpublished changes", reverse('unpublished_changes_report'), icon_name=UnpublishedChangesReportView.header_icon, order=700)

@hooks.register('register_admin_urls')
def register_unpublished_changes_report_url():
    return [
        path('reports/unpublished-changes/', UnpublishedChangesReportView.as_view(), name='unpublished_changes_report'),
        # Add a results-only view to add support for AJAX-based filtering
        path('reports/unpublished-changes/results/', UnpublishedChangesReportView.as_view(results_only=True), name='unpublished_changes_report_results'),
    ]
```

Here, we use the `AdminOnlyMenuItem` class to ensure our report icon is only shown to superusers. To make the report visible to all users, you could replace this with `MenuItem`.

### Setting up permission restriction

Even with the menu item hidden, it would still be possible for any user to visit the report's URL directly, and so it is necessary to set up a permission restriction on the report view itself. This can be done by adding a `dispatch` method to the existing `UnpublishedChangesReportView` view:

```python

    # add the below dispatch method to the existing UnpublishedChangesReportView view
    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_superuser:
            return permission_denied(request)
        return super().dispatch(request, *args, **kwargs)
```

### The full code

```python
# <project>/views.py

from wagtail.admin.auth import permission_denied
from wagtail.admin.views.reports import PageReportView
from wagtail.models import Page

class UnpublishedChangesReportView(PageReportView):
    index_url_name = "unpublished_changes_report"
    index_results_url_name = "unpublished_changes_report_results"
    header_icon = 'doc-empty-inverse'
    results_template_name = 'reports/unpublished_changes_report_results.html'
    page_title = "Pages with unpublished changes"

    list_export = PageReportView.list_export + ['last_published_at']
    export_headings = dict(last_published_at='Last Published', **PageReportView.export_headings)

    def get_queryset(self):
        return Page.objects.filter(has_unpublished_changes=True)

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_superuser:
            return permission_denied(request)
        return super().dispatch(request, *args, **kwargs)
```

```python
# <project>/wagtail_hooks.py

from django.urls import path, reverse

from wagtail.admin.menu import AdminOnlyMenuItem
from wagtail import hooks

from .views import UnpublishedChangesReportView

@hooks.register('register_reports_menu_item')
def register_unpublished_changes_report_menu_item():
    return AdminOnlyMenuItem("Pages with unpublished changes", reverse('unpublished_changes_report'), icon_name=UnpublishedChangesReportView.header_icon, order=700)

@hooks.register('register_admin_urls')
def register_unpublished_changes_report_url():
    return [
        path('reports/unpublished-changes/', UnpublishedChangesReportView.as_view(), name='unpublished_changes_report'),
        path('reports/unpublished-changes/results/', UnpublishedChangesReportView.as_view(results_only=True), name='unpublished_changes_report_results'),
    ]
```

```html+django
{# <project>/templates/reports/unpublished_changes_report_results.html #}

{% extends 'wagtailadmin/reports/base_page_report_results.html' %}

{% block results %}
    {% include 'reports/include/_list_unpublished_changes.html' %}
{% endblock %}

{% block no_results_message %}
    <p>No pages with unpublished changes.</p>
{% endblock %}
```

```html+django
{# <project>/templates/reports/include/_list_unpublished_changes.html #}

{% extends 'wagtailadmin/reports/listing/_list_page_report.html' %}

{% block extra_columns %}
    <th>Last Published</th>
{% endblock %}

{% block extra_page_data %}
    <td valign="top">
        {{ page.last_published_at }}
    </td>
{% endblock %}
```
