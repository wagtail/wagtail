.. _modeladmin_reversing_urls:

======================================
Reversing ModelAdmin URLs
======================================

You can use the ModelAdmin's ``url_helper`` methods to easily get admin URLs for the various
actions such as create, view or edit.

.. contents::
    :local:
    :depth: 1

----------------------
Getting the URL Helper
----------------------

You will need to import your ``MyModelAdmin`` that was creaed,
instantiate it and then access the url_helper method.

.. code-block:: python

    from .wagtail_hooks import MyModelAdmin

    url_helper = MyModelAdmin().url_helper


.. _modeladmin_url_helper_get_action_url:

-----------------------------
``url_helper.get_action_url``
-----------------------------

**Expected value**: A string - action name.
**Expected value**: A quoted string - if getting a URL for a specific ID.

``get_action_url`` can be called with just an action name such as ``'index'`` or ``'create'``.
This will return a relative URL to load that action for the specific model, eg. `/admin/my-page-model/edit`.
If you pass in a second argument, it will be treated as the Primary Key (PK) or ID of the entity, ensure you wrap any data in ``quote`` to ensure it is safe to use in a URL.

.. code-block:: python

    from django.contrib.admin.utils import quote
    from .wagtail_hooks import MyPageModelAdmin

    url_helper = MyPageModelAdmin().url_helper

    index_url = url_helper.get_action_url('index')
    edit_person_1_url = url_helper.get_action_url('edit', quote(1))
    delete_person_1_url = url_helper.get_action_url('delete', quote(1))


The default available actions are:

* ``'index'``
* ``'create'``
* ``'choose_parent'`` **only for page models**
* ``'edit'`` **requires pk**
* ``'delete'`` **requires pk**
* ``'inspect'`` **requires pk & inspect enabled**

Read more about how [customise to the behaviour of url_helper see :ref:`modeladmin_url_helper_class`.

.. _modeladmin_url_helper_index_url:

------------------------
``url_helper.index_url``
------------------------

The ``index_url`` is cached and available via ``url_helper.index_url``.

.. code-block:: python

    from django.contrib.admin.utils import quote
    from .wagtail_hooks import MyModelAdmin

    url_helper = MyModelAdmin().url_helper

    index_url = url_helper.get_action_url('index')
    also_index_url = url_helper.index_url



.. _modeladmin_url_helper_create_url:

-------------------------
``url_helper.create_url``
-------------------------

The ``create_url`` is cached and available via ``url_helper.create_url``.

.. code-block:: python

    from django.contrib.admin.utils import quote
    from .wagtail_hooks import MyModelAdmin

    url_helper = MyModelAdmin().url_helper

    create_url = url_helper.get_action_url('create')
    also_create_url = url_helper.create_url
