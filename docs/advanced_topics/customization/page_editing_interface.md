# Customizing the editing interface

(customizing_the_tabbed_interface)=

## Customizing the tabbed interface

As standard, Wagtail organizes panels for pages into two tabs: 'Content' and 'Promote'. For snippets, Wagtail puts all panels into one page. Depending on the requirements of your site, you may wish to customize this for specific page types or snippets - for example, adding an additional tab for sidebar content. This can be done by specifying an `edit_handler` attribute on the page or snippet model. For example:

```python
from wagtail.admin.panels import TabbedInterface, TitleFieldPanel, ObjectList

class BlogPage(Page):
    # field definitions omitted

    content_panels = [
        TitleFieldPanel('title', classname="title"),
        FieldPanel('date'),
        FieldPanel('body'),
    ]
    sidebar_content_panels = [
        FieldPanel('advert'),
        InlinePanel('related_links'),
    ]

    edit_handler = TabbedInterface([
        ObjectList(content_panels, heading='Content'),
        ObjectList(sidebar_content_panels, heading='Sidebar content'),
        ObjectList(Page.promote_panels, heading='Promote'),
        ObjectList(Page.settings_panels, heading='Settings'), # The default settings are now displayed in the sidebar but need to be in the `TabbedInterface`.
    ])
```

Permissions can be set using `permission` on the `ObjectList` to restrict entire groups of panels to specific users.

```python
from wagtail.admin.panels import TabbedInterface, TitleFieldPanel, ObjectList

class FundingPage(Page):
    # field definitions omitted

    shared_panels = [
        TitleFieldPanel('title', classname="title"),
        FieldPanel('date'),
        FieldPanel('body'),
    ]
    private_panels = [
        FieldPanel('approval'),
    ]

    edit_handler = TabbedInterface([
        ObjectList(shared_panels, heading='Details'),
        ObjectList(private_panels, heading='Admin only', permission="superuser"),
        ObjectList(Page.promote_panels, heading='Promote'),
        ObjectList(Page.settings_panels, heading='Settings'), # The default settings are now displayed in the sidebar but need to be in the `TabbedInterface`.
    ])
```

For more details on how to work with `Panel` and `PanelGroup` classes, see [](forms_panels_overview).

(rich_text_field)=

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

`RichTextField` inherits from Django's basic `TextField` field, so you can pass any field parameters into `RichTextField` as if using a normal Django field. This field does not need a special panel and can be defined with `FieldPanel`. However, template output from `RichTextField` is special and needs to be filtered in order to preserve embedded content. See [](rich_text_filter).

If `max_length` is specified, length validation will automatically ignore any rich text formatting. To enforce minimum length in the same manner, pass an instance of `wagtail.rich_text.RichTextMinLengthValidator` as part of the `validators` argument.

(rich_text_features)=

### Limiting features in a rich text field

By default, the rich text editor provides users with a wide variety of options for text formatting and inserting embedded content such as images. However, we may wish to restrict a rich text field to a more limited set of features - for example:

-   The field might be intended for a short text snippet, such as a summary to be pulled out on index pages, where embedded images or videos would be inappropriate;
-   When page content is defined using [StreamField](../../topics/streamfield), elements such as headings, images, and videos are usually given their own block types, alongside a rich text block type used for ordinary paragraph text; in this case, allowing headings and images to also exist within the rich text content is redundant (and liable to result in inconsistent designs).

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

On loading, Wagtail will search for any app with the file `image_formats.py` and execute the contents. This provides a way to customize the formatting options shown to the editor when inserting images in the `RichTextField` editor.

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
Any class names you provide must have CSS rules matching them written separately, as part of the frontend CSS code. Specifying a `classname` value of `left` will only ensure that class is output in the generated markup, it won't cause the image to align itself left.
```

**`filter_spec`**
The string specification to create the image rendition. For more, see [](image_tag).

To unregister, call `unregister_image_format` with the string of the `name` of the `Format` as the only argument.

```{warning}
Unregistering ``Format`` objects will cause errors when viewing or editing pages that reference them.
```

(date_field_validation)=

## Date field validation

The `NoFutureDateValidator` prevents users from entering dates in the future. This is particularly useful for fields that should only contain past or present dates, such as:

-   Birth dates
-   Historical event dates
-   Publication dates for content that has already been published
-   Completion dates for finished projects

```python
from django.db import models
from wagtail.fields import NoFutureDateValidator
from wagtail.admin.panels import FieldPanel
from wagtail.models import Page


class EventPage(Page):
    event_date = models.DateField(
        validators=[NoFutureDateValidator()],
        help_text="The date when this event occurred"
    )
    birth_date = models.DateField(
        validators=[NoFutureDateValidator("Birth date cannot be in the future.")],
        help_text="Person's date of birth"
    )

    content_panels = Page.content_panels + [
        FieldPanel('event_date'),
        FieldPanel('birth_date'),
    ]
```

The validator also accepts an optional custom error message:

```python
# Using default message: "Date cannot be in the future."
event_date = models.DateField(validators=[NoFutureDateValidator()])

# Using custom message
birth_date = models.DateField(
    validators=[NoFutureDateValidator("Please enter a valid birth date.")]
)
```

The validator will raise a validation error if the entered date is after today's date.

(custom_edit_handler_forms)=

## Customizing generated forms

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

(custom_page_copy_form)=

## Customizing the generated copy page form

```{eval-rst}
.. class:: wagtail.admin.forms.CopyForm
```

When copying a page, Wagtail will generate a form to allow the user to modify the copied page. By default, this form subclasses [CopyForm](wagtail.admin.forms.CopyForm). A custom base form class can be configured by setting the `copy_form_class` attribute on any model. Custom forms must subclass [CopyForm](wagtail.admin.forms.CopyForm).

This can be used to specify alterations to the copied form on a per-model basis.

For example, auto-incrementing the slug field:

```python
from django import forms
from django.db import models

from wagtail.admin.forms.pages import CopyForm
from wagtail.admin.panels import FieldPanel
from wagtail.models import Page


class CustomCopyForm(CopyForm):
    def __init__(self, *args, **kwargs):
        """
        Override the default copy form to auto-increment the slug.
        """
        super().__init__(*args, **kwargs)
        suffix = 2 # set initial_slug as incremented slug
        parent_page = self.page.get_parent()
        if self.page.slug:
            try:
                suffix = int(self.page.slug[-1])+1
                base_slug = self.page.slug[:-2]

            except ValueError:
                base_slug = self.page.slug

        new_slug = base_slug + f"-{suffix}"
        while not Page._slug_is_available(new_slug, parent_page):
            suffix += 1
            new_slug = f"{base_slug}-{suffix}"

        self.fields["new_slug"].initial = new_slug

class BlogPage(Page):
    copy_form_class = CustomCopyForm # Set the custom copy form for all EventPage models

    introduction = models.TextField(blank=True)
    body = RichTextField()

    content_panels = Page.content_panels + [
        FieldPanel('introduction'),
        FieldPanel('body'),
    ]
```

(customizing_slug_widget)=

## Customizing Page slug generation

The `SlugInput` widget accepts additional kwargs or can be extended for custom slug generation.

Django's `models.SlugField` fields will automatically use the Wagtail admin's `SlugInput`. To change its behavior you will first need to override the widget.

```python
# models.py

# ... imports

class MyPage(Page):
    promote_panels = [
        FieldPanel("slug"), # automatically uses `SlugInput`
        # ... other panels
    ]
```

### Overriding `SlugInput`

There are multiple ways to override the `SlugInput`, depending on your use case and admin setup.

#### Via `promote_panels`

The simplest, if you have already set custom `promote_panels`, is to leverage the `FieldPanel` widget kwarg as follows.

```python
from wagtail.admin.widgets.slug import SlugInput
# ... other imports

class MyPage(Page):
    promote_panels = [
        FieldPanel("slug", widget=SlugInput(locale="uk-UK")), # force a specific locale for this page's slug only
        # ... other panels need to be declared
    ]
```

#### Via a custom form using `base_form_class`

If you do not want to re-declare the `promote_panels`, your Page model's `base_form_class` can be set to a form class that overrides the widget.

```py
# models.py

from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.admin.widgets import SlugInput
from wagtail.models import Page
# ... other imports


class MyPageForm(WagtailAdminPageForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # force a specific locale for this page's slug only
        self.fields["slug"].widget = SlugInput(locale="uk-UK")


class MyPage(Page):
    base_form_class = MyPageForm
    # other fields
    # no need to declare `promote_panels`
```

#### Globally, via `register_form_field_override`

If you want to override the `models.SlugField` widget for the entire admin, this can be done using the Wagtail admin util.

It's best to add this to a `wagtail_hooks.py` file as this will get run at the right time.

```py
# wagtail_hooks.py

from django.db import models
from wagtail.admin.forms.models import register_form_field_override
from wagtail.admin import widgets

# .. other imports & hooks


register_form_field_override(
    models.SlugField,
    override={"widget": widgets.SlugInput(locale="uk-UK")},
)
```

The following sections will only focus on the `SlugInput(...)` usage and not where to override this.

### Overriding the default locale behavior via `locale`

The `SlugInput` is locale aware and will adjust the transliteration (Unicode to ASCII conversion) based on the most suitable locale, only when [`WAGTAIL_ALLOW_UNICODE_SLUGS`](wagtail_allow_unicode_slugs) is `False`.

The locale will be determined from the target translation locale if [](internationalisation) is enabled.

If internationalization is not in use, it will be based on the language of the admin for the currently logged in user. This behavior can be overridden - see below.

#### Examples

| `SlugInput`                                             | Description                                                                                                                                          |
| ------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `SlugInput(locale="uk-UK")` or `SlugInput(locale="uk")` | Override the locale for a specific language code only (Ukrainian in this example)                                                                    |
| `SlugInput(locale=False)`                               | Avoid the default logic for determining the locale and do not attempt to be locale aware, transliteration will still apply but use a basic approach. |
| `SlugInput(locale=my_page_instance.locale)`             | Use a [`Locale`](locale_model_ref) instance from some other model source.                                                                            |

### Adding custom formatters via `formatters`

`SlugInput` also accepts a `formatters` kwarg, allowing a list of custom formatters to be applied, each formatter item can be one of the following.

1. A regex pattern or string (for example `r"\d"`, `re.compile(r"\d")`)
2. A list-like value containing a regex pattern/string and a replacement string (for example `[r"\d", "n"]`)
3. A list-like value containing a regex pattern/string and a replacement string & custom base JavaScript regex flags (for example `[r"\d", "n", "u"]`)

As a reminder, ensure that regex strings are appropriately escaped.

For example, here's a formatter that will remove common stop words from the slug. If the title is entered as `The weather and the times`, this will produce a slug of `weather-times`.

```py
# models.py

from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.admin.widgets import SlugInput
from wagtail.models import Page
# ... other imports


class MyPageForm(WagtailAdminPageForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].widget = SlugInput(
            formatters = [
                r"(?i)\b(?:and|or|the|in|of|to)\b", # remove common stop words
            ]
        )


class MyPage(Page):
    base_form_class = MyPageForm
```

#### Examples

| `SlugInput`                                                                            | Description                                                     | Input (title)                             | Output (slug)                                  |
| -------------------------------------------------------------------------------------- | --------------------------------------------------------------- | ----------------------------------------- | ---------------------------------------------- |
| `SlugInput(formatters=[r"\d"])`                                                        | Remove digits before generating the slug.                       | `3 train rides`                           | `train-rides`                                  |
| `SlugInput(formatters=[[r"ABC", "Acme Building Company"]])`                            | Replace company abbreviation with the full name.                | `ABC retreat`                             | `acme-building-company-retreat`                |
| `SlugInput(formatters=[[r"the", '', "u"]])`                                            | Replace the first found occurrence of 'the' with a blank space. | `The Great Gatsby review`                 | `great-gatsby-review`                          |
| `SlugInput(formatters=[re.compile(r"(?i)\b(?:and\|or\|the\|in\|of\|to)\b")])`          | Replace common stop words, case insensitive.                    | `The joy of living green`                 | `joy-living-green`                             |
| `SlugInput(formatters=[[re.compile(r"^(?!blog[-\s])", flags=re.MULTILINE), 'blog-']])` | Enforce a prefix of `blog-` for every slug.                     | `Last week in Spain` / `Blog about a dog` | `blog-last-week-in-spain` / `blog-about-a-dog` |
| `SlugInput(formatters=[[[r"(?<!\S)Й", "Y"], [r"(?<!\S)Є", "Ye"]]])`                    | Replace specific characters at the start of words only.         | `Єєвропа`                                 | `yeivropa`                                     |

#### Considerations

There are some considerations to make when using the formatters, if you need to reach for more complex customizations it may make sense to override the Stimulus controller.

##### Changing slug formatters or locale for existing slug values

A caveat of changing these after a page is created is that the title & slug sync may no longer be in sync, meaning that if the page is not published and there is already a slug that was created from different logic, subsequent changes to the title will not be reflected on the slug.

To work around this, users can clear the slug field manually, then click & click away on the title field, this will re-create the new slug based on the new logic.

This is intentional behavior so that manual changes to slugs do not normally get overwritten by subsequent changes to the title.

##### Regex conversion

The regex formatters run in JavaScript so some differences need to be considered (such as word boundaries accounting for unicode in Python).

In addition, some Python regex features are not supported (such as `re.VERBOSE`, named capture groups) as these cannot be easily converted to their JavaScript equivalent.

When working with the `formatters`, be sure to check the browser console within the admin for any conversion issues that may occur.
