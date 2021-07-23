.. _audit_log:

Audit log
=========

Wagtail provides a mechanism to log actions performed on its objects. Common activities such as page creation, update, deletion,
locking and unlocking, revision scheduling and privacy changes are automatically logged at the model level.

The Wagtail admin uses the action log entries to provide a site-wide and page specific history of changes. It uses a
registry of 'actions' that provide additional context for the logged action.

The audit log-driven Page history replaces the revisions list page, but provide a filter for revision-specific entries.

.. note:: The audit log does not replace revisions

To provide additional ``Page`` logging for your site or package, invoke the :meth:`~PageLogEntryManger.log_action` manager method
via ``PageLogEntry.objects.log_action(object_instance, action)`` and register a ``register_log_actions`` hook to
describe your action (see :ref:`register_log_actions`).

.. note:: When adding logging, you need to log the action or actions that happen to the ``Page``. For example, if the
        user creates and publishes, there should be a "create" entry and a "publish" entry. Or, if the user copies a
        published page and chooses to keep it published, there should be a "copy" and a "publish" entry for new page.

You can provide additional metadata by passing additional parameters:

- ``user`` - a user object.
- ``data`` - a data dictionary, stored as JSON
- ``title`` - by default, Wagtail will attempt to use ``get_admin_display_title`` or the string representation of the passed object.

.. code-block:: python

    # mypackage/views.py
    from wagtail.core.models import PageLogEntry

    def copy_for_translation(page):
        # ...
        page.copy(log_action='mypackage.copy_for_translation')

    def my_method(request, page):
        # ..
        # Manually log an action
        data = {
            'make': {'it': 'so'}
        }
        PageLogEntry.objects.log_action(
            instance=page, action='mypackage.custom_action', user=request.user, data=data
        )

To log actions for your non-page model, you can create a class that inherits from ``BaseLogEntry`` with the appropriate
linking.

Log actions provided by Wagtail
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

===================================  =====
Action                               Notes
===================================  =====
``wagtail.create``                   The page was created
``wagtail.edit``                     A draft was saved
``wagtail.delete``                   The page was deleted. Will only surface in the Site History for administrators
``wagtail.publish``                  The page was published
``wagtail.publish.schedule``         Draft is scheduled for publishing
``wagtail.publish.scheduled``        Draft published via ``publish_scheduled_pages`` management command
``wagtail.schedule.cancel``          Draft scheduled for publishing cancelled via "Cancel scheduled publish"
``wagtail.unpublish``                The page was unpublished
``wagtail.unpublish.scheduled``      Page unpublished via ``publish_scheduled_pages`` management command
``wagtail.lock``                     Page was locked
``wagtail.unlock``                   Page was unlocked
``wagtail.moderation.approve``       The revision was approved for moderation
``wagtail.moderation.reject``        The revision was rejected
``wagtail.rename``                   A page was renamed
``wagtail.revert``                   The page was reverted to a previous draft
``wagtail.copy``                     The page was copied to a new location
``wagtail.copy_for_translation``     The page was copied into a new locale for translation
``wagtail.move``                     The page was moved to a new location
``wagtail.reorder``                  The order of the page under it's parent was changed
``wagtail.view_restriction.create``  The page was restricted
``wagtail.view_restriction.edit``    The page restrictions were updated
``wagtail.view_restriction.delete``  The page restrictions were removed

``wagtail.workflow.start``           The page was submitted for moderation in a Workflow
``wagtail.workflow.approve``         The draft was approved at a Workflow Task
``wagtail.workflow.reject``          The draft was rejected, and changes requested at a Workflow Task
``wagtail.workflow.resume``          The draft was resubmitted to the workflow
``wagtail.workflow.cancel``          The workflow was cancelled
===================================  =====
