JavaScript coding guidelines
============================

Write JavaScript according to the `Airbnb Styleguide <http://github.com/airbnb/javascript>`_, with some exceptions:

-  Use soft-tabs with a four space indent. Spaces are the only way to
   guarantee code renders the same in any person's environment.
-  We accept ``snake_case`` in object properties, such as
   ``ajaxResponse.page_title``, however camelCase or UPPER_CASE should be used
   everywhere else.


Linting and formatting code
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Wagtail provides some tooling configuration to help check your code meets the
styleguide. You'll need node.js and npm on your development machine.
Ensure project dependencies are installed by running ``npm install``

Linting code
------------

.. code-block:: console

    $ npm run lint:js

This will lint all the JS in the wagtail project, excluding vendor
files and compiled libraries.

Some of the modals are generated via server-side scripts. These include
template tags that upset the linter, so modal workflow JavaScript is
excluded from the linter.

Formatting code
---------------

.. code-block:: console

    $ npm run format:js

This will perform safe edits to conform your JS code to the styleguide.
It won't touch the line-length, or convert quotemarks from double to single.

Run the linter after you've formatted the code to see what manual fixes
you need to make to the codebase.

Changing the linter configuration
---------------------------------

Under the hood, the tasks use the `JavaScript Code Style <http://jscs.info/>`_ library.

To edit the settings for ignored files, or to change the linting rules,
edit the ``.jscsrc`` file in the wagtail project root.

A complete list of the possible linting rules can be found here:
`JSCS Rules <http://jscs.info/rules.html>`_
