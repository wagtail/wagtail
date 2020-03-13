Adding reports
==============

Reports are views with listings of pages matching a specific query. They can also export these listings in spreadsheet format.
They are found in the `Reports` submenu: by default, the `Locked Pages` report is provided, allowing an overview of locked pages on the site.

It is possible to create your own custom reports in the Wagtail admin. To do this, you will need to subclass
``wagtail.admin.views.reports.ReportView``, which provides basic listing and spreadsheet export functionality:

.. code-block:: python

    # <project>/views.py

    from wagtail.admin.views.report.ReportView


    class CustomReportView(ReportView):
        pass


Defining your report
~~~~~~~~~~~~~~~~~~~~~

The most important attributes and methods to customise to define your report are:

.. method:: get_queryset(self)

This retrieves the queryset of pages for your report. For example, if you wanted a report on all pages shown in menus:

.. code-block:: python

    # <project>/views.py

    from wagtail.admin.views.report.ReportView
    from wagtail.core.models import Page


    class MenuReportView(ReportView):
        
        def get_queryset(self):
            return Page.objects.in_menu()

.. attribute:: template_name

(string)

The template used to render your report. By default, this is ``"wagtailadmin/reports/base_report.html"``,
which has a listing based on the explorer views, displaying action buttons, as well as the title,
time of the last update, status, and specific type of any pages.

.. attribute:: title

(string)

The name of your report, which will be displayed in the header.

.. attribute:: ReportView.header_icon

(string)

The name of the icon, using the standard Wagtail icon names. For example, the locked pages view uses ``"locked"``.

Spreadsheet exports
-------------------

.. attribute:: list_export

(list)

A list of the fields/attributes for each model which are exported as columns in the spreadsheet view. By default,
this is identical to the listing fields: the title, time of the last update, status, and specific type of any pages.

.. attribute:: export_heading_overrides

(dictionary)

A dictionary of any fields/attributes in ``list_export`` for which you wish to manually specify a heading for the spreadsheet
column, and their headings. If unspecified, heading will be taken from the field ``verbose_name`` if applicable, and the
attribute string otherwise.

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


Adding a menu item and admin URL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To add a menu item for your new report to the `Reports` submenu, you will need to use the ``register_reports_menu_item`` hook (see: :ref:`register_reports_menu_item`). To add an admin
url for the report, you will need to use the ``register_admin_urls`` hook (see :ref:`register_admin_urls`). This can be done as follows:

.. code-block:: python

    # <project>/wagtail_hooks.py

    from django.conf.urls import url

    from wagtail.admin.menu import MenuItem
    from wagtail.core import hooks

    from .views import CustomReportView

    @hooks.register('register_reports_menu_item')
    def register_my_custom_report_menu_item():
        return MenuItem("My Custom Report", reverse('my_custom_report'), classnames='icon icon-' + CustomReportView.header_icon, order=700)
    
    @hooks.register('register_admin_urls')
    def register_my_custom_report_url():
        return [
            url(r'^reports/my-custom-report/$', CustomReportView.as_view(), name='my_custom_report'),
        ]