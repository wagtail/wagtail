Adding reports
==============

Reports are views with listings of pages matching a specific query. They can also export these listings in spreadsheet format.
They are found in the `Reports` submenu: by default, the `Locked Pages` report is provided, allowing an overview of locked pages on the site.

It is possible to create your own custom reports in the Wagtail admin. To do this, you will need to subclass
``wagtail.admin.views.reports.ReportView``, which provides basic listing and spreadsheet export functionality.
For this example, we'll add a report which shows any pages with unpublished changes.

.. code-block:: python

    # <project>/views.py

    from wagtail.admin.views.reports import ReportView


    class UnpublishedChangesReportView(ReportView):
        pass


Defining your report
~~~~~~~~~~~~~~~~~~~~~

The most important attributes and methods to customise to define your report are:

.. method:: get_queryset(self)

This retrieves the queryset of pages for your report. For our example:

.. code-block:: python

    # <project>/views.py

    from wagtail.admin.views.reports import ReportView
    from wagtail.core.models import Page


    class UnpublishedChangesReportView(ReportView):
        
        def get_queryset(self):
            return Page.objects.filter(has_unpublished_changes=True)

.. attribute:: template_name

(string)

The template used to render your report. By default, this is ``"wagtailadmin/reports/base_report.html"``,
which provides an empty report page layout; an alternative base template ``"wagtailadmin/reports/base_page_report.html"``
is available, providing a listing based on the explorer views, displaying action buttons, as well as the title,
time of the last update, status, and specific type of any pages. In this example, we'll change this
to a new template in a later section.

.. attribute:: title

(string)

The name of your report, which will be displayed in the header. For our example, we'll set it to
``"Pages with unpublished changes"``.

.. attribute:: header_icon

(string)

The name of the icon, using the standard Wagtail icon names. For example, the locked pages view uses ``"locked"``,
and for our example report, we'll set it to ``'doc-empty-inverse'``.

Spreadsheet exports
-------------------

.. attribute:: list_export

(list)

A list of the fields/attributes for each model which are exported as columns in the spreadsheet view. By default,
this is identical to the listing fields: the title, time of the last update, status, and specific type of any pages.
For our example, we might want to know when the page was last published, so we'll set ``list_export`` as follows:

``list_export = ReportView.list_export + ['last_published_at']``

.. attribute:: export_headings

(dictionary)

A dictionary of any fields/attributes in ``list_export`` for which you wish to manually specify a heading for the spreadsheet
column, and their headings. If unspecified, the heading will be taken from the field ``verbose_name`` if applicable, and the
attribute string otherwise. For our example, ``last_published_at`` will automatically get a heading of ``"Last Published At"``,
but a simple "Last Published" looks neater. We'll add that by setting ``export_headings``:

``export_headings = dict(last_published_at='Last Published', **ReportView.export_headings)``

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

Customising templates
---------------------

For this example "pages with unpublished changes" report, we'll add an extra column to the listing template, showing the last
publication date for each page. To do this, we'll extend two templates: ``wagtailadmin/reports/base_page_report.html``, and
``wagtailadmin/reports/listing/_list_report.html``.

.. code-block:: html

    {# <project>/templates/reports/unpublished_changes_report.html #}

    {% extends 'wagtailadmin/reports/base_page_report.html' %}

    {% block listing %}
        {% include 'reports/include/_list_unpublished_changes.html' %}
    {% endblock %}

    {% block no_results %}
        <p>No pages with unpublished changes.</p>
    {% endblock %}


.. code-block:: html

    {# <project>/templates/reports/include/_list_unpublished_changes.html #}

    {% extends 'wagtailadmin/reports/listing/_list_report.html' %}

    {% block extra_columns %}
        <th>Last Published</th>
    {% endblock %}

    {% block extra_page_data %}
        <td valign="top">
            {{ page.last_published_at }}
        </td>
    {% endblock %}

Finally, we'll set ``UnpublishedChangesReportView.template_name`` to this new template: ``'reports/unpublished_changes_report.html'``.


Adding a menu item and admin URL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To add a menu item for your new report to the `Reports` submenu, you will need to use the ``register_reports_menu_item`` hook (see: :ref:`register_reports_menu_item`). To add an admin
url for the report, you will need to use the ``register_admin_urls`` hook (see :ref:`register_admin_urls`). This can be done as follows:

.. code-block:: python

    # <project>/wagtail_hooks.py

    from django.conf.urls import url

    from wagtail.admin.menu import AdminOnlyMenuItem
    from wagtail.core import hooks

    from .views import UnpublishedChangesReportView

    @hooks.register('register_reports_menu_item')
    def register_unpublished_changes_report_menu_item():
        return AdminOnlyMenuItem("Pages with unpublished changes", reverse('unpublished_changes_report'), classnames='icon icon-' + UnpublishedChangesReportView.header_icon, order=700)
    
    @hooks.register('register_admin_urls')
    def register_unpublished_changes_report_url():
        return [
            url(r'^reports/unpublished-changes/$', UnpublishedChangesReportView.as_view(), name='unpublished_changes_report'),
        ]

Here, we use the ``AdminOnlyMenuItem`` class to ensure our report icon is only shown to superusers. To make the report visible to all users,
you could replace this with ``MenuItem``.


The full code
~~~~~~~~~~~~~

.. code-block:: python

    # <project>/views.py

    from wagtail.admin.views.reports import ReportView
    from wagtail.core.models import Page


    class UnpublishedChangesReportView(ReportView):

        header_icon = 'doc-empty-inverse'
        template_name = 'reports/unpublished_changes_report.html'
        title = "Pages with unpublished changes"

        list_export = ReportView.list_export + ['last_published_at']
        export_headings = dict(last_published_at='Last Published', **ReportView.export_headings)
        
        def get_queryset(self):
            return Page.objects.filter(has_unpublished_changes=True)

.. code-block:: python

    # <project>/wagtail_hooks.py

    from django.conf.urls import url

    from wagtail.admin.menu import AdminOnlyMenuItem
    from wagtail.core import hooks

    from .views import UnpublishedChangesReportView

    @hooks.register('register_reports_menu_item')
    def register_unpublished_changes_report_menu_item():
        return AdminOnlyMenuItem("Pages with unpublished changes", reverse('unpublished_changes_report'), classnames='icon icon-' + UnpublishedChangesReportView.header_icon, order=700)
    
    @hooks.register('register_admin_urls')
    def register_unpublished_changes_report_url():
        return [
            url(r'^reports/unpublished-changes/$', UnpublishedChangesReportView.as_view(), name='unpublished_changes_report'),
        ]

.. code-block:: html

    {# <project>/templates/reports/unpublished_changes_report.html #}

    {% extends 'wagtailadmin/reports/base_page_report.html' %}

    {% block listing %}
        {% include 'reports/include/_list_unpublished_changes.html' %}
    {% endblock %}

    {% block no_results %}
        <p>No pages with unpublished changes.</p>
    {% endblock %}


.. code-block:: html

    {# <project>/templates/reports/include/_list_unpublished_changes.html #}

    {% extends 'wagtailadmin/reports/listing/_list_report.html' %}

    {% block extra_columns %}
        <th>Last Published</th>
    {% endblock %}

    {% block extra_page_data %}
        <td valign="top">
            {{ page.last_published_at }}
        </td>
    {% endblock %}