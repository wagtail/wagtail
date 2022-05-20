.. _custom_bulk_actions:

Adding custom bulk actions
==========================================

This document describes how to add custom bulk actions to different listings.


Registering a custom bulk action
--------------------------------

.. code-block:: python

    from wagtail.admin.views.bulk_action import BulkAction
    from wagtail import hooks


    @hooks.register('register_bulk_action')
    class CustomDeleteBulkAction(BulkAction):
        display_name = _("Delete")
        aria_label = _("Delete selected objects")
        action_type = "delete"
        template_name = "/path/to/confirm_bulk_delete.html"
        models = [...]

        @classmethod
        def execute_action(cls, objects, **kwargs):
            for obj in objects:
                do_something(obj)
            return num_parent_objects, num_child_objects  # return the count of updated objects

The attributes are as follows:

- ``display_name`` - The label that will be displayed on the button in the user interface
- ``aria_label`` - The ``aria-label`` attribute that will be applied to the button in the user interface
- ``action_type`` - A unique identifier for the action. Will be required in the url for bulk actions
- ``template_name`` - The path to the confirmation template
- ``models`` - A list of models on which the bulk action can act
- ``action_priority`` (optional) - A number that is used to determine the placement of the button in the list of buttons
- ``classes`` (optional) - A set of CSS classnames that will be used on the button in the user interface

An example for a confirmation template is as follows:

.. code-block:: django

  <!-- /path/to/confirm_bulk_delete.html -->

  {% extends 'wagtailadmin/bulk_actions/confirmation/base.html' %}
  {% load i18n wagtailadmin_tags %}

  {% block titletag %}{% blocktrans trimmed count counter=items|length %}Delete 1 item{% plural %}Delete {{ counter }} items{% endblocktrans %}{% endblock %}

  {% block header %}
      {% trans "Delete" as del_str %}
      {% include "wagtailadmin/shared/header.html" with title=del_str icon="doc-empty-inverse" %}
  {% endblock header %}

  {% block items_with_access %}
          {% if items %}
          <p>{% trans "Are you sure you want to delete these items?" %}</p>
          <ul>
              {% for item in items %}
              <li>
                  <a href="" target="_blank" rel="noreferrer">{{ item.item.title }}</a>
              </li>
              {% endfor %}
          </ul>
          {% endif %}
  {% endblock items_with_access %}

  {% block items_with_no_access %}

  {% blocktrans trimmed asvar no_access_msg count counter=items_with_no_access|length %}You don't have permission to delete this item{% plural %}You don't have permission to delete these items{% endblocktrans %}
  {% include './list_items_with_no_access.html' with items=items_with_no_access no_access_msg=no_access_msg %}

  {% endblock items_with_no_access %}

  {% block form_section %}
  {% if items %}
      {% trans 'Yes, delete' as action_button_text %}
      {% trans "No, don't delete" as no_action_button_text %}
      {% include 'wagtailadmin/bulk_actions/confirmation/form.html' with action_button_class="serious" %}
  {% else %}
      {% include 'wagtailadmin/bulk_actions/confirmation/go_back.html' %}
  {% endif %}
  {% endblock form_section %}


.. code-block:: django

  <!-- ./list_items_with_no_access.html -->
  {% extends 'wagtailadmin/bulk_actions/confirmation/list_items_with_no_access.html' %}
  {% load i18n %}

  {% block per_item %}
      {% if item.can_edit %}
      <a href="{% url 'wagtailadmin_pages:edit' item.item.id %}" target="_blank" rel="noreferrer">{{ item.item.title }}</a>
      {% else %}
      {{ item.item.title }}
      {% endif %}
  {% endblock per_item %}


The ``execute_action`` classmethod is the only method that must be overridden for the bulk action to work properly. It
takes a list of objects as the only required argument, and a bunch of keyword arguments that can be supplied by overriding
the ``get_execution_context`` method. For example.

.. code-block:: python

    @classmethod
    def execute_action(cls, objects, **kwargs):
        # the kwargs here is the output of the get_execution_context method
        user = kwargs.get('user', None)
        num_parent_objects, num_child_objects = 0, 0
        # you could run the action per object or run them in bulk using django's bulk update and delete methods
        for obj in objects:
            num_child_objects += obj.get_children().count()
            num_parent_objects += 1
            obj.delete(user=user)
            num_parent_objects += 1
        return num_parent_objects, num_child_objects


The ``get_execution_context`` method can be overridden to provide context to the ``execute_action``

.. code-block:: python

    def get_execution_context(self):
        return {
            'user': self.request.user
        }


The ``get_context_data`` method can be overridden to pass additional context to the confirmation template.

.. code-block:: python

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['new_key'] = some_value
        return context


The ``check_perm`` method can be overridden to check if an object has some permission or not. objects for which the ``check_perm``
returns ``False`` will be available in the context under the key ``'items_with_no_access'``.

.. code-block:: python

    def check_perm(self, obj):
        return obj.has_perm('some_perm')  # returns True or False


The success message shown on the admin can be customised by overriding the ``get_success_message`` method.

.. code-block:: python

    def get_success_message(self, num_parent_objects, num_child_objects):
        return _("{} objects, including {} child objects have been updated".format(num_parent_objects, num_child_objects))



Adding bulk actions to the page explorer
----------------------------------------

When creating a custom bulk action class for pages, subclass from ``wagtail.admin.views.pages.bulk_actions.page_bulk_action.PageBulkAction``
instead of ``wagtail.admin.views.bulk_action.BulkAction``

Basic example
~~~~~~~~~~~~~

.. code-block:: python

    from wagtail.admin.views.pages.bulk_actions.page_bulk_action import PageBulkAction
    from wagtail import hooks


    @hooks.register('register_bulk_action')
    class CustomPageBulkAction(PageBulkAction):
        ...



Adding bulk actions to the Images listing
-----------------------------------------

When creating a custom bulk action class for images, subclass from ``wagtail.images.views.bulk_actions.image_bulk_action.ImageBulkAction``
instead of ``wagtail.admin.views.bulk_action.BulkAction``

Basic example
~~~~~~~~~~~~~

.. code-block:: python

    from wagtail.images.views.bulk_actions.image_bulk_action import ImageBulkAction
    from wagtail import hooks


    @hooks.register('register_bulk_action')
    class CustomImageBulkAction(ImageBulkAction):
        ...



Adding bulk actions to the documents listing
--------------------------------------------

When creating a custom bulk action class for documents, subclass from ``wagtail.documents.views.bulk_actions.document_bulk_action.DocumentBulkAction``
instead of ``wagtail.admin.views.bulk_action.BulkAction``

Basic example
~~~~~~~~~~~~~

.. code-block:: python

    from wagtail.documents.views.bulk_actions.document_bulk_action import DocumentBulkAction
    from wagtail import hooks


    @hooks.register('register_bulk_action')
    class CustomDocumentBulkAction(DocumentBulkAction):
        ...



Adding bulk actions to the user listing
---------------------------------------

When creating a custom bulk action class for users, subclass from ``wagtail.users.views.bulk_actions.user_bulk_action.UserBulkAction``
instead of ``wagtail.admin.views.bulk_action.BulkAction``

Basic example
~~~~~~~~~~~~~

.. code-block:: python

    from wagtail.users.views.bulk_actions.user_bulk_action import UserBulkAction
    from wagtail import hooks


    @hooks.register('register_bulk_action')
    class CustomUserBulkAction(UserBulkAction):
        ...


Adding bulk actions to the snippets listing
-------------------------------------------

When creating a custom bulk action class for snippets, subclass from ``wagtail.snippets.bulk_actions.snippet_bulk_action.SnippetBulkAction``
instead of ``wagtail.admin.views.bulk_action.BulkAction``

Basic example
~~~~~~~~~~~~~

.. code-block:: python

    from wagtail.snippets.bulk_actions.snippet_bulk_action import SnippetBulkAction
    from wagtail import hooks


    @hooks.register('register_bulk_action')
    class CustomSnippetBulkAction(SnippetBulkAction):
        ...

If you want to apply an action only to certain snippets, override the ``models`` list in the action class

.. code-block:: python

    from wagtail.snippets.bulk_actions.snippet_bulk_action import SnippetBulkAction
    from wagtail import hooks


    @hooks.register('register_bulk_action')
    class CustomSnippetBulkAction(SnippetBulkAction):
        models = [SnippetA, SnippetB]
        ...
