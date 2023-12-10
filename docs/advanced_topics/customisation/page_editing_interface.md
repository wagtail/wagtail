# Customising the editing interface

(customising_the_tabbed_interface)=

## Customising the tabbed interface


The simplest way to customise the tabs that appear when editing a model instance is to utlize `wagtail.admin.utils.TabbedEditHandlerGeneratorMixin`. This mixin adds a number of properties and methods that can be overridden to fit your needs.

If your model is a subclass of `Page`, you're in luck! Wagtail's `Page` model already incorporates `TabbedEditHandlerGeneratorMixin`, granting access to numerous customisation options. However, snippets and other models, you'll need to import and apply it explicitly in your model definition, as shown below:

```python
from wagtail.admin.utils import TabbedEditHandlerGeneratorMixin


class Employee(models.Model, TabbedEditHandlerGeneratorMixin):
    ...
```

### Adding tabs to a non-page model

The simplest method for controlling the interface is to use attribute values on the model class.

Tab names and labels are controlled via the `edit_handler_tabs` attribute.

`TabbedEditHandlerGeneratorMixin` automatically looks for attributes following the pattern `{tab_name}_panels` to determine the panels for each tab. Consider the following example for the `Employee` model:

```python

from django.utils.translation import gettext_lazy as _

from wagtail.admin.panels import FieldPanel
from wagtail.admin.utils import TabbedEditHandlerGeneratorMixin


class Employee(models.Model, TabbedEditHandlerGeneratorMixin):

    # The names and labels of tabs that should appear in the
    # edit interface
    edit_handler_tabs = [
        ("personal", _("Personal details")),
        ("professional", _("Professional details")),
    ]

    # Panels to appear under the 'Personal details' tab
    personal_panels = [
        FieldPanel("first_name"),
        FieldPanel("last_name"),
        FieldPanel("email"),
        FieldPanel("dob"),
    ]

    # Panels to appear under the 'Professional details' tab.
    professional_panels = [
        FieldPanel("employment_start_date"),
        FieldPanel("line_manager"),
        FieldPanel("current_role"),
        FieldPanel("current_role_start_date"),
    ]
```

### Extending default tabs for page types

For `Page` models, tab customization follows the same principles. You just need to bear in mind that `Page` models already have an `edit_handler_tabs` attribute with the following value:

```python
    edit_handler_tabs = [
        ("content", "Content"),
        ("promote", "Promote"),
        ("settings", "Settings"),
    ]
```

Adding a new tab (such as "Related") after the "Promote" tab could be achieved by setting the `edit_handler_tabs` attribute on your custom class like this:


```python
from django.utils.translation import gettext_lazy as _

from wagtail.admin.panels import FieldPanel


class BlogPage(Page):

    edit_handler_tabs = Page.edit_handler_tabs[:2] + [
        ("related", _("Related")),
    ] + Page.edit_handler_tabs[2:]

    # Panels to appear under the 'Related' tab.
    related_panels = [
        InlinePanel("related_blogs"),
        FieldPanel("categories"),
        FieldPanel("tags"),
    ]
```

For enhanced flexibility in defining a list of panels, consider using a class method with the name `get_{tab_name}_panels()` instead. This approach allows for conditional panel inclusion based on other attributes or settings, as illustrated below:

```python
from django.utils.translation import gettext_lazy as _

from wagtail.admin.panels import FieldPanel


class BlogPage(Page):

    # An attribute to toggle the inclusion of `migration_details_panel`
    # at the bottom of the content tab. It is set to `True` on at least
    # one subclass
    is_migrated = False

    migration_details_panel = MultiFieldPanel(
        heading=_("Migration details")),
        children=[
            FieldPanel("migration_source", read_only=True),
            FieldPanel("migration_source_id", read_only=True),
            FieldPanel("last_updated_from_source", read_only=True),
        ],
    )

    @classmethod
    def get_content_panels(cls):
        # Start with the attribute value
        panels = list(cls.content_panels)

        # Add additional read-only fields for migrated blog types
        if cls.is_migrated:
            panels.append(cls.migration_details_panel)

        return panels
```

Where you have a mixture of fixed and dynamically added panels in a tab, a sensible approach is to define the fixed panels using an attribute, then make any necessary adjustments in the class method.

### Changing the class used for the interface

By default, the `wagtail.admin.panels.TabbedInterface` class is used to define tabbed edit interfaces for models, but you use the `edit_handler_class` attribute to specify an alternative. For example:

```python
class BlogPage(Page):
    edit_handler_class = "yourproject.appname.panels.CustomTabbedInterface"
```

The class should be a subclass of `TabbedInterface`, and the attribute value can be a class or an import path to one.

For additionaly flexibility, consider overriding the `get_edit_handler_class()` class method:

```python
from yourproject.appname.panels import CustomTabbedInterface


class BlogPage(Page):

    @classmethod
    def get_edit_handler_class(cls):
        return CustomTabbedInterface
```

### Changing the class used for tabs

By default, the `wagtail.admin.panels.ObjectList` class is used to create tabs for the interface. You can use the `edit_handler_tab_class` attribute to specify an alternative for ALL tabs. The value should be a subclass of `ObjectList`, and you can use the class as a value directly, or supply the import path as a string. For example:

```python
class Employee(models.Model, TabbedEditHandlerGeneratorMixin):
    edit_handler_tab_class = "yourproject.appname.panels.CustomObjectList"
```

If you want to use a alternative class for a specific tab, or the class attribute does not enough flexibility, you can override the `get_edit_handler_tab_class()` class method instead. For example:

```python
from wagtail.admin.panels import ObjectList
from yourproject.appname.panels import CustomObjectList

class Employee(models.Model, TabbedEditHandlerGeneratorMixin):

    @classmethod
    def get_edit_handler_tab_class(cls, tab_name: str):
        if tab_name == "personal":
            return CustomObjectList
        return ObjectList
```

### Hiding tabs

Tabs for which no panels can be found (or where the value is an empty list) are automatically excluded from tabbed interfaces. You can also explicitly control tab visibility using a `hide_{tab_name}_tab` attribute. For example:

```python
class BlogPage(Page):
    hide_related_tab = True
```

With this approach, turning the tab 'back on' for specific subclasses is as easy as changing the value to `False`. For example:

```python
class ShinyBlogPage(BlogPage):
    hide_related_tab = False
```

### Conditionally groups of panels depending on user permissions

Django's permission system can be leaveraged to restrict visibility of tabs (or other groups of panels) to users with specific permissions. The `PanelGroup` class (which `ObjectList` is a subclass of) has a `permission` option to support this. While `TabbedEditHandlerGeneratorMixin` does not provide a direct shortcut for utlizing this option, you can override the `create_edit_handler_tab()` class method to customize how tabs are initialized:

```python
from wagtail.admin.panels import FieldPanel, TitleFieldPanel


class FundingPage(Page):

    edit_handler_tabs = [
        ("shared", _("Details")),
        ("private", _("Admin only")),
    ]

    shared_panels = [
        TitleFieldPanel('title', classname="title"),
        FieldPanel('date'),
        FieldPanel('body'),
    ]

    private_panels = [
        FieldPanel('approval'),
    ]

    @classmethod
    def create_edit_handler_tab(cls, name: str, heading: str):
        # Start by creating a tab the usual way
        tab = super().create_edit_handler_tab(name, heading)
        # Restrict visibility of 'private' tab to superusers
        if name == "private":
            tab.permission = "superuser"
        return tab
```

For more details on how to work with `Panel`s and `PanelGroup`, see [](forms_panels_overview).

(rich_text)=

## Rich Text (HTML)

Wagtail provides a general-purpose WYSIWYG editor for creating rich text content (HTML) and embedding media such as images, video, and documents. To include this in your models, use the `RichTextField` function when defining a model field:

```python
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel


class BookPage(Page):
    body = RichTextField()

    content_panels = Page.content_panels + [
        FieldPanel('body'),
    ]
```

`RichTextField` inherits from Django's basic `TextField` field, so you can pass any field parameters into `RichTextField` as if using a normal Django field. Its `max_length` will ignore any rich text formatting. This field does not need a special panel and can be defined with `FieldPanel`.

However, template output from `RichTextField` is special and needs to be filtered in order to preserve embedded content. See [](rich_text_filter).

(rich_text_features)=

### Limiting features in a rich text field

By default, the rich text editor provides users with a wide variety of options for text formatting and inserting embedded content such as images. However, we may wish to restrict a rich text field to a more limited set of features - for example:

-   The field might be intended for a short text snippet, such as a summary to be pulled out on index pages, where embedded images or videos would be inappropriate;
-   When page content is defined using [StreamField](../../topics/streamfield), elements such as headings, images and videos are usually given their own block types, alongside a rich text block type used for ordinary paragraph text; in this case, allowing headings and images to also exist within the rich text content is redundant (and liable to result in inconsistent designs).

This can be achieved by passing a `features` keyword argument to `RichTextField`, with a list of identifiers for the features you wish to allow:

```python
body = RichTextField(features=['h2', 'h3', 'bold', 'italic', 'link'])
```

The feature identifiers provided on a default Wagtail installation are as follows:

-   `h2`, `h3`, `h4` - heading elements
-   `bold`, `italic` - bold / italic text
-   `ol`, `ul` - ordered / unordered lists
-   `hr` - horizontal rules
-   `link` - page, external and email links
-   `document-link` - links to documents
-   `image` - embedded images
-   `embed` - embedded media (see [](embedded_content))

We have a few additional feature identifiers as well. They are not enabled by default, but you can use them in your list of identifiers. These are as follows:

-   `h1`, `h5`, `h6` - heading elements
-   `code` - inline code
-   `superscript`, `subscript`, `strikethrough` - text formatting
-   `blockquote` - blockquote

The process for creating new features is described in the following pages:

-   [](../../extending/rich_text_internals)
-   [](../../extending/extending_draftail)

You can also provide a setting for naming a group of rich text features. See [WAGTAILADMIN_RICH_TEXT_EDITORS](wagtailadmin_rich_text_editors).

(rich_text_image_formats)=

### Image Formats in the Rich Text Editor

On loading, Wagtail will search for any app with the file `image_formats.py` and execute the contents. This provides a way to customise the formatting options shown to the editor when inserting images in the `RichTextField` editor.

As an example, add a "thumbnail" format:

```python
# image_formats.py
from wagtail.images.formats import Format, register_image_format

register_image_format(Format('thumbnail', 'Thumbnail', 'richtext-image thumbnail', 'max-120x120'))
```

To begin, import the `Format` class, `register_image_format` function, and optionally `unregister_image_format` function. To register a new `Format`, call the `register_image_format` with the `Format` object as the argument. The `Format` class takes the following constructor arguments:

**`name`**\
The unique key used to identify the format. To unregister this format, call `unregister_image_format` with this string as the only argument.

**`label`**\
The label used in the chooser form when inserting the image into the `RichTextField`.

**`classname`**\
The string to assign to the `class` attribute of the generated `<img>` tag.

```{note}
Any class names you provide must have CSS rules matching them written separately, as part of the front end CSS code. Specifying a `classname` value of `left` will only ensure that class is output in the generated markup, it won't cause the image to align itself left.
```

**`filter_spec`**
The string specification to create the image rendition. For more, see [](image_tag).

To unregister, call `unregister_image_format` with the string of the `name` of the `Format` as the only argument.

```{warning}
Unregistering ``Format`` objects will cause errors viewing or editing pages that reference them.
```

(custom_edit_handler_forms)=

## Customising generated forms

```{eval-rst}
.. class:: wagtail.admin.forms.WagtailAdminModelForm
.. class:: wagtail.admin.forms.WagtailAdminPageForm
```

Wagtail automatically generates forms using the panels configured on the model.
By default, this form subclasses [WagtailAdminModelForm](wagtail.admin.forms.WagtailAdminModelForm),
or [WagtailAdminPageForm](wagtail.admin.forms.WagtailAdminPageForm) for pages.
A custom base form class can be configured by setting the `base_form_class` attribute on any model.
Custom forms for snippets must subclass [WagtailAdminModelForm](wagtail.admin.forms.WagtailAdminModelForm),
and custom forms for pages must subclass [WagtailAdminPageForm](wagtail.admin.forms.WagtailAdminPageForm).

This can be used to add non-model fields to the form, to automatically generate field content,
or to add custom validation logic for your models:

```python
from django import forms
from django.db import models
import geocoder  # not in Wagtail, for example only - https://geocoder.readthedocs.io/
from wagtail.admin.panels import TitleFieldPanel, FieldPanel
from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.models import Page


class EventPageForm(WagtailAdminPageForm):
    address = forms.CharField()

    def clean(self):
        cleaned_data = super().clean()

        # Make sure that the event starts before it ends
        start_date = cleaned_data['start_date']
        end_date = cleaned_data['end_date']
        if start_date and end_date and start_date > end_date:
            self.add_error('end_date', 'The end date must be after the start date')

        return cleaned_data

    def save(self, commit=True):
        page = super().save(commit=False)

        # Update the duration field from the submitted dates
        page.duration = (page.end_date - page.start_date).days

        # Fetch the location by geocoding the address
        page.location = geocoder.arcgis(self.cleaned_data['address'])

        if commit:
            page.save()
        return page


class EventPage(Page):
    start_date = models.DateField()
    end_date = models.DateField()
    duration = models.IntegerField()
    location = models.CharField(max_length=255)

    content_panels = [
        TitleFieldPanel('title'),
        FieldPanel('start_date'),
        FieldPanel('end_date'),
        FieldPanel('address'),
    ]
    base_form_class = EventPageForm
```

Wagtail will generate a new subclass of this form for the model,
adding any fields defined in `panels` or `content_panels`.
Any fields already defined on the model will not be overridden by these automatically added fields,
so the form field for a model field can be overridden by adding it to the custom form.
