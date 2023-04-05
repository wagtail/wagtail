(editing-api)=

# Panel types

## Built-in Fields and Choosers

Django's field types are automatically recognised and provided with an appropriate widget for input. Just define that field the normal Django way and pass the field name into
[`FieldPanel`](wagtail.admin.panels.FieldPanel) when defining your panels. Wagtail will take care of the rest.

Here are some Wagtail-specific types that you might include as fields in your models.

```{eval-rst}
.. module:: wagtail.admin.panels
   :noindex:
```

(field_panel)=

### FieldPanel

```{eval-rst}
.. class:: FieldPanel(field_name, classname=None, widget=None, icon=None, heading='', disable_comments=False, permission=None)

    This is the panel used for basic Django field types.

    .. attribute:: FieldPanel.field_name

        This is the name of the class property used in your model definition.

    .. attribute:: FieldPanel.classname (optional)

        This is a string of optional CSS classes given to the panel which are used in formatting and scripted interactivity.

        The CSS class ``title`` can be used to give the field a larger text size, suitable for representing page titles and section headings.

    .. attribute:: FieldPanel.widget (optional)

        This parameter allows you to specify a :doc:`Django form widget <django:ref/forms/widgets>` to use instead of the default widget for this field type.

    .. attribute:: FieldPanel.icon (optional)

        This allows you to override the icon for the panel. If unset, Wagtail uses a set of default icons for common model field types. For a list of icons available out of the box, see :ref:`available_icons`. Project-specific icons are also displayed in the :ref:`styleguide`.

    .. attribute:: FieldPanel.heading (optional)

        This allows you to override the heading for the panel, which will otherwise be set automatically using the form field's label (taken in turn from a model field's ``verbose_name``).

    .. attribute:: FieldPanel.help_text (optional)

        Help text to be displayed against the field. This takes precedence over any help text set on the model field.

    .. attribute:: FieldPanel.disable_comments (optional)

        This allows you to prevent a field level comment button showing for this panel if set to ``True``. See `Create and edit comments <https://guide.wagtail.org/en-latest/how-to-guides/manage-pages/#create-and-edit-comments>`_.

    .. attribute:: FieldPanel.permission (optional)

        Allows a field to be selectively shown to users with sufficient permission. Accepts a permission codename such as ``'myapp.change_blog_category'`` - if the logged-in user does not have that permission, the field will be omitted from the form. See Django's documentation on :ref:`custom permissions <django:custom-permissions>` for details on how to set permissions up; alternatively, if you want to set a field as only available to superusers, you can use any arbitrary string (such as ``'superuser'``) as the codename, since superusers automatically pass all permission tests.
```

### MultiFieldPanel

```{eval-rst}
.. class:: MultiFieldPanel(children, heading="", classname=None)

    This panel condenses several :class:`~wagtail.admin.panels.FieldPanel` s or choosers, from a ``list`` or ``tuple``, under a single ``heading`` string.

    .. attribute:: MultiFieldPanel.children

        A ``list`` or ``tuple`` of child panels

    .. attribute:: MultiFieldPanel.heading (optional)

        A heading for the fields

    .. attribute:: MultiFieldPanel.help_text (optional)

        Help text to be displayed against the panel.

    .. attribute:: MultiFieldPanel.permission (optional)

        Allows a panel to be selectively shown to users with sufficient permission. Accepts a permission codename such as ``'myapp.change_blog_category'`` - if the logged-in user does not have that permission, the panel will be omitted from the form. Similar to ``FieldPanel.permission``.
```

(inline_panels)=

### InlinePanel

```{eval-rst}
.. class:: InlinePanel(relation_name, panels=None, classname='', heading='', label='', help_text='', min_num=None, max_num=None)

    This panel allows for the creation of a "cluster" of related objects over a join to a separate model, such as a list of related links or slides to an image carousel. For a full explanation on the usage of ``InlinePanel``, see :ref:`inline_models`.

    .. attribute:: InlinePanel.relation_name

        The related_name label given to the cluster’s ParentalKey relation.

    .. attribute:: InlinePanel.panels (optional)

        The list of panels that will make up the child object's form. If not specified here, the `panels` definition on the child model will be used.

    .. attribute:: InlinePanel.classname (optional)

        A class to apply to the InlinePanel as a whole.

    .. attribute:: InlinePanel.heading

        A heading for the panel in the Wagtail editor.

    .. attribute:: InlinePanel.label

        Text for the add button and heading for child panels. Used as the heading when ``heading`` is not present.

    .. attribute:: InlinePanel.help_text (optional)

        Help text to be displayed in the Wagtail editor.

    .. attribute:: InlinePanel.min_num (optional)

        Minimum number of forms a user must submit.

    .. attribute:: InlinePanel.max_num (optional)

        Maximum number of forms a user must submit.

```

#### Collapsing InlinePanels to save space

Note that you can use `classname="collapsed"` to load the panel collapsed under its heading in order to save space in the Wagtail admin.

(multiple_chooser_panel)=

### MultipleChooserPanel

```{versionadded} 4.2
The `MultipleChooserPanel` panel type was added.
```

```{eval-rst}
.. class:: MultipleChooserPanel(relation_name, chooser_field_name=None, panels=None, classname='', heading='', label='', help_text='', min_num=None, max_num=None)
```

This is a variant of `InlinePanel` that improves the editing experience when the main feature of the child panel is a chooser for a `ForeignKey` relation (usually to an image, document, snippet or another page). Rather than the "Add" button inserting a new form to be filled in individually, it immediately opens up the chooser interface for that related object, in a mode that allows multiple items to be selected. The user is then returned to the main edit form with the appropriate number of child panels added and pre-filled.

`MultipleChooserPanel` accepts an additional required argument `chooser_field_name`, specifying the name of the `ForeignKey` relation that the chooser is linked to.

For example, given a child model that provies a gallery of images on `BlogPage`:

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

### FieldRowPanel

```{eval-rst}
.. class:: FieldRowPanel(children, classname=None, permission=None)

    This panel creates a columnar layout in the editing interface, where each of the child Panels appears alongside each other rather than below.

    Use of FieldRowPanel particularly helps reduce the "snow-blindness" effect of seeing so many fields on the page, for complex models. It also improves the perceived association between fields of a similar nature. For example if you created a model representing an "Event" which had a starting date and ending date, it may be intuitive to find the start and end date on the same "row".

    By default, the panel is divided into equal-width columns, but this can be overridden by adding ``col*`` class names to each of the child Panels of the FieldRowPanel. The Wagtail editing interface is laid out using a grid system. Classes ``col1``-``col12`` can be applied to each child of a FieldRowPanel to define how many columns they span out of the total number of columns. When grid items add up to 12 columns, the class ``col3`` will ensure that field appears 3 columns wide or a quarter the width. ``col4`` would cause the field to be 4 columns wide, or a third the width.

    .. attribute:: FieldRowPanel.children

        A ``list`` or ``tuple`` of child panels to display on the row

    .. attribute:: FieldRowPanel.classname (optional)

        A class to apply to the FieldRowPanel as a whole

    .. attribute:: FieldRowPanel.help_text (optional)

        Help text to be displayed against the panel.

    .. attribute:: FieldRowPanel.permission (optional)

        Allows a panel to be selectively shown to users with sufficient permission. Accepts a permission codename such as ``'myapp.change_blog_category'`` - if the logged-in user does not have that permission, the panel will be omitted from the form. Similar to ``FieldPanel.permission``.
```

### HelpPanel

```{eval-rst}
.. class:: HelpPanel(content='', template='wagtailadmin/panels/help_panel.html', heading='', classname='')

    .. attribute:: HelpPanel.content

        HTML string that gets displayed in the panel.

    .. attribute:: HelpPanel.template

        Path to a template rendering the full panel HTML.

    .. attribute:: HelpPanel.heading

        A heading for the help content.

    .. attribute:: HelpPanel.classname

        String of CSS classes given to the panel which are used in formatting and scripted interactivity.
```

### PageChooserPanel

```{eval-rst}
.. class:: PageChooserPanel(field_name, page_type=None, can_choose_root=False)

    You can explicitly link :class:`~wagtail.models.Page`-derived models together using the :class:`~wagtail.models.Page` model and ``PageChooserPanel``.

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

    Passing ``can_choose_root=True`` will allow the editor to choose the tree root as a page. Normally this would be undesirable, since the tree root is never a usable page, but in some specialised cases it may be appropriate; for example, a page with an automatic "related articles" feed could use a PageChooserPanel to select which subsection articles will be taken from, with the root corresponding to 'everywhere'.
```

### FormSubmissionsPanel

```{eval-rst}
.. module:: wagtail.contrib.forms.panels

.. class:: FormSubmissionsPanel

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

## Field Customisation

By adding CSS classes to your panel definitions or adding extra parameters to your field definitions, you can control much of how your fields will display in the Wagtail page editing interface. Wagtail's page editing interface takes much of its behaviour from Django's admin, so you may find many options for customisation covered there.
(See [Django model field reference](django:ref/models/fields)).

### Titles

Use `classname="title"` to make Page's built-in title field stand out with more vertical padding.

(collapsible)=

### Collapsible

Using `classname="collapsed"` will load the editor page with the panel collapsed under its heading.

```python
    content_panels = [
        MultiFieldPanel(
            [
                FieldPanel('cover'),
                FieldPanel('book_file'),
                FieldPanel('publisher'),
            ],
            heading="Collection of Book Fields",
            classname="collapsed"
        ),
    ]
```

### Placeholder Text

By default, Wagtail uses the field's label as placeholder text. To change it, pass to the FieldPanel a widget with a placeholder attribute set to your desired text. You can select widgets from [Django's form widgets](django:ref/forms/widgets), or any of the Wagtail's widgets found in `wagtail.admin.widgets`.

For example, to customise placeholders for a Book model exposed via ModelAdmin:

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
        FieldPanel('title', widget=title_widget), # then add them as a variable
        FieldPanel('release_date', widget=date_widget),
        FieldPanel('price', widget=forms.NumberInput(attrs={'placeholder': 'Retail price on release'})) # or directly inline
    ]
```

### Required Fields

To make input or chooser selection mandatory for a field, add [`blank=False`](django.db.models.Field.blank) to its model definition.

### Hiding Fields

Without a panel definition, a default form field (without label) will be used to represent your fields. If you intend to hide a field on the Wagtail page editor, define the field with [`editable=False`](django.db.models.Field.editable).
