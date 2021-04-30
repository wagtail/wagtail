CSS coding guidelines
===========================

Our CSS is written in `Sass <https://sass-lang.com/>`_, using the SCSS syntax.

Compiling
~~~~~~~~~

The SCSS source files are compiled to CSS using the
`gulp <https://gulpjs.com/>`_ build system.
This requires `Node.js <https://nodejs.org>`_ to run.
To install the libraries required for compiling the SCSS,
run the following from the Wagtail repository root:

.. code-block:: console

    $ npm install --no-save


To compile the assets, run:

.. code-block:: console

    $ npm run build


Alternatively, the SCSS files can be monitored,
automatically recompiling when any changes are observed, by running:

.. code-block:: console

    $ npm start


Linting and formatting SCSS
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Wagtail uses the `stylelint <https://stylelint.io/>`_ linter.
You'll need Node.js and npm on your development machine.
Ensure project dependencies are installed by running ``npm install --no-save``

Linting code
------------

Run the linter from the wagtail project root:

.. code-block:: console

    $ npm run lint:css


The linter is configured to check your code for adherence to the guidelines
below, plus a little more.

Formatting code
---------------

If you want to autofix errors, you can run that command directly with:

.. code-block:: console

    $ npm run lint:css -- --fix

Changing the linter configuration
---------------------------------

The configuration for the linting rules is managed in an external
repository so that it can be easily shared across other Wagtail projects
or plugins. This configuration can be found at
`stylelint-config-wagtail <https://github.com/wagtail/stylelint-config-wagtail>`_.

Styleguide Reference
~~~~~~~~~~~~~~~~~~~~

Spacing
-------

-  Use soft-tabs with a four space indent. Spaces are the only way to
   guarantee code renders the same in any person's environment.
-  Put spaces after ``:`` in property declarations.
-  Put spaces before ``{`` in rule declarations.
-  Put line breaks between rulesets.
-  When grouping selectors, put each selector on its own line.
-  Place closing braces of declaration blocks on a new line.
-  Each declaration should appear on its own line for more accurate
   error reporting.
-  Add a newline at the end of your ``.scss`` files.
-  Strip trailing whitespace from your rules.
-  Add a space after the comma, in comma-delimited property values e.g ``rgba()``

Formatting
----------

-  Use hex color codes ``#000`` unless using ``rgba()`` in raw CSS
   (SCSS' ``rgba()`` function is overloaded to accept hex colors as a
   param, e.g., ``rgba(#000, .5)``).
-  Use ``//`` for comment blocks (instead of ``/* */``).
-  Use single quotes for string values
   ``background: url('my/image.png')``
-  Avoid specifying units for zero values, e.g., ``margin: 0;`` instead
   of ``margin: 0px;``.
-  Strive to limit use of shorthand declarations to instances where you
   must explicitly set all the available values.

Sass imports
------------

Leave off underscores and file extensions in includes:

.. code-block:: scss

    // Bad
    @import 'components/_widget.scss'

    // Better
    @import 'components/widget'

Pixels vs. ems
--------------

Use ``rems`` for ``font-size``, because they offer
absolute control over text. Additionally, unit-less ``line-height`` is
preferred because it does not inherit a percentage value of its parent
element, but instead is based on a multiplier of the ``font-size``.

Specificity (classes vs. ids)
-----------------------------

Always use classes instead of IDs in CSS code. IDs are overly specific and lead
to duplication of CSS.

When styling a component, start with an element + class namespace,
prefer direct descendant selectors by default, and use as little
specificity as possible. Here is a good example:

.. code-block:: html

    <ul class="category-list">
        <li class="item">Category 1</li>
        <li class="item">Category 2</li>
        <li class="item">Category 3</li>
    </ul>

.. code-block:: scss

    .category-list { // element + class namespace

        // Direct descendant selector > for list items
        > li {
            list-style-type: disc;
        }

        // Minimal specificity for all links
        a {
            color: #f00;
        }
    }

Class naming conventions
------------------------

Never reference ``js-`` prefixed class names from CSS files. ``js-`` are
used exclusively from JS files.

Use the SMACSS ``is-`` `prefix <https://smacss.com/book/type-state>`__
for state rules that are shared between CSS and JS.

Misc
----

As a rule of thumb, avoid unnecessary nesting in SCSS. At most, aim for
three levels. If you cannot help it, step back and rethink your overall
strategy (either the specificity needed, or the layout of the nesting).

Examples
--------

Here are some good examples that apply the above guidelines:

.. code-block:: scss

    // Example of good basic formatting practices
    .styleguide-format {
        color: #000;
        background-color: rgba(0, 0, 0, .5);
        border: 1px solid #0f0;
    }

    // Example of individual selectors getting their own lines (for error reporting)
    .multiple,
    .classes,
    .get-new-lines {
        display: block;
    }

    // Avoid unnecessary shorthand declarations
    .not-so-good {
        margin: 0 0 20px;
    }
    .good {
        margin-bottom: 20px;
    }
