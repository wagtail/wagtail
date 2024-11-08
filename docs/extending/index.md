# Extending

The Wagtail admin interface is a suite of Django apps, and so the familiar concepts from Django development - views, templates, URL routes and so on - can be used to add new functionality to Wagtail. Numerous [third-party packages](https://wagtail.org/packages/) can be installed to extend Wagtail's capabilities.

This section describes the various mechanisms that can be used to integrate your own code into Wagtail's admin interface.

```{note}
The features described in this section and their corresponding reference
documentation are not subject to the same level of stability described in our
[](deprecation_policy). Any backwards-incompatible changes to these features
will be called out in the upgrade considerations of the [](../releases/index).
```

```{toctree}
---
maxdepth: 2
---
admin_views
generic_views
template_components
forms
adding_reports
custom_tasks
audit_log
custom_account_settings
customizing_group_views
custom_image_filters
extending_client_side
rich_text_internals
extending_draftail
custom_bulk_actions
```
