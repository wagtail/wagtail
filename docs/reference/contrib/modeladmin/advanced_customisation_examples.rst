
.. _modeladmin_advanced_customisation_intro:

==========================================
Advanced modeladmin customisation examples
==========================================

Unlike Django's class of the same name, Wagtail's ``ModelAmin`` class acts
as a 'controller', calling upon many swappable, reuseable components to do the
brunt of the work. The theory is: If you want to do something differently, you
can write new classes (or extend the ones provided by  ``modeladmin``) and
easily configure your ``ModelAdmin`` class use those instead.

.. _modeladmin_advanced_customisation_considerations:

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

----------------------
Customisation examples
----------------------

.. _customising_modeladmin_list_thumbnail:

Displaying a thumbnail image for each item in the listing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Content to follow.

.. _customising_modeladmin_adding_a_button:
 
Adding a new buttons for each row in IndexView
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Content to follow.

.. _customising_modeladmin_save_current_user_on_object:

Adding the user from the request to an object on save
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Content to follow.
