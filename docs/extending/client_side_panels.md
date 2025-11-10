# Accessing panels from client-side code

On model creation and editing views that are defined through [panels](forms_panels_overview) - including the views for pages, [snippets](snippets) and [site settings](../reference/contrib/settings) - the panel structure is accessible to client-side code as the variable `window.wagtail.editHandler`. This makes it possible to retrieve and manipulate the form contents without navigating the HTML structure of the page, which is not guaranteed to remain stable across releases of Wagtail.

## `Panel`

`window.wagtail.editHandler` gives a `Panel` object corresponding to the top-level panel, usually a `TabbedInterface` or `ObjectList`. All panel objects have the following attributes and methods:

```{eval-rst}
.. js:attribute:: type

   The class name of the corresponding Python-side panel class, as a string.

.. js:attribute:: prefix

   The unique string identifier assigned to this panel; HTML elements within this panel may use this as a prefix on ``id`` attributes to ensure that they are globally unique.

.. js:function:: getPanelByName(name)

   Returns the descendant panel object that handles the model field or relation with the given name, or null if no such panel exists. This panel will typically be a ``FieldPanel``, ``InlinePanel`` or ``MultipleChooserPanel``.
```

## `PanelGroup`

Panels that act as a container for other panels (such as `ObjectList`, `TabbedInterface`, `FieldRowPanel` and `MultiFieldPanel`) are instances of `PanelGroup`. This provides one additional attribute:

```{eval-rst}
.. js:attribute:: children

   An array of child panels.
```


## `FieldPanel`

`FieldPanel` has the following additional methods:

```{eval-rst}
.. js:function:: getBoundWidget()

   Returns the :ref:`bound widget <bound_widget_api>` instance managed by the ``FieldPanel``. This provides access to the form field's value. For ``StreamField``, the returned object is the top-level block of the stream.

   .. note::
      This function may not be available for some third-party widget types, as it relies on the widget either rendering a single input element with the appropriate name, or providing a :ref:`telepath adapter <streamfield_widget_api>` with a ``getByName`` method (which was not part of the API prior to Wagtail 7.1).

.. js:function:: getErrorMessage()

   Returns the error message string currently being displayed within this panel, or null if there is no error.

.. js:function:: setErrorMessage(message)

   Sets the error message displayed within this panel to the given string; pass null to remove the error.
```

## `InlinePanel`

`InlinePanel` has the following additional method:

```{eval-rst}
.. js:function:: addForm()

   Appends a new blank form to the panel.
```
