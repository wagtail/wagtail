
TableBlock
==========

The TableBlock module provides an HTML table block type for StreamField. This module uses `handsontable 6.2.2 <https://handsontable.com/>`_ to provide users with the ability to create and edit HTML tables in Wagtail. Table blocks provides a caption field for accessibility.

.. image:: ../../_static/images/screen40_table_block.png


Installation
------------

Add ``"wagtail.contrib.table_block"`` to your INSTALLED_APPS:

.. code-block:: python

    INSTALLED_APPS = [
      ...

      "wagtail.contrib.table_block",
    ]


Basic Usage
-----------

After installation, the TableBlock module can be used in a similar fashion to other StreamField blocks in the Wagtail core.

Import the TableBlock ``from wagtail.contrib.table_block.blocks import TableBlock`` and add it to your StreamField declaration.

.. code-block:: python

  class DemoStreamBlock(StreamBlock):
      ...
      table = TableBlock()


Then, on your page template, the ``{% include_block %}`` tag (called on either the individual block, or the StreamField value as a whole) will render any table blocks it encounters as an HTML ``<table>`` element:

.. code-block:: html+django

    {% load wagtailcore_tags %}

    {% include_block page.body %}

Or:

.. code-block:: html+django

    {% load wagtailcore_tags %}

    {% for block in page.body %}
        {% if block.block_type == 'table' %}
            {% include_block block %}
        {% else %}
            {# rendering for other block types #}
        {% endif %}
    {% endfor %}


Advanced Usage
--------------

Default Configuration
^^^^^^^^^^^^^^^^^^^^^

When defining a TableBlock, Wagtail provides the ability to pass an optional ``table_options`` dictionary. The default TableBlock dictionary looks like this:

.. code-block:: python

  default_table_options = {
      'minSpareRows': 0,
      'startRows': 3,
      'startCols': 3,
      'colHeaders': False,
      'rowHeaders': False,
      'contextMenu': [
          'row_above',
          'row_below',
          '---------',
          'col_left',
          'col_right',
          '---------',
          'remove_row',
          'remove_col',
          '---------',
          'undo',
          'redo'
      ],
      'editor': 'text',
      'stretchH': 'all',
      'height': 108,
      'language': language,
      'renderer': 'text',
      'autoColumnSize': False,
  }


Configuration Options
^^^^^^^^^^^^^^^^^^^^^

Every key in the ``table_options`` dictionary maps to a `handsontable <https://handsontable.com/>`_ option. These settings can be changed to alter the behaviour of tables in Wagtail. The following options are available:

* `minSpareRows <https://handsontable.com/docs/6.2.2/Options.html#minSpareRows>`_ - The number of rows to append to the end of an empty grid. The default setting is 0.
* `startRows <https://handsontable.com/docs/6.2.2/Options.html#startRows>`_ - The default number of rows for a new table.
* `startCols <https://handsontable.com/docs/6.2.2/Options.html#startCols>`_ - The default number of columns for new tables.
* `colHeaders <https://handsontable.com/docs/6.2.2/Options.html#colHeaders>`_ - Can be set to ``True`` or ``False``. This setting designates if new tables should be created with column headers. **Note:** this only sets the behaviour for newly created tables. Page editors can override this by checking the the “Column header” checkbox in the table editor in the Wagtail admin.
* `rowHeaders <https://handsontable.com/docs/6.2.2/Options.html#rowHeaders>`_ - Operates the same as ``colHeaders`` to designate if new tables should be created with the first column as a row header. Just like ``colHeaders`` this option can be overridden by the page editor in the Wagtail admin.
* `contextMenu <https://handsontable.com/docs/6.2.2/Options.html#contextMenu>`_ - Enables or disables the Handsontable right-click menu. By default this is set to ``True``. Alternatively you can provide a list or a dictionary with [specific options](https://handsontable.com/docs/6.2.2/demo-context-menu.html#page-specific).
* `editor <https://handsontable.com/docs/6.2.2/Options.html#editor>`_ - Defines the editor used for table cells. The default setting is text.
* `stretchH <https://handsontable.com/docs/6.2.2/Options.html#stretchH>`_ - Sets the default horizontal resizing of tables. Options include, 'none', 'last', and 'all'. By default TableBlock uses 'all' for the even resizing of columns.
* `height <https://handsontable.com/docs/6.2.2/Options.html#height>`_ - The default height of the grid. By default TableBlock sets the height to ``108`` for the optimal appearance of new tables in the editor. This is optimized for tables with ``startRows`` set to ``3``. If you change the number of ``startRows`` in the configuration, you might need to change the ``height`` setting to improve the default appearance in the editor.
* `language <https://handsontable.com/docs/6.2.2/Options.html#language>`_ - The default language setting. By default TableBlock tries to get the language from ``django.utils.translation.get_language``. If needed, this setting can be overridden here.
* `renderer <https://handsontable.com/docs/6.2.2/Options.html#renderer>`_ - The default setting Handsontable uses to render the content of table cells.
* `autoColumnSize <https://handsontable.com/docs/6.2.2/Options.html#autoColumnSize>`_ - Enables or disables the ``autoColumnSize`` plugin. The TableBlock default setting is ``False``.

A `complete list of handsontable options <https://handsontable.com/docs/6.2.2/Options.html>`_ can be found on the Handsontable website.


Changing the default table_options
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To change the default table options just pass a new table_options dictionary when a new TableBlock is declared.

.. code-block:: python

  new_table_options = {
      'minSpareRows': 0,
      'startRows': 6,
      'startCols': 4,
      'colHeaders': False,
      'rowHeaders': False,
      'contextMenu': True,
      'editor': 'text',
      'stretchH': 'all',
      'height': 216,
      'language': 'en',
      'renderer': 'text',
      'autoColumnSize': False,
  }

  class DemoStreamBlock(StreamBlock):
      ...
      table = TableBlock(table_options=new_table_options)


Supporting cell alignment
^^^^^^^^^^^^^^^^^^^^^^^^^^

You can activate the `alignment` option by setting a custom `contextMenu` which allows you to set the alignment on a cell selection.
HTML classes set by handsontable will be kept on the rendered block. You'll then be able to apply your own custom CSS rules to preserve the style. Those class names are:

* Horizontal: ``htLeft``, ``htCenter``, ``htRight``, ``htJustify``
* Vertical: ``htTop``, ``htMiddle``, ``htBottom``

.. code-block:: python

  new_table_options = {
      'contextMenu': [
          'row_above',
          'row_below',
          '---------',
          'col_left',
          'col_right',
          '---------',
          'remove_row',
          'remove_col',
          '---------',
          'undo',
          'redo',
          '---------',
          'copy',
          'cut'
          '---------',
          'alignment',
      ],
  }

    class DemoStreamBlock(StreamBlock):
        ...
        table = TableBlock(table_options=new_table_options)
