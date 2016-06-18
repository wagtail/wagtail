
.. _customising_modeladmin_intro:

====================================
Customising ``modeladmin`` behaviour
====================================

For developers wanting to customise the representation of their models within 
Wagtail even further, or perhaps offer additional functionality to editors, the 
`ModelAdmin` class provides the means to do help you do that.

Unlike Django's class of the same name, Wagtail's ``ModelAmin`` class acts
as a 'controller', calling upon many swappable, reuseable components to do the
brunt of the work. The theory is: If you want to do something differently, you
can write new classes (or extend the ones provided by  ``modeladmin``) and
easily configure your ``ModelAdmin`` class use those instead.

.. _customising_modeladmin_considerations:

--------------------------
Development considerations
--------------------------

There are a few of points to consider before jumping into customisation:

-   Currently, the ``modeladmin`` app only provides add, edit and delete
    functionality for non page type models. Wagtail's existing
    page manangement views are used for performing most actions on page type
    instances, meaning customisation is limited.

-   `modeladmin` is a new part of Wagtail, and as such, component classes
    within the app may change in future releases as we strive to improve 
    functionality and performance. While we will never add breaking changes to
    future releases without notice or guidance on upgrade considerations,
    heavily customised `modeladmin` implementations will undoubtedly make it
    more complicated to update your project to use future Wagtail releases.

-   We cannot provide support for customised modeladmin implementations. 

.. _customising_modeladmin_components:

---------------------
What can I customise?
---------------------

.. _customising_modeladmin_helper_classes:

Helper classes
^^^^^^^^^^^^^^

Content to follow.

.. _customising_modeladmin_forms:

Form classes
^^^^^^^^^^^^

Content to follow.

.. _customising_modeladmin_view_classes:

View classes
^^^^^^^^^^^^

Content to follow.

.. _customising_modeladmin_methods:

``ModelAdmin`` class methods 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Content to follow.

.. _customising_modeladmin_examples:

----------------------
Customisation examples
----------------------

.. _customising_modeladmin_inspect_view:

Enabling the 'Inspect' view
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Content to follow.

.. _customising_modeladmin_list_thumbnail:

Displaying a thumbnail image for each item in the listing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Content to follow.

.. _customising_modeladmin_changing_buttons:
 
Changing the buttons that appear for each item in the listing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Content to follow.

.. _customising_modeladmin_save_current_user_on_object:

Adding current user from the request to an object on save
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Content to follow.
