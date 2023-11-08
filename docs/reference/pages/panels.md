(editing_api)=

# Panel types

## Built-in Fields and Choosers

Wagtail's panel mechanism automatically recognises Django model fields and provides them with an appropriate widget for input. You can use it by defining the field in your Django model as normal and passing the field name into
[`FieldPanel`](wagtail.admin.panels.FieldPanel) (or a suitable panel type) when defining your panels.

Here are some built-in panel types that you can use in your panel definitions. These are all subclasses of the base [`Panel`](wagtail.admin.panels.Panel) class, and unless otherwise noted, they accept all of `Panel`'s parameters in addition to their own.

```{eval-rst}
.. module:: wagtail.admin.panels
   :noindex:
```

(field_panel)=

### FieldPanel

```{eval-rst}
.. autoclass:: FieldPanel

    This is the panel to use for basic Django model field types. It provides a default icon and heading based on the model field definition, but they can be customised by passing additional arguments to the constructor. For more details, see :ref:`customising_panels`.

    .. attribute:: FieldPanel.field_name

        This is the name of the class property used in your model definition.

    .. attribute:: FieldPanel.widget (optional)

        This parameter allows you to specify a :doc:`Django form widget <django:ref/forms/widgets>` to use instead of the default widget for this field type.

    .. attribute:: FieldPanel.disable_comments (optional)

        This allows you to prevent a field level comment button showing for this panel if set to ``True``. See `Create and edit comments <https://guide.wagtail.org/en-latest/how-to-guides/manage-pages/#create-and-edit-comments>`_.

    .. attribute:: FieldPanel.permission (optional)

        Allows a field to be selectively shown to users with sufficient permission. Accepts a permission codename such as ``'myapp.change_blog_category'`` - if the logged-in user does not have that permission, the field will be omitted from the form. See Django's documentation on :ref:`custom permissions <django:custom-permissions>` for details on how to set permissions up; alternatively, if you want to set a field as only available to superusers, you can use any arbitrary string (such as ``'superuser'``) as the codename, since superusers automatically pass all permission tests.

    .. attribute:: FieldPanel.read_only (optional)

        Allows you to prevent a model field value from being set or updated by editors.

        For most field types, the field value will be rendered in the form for editors to see (along with field's label and help text), but no form inputs will be displayed, and the form will ignore attempts to change the value in POST data. For example by injecting a hidden input into the form HTML before submitting.

        By default, field values from ``StreamField`` or ``RichTextField`` are redacted to prevent rendering of potentially insecure HTML mid-form. You can change this behaviour for custom panel types by overriding ``Panel.format_value_for_display()``.

    .. attribute:: FieldPanel.attrs (optional)

        Allows a dictionary containing HTML attributes to be set on the rendered panel. If you assign a value of ``True`` or ``False`` to an attribute, it will be rendered as an HTML5 boolean attribute.

```

### MultiFieldPanel

```{eval-rst}
.. class:: MultiFieldPanel(children=(), *args, permission=None, **kwargs)

    This panel condenses several :class:`~wagtail.admin.panels.FieldPanel` s or choosers, from a ``list`` or ``tuple``, under a single ``heading`` string. To save space, you can :ref:`collapse the panel by default <collapsible>`.

    .. attribute:: MultiFieldPanel.children

        A ``list`` or ``tuple`` of child panels

    .. attribute:: MultiFieldPanel.permission (optional)

        Allows a panel to be selectively shown to users with sufficient permission. Accepts a permission codename such as ``'myapp.change_blog_category'`` - if the logged-in user does not have that permission, the panel will be omitted from the form. Similar to :attr:`FieldPanel.permission`.

    .. attribute:: MultiFieldPanel.attrs (optional)

        Allows a dictionary containing HTML attributes to be set on the rendered panel. If you assign a value of ``True`` or ``False`` to an attribute, it will be rendered as an HTML5 boolean attribute.

```

(inline_panels)=

### InlinePanel

```{eval-rst}
.. class:: InlinePanel(relation_name, panels=None, label='', min_num=None, max_num=None, **kwargs)

    This panel allows for the creation of a "cluster" of related objects over a join to a separate model, such as a list of related links or slides to an image carousel. For a full explanation on the usage of ``InlinePanel``, see :ref:`inline_models`. To save space, you can :ref:`collapse the panel by default <collapsible>`.

    .. attribute:: InlinePanel.relation_name

        The related_name label given to the cluster’s ParentalKey relation.

    .. attribute:: InlinePanel.panels (optional)

        The list of panels that will make up the child object's form. If not specified here, the `panels` definition on the child model will be used.

    .. attribute:: InlinePanel.label

        Text for the add button and heading for child panels. Used as the heading when ``heading`` is not present.

    .. attribute:: InlinePanel.min_num (optional)

        Minimum number of forms a user must submit.

    .. attribute:: InlinePanel.max_num (optional)

        Maximum number of forms a user must submit.

    .. attribute:: InlinePanel.attrs (optional)

        Allows a dictionary containing HTML attributes to be set on the rendered panel. If you assign a value of ``True`` or ``False`` to an attribute, it will be rendered as an HTML5 boolean attribute.

```

(inline_panel_events)=

#### JavaScript DOM events

You may want to execute some JavaScript when `InlinePanel` items are ready, added or removed. The `w-formset:ready`, `w-formset:added` and `w-formset:removed` events allow this.

```{versionadded} 5.2

```

For example, given a child model that provides a relationship between Blog and Person on `BlogPage`.

```python
class CustomInlinePanel(InlinePanel):
    class BoundPanel(InlinePanel.BoundPanel):
        class Media:
            js = ["js/inline-panel.js"]


class BlogPage(Page):
        # .. fields

        content_panels = Page.content_panels + [
               CustomInlinePanel("blog_person_relationship"),
              # ... other panels
        ]
```

Using the JavaScript as follows.

```javascript
// static/js/inline-panel.js

document.addEventListener('w-formset:ready', function (event) {
    console.info('ready', event);
});

document.addEventListener('w-formset:added', function (event) {
    console.info('added', event);
});

document.addEventListener('w-formset:removed', function (event) {
    console.info('removed', event);
});
```

Events will be dispatched and can trigger custom JavaScript logic such as setting up a custom widget.

(multiple_chooser_panel)=

### MultipleChooserPanel

````{class} MultipleChooserPanel(relation_name, chooser_field_name=None, panels=None, label='', min_num=None, max_num=None, **kwargs)

This is a variant of `InlinePanel` that improves the editing experience when the main feature of the child panel is a chooser for a `ForeignKey` relation (usually to an image, document, snippet or another page). Rather than the "Add" button inserting a new form to be filled in individually, it immediately opens up the chooser interface for that related object, in a mode that allows multiple items to be selected. The user is then returned to the main edit form with the appropriate number of child panels added and pre-filled.

`MultipleChooserPanel` accepts an additional required argument `chooser_field_name`, specifying the name of the `ForeignKey` relation that the chooser is linked to.

For example, given a child model that provides a gallery of images on `BlogPage`:

```python
class BlogPageGalleryImage(Orderable):
    page = ParentalKey(BlogPage, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.CASCADE, related_name='+'
    )
    caption = models.CharField(blank=True, max_length=250)

    panels = [
        FieldPanel('image'),
        FieldPanel('caption'),
    ]
```

The `MultipleChooserPanel` definition on `BlogPage` would be:

```python
        MultipleChooserPanel(
            'gallery_images', label="Gallery images", chooser_field_name="image"
        )
```

````

### FieldRowPanel

```{eval-rst}
.. class:: FieldRowPanel(children=(), *args, permission=None, **kwargs)

    This panel creates a columnar layout in the editing interface, where each of the child Panels appears alongside each other rather than below.

    Use of ``FieldRowPanel`` particularly helps reduce the "snow-blindness" effect of seeing so many fields on the page, for complex models. It also improves the perceived association between fields of a similar nature. For example if you created a model representing an "Event" which had a starting date and ending date, it may be intuitive to find the start and end date on the same "row".

    By default, the panel is divided into equal-width columns, but this can be overridden by adding ``col*`` class names to each of the child Panels of the FieldRowPanel. The Wagtail editing interface is laid out using a grid system. Classes ``col1``-``col12`` can be applied to each child of a FieldRowPanel to define how many columns they span out of the total number of columns. When grid items add up to 12 columns, the class ``col3`` will ensure that field appears 3 columns wide or a quarter the width. ``col4`` would cause the field to be 4 columns wide, or a third the width.

    .. attribute:: FieldRowPanel.children

        A ``list`` or ``tuple`` of child panels to display on the row

    .. attribute:: FieldRowPanel.permission (optional)

        Allows a panel to be selectively shown to users with sufficient permission. Accepts a permission codename such as ``'myapp.change_blog_category'`` - if the logged-in user does not have that permission, the panel will be omitted from the form. Similar to :attr:`FieldPanel.permission`.

    .. attribute:: FieldRowPanel.attrs (optional)

        Allows a dictionary containing HTML attributes to be set on the rendered panel. If you assign a value of ``True`` or ``False`` to an attribute, it will be rendered as an HTML5 boolean attribute.

```

### HelpPanel

```{eval-rst}
.. autoclass:: HelpPanel

    .. attribute:: HelpPanel.content

        HTML string that gets displayed in the panel.

    .. attribute:: HelpPanel.template

        Path to a template rendering the full panel HTML.

    .. attribute:: HelpPanel.attrs (optional)

        Allows a dictionary containing HTML attributes to be set on the rendered panel. If you assign a value of ``True`` or ``False`` to an attribute, it will be rendered as an HTML5 boolean attribute.

```

### PageChooserPanel

```{eval-rst}
.. autoclass:: PageChooserPanel

    While ``FieldPanel`` also supports ``ForeignKey`` to :class:`~wagtail.models.Page` models, you can explicitly use ``PageChooserPanel`` to allow ``Page``-specific customisations.

    .. code-block:: python

        from wagtail.models import Page
        from wagtail.admin.panels import PageChooserPanel


        class BookPage(Page):
            related_page = models.ForeignKey(
                'wagtailcore.Page',
                null=True,
                blank=True,
                on_delete=models.SET_NULL,
                related_name='+',
            )

            content_panels = Page.content_panels + [
                PageChooserPanel('related_page', 'demo.PublisherPage'),
            ]

    ``PageChooserPanel`` takes one required argument, the field name. Optionally, specifying a page type (in the form of an ``"appname.modelname"`` string) will filter the chooser to display only pages of that type. A list or tuple of page types can also be passed in, to allow choosing a page that matches any of those page types:

    .. code-block:: python

        PageChooserPanel('related_page', ['demo.PublisherPage', 'demo.AuthorPage'])

    Passing ``can_choose_root=True`` will allow the editor to choose the tree root as a page. Normally this would be undesirable, since the tree root is never a usable page, but in some specialised cases it may be appropriate; for example, a page with an automatic "related articles" feed could use a ``PageChooserPanel`` to select which subsection articles will be taken from, with the root corresponding to 'everywhere'.
```

### FormSubmissionsPanel

```{eval-rst}
.. module:: wagtail.contrib.forms.panels

.. class:: FormSubmissionsPanel(**kwargs)

    This panel adds a single, read-only section in the edit interface for pages implementing the :class:`~wagtail.contrib.forms.models.AbstractForm` model.
    It includes the number of total submissions for the given form and also a link to the listing of submissions.

    .. code-block:: python

        from wagtail.contrib.forms.models import AbstractForm
        from wagtail.contrib.forms.panels import FormSubmissionsPanel

        class ContactFormPage(AbstractForm):
            content_panels = [
                FormSubmissionsPanel(),
            ]
```

(title_field_panel)=

### TitleFieldPanel

```{eval-rst}
.. module:: wagtail.admin.panels
   :noindex:

.. autoclass:: TitleFieldPanel

    This is the panel to use for Page title fields or main titles on other models. It provides a default classname, placeholder and widget attributes to enable the automatic sync with the slug field in the form. Many of these defaults can be customised by passing additional arguments to the constructor. All the same `FieldPanel` arguments are supported including a custom widget. For more details, see :ref:`customising_panels`.

```

(customising_panels)=

## Panel customisation

By adding extra parameters to your panel/field definitions, you can control much of how your fields will display in the Wagtail page editing interface. Wagtail's page editing interface takes much of its behaviour from Django's admin, so you may find many options for customisation covered there.
(See [Django model field reference](django:ref/models/fields)).

(customising_panel_icons)=

### Icons

Use the `icon` argument to the panel constructor to override the icon to be displayed next to the panel's heading. For a list of available icons, see [](available_icons).

### Heading

Use the `heading` argument to the panel constructor to set the panel's heading. This will be used for the input's label and displayed on the content minimap. If left unset for `FieldPanel`s, it will be set automatically using the form field's label (taken in turn from a model field's `verbose_name`).

### CSS classes

Use the `classname` argument to the panel constructor to add CSS classes to the panel. The class will be applied to the HTML `<section>` element of the panel. This can be used to add extra styling to the panel or to control its behaviour.

The `title` class can be used to make the input stand out with a bigger font size and weight.

(collapsible)=
The `collapsed` class will load the editor page with the panel collapsed under its heading.

```python
    content_panels = [
        MultiFieldPanel(
            [
                FieldPanel('cover'),
                FieldPanel('book_file'),
                FieldPanel('publisher'),
            ],
            heading="Collection of Book Fields",
            classname="collapsed",
        ),
    ]
```

### Help text

Use the `help_text` argument to the panel constructor to customise the help text to be displayed above the input. If unset for `FieldPanel`s, it will be set automatically using the form field's `help_text` (taken in turn from a model field's `help_text`).

### Placeholder text

By default, Wagtail uses the field's label as placeholder text. To change it, pass to the `FieldPanel` a widget with a placeholder attribute set to your desired text. You can select widgets from [Django's form widgets](django:ref/forms/widgets), or any of the Wagtail's widgets found in `wagtail.admin.widgets`.

For example, to customise placeholders for a `Book` snippet model:

```python
# models.py
from django import forms            # the default Django widgets live here
from wagtail.admin import widgets   # to use Wagtail's special datetime widget

class Book(models.Model):
    title = models.CharField(max_length=256)
    release_date = models.DateField()
    price = models.DecimalField(max_digits=5, decimal_places=2)

    # you can create them separately
    title_widget = forms.TextInput(
        attrs = {
            'placeholder': 'Enter Full Title'
        }
    )
    # using the correct widget for your field type and desired effect
    date_widget = widgets.AdminDateInput(
        attrs = {
            'placeholder': 'dd-mm-yyyy'
        }
    )

    panels = [
        TitleFieldPanel('title', widget=title_widget), # then add them as a variable
        FieldPanel('release_date', widget=date_widget),
        FieldPanel('price', widget=forms.NumberInput(attrs={'placeholder': 'Retail price on release'})) # or directly inline
    ]
```

### Required fields

To make input or chooser selection mandatory for a field, add [`blank=False`](django.db.models.Field.blank) to its model definition.

### Hiding fields

Without a top-level panel definition, a `FieldPanel` will be constructed for each field in your model. If you intend to hide a field on the Wagtail page editor, define the field with [`editable=False`](django.db.models.Field.editable). If a field is not present in the panels definition, it will also be hidden.

(panels_permissions)=

### Permissions

Most panels can accept a `permission` kwarg, allowing the set of panels or specific panels to be restricted to a set permissions.
See [](permissions_overview) for details about working with permissions in Wagtail.

In this example, 'notes' will be visible to all editors, 'cost' and 'details' will only be visible to those with the `submit` permission, 'budget approval' will be visible to super users only. Note that super users will have access to all fields.

```python
    content_panels = [
        FieldPanel("notes"),
        MultiFieldPanel(
            [
                FieldPanel("cost"),
                FieldPanel("details"),
            ],
            heading="Budget details",
            classname="collapsed",
            permission="submit"
        ),
        FieldPanel("budget_approval", permission="superuser"),
    ]
```

(panels_attrs)=

### Additional HTML attributes

Use the `attrs` parameter to add custom attributes to the HTML element of the panel. This allows you to specify additional attributes, such as `data-*` attributes. The `attrs` parameter accepts a dictionary where the keys are the attribute names and these will be rendered in the same way as Django's widget {attr}`~django.forms.Widget.attrs` where `True` and `False` will be treated as HTML5 boolean attributes.

For example, you can use the `attrs` parameter to integrate your Stimulus controller to the panel:

```python
    content_panels = [
        MultiFieldPanel(
            [
                FieldPanel('cover'),
                FieldPanel('book_file'),
                FieldPanel('publisher', attrs={'data-my-controller-target': 'myTarget'}),
            ],
            heading="Collection of Book Fields",
            classname="collapsed",
            attrs={'data-controller': 'my-controller'},
        ),
    ]
```
