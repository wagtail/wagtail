# Rich text internals

At first glance, Wagtail's rich text capabilities appear to give editors direct control over a block of HTML content. In reality, it's necessary to give editors a representation of rich text content that is several steps removed from the final HTML output, for several reasons:

-   The editor interface needs to filter out certain kinds of unwanted markup; this includes malicious scripting, font styles pasted from an external word processor, and elements which would break the validity or consistency of the site design (for example, pages will generally reserve the `<h1>` element for the page title, and so it would be inappropriate to allow users to insert their own additional `<h1>` elements through rich text).
-   Rich text fields can specify a `features` argument to further restrict the elements permitted in the field - see [Rich Text Features](rich_text_features).
-   Enforcing a subset of HTML helps to keep presentational markup out of the database, making the site more maintainable, and making it easier to repurpose site content (including, potentially, producing non-HTML output such as [LaTeX](https://www.latex-project.org/)).
-   Elements such as page links and images need to preserve metadata such as the page or image ID, which is not present in the final HTML representation.

This requires the rich text content to go through a number of validation and conversion steps; both between the editor interface and the version stored in the database, and from the database representation to the final rendered HTML.

For this reason, extending Wagtail's rich text handling to support a new element is more involved than simply saying (for example) "enable the `<blockquote>` element", since various components of Wagtail - both client and server-side - need to agree on how to handle that feature, including how it should be exposed in the editor interface, how it should be represented within the database, and (if appropriate) how it should be translated when rendered on the front-end.

The components involved in Wagtail's rich text handling are described below.

## Data format

Rich text data (as handled by [RichTextField](rich-text), and `RichTextBlock` within [StreamField](../topics/streamfield.rst)) is stored in the database in a format that is similar, but not identical, to HTML. For example, a link to a page might be stored as:

```html
<p><a linktype="page" id="3">Contact us</a> for more information.</p>
```

Here, the `linktype` attribute identifies a rule that shall be used to rewrite the tag. When rendered on a template through the `|richtext` filter (see [rich text filter](rich_text_filter)), this is converted into valid HTML:

```html
<p><a href="/contact-us/">Contact us</a> for more information.</p>
```

In the case of `RichTextBlock`, the block's value is a `RichText` object which performs this conversion automatically when rendered as a string, so the `|richtext` filter is not necessary.

Likewise, an image inside rich text content might be stored as:

```html
<embed embedtype="image" id="10" alt="A pied wagtail" format="left" />
```

which is converted into an `img` element when rendered:

```html
<img
    alt="A pied wagtail"
    class="richtext-image left"
    height="294"
    src="/media/images/pied-wagtail.width-500_ENyKffb.jpg"
    width="500"
/>
```

Again, the `embedtype` attribute identifies a rule that shall be used to rewrite the tag. All tags other than `<a linktype="...">` and `<embed embedtype="..." />` are left unchanged in the converted HTML.

A number of additional constraints apply to `<a linktype="...">` and `<embed embedtype="..." />` tags, to allow the conversion to be performed efficiently via string replacement:

-   The tag name and attributes must be lower-case
-   Attribute values must be quoted with double-quotes
-   `embed` elements must use XML self-closing tag syntax (those that end in `/>` instead of a closing `</embed>` tag)
-   The only HTML entities permitted in attribute values are `&lt;`, `&gt;`, `&amp;` and `&quot;`

## The feature registry

Any app within your project can define extensions to Wagtail's rich text handling, such as new `linktype` and `embedtype` rules. An object known as the _feature registry_ serves as a central source of truth about how rich text should behave. This object can be accessed through the [Register Rich Text Features](register_rich_text_features) hook, which is called on startup to gather all definitions relating to rich text:

```python

    # my_app/wagtail_hooks.py

    from wagtail import hooks

    @hooks.register('register_rich_text_features')
    def register_my_feature(features):
        # add new definitions to 'features' here
```

(rich_text_rewrite_handlers)=

## Rewrite handlers

Rewrite handlers are classes that know how to translate the content of rich text tags like `<a linktype="...">` and `<embed embedtype="..." />` into front-end HTML. For example, the `PageLinkHandler` class knows how to convert the rich text tag `<a linktype="page" id="123">` into the HTML tag `<a href="/path/to/page/123">`.

Rewrite handlers can also provide other useful information about rich text tags. For example, given an appropriate tag, `PageLinkHandler` can be used to extract which page is being referred to. This can be useful for downstream code that may want information about objects being referenced in rich text.

You can create custom rewrite handlers to support your own new `linktype` and `embedtype` tags. New handlers must be Python classes that inherit from either `wagtail.richtext.LinkHandler` or `wagtail.richtext.EmbedHandler`. Your new classes should override at least some of the following methods (listed here for `LinkHandler`, although `EmbedHandler` has an identical signature):

```{eval-rst}
.. class:: LinkHandler

    .. attribute:: identifier

        Required. The ``identifier`` attribute is a string that indicates which rich text tags should be handled by this handler.

        For example, ``PageLinkHandler.identifier`` is set to the string ``"page"``, indicating that any rich text tags with ``<a linktype="page">`` should be handled by it.

    .. method:: expand_db_attributes(attrs)

        Required. The ``expand_db_attributes`` method is expected to take a dictionary of attributes from a database rich text ``<a>`` tag (``<embed>`` for ``EmbedHandler``) and use it to generate valid frontend HTML.

        For example, ``PageLinkHandler.expand_db_attributes`` might receive ``{'id': 123}``, use it to retrieve the Wagtail page with ID 123, and render a link to its URL like ``<a href="/path/to/page/123">``.

    .. method:: get_model()

        Optional. The static ``get_model`` method only applies to those handlers that are used to render content related to Django models. This method allows handlers to expose the type of content that they know how to handle.

        For example, ``PageLinkHandler.get_model`` returns the Wagtail class ``Page``.

        Handlers that aren't related to Django models can leave this method undefined, and calling it will raise ``NotImplementedError``.

    .. method:: get_instance(attrs)

        Optional. The static or classmethod ``get_instance`` method also only applies to those handlers that are used to render content related to Django models. This method is expected to take a dictionary of attributes from a database rich text ``<a>`` tag (``<embed>`` for ``EmbedHandler``) and use it to return the specific Django model instance being referred to.

        For example, ``PageLinkHandler.get_instance`` might receive ``{'id': 123}`` and return the instance of the Wagtail ``Page`` class with ID 123.

        If left undefined, a default implementation of this method will query the ``id`` model field on the class returned by ``get_model`` using the provided ``id`` attribute; this can be overridden in your own handlers should you want to use some other model field.
```

Below is an example custom rewrite handler that implements these methods to add support for rich text linking to user email addresses. It supports the conversion of rich text tags like `<a linktype="user" username="wagtail">` to valid HTML like `<a href="mailto:hello@wagtail.org">`. This example assumes that equivalent front-end functionality has been added to allow users to insert these kinds of links into their rich text editor.

```python
from django.contrib.auth import get_user_model
from wagtail.rich_text import LinkHandler

class UserLinkHandler(LinkHandler):
    identifier = 'user'

    @staticmethod
    def get_model():
        return get_user_model()

    @classmethod
    def get_instance(cls, attrs):
        model = cls.get_model()
        return model.objects.get(username=attrs['username'])

    @classmethod
    def expand_db_attributes(cls, attrs):
        user = cls.get_instance(attrs)
        return '<a href="mailto:%s">' % user.email
```

### Registering rewrite handlers

Rewrite handlers must also be registered with the feature registry via the [register rich text features](register_rich_text_features) hook. Independent methods for registering both link handlers and embed handlers are provided.

```{eval-rst}
.. method:: FeatureRegistry.register_link_type(handler)

This method allows you to register a custom handler deriving from ``wagtail.rich_text.LinkHandler``, and adds it to the list of link handlers available during rich text conversion.
```

```python
# my_app/wagtail_hooks.py

from wagtail import hooks
from my_app.handlers import MyCustomLinkHandler

@hooks.register('register_rich_text_features')
def register_link_handler(features):
    features.register_link_type(MyCustomLinkHandler)
```

It is also possible to define link rewrite handlers for Wagtail’s built-in `external` and `email` links, even though they do not have a predefined `linktype`. For example, if you want external links to have a `rel="nofollow"` attribute for SEO purposes:

```python
from django.utils.html import escape
from wagtail import hooks
from wagtail.rich_text import LinkHandler

class NoFollowExternalLinkHandler(LinkHandler):
    identifier = 'external'

    @classmethod
    def expand_db_attributes(cls, attrs):
        href = attrs["href"]
        return '<a href="%s" rel="nofollow">' % escape(href)

@hooks.register('register_rich_text_features')
def register_external_link(features):
    features.register_link_type(NoFollowExternalLinkHandler)
```

Similarly, you can use `email` linktype to add a custom rewrite handler for email links (for example to obfuscate emails in rich text).

```{eval-rst}
.. method:: FeatureRegistry.register_embed_type(handler)

This method allows you to register a custom handler deriving from ``wagtail.rich_text.EmbedHandler``, and adds it to the list of embed handlers available during rich text conversion.
```

```python
# my_app/wagtail_hooks.py

from wagtail import hooks
from my_app.handlers import MyCustomEmbedHandler

@hooks.register('register_rich_text_features')
def register_embed_handler(features):
    features.register_embed_type(MyCustomEmbedHandler)
```

## Editor widgets

The editor interface used on rich text fields can be configured with the [WAGTAILADMIN_RICH_TEXT_EDITORS](wagtailadmin_rich_text_editors) setting. Wagtail provides an implementation: `wagtail.admin.rich_text.DraftailRichTextArea` (the [Draftail](https://www.draftail.org/) editor based on [Draft.js](https://draftjs.org/)).

It is possible to create your own rich text editor implementation. At minimum, a rich text editor is a Django **_class_ django.forms.Widget** subclass whose constructor accepts an `options` keyword argument (a dictionary of editor-specific configuration options sourced from the `OPTIONS` field in `WAGTAILADMIN_RICH_TEXT_EDITORS`), and which consumes and produces string data in the HTML-like format described above.

Typically, a rich text widget also receives a `features` list, passed from either `RichTextField` / `RichTextBlock` or the `features` option in `WAGTAILADMIN_RICH_TEXT_EDITORS`, which defines the features available in that instance of the editor (see [rich text features](rich_text_features)). To opt in to supporting features, set the attribute `accepts_features = True` on your widget class; the widget constructor will then receive the feature list as a keyword argument `features`.

There is a standard set of recognised feature identifiers as listed under [rich text features](rich_text_features), but this is not a definitive list; feature identifiers are only defined by convention, and it is up to each editor widget to determine which features it will recognise, and adapt its behaviour accordingly. Individual editor widgets might implement fewer or more features than the default set, either as built-in functionality or through a plugin mechanism if the editor widget has one.

For example, a third-party Wagtail extension might introduce `table` as a new rich text feature, and provide implementations for the Draftail editor (which provides a plugin mechanism). In this case, the third-party extension will not be aware of your custom editor widget, and so the widget will not know how to handle the `table` feature identifier. Editor widgets should silently ignore any feature identifiers that they do not recognise.

The `default_features` attribute of the feature registry is a list of feature identifiers to be used whenever an explicit feature list has not been given in `RichTextField` / `RichTextBlock` or `WAGTAILADMIN_RICH_TEXT_EDITORS`. This list can be modified within the `register_rich_text_features` hook to make new features enabled by default, and retrieved by calling `get_default_features()`.

```python
@hooks.register('register_rich_text_features')
def make_h1_default(features):
    features.default_features.append('h1')
```

Outside of the `register_rich_text_features` hook - for example, inside a widget class - the feature registry can be imported as the object `wagtail.rich_text.features`. A possible starting point for a rich text editor with feature support would be:

```python
from django.forms import widgets
from wagtail.rich_text import features

class CustomRichTextArea(widgets.TextArea):
    accepts_features = True

    def __init__(self, *args, **kwargs):
        self.options = kwargs.pop('options', None)

        self.features = kwargs.pop('features', None)
        if self.features is None:
            self.features = features.get_default_features()

        super().__init__(*args, **kwargs)
```

## Editor plugins

```{eval-rst}
.. method:: FeatureRegistry.register_editor_plugin(editor_name, feature_name, plugin_definition)

Rich text editors often provide a plugin mechanism to allow extending the editor with new functionality. The ``register_editor_plugin`` method provides a standardised way for ``register_rich_text_features`` hooks to define plugins to be pulled into the editor when a given rich text feature is enabled.

``register_editor_plugin`` is passed an editor name (a string uniquely identifying the editor widget - Wagtail uses the identifier ``draftail`` for the built-in editor), a feature identifier, and a plugin definition object. This object is specific to the editor widget and can be any arbitrary value, but will typically include a :doc:`Django form media <django:topics/forms/media>` definition referencing the plugin's JavaScript code - which will then be merged into the editor widget's own media definition - along with any relevant configuration options to be passed when instantiating the editor.

.. method:: FeatureRegistry.get_editor_plugin(editor_name, feature_name)

Within the editor widget, the plugin definition for a given feature can be retrieved via the ``get_editor_plugin`` method, passing the editor's own identifier string and the feature identifier. This will return ``None`` if no matching plugin has been registered.

For details of the plugin formats for Wagtail's built-in editors, see :doc:`./extending_draftail`.
```

(rich_text_format_converters)=

## Format converters

Editor widgets will often be unable to work directly with Wagtail's rich text format, and require conversion to their own native format. For Draftail, this is a JSON-based format known as ContentState (see [How Draft.js Represents Rich Text Data](https://rajaraodv.medium.com/how-draft-js-represents-rich-text-data-eeabb5f25cf2)). Editors based on HTML's `contentEditable` mechanism require valid HTML, and so Wagtail uses a convention referred to as "editor HTML", where the additional data required on link and embed elements is stored in `data-` attributes, for example: `<a href="/contact-us/" data-linktype="page" data-id="3">Contact us</a>`.

Wagtail provides two utility classes, `wagtail.admin.rich_text.converters.contentstate.ContentstateConverter` and `wagtail.admin.rich_text.converters.editor_html.EditorHTMLConverter`, to perform conversions between rich text format and the native editor formats. These classes are independent of any editor widget and distinct from the rewriting process that happens when rendering rich text onto a template.

Both classes accept a `features` list as an argument to their constructor and implement two methods, `from_database_format(data)` which converts Wagtail rich text data to the editor's format, and `to_database_format(data)` which converts editor data to Wagtail rich text format.

As with editor plugins, the behaviour of a converter class can vary according to the feature list passed to it. In particular, it can apply whitelisting rules to ensure that the output only contains HTML elements corresponding to the currently active feature set. The feature registry provides a `register_converter_rule` method to allow `register_rich_text_features` hooks to define conversion rules that will be activated when a given feature is enabled.

```{eval-rst}
.. method:: FeatureRegistry.register_converter_rule(converter_name, feature_name, rule_definition)

``register_editor_plugin`` is passed a converter name (a string uniquely identifying the converter class - Wagtail uses the identifiers ``contentstate`` and ``editorhtml``), a feature identifier, and a rule definition object. This object is specific to the converter and can be any arbitrary value.

For details of the rule definition format for the ``contentstate`` converter, see :doc:`./extending_draftail`.

.. method:: FeatureRegistry.get_converter_rule(converter_name, feature_name)

Within a converter class, the rule definition for a given feature can be retrieved via the ``get_converter_rule`` method, passing the converter's own identifier string and the feature identifier. This will return ``None`` if no matching rule has been registered.
```
