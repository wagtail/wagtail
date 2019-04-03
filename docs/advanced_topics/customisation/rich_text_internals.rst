Rich text internals
===================

At first glance, Wagtail's rich text capabilities appear to give editors direct control over a block of HTML content. In reality, it's necessary to give editors a representation of rich text content that is several steps removed from the final HTML output, for several reasons:

 * The editor interface needs to filter out certain kinds of unwanted markup; this includes malicious scripting, font styles pasted from an external word processor, and elements which would break the validity or consistency of the site design (for example, pages will generally reserve the ``<h1>`` element for the page title, and so it would be inappropriate to allow users to insert their own additional ``<h1>`` elements through rich text).
 * Rich text fields can specify a ``features`` argument to further restrict the elements permitted in the field - see :ref:`rich_text_features`.
 * Enforcing a subset of HTML helps to keep presentational markup out of the database, making the site more maintainable, and making it easier to repurpose site content (including, potentially, producing non-HTML output such as `LaTeX <https://www.latex-project.org/>`_).
 * Elements such as page links and images need to preserve metadata such as the page or image ID, which is not present in the final HTML representation.

This requires the rich text content to go through a number of validation and conversion steps; both between the editor interface and the version stored in the database, and from the database representation to the final rendered HTML.

For this reason, extending Wagtail's rich text handling to support a new element is more involved than simply saying (for example) "enable the ``<blockquote>`` element", since various components of Wagtail - both client and server-side - need to agree on how to handle that feature, including how it should be exposed in the editor interface, how it should be represented within the database, and (if appropriate) how it should be translated when rendered on the front-end.

The components involved in Wagtail's rich text handling are described below.


Data format
-----------

Rich text data (as handled by :ref:`RichTextField <rich-text>`, and ``RichTextBlock`` within :doc:`StreamField </topics/streamfield>`) is stored in the database in a format that is similar, but not identical, to HTML. For example, a link to a page might be stored as:

.. code-block:: html

    <p><a linktype="page" id="3">Contact us</a> for more information.</p>

Here, the ``linktype`` attribute identifies a rule that shall be used to rewrite the tag. When rendered on a template through the ``|richtext`` filter (see :ref:`rich-text-filter`), this is converted into valid HTML:

.. code-block:: html

    <p><a href="/contact-us/">Contact us</a> for more information.</p>

In the case of ``RichTextBlock``, the block's value is a ``RichText`` object which performs this conversion automatically when rendered as a string, so the ``|richtext`` filter is not necessary.

Likewise, an image inside rich text content might be stored as:

.. code-block:: html

    <embed embedtype="image" id="10" alt="A pied wagtail" format="left" />

which is converted into an ``img`` element when rendered:

.. code-block:: html

    <img alt="A pied wagtail" class="richtext-image left" height="294" src="/media/images/pied-wagtail.width-500_ENyKffb.jpg" width="500">

Again, the ``embedtype`` attribute identifies a rule that shall be used to rewrite the tag. All tags other than ``<a linktype="...">`` and ``<embed embedtype="..." />`` are left unchanged in the converted HTML.

A number of additional constraints apply to ``<a linktype="...">`` and ``<embed embedtype="..." />`` tags, to allow the conversion to be performed efficiently via string replacement:

 * The tag name and attributes must be lower-case
 * Attribute values must be quoted with double-quotes
 * ``embed`` elements must use XML self-closing tag syntax (i.e. end in ``/>`` instead of a closing ``</embed>`` tag)
 * The only HTML entities permitted in attribute values are ``&lt;``, ``&gt;``, ``&amp;`` and ``&quot;``


The feature registry
--------------------

Any app within your project can define extensions to Wagtail's rich text handling, such as new ``linktype`` and ``embedtype`` rules. An object known as the *feature registry* serves as a central source of truth about how rich text should behave. This object can be accessed through the :ref:`register_rich_text_features` hook, which is called on startup to gather all definitions relating to rich text:

.. code-block:: python

    # my_app/wagtail_hooks.py

    from wagtail.core import hooks

    @hooks.register('register_rich_text_features')
    def register_my_feature(features):
        # add new definitions to 'features' here


Link rewrite handlers
---------------------

.. method:: FeatureRegistry.register_link_type(linktype, handler)

The ``register_link_type`` method allows you to define a function to be called when an ``<a>`` tag with a given ``linktype`` attribute is encountered. This function receives a dictionary of attributes from the original ``<a>`` tag, and returns a string to replace that opening tag (which must be a valid HTML ``<a>`` tag). The link element content and closing ``</a>`` tag is left unchanged.

.. code-block:: python

    from django.utils.html import escape
    from wagtail.core import hooks
    from myapp.models import Report

    def report_link_handler(attrs):
        # Handle a link of the form `<a linktype="report" id="123">`
        try:
            report = Report.objects.get(id=attrs['id'])
        except (Report.DoesNotExist, KeyError):
            return "<a>"

        return '<a href="%s">' % escape(report.url)


    @hooks.register('register_rich_text_features')
    def register_report_link(features):
        features.register_link_type('report', report_link_handler)

It is also possible to define link rewrite handler for Wagtail’s built-in ``external`` and ``email`` links, even though they do not have a predefined ``linktype``. For example, if you want external links to have a ``rel="nofollow"`` attribute for SEO purposes:

.. code-block:: python

    from django.utils.html import escape
    from wagtail.core import hooks

    def external_link_handler(attrs):
        href = attrs["href"]
        return '<a href="%s" rel="nofollow">' % escape(href)

    @hooks.register('register_rich_text_features')
    def register_external_link(features):
        features.register_link_type('external', external_link_handler)

Similarly you can use ``email`` linktype to add a custom rewrite handler for email links (e.g. to obfuscate emails in rich text).

Embed rewrite handlers
----------------------

.. method:: FeatureRegistry.register_embed_type(embedtype, handler)

The ``register_embed_type`` method allows you to define a function to be called when an ``<embed />`` tag with a given ``embedtype`` attribute is encountered. This function receives a dictionary of attributes from the original ``<embed>`` element, and returns an HTML string to replace it.

.. code-block:: python

    from wagtail.core import hooks
    from myapp.models import Chart

    def chart_embed_handler(attrs):
        # Handle an embed of the form `<embed embedtype="chart" id="123" color="red" />`
        try:
            chart = Chart.objects.get(id=attrs['id'])
        except (Chart.DoesNotExist, KeyError):
            return ""

        return chart.as_html(color=attrs.get('color', 'black'))


    @hooks.register('register_rich_text_features')
    def register_chart_embed(features):
        features.register_embed_type('chart', chart_embed_handler)


Editor widgets
--------------

The editor interface used on rich text fields can be configured with the :ref:`WAGTAILADMIN_RICH_TEXT_EDITORS <WAGTAILADMIN_RICH_TEXT_EDITORS>` setting. Wagtail provides two editor implementations: ``wagtail.admin.rich_text.DraftailRichTextArea`` (the `Draftail <https://www.draftail.org/>`_ editor based on `Draft.js <https://draftjs.org/>`_) and ``wagtail.admin.rich_text.HalloRichTextArea`` (deprecated, based on `Hallo.js <http://hallojs.org/>`_).

It is possible to create your own rich text editor implementation. At minimum, a rich text editor is a Django :class:`~django.forms.Widget` subclass whose constructor accepts an ``options`` keyword argument (a dictionary of editor-specific configuration options sourced from the ``OPTIONS`` field in ``WAGTAILADMIN_RICH_TEXT_EDITORS``), and which consumes and produces string data in the HTML-like format described above.

Typically, a rich text widget also receives a ``features`` list, passed from either ``RichTextField`` / ``RichTextBlock`` or the ``features`` option in ``WAGTAILADMIN_RICH_TEXT_EDITORS``, which defines the features available in that instance of the editor (see :ref:`rich_text_features`). To opt in to supporting features, set the attribute ``accepts_features = True`` on your widget class; the widget constructor will then receive the feature list as a keyword argument ``features``.

There is a standard set of recognised feature identifiers as listed under :ref:`rich_text_features`, but this is not a definitive list; feature identifiers are only defined by convention, and it is up to each editor widget to determine which features it will recognise, and adapt its behaviour accordingly. Individual editor widgets might implement fewer or more features than the default set, either as built-in functionality or through a plugin mechanism if the editor widget has one.

For example, a third-party Wagtail extension might introduce ``table`` as a new rich text feature, and provide implementations for the Draftail and Hallo editors (which both provide a plugin mechanism). In this case, the third-party extension will not be aware of your custom editor widget, and so the widget will not know how to handle the ``table`` feature identifier. Editor widgets should silently ignore any feature identifiers that they do not recognise.

The ``default_features`` attribute of the feature registry is a list of feature identifiers to be used whenever an explicit feature list has not been given in ``RichTextField`` / ``RichTextBlock`` or ``WAGTAILADMIN_RICH_TEXT_EDITORS``. This list can be modified within the ``register_rich_text_features`` hook to make new features enabled by default, and retrieved by calling ``get_default_features()``.

.. code-block:: python

    @hooks.register('register_rich_text_features')
    def make_h1_default(features):
        features.default_features.append('h1')


Outside of the ``register_rich_text_features`` hook - for example, inside a widget class - the feature registry can be imported as the object ``wagtail.core.rich_text.features``. A possible starting point for a rich text editor with feature support would be:

.. code-block:: python

    from django.forms import widgets
    from wagtail.core.rich_text import features

    class CustomRichTextArea(widgets.TextArea):
        accepts_features = True

        def __init__(self, *args, **kwargs):
            self.options = kwargs.pop('options', None)

            self.features = kwargs.pop('features', None)
            if self.features is None:
                self.features = features.get_default_features()

            super().__init__(*args, **kwargs)


Editor plugins
--------------

.. method:: FeatureRegistry.register_editor_plugin(editor_name, feature_name, plugin_definition)

Rich text editors often provide a plugin mechanism to allow extending the editor with new functionality. The ``register_editor_plugin`` method provides a standardised way for ``register_rich_text_features`` hooks to define plugins to be pulled in to the editor when a given rich text feature is enabled.

``register_editor_plugin`` is passed an editor name (a string uniquely identifying the editor widget - Wagtail uses the identifiers ``draftail`` and ``hallo`` for its built-in editors), a feature identifier, and a plugin definition object. This object is specific to the editor widget and can be any arbitrary value, but will typically include a :doc:`Django form media <django:topics/forms/media>` definition referencing the plugin's JavaScript code - which will then be merged into the editor widget's own media definition - along with any relevant configuration options to be passed when instantiating the editor.

.. method:: FeatureRegistry.get_editor_plugin(editor_name, feature_name)

Within the editor widget, the plugin definition for a given feature can be retrieved via the ``get_editor_plugin`` method, passing the editor's own identifier string and the feature identifier. This will return ``None`` if no matching plugin has been registered.

For details of the plugin formats for Wagtail's built-in editors, see :doc:`./extending_draftail` and :doc:`./extending_hallo`.


Format converters
-----------------

Editor widgets will often be unable to work directly with Wagtail's rich text format, and require conversion to their own native format. For Draftail, this is a JSON-based format known as ContentState (see `How Draft.js Represents Rich Text Data <https://medium.com/@rajaraodv/how-draft-js-represents-rich-text-data-eeabb5f25cf2>`_). Hallo.js and other editors based on HTML's ``contentEditable`` mechanism require valid HTML, and so Wagtail uses a convention referred to as "editor HTML", where the additional data required on link and embed elements is stored in ``data-`` attributes, for example: ``<a href="/contact-us/" data-linktype="page" data-id="3">Contact us</a>``.

Wagtail provides two utility classes, ``wagtail.admin.rich_text.converters.contentstate.ContentstateConverter`` and ``wagtail.admin.rich_text.converters.editor_html.EditorHTMLConverter``, to perform conversions between rich text format and the native editor formats. These classes are independent of any editor widget, and distinct from the rewriting process that happens when rendering rich text onto a template.

Both classes accept a ``features`` list as an argument to their constructor, and implement two methods, ``from_database_format(data)`` which converts Wagtail rich text data to the editor's format, and ``to_database_format(data)`` which converts editor data to Wagtail rich text format.

As with editor plugins, the behaviour of a converter class can vary according to the feature list passed to it. In particular, it can apply whitelisting rules to ensure that the output only contains HTML elements corresponding to the currently active feature set. The feature registry provides a ``register_converter_rule`` method to allow ``register_rich_text_features`` hooks to define conversion rules that will be activated when a given feature is enabled.

.. method:: FeatureRegistry.register_converter_rule(converter_name, feature_name, rule_definition)

``register_editor_plugin`` is passed a converter name (a string uniquely identifying the converter class - Wagtail uses the identifiers ``contentstate`` and ``editorhtml``), a feature identifier, and a rule definition object. This object is specific to the converter and can be any arbitrary value.

For details of the rule definition format for the ``contentstate`` and ``editorhtml`` converters, see :doc:`./extending_draftail` and :doc:`./extending_hallo` respectively.

.. method:: FeatureRegistry.get_converter_rule(converter_name, feature_name)

Within a converter class, the rule definition for a given feature can be retrieved via the ``get_converter_rule`` method, passing the converter's own identifier string and the feature identifier. This will return ``None`` if no matching rule has been registered.
