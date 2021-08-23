Adding custom bulk actions
==========================================

This document describes how to add custom bulk actions to different listings


Registering a custom bulk action
--------------------------------

    .. code-block:: python

        from wagtail.admin.views.bulk_action import BulkAction
        from wagtail.core import hooks


        @hooks.register('register_bulk_action')
        class CustomPageBulkAction(BulkAction):
            display_name = _("Custom Action")
            aria_label = _("Do custom action")
            action_type = "action"
            template_name = "/path/to/template"
            models = [...]

            @classmethod
            def execute_action(cls, objects, **kwargs):
                for object in objects:
                    do_something(object)
                return num_parent_objects, num_child_objects  # return the count of updated objects

The attributes are as follows:

- ``display_name`` - The label that will be displayed on the button in the ui
- ``aria_label`` - The ``aria-label`` attribute that will be applied to the button in the ui
- ``action_type`` - A unique identifier for the action. Will be required in the url for bulk actions
- ``template_name`` - The path to the confirmation template
- ``models`` - A list of models on which the bulk action can act upon
- ``action_priority`` (optional) - A number that is used to determine the placement of the button in the list of buttons
- ``object_key`` (optional) - The key that will be used to create the context of objects
- ``classes`` (optional) - A set of css classnames that will be used on the button in the ui


Adding bulk actions to the page explorer
----------------------------------------

When creating a custom bulk action class for pages, subclass from ``wagtail.admin.views.pages.bulk_actions.page_bulk_action.PageBulkAction``
instead of ``wagtail.admin.views.bulk_action.BulkAction``

Basic example
~~~~~~~~~~~~~

  .. code-block:: python

    from wagtail.admin.views.pages.bulk_actions.page_bulk_action import PageBulkAction
    from wagtail.core import hooks


    @hooks.register('register_bulk_action')
    class CustomPageBulkAction(PageBulkAction):
        ...



Adding bulk actions to images listing
----------------------------------------

When creating a custom bulk action class for images, subclass from ``wagtail.images.views.bulk_actions.image_bulk_action.ImageBulkAction``
instead of ``wagtail.admin.views.bulk_action.BulkAction``

Basic example
~~~~~~~~~~~~~

  .. code-block:: python

    from wagtail.images.views.bulk_actions.image_bulk_action import ImageBulkAction
    from wagtail.core import hooks


    @hooks.register('register_bulk_action')
    class CustomImageBulkAction(ImageBulkAction):
        ...



Adding bulk actions to document listing
----------------------------------------

When creating a custom bulk action class for documents, subclass from ``wagtail.documents.views.bulk_actions.document_bulk_action.DocumentBulkAction``
instead of ``wagtail.admin.views.bulk_action.BulkAction``

Basic example
~~~~~~~~~~~~~

  .. code-block:: python

    from wagtail.documents.views.bulk_actions.document_bulk_action import DocumentBulkAction
    from wagtail.core import hooks


    @hooks.register('register_bulk_action')
    class CustomDocumentBulkAction(DocumentBulkAction):
        ...



Adding bulk actions to user listing
----------------------------------------

When creating a custom bulk action class for users, subclass from ``wagtail.users.views.bulk_actions.user_bulk_action.UserBulkAction``
instead of ``wagtail.admin.views.bulk_action.BulkAction``

Basic example
~~~~~~~~~~~~~

  .. code-block:: python

    from wagtail.users.views.bulk_actions.user_bulk_action import UserBulkAction
    from wagtail.core import hooks


    @hooks.register('register_bulk_action')
    class CustomUserBulkAction(UserBulkAction):
        ...

