(streamfield_widget_api)=

# Form widget client-side API

In order for the StreamField editing interface to dynamically create form fields, any Django form widgets used within StreamField blocks must have an accompanying JavaScript implementation, defining how the widget is rendered client-side and populated with data, and how to extract data from that field. Wagtail provides this implementation for widgets inheriting from `django.forms.widgets.Input`, `django.forms.Textarea`, `django.forms.Select` and `django.forms.RadioSelect`. For any other widget types, or ones which require custom client-side behaviour, you will need to provide your own implementation.

The [telepath](https://wagtail.github.io/telepath/) library is used to set up mappings between Python widget classes and their corresponding JavaScript implementations. To create a mapping, define a subclass of `wagtail.widget_adapters.WidgetAdapter` and register it with `wagtail.telepath.register`.

```python
from wagtail.telepath import register
   from wagtail.widget_adapters import WidgetAdapter

   class FancyInputAdapter(WidgetAdapter):
       # Identifier matching the one registered on the client side
       js_constructor = 'myapp.widgets.FancyInput'

       # Arguments passed to the client-side object
       def js_args(self, widget):
           return [
               # Arguments typically include the widget's HTML representation
               # and label ID rendered with __NAME__ and __ID__ placeholders,
               # for use in the client-side render() method
               widget.render('__NAME__', None, attrs={'id': '__ID__'}),
               widget.id_for_label('__ID__'),
               widget.extra_options,
           ]

       class Media:
           # JS / CSS includes required in addition to the widget's own media;
           # generally this will include the client-side adapter definition
           js = ['myapp/js/fancy-input-adapter.js']


   register(FancyInputAdapter(), FancyInput)
```

The JavaScript object associated with a widget instance should provide a single method:

```{eval-rst}
.. js:function:: render(placeholder, name, id, initialState)

   Render a copy of this widget into the current page, and perform any initialisation required.

   :param placeholder: An HTML DOM element to be replaced by the widget's HTML.
   :param name: A string to be used as the ``name`` attribute on the input element. For widgets that use multiple input elements (and have server-side logic for collating them back into a final value), this can be treated as a prefix, with further elements delimited by dashes. (For example, if ``name`` is ``'person-0'``, the widget may create elements with names ``person-0-first_name`` and ``person-0-surname`` without risking collisions with other field names on the form.)
   :param id: A string to be used as the ``id`` attribute on the input element. As with ``name``, this can be treated as a prefix for any further identifiers.
   :param initialState: The initial data to populate the widget with.

A widget's state will often be the same as the form field's value, but may contain additional data beyond what is processed in the form submission. For example, a page chooser widget consists of a hidden form field containing the page ID, and a read-only label showing the page title: in this case, the page ID by itself does not provide enough information to render the widget, and so the state is defined as a dictionary with `id` and `title` items.

The value returned by ``render`` is a 'bound widget' object allowing this widget instance's data to be accessed. This object should implement the following attributes and methods:

.. js:attribute:: idForLabel

   The HTML ID to use as the ``for`` attribute of a label referencing this widget, or null if no suitable HTML element exists.

.. js:function:: getValue()

   Returns the submittable value of this widget (typically the same as the input element's value).

.. js:function:: getState()

   Returns the internal state of this widget, as a value suitable for passing as the ``render`` method's ``initialState`` argument.

.. js:function:: setState(newState)

   Optional: updates this widget's internal state to the passed value.

.. js:function:: focus(soft)

   Sets the browser's focus to this widget, so that it receives input events. Widgets that do not have a concept of focus should do nothing. If ``soft`` is true, this indicates that the focus event was not explicitly triggered by a user action (for example, when a new block is inserted, and the first field is focused as a convenience to the user) - in this case, the widget should avoid performing obtrusive UI actions such as opening modals.
```
