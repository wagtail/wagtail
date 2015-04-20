CSS coding guidelines
===========================

Our CSS is written in Sass, using the SCSS syntax.

Spacing
~~~~~~~

-  Use soft-tabs with a four space indent. Spaces are the only way to
   guarantee code renders the same in any person's environment.
-  Put spaces after ``:`` in property declarations.
-  Put spaces before ``{`` in rule declarations.
-  Put line breaks between rulesets.
-  When grouping selectors, keep individual selectors to a single line.
-  Place closing braces of declaration blocks on a new line.
-  Each declaration should appear on its own line for more accurate
   error reporting.
-  Add a newline at the end of your ``.scss`` files.
-  Strip trailing whitespace from your rules.

Formatting
~~~~~~~~~~

-  Use hex color codes ``#000`` unless using ``rgba()`` in raw CSS
   (SCSS' ``rgba()`` function is overloaded to accept hex colors as a
   param, e.g., ``rgba(#000, .5)``).
-  Use ``//`` for comment blocks (instead of ``/* */``).
-  Use single quotes for string values
   ``background: url('my/image.png')`` or ``content: 'moose'``
-  Avoid specifying units for zero values, e.g., ``margin: 0;`` instead
   of ``margin: 0px;``.
-  Strive to limit use of shorthand declarations to instances where you
   must explicitly set all the available values.

Sass imports
~~~~~~~~~~~~

Leave off underscores and file extensions in includes:

.. code-block:: scss

    // Bad
    @import 'components/_widget.scss'

    // Better
    @import 'components/widget'

Pixels vs. ems
~~~~~~~~~~~~~~

Use ``rems`` for ``font-size``, because they offer
absolute control over text. Additionally, unit-less ``line-height`` is
preferred because it does not inherit a percentage value of its parent
element, but instead is based on a multiplier of the ``font-size``.

Specificity (classes vs. ids)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~~

Never reference ``js-`` prefixed class names from CSS files. ``js-`` are
used exclusively from JS files.

Use the SMACSS ``is-`` `prefix <https://smacss.com/book/type-state>`__
for state rules that are shared between CSS and JS.

Misc
~~~~

As a rule of thumb, avoid unnecessary nesting in SCSS. At most, aim for
three levels. If you cannot help it, step back and rethink your overall
strategy (either the specificity needed, or the layout of the nesting).

Examples
~~~~~~~~

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

Vendor prefixes
~~~~~~~~~~~~~~~

Line up your vendor prefixes.

.. code-block:: scss

    // Example of good prefix formatting practices
    .styleguide-format {
        -webkit-transition: opacity 0.2s ease-out;
           -moz-transition: opacity 0.2s ease-out;
            -ms-transition: opacity 0.2s ease-out;
             -o-transition: opacity 0.2s ease-out;
                transition: opacity 0.2s ease-out;
    }

Don't write vendor prefixes for ``border-radius``, it's pretty well supported.

If you're unsure, you can always check support at
`caniuse <http://caniuse.com/>`_


Linting SCSS
~~~~~~~~~~~~

The guidelines are included in a ``.scss-lint.yml`` file so that you can
check that your code conforms to the style guide.

Run the linter with ``scss-lint .`` from the wagtail project root.
You'll need to have the linter installed to do this. You can get it by
running:

.. code-block:: bash

    gem install scss-lint
