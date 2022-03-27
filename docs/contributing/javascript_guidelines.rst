JavaScript coding guidelines
============================

Write JavaScript according to the `Airbnb Styleguide <https://github.com/airbnb/javascript>`_, with some exceptions:

-  Use `Prettier <https://prettier.io/>`_ for all formatting considerations.
-  We accept ``snake_case`` in object properties, such as
   ``ajaxResponse.page_title``, however camelCase or UPPER_CASE should be used
   everywhere else.


Linting and formatting code
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Wagtail uses `ESLint <https://eslint.org/>`_ and `Prettier <https://prettier.io/>`_.
You'll need Node and npm on your development machine.
Ensure project dependencies are installed by running ``npm install --no-save``.

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

For Prettier auto-formatting, run:

.. code-block:: console

    $ npm run format

If you want to autofix linting errors:

.. code-block:: console

    $ npm run lint:js -- --fix

This will perform safe edits to conform your JS code to the styleguide.
It won't touch the line-length, or convert quotemarks from double to single.

Run the linter after you've formatted the code to see what manual fixes
you need to make to the codebase.

Changing the linter configuration
---------------------------------

The configuration for the linting rules is managed in an external
repository so that it can be easily shared across other Wagtail projects
or plugins. This configuration can be found at
`eslint-config-wagtail <https://github.com/wagtail/eslint-config-wagtail>`_.
