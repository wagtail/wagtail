Extending the Draftail Editor
=============================

Wagtail’s rich text editor is built with `Draftail <https://github.com/springload/draftail>`_, and its functionality can be extended through plugins.

Plugins come in three types:

* Inline styles – To format a portion of a line, eg. ``bold``, ``italic``, ``monospace``.
* Blocks – To indicate the structure of the content, eg. ``blockquote``, ``ol``.
* Entities – To enter additional data/metadata, eg. ``link`` (with a URL), ``image`` (with a file).

All of these plugins are created with a similar baseline, which we can demonstrate with one of the simplest examples – a custom feature for an inline style of ``strikethrough``.

.. code-block:: python

    import wagtail.admin.rich_text.editors.draftail.features as draftail_features
    from wagtail.admin.rich_text.converters.html_to_contentstate import InlineStyleElementHandler
    from wagtail.core import hooks

    # 1. Use the register_rich_text_features hook.
    @hooks.register('register_rich_text_features')
    def register_strikethrough_feature(features):
        """
        Registering the `strikethrough` feature, which uses the `STRIKETHROUGH` Draft.js inline style type,
        and is stored as HTML with an `<s>` tag.
        """
        feature_name = 'strikethrough'
        type_ = 'STRIKETHROUGH'
        tag = 's'

        # 2. Configure how Draftail handles the feature in its toolbar.
        control = {
            'type': type_,
            'label': 'S',
            'description': 'Strikethrough',
            # This isn’t even required – Draftail has predefined styles for STRIKETHROUGH.
            # 'style': {'textDecoration': 'line-through'},
        }

        # 3. Call register_editor_plugin to register the configuration for Draftail.
        features.register_editor_plugin(
            'draftail', feature_name, draftail_features.InlineStyleFeature(control)
        )

        # 4.configure the content transform from the DB to the editor and back.
        db_conversion = {
            'from_database_format': {tag: InlineStyleElementHandler(type_)},
            'to_database_format': {'style_map': {type_: tag}},
        }

        # 5. Call register_converter_rule to register the content transformation conversion.
        features.register_converter_rule('contentstate', feature_name, db_conversion)

These five steps will always be the same for all Draftail plugins. The important parts are to:

* Consistently use the feature’s Draft.js type or Wagtail feature names where appropriate.
* Give enough information to Draftail so it knows how to make a button for the feature, and how to render it (more on this later).
* Configure the conversion to use the right HTML element (as they are stored in the DB).

For detailed configuration options, head over to the `Draftail documentation <https://github.com/springload/draftail#formatting-options>`_ to see all of the details. Here are some parts worth highlighting about controls:

* The ``type`` is the only mandatory piece of information.
* To display the control in the toolbar, combine ``icon``, ``label`` and ``description``.
* The controls’ ``icon`` can be a string to use an icon font with CSS classes, say ``'icon': 'fas fa-user',``. It can also be an array of strings, to use SVG paths, or SVG symbol references eg. ``'icon': ['M100 100 H 900 V 900 H 100 Z'],``. The paths need to be set for a 1024x1024 viewbox.

Creating new inline styles
~~~~~~~~~~~~~~~~~~~~~~~~~~

In addition to the initial example, inline styles take a ``style`` property to define what CSS rules will be applied to text in the editor. Be sure to read the `Draftail documentation <https://github.com/springload/draftail#formatting-options>`_ on inline styles.

Finally, the DB to/from conversion uses an ``InlineStyleElementHandler`` to map from a given tag (``<s>`` in the example above) to a Draftail type, and the inverse mapping is done with `Draft.js exporter configuration <https://github.com/springload/draftjs_exporter>`_ of the ``style_map``.

Creating new blocks
~~~~~~~~~~~~~~~~~~~

Blocks are nearly as simple as inline styles:

.. code-block:: python

    from wagtail.admin.rich_text.converters.html_to_contentstate import BlockElementHandler

    @hooks.register('register_rich_text_features')
    def register_blockquote_feature(features):
        """
        Registering the `blockquote` feature, which uses the `blockquote` Draft.js block type,
        and is stored as HTML with a `<blockquote>` tag.
        """
        feature_name = 'blockquote'
        type_ = 'blockquote'
        tag = 'blockquote'

        control = {
            'type': type_,
            'label': '❝',
            'description': 'Blockquote',
            # We need to tell Draftail what element to use when displaying those blocks in the editor.
            'element': 'blockquote',
            # This isn't required as the blockquote tag could be styled directly.
            # 'className': 'editor__blockquote',
        }

        features.register_editor_plugin(
            'draftail', feature_name, draftail_features.BlockFeature(control)
        )

        features.register_converter_rule('contentstate', feature_name, {
            'from_database_format': {tag: BlockElementHandler(type_)},
            'to_database_format': {'block_map': {type_: tag}},
        })

Here are the main differences:

* We need to configure an ``element`` to tell Draftail how to render those blocks in the editor.
* We could use a ``className`` (say if ``element`` was ``div``) to style the blockquotes in the editor.
* We register the plugin with ``BlockFeature``.
* We set up the conversion with ``BlockElementHandler`` and ``block_map``.

That’s it! The extra complexity is that you may need to write CSS in conjunction with the ``className`` to style the blocks in the editor.

Creating new entities
~~~~~~~~~~~~~~~~~~~~~

.. warning::
    This is an advanced feature. Please carefully consider whether you really need this.

Entities aren’t simply formatting buttons in the toolbar. They usually need to be much more versatile, communicating to APIs or requesting further user input. As such,

* You will most likely need to write a **hefty dose of JavaScript**, some of it with React.
* The API is very **low-level**. You will most likely need some **Draft.js knowledge**.
* Custom UIs in rich text can be brittle. Be ready to spend time **testing in multiple browsers**.

The good news is that having such a low-level API will enable third-party Wagtail plugins to innovate on rich text features, proposing new kinds of experiences.
But in the meantime, consider implementing your UI through :doc:`StreamField <../../topics/streamfield>` instead, which has a battle-tested API meant for Django developers.

----

Here are the main requirements to create a new entity feature:

* Like for inline styles and blocks, register an editor plugin.
* The editor plugin must define a ``source``: a React component responsible for creating new entity instances in the editor, using the Draft.js API.
* The editor plugin also needs a ``decorator`` (for inline entities) or ``block`` (for block entities): a React component responsible for displaying entity instances within the editor.
* Like for inline styles and blocks, set up the to/from DB conversion.
* The conversion usually is more involved, since entities contain data that needs to be serialised to HTML.

To write the React components, Wagtail exposes its own React and Draft.js dependencies as global variables. Read more about this in :ref:`extending_clientside_components`.
To go further, please look at the `Draftail documentation <https://github.com/springload/draftail#formatting-options>`_ as well as the `Draft.js exporter documentation <https://github.com/springload/draftjs_exporter>`_.

Here is a detailed example to showcase how those tools are used in the context of Wagtail.
For the sake of our example, we can imagine a news team working at a financial newspaper.
They want to write articles about the stock market, refer to specific stocks anywhere inside of their content (eg. "$TSLA" tokens in a sentence), and then have their article automatically enriched with the stock’s information (a link, a number, a sparkline).

The editor toolbar could contain a "stock chooser" that displays a list of available stocks, then inserts the user’s selection as a textual token. For our example, we will just pick a stock at random:

.. image:: ../../_static/images/draftail_entity_stock_source.gif

Those tokens are then saved in the rich text on publish. When the news article is displayed on the site, we then insert live market data coming from an API next to each token:

.. image:: ../../_static/images/draftail_entity_stock_rendering.png
