.. _audit_log:

Audit log
=========

Wagtail provides a mechanism to log actions performed on its objects. Common activities like page creation, update, deletion,
locking and unlocking, revision scheduling and privacy changes are automatically logged at the model level.

The Wagtail admin uses the action log entries to provide a site-wide and page specific history of changes. It uses a
registry of 'actions' that provide additional context for the logged action.

The audit log-driven Page history replaces the revisions list page, but provide a filter for revision-specific entries.

.. note:: The audit log does not replace revisions

To provide additional logging for your site or package, invoke the :meth:`~LogEntryManger.log_action` manager method via ``LogEntry.objects.log_action(object_instance, action)``
and register a ``register_log_actions`` hook to describe your action (see :ref:`register_log_actions`).

You can provide additional metadata by passing additional parameters:

- ``user`` - a user object.
- ``data`` - a data dictionary, stored as JSON
- ``title`` - by default, Wagtail will attempt to use ``get_admin_display_title`` or the string representation of the passed object.

.. code-block:: python

    # mypackage/views.py
    from wagtail.core.models import LogEntry

    def copy_for_translation(page):
        # ...
        page.copy(log_action='mypackage.copy_for_translation')

    def my_method(request, page):
        # ..
        # Manually log an action
        data = {
            'make': {'it': 'so'}
        }
        LogEntry.objects.log_action(
            instance=page, action='mypackage.custom_action', user=request.user, data=data
        )
