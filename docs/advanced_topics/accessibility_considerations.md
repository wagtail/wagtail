# Accessibility considerations

Accessibility for CMS-driven websites is a matter of [modeling content appropriately](content_modeling), [creating accessible templates](accessibility_in_templates), and [authoring accessible content](authoring_accessible_content) with readability and accessibility guidelines in mind.

Wagtail generally puts developers in control of content modeling and front-end markup, but there are a few areas to be aware of nonetheless, and ways to help authors be aware of readability best practices.
Note there is much more to building accessible websites than we cover here – see our list of [accessibility resources](accessibility_resources) for more information.

```{contents}
---
local:
depth: 1
---
```

(content_modeling)=

## Content modeling

As part of defining your site’s models, here are areas to pay special attention to:

### Alt text for images

Wherever an image is used, the content editor should be able to mark the image as decorative or provide a context-specific text alternative. The image embed in our rich text editor supports this behavior. Wagtail 6.3 added [`ImageBlock`](streamfield_imageblock) to provide this behavior for images within StreamFields.

Wagtail 6.3 also added an optional `description` field to the Wagtail image model and to custom image models inheriting from `wagtail.images.models.AbstractImage`. Text in that field will be offered as the default alt text when inserting images in rich text or using ImageBlock. If the description field is empty, the title field will be used instead. If you would like to customize this behavior, [override the `default_alt_text` property](custom_image_model) in your image model.

```{note}
Important considerations

- Alt text should be written based on the context the image is displayed in.
- When specifying alt text fields, make sure they are optional so editors can choose to not write any alt text for decorative images. An image might be decorative in some cases but not in others. For example, thumbnails in page listings can often be considered decorative.
- If the alt text’s content is already part of the rest of the page, ideally the image should not repeat the same content.
- Take the time to provide `help_text` with appropriate guidance. For example, linking to [established resources on alt text](https://axesslab.com/alt-texts/).
```

### Embeds title

Missing embed titles are common failures in accessibility audits of Wagtail websites. In some cases, Wagtail embeds’ iframe doesn’t have a `title` attribute set. This is often a problem with OEmbed providers.
This is very problematic for screen reader users, who rely on the title to understand what the embed is, and whether to interact with it or not.

If your website relies on embeds that have missing titles, make sure to either:

-   Add the OEmbed _title_ field as a `title` on the `iframe`.
-   Add a custom mandatory Title field to your embeds, and add it as the `iframe`’s `title`.

### Available heading levels

Wagtail makes it very easy for developers to control which heading levels should be available for any given content, via [rich text features](rich_text_features) or custom StreamField blocks.
In both cases, take the time to restrict what heading levels are available so the pages’ document outline is more likely to be logical and sequential. Consider using the following restrictions:

-   Disallow `h1` in rich text. There should only be one `h1` tag per page, which generally maps to the page’s `title`.
-   Limit heading levels to `h2` for the main content of a page. Add `h3` only if deemed necessary. Avoid other levels as a general rule.
-   For content that is displayed in a specific section of the page, limit heading levels to those directly below the section’s main heading.

If managing headings via StreamField, make sure to apply the same restrictions there.

### Bold and italic formatting in rich text

By default, Wagtail stores its bold formatting as a `b` tag, and italic as `i` ([#4665](https://github.com/wagtail/wagtail/issues/4665)). While those tags don’t necessarily always have correct semantics (`strong` and `em` are more ubiquitous), there isn’t much consequence for screen reader users, as by default screen readers do not announce content differently based on emphasis.

If this is a concern to you, you can change which tags are used when saving content with [rich text format converters](rich_text_format_converters). In the future, [rich text rewrite handlers](rich_text_rewrite_handlers) should also support this being done without altering the storage format ([#4223](https://github.com/wagtail/wagtail/issues/4223)).

### TableBlock

Screen readers will use row and column headers to announce the context of each table cell. Please encourage editors to set row headers and/or column headers as appropriate for their table.

Always add a Caption, so screen reader users navigating the site’s tables get an overview of the table content before it is read.

(accessibility_in_templates)=

## Accessibility in templates

Here are common gotchas to be aware of to make the site’s templates as accessible as possible.

### Alt text in templates

See the [content modeling](content_modeling) section above. Additionally, make sure to [customize images’ alt text](image_tag_alt), either setting it to the relevant field, or to an empty string for decorative images, or images where the alt text would be a repeat of other content.
Even when your images have alt text coming directly from the image model, you still need to decide whether there should be alt text for the particular context the image is used in. For example, avoid alt text in listings where the alt text just repeats the listing items’ title.

### Empty heading tags

In both rich text and custom StreamField blocks, it’s easy for editors to create a heading block but not add any content to it. The [built-in accessibility checker](built_in_accessibility_checker) will highlight empty headings so editors can find and fix them. If you need stricter enforcement:

-   Add validation rules to those fields, making sure the page can’t be saved with the empty headings, for example by using the [StreamField](../topics/streamfield) `CharBlock` which is required by default.
-   Consider adding similar validation rules for rich text fields.

Alternately, you can hide empty heading blocks with CSS:

```css
h1:empty,
h2:empty,
h3:empty,
h4:empty,
h5:empty,
h6:empty {
    display: none;
}
```

### Forms

The [Form builder](form_builder) uses Django’s forms API. Here are considerations specific to forms in templates:

-   Avoid rendering helpers such as `as_table`, `as_ul`, `as_p`, which can make forms harder to navigate for screen reader users or cause HTML validation issues (see Django ticket [#32339](https://code.djangoproject.com/ticket/32339)).
-   Make sure to visually distinguish required and optional fields.
-   Take the time to group related fields together in `fieldset`, with an appropriate `legend`, in particular for radios and checkboxes (see Django ticket [#32338](https://code.djangoproject.com/ticket/32338)).
-   If relevant, use the appropriate `autocomplete` and `autocapitalize` attributes.
-   For Date and Datetime fields, make sure to display the expected format or an example value (see Django ticket [#32340](https://code.djangoproject.com/ticket/32340)). Or use [input type="date"](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/date).
-   For Number fields, consider whether `input type="number"` really is appropriate, or whether there may be [better alternatives such as inputmode](https://technology.blog.gov.uk/2020/02/24/why-the-gov-uk-design-system-team-changed-the-input-type-for-numbers/).

Make sure to test your forms’ implementation with assistive technologies, and review [official W3C guidance on accessible forms development](https://www.w3.org/WAI/tutorials/forms/) for further information.

(authoring_accessible_content)=

## Authoring accessible content

A number of built-in tools and additional resources are available to help create accessible content.

(built_in_accessibility_checker)=

### Built-in accessibility checker

Wagtail includes an accessibility checker built into the [user bar](wagtailuserbar_tag) and editing views supporting previews. The checker can help authors create more accessible websites following best practices and accessibility standards like [WCAG](https://www.w3.org/WAI/standards-guidelines/wcag/).

The checker is based on the [Axe](https://github.com/dequelabs/axe-core) testing engine and scans the loaded page for errors.

By default, the checker includes the following rules to find common accessibility issues in authored content:

-   `button-name`: `<button>` elements must always have a text label.
-   `empty-heading`: This rule checks for headings with no text content. Empty headings are confusing to screen readers users and should be avoided.
-   `empty-table-header`: Table header text should not be empty
-   `frame-title`: `<iframe>` elements must always have a text label.
-   `heading-order`: This rule checks for incorrect heading order. Headings should be ordered in a logical and consistent manner, with the main heading (h1) followed by subheadings (h2, h3, etc.).
-   `input-button-name`: `<input>` button elements must always have a text label.
-   `link-name`: `<a>` link elements must always have a text label.
-   `p-as-heading`: This rule checks for paragraphs that are styled as headings. Paragraphs should not be styled as headings, as they don’t help users who rely on headings to navigate content.
-   `alt-text-quality`: A custom rule ensures that image alt texts don't contain anti-patterns like file extensions and underscores.

To customize how the checker is run (such as what rules to test), you can define a custom subclass of {class}`~wagtail.admin.userbar.AccessibilityItem` and override the attributes to your liking. Then, swap the instance of the default `AccessibilityItem` with an instance of your custom class via the [`construct_wagtail_userbar`](construct_wagtail_userbar) hook.

For example, Axe's [`p-as-heading`](https://github.com/dequelabs/axe-core/blob/develop/lib/checks/navigation/p-as-heading.json) rule evaluates combinations of font weight, size, and italics to decide if a paragraph is acting as a heading visually. Depending on your heading styles, you might want Axe to rely only on font weight to flag short, bold paragraphs as potential headings.

```python
from wagtail.admin.userbar import AccessibilityItem


class CustomAccessibilityItem(AccessibilityItem):
    def get_axe_custom_checks(self, request):
        checks = super().get_axe_custom_checks(request)
        # Flag heading-like paragraphs based only on font weight compared to surroundings.
        checks.append(
            {
                "id": "p-as-heading",
                "options": {
                    "margins": [
                        { "weight": 150 },
                    ],
                    "passLength": 1,
                    "failLength": 0.5
                },
            },
        )
        return checks


@hooks.register('construct_wagtail_userbar')
def replace_userbar_accessibility_item(request, items, page):
    items[:] = [CustomAccessibilityItem() if isinstance(item, AccessibilityItem) else item for item in items]
```

The checks you run in production should be restricted to issues your content editors can fix themselves; warnings about things out of their control will only teach them to ignore all warnings. However, it may be useful for you to run additional checks in your development environment.

```python
from wagtail.admin.userbar import AccessibilityItem


class CustomAccessibilityItem(AccessibilityItem):
    # Run all Axe rules with these tags in the development environment
    axe_rules_in_dev = [
        "wcag2a",
        "wcag2aa",
        "wcag2aaa",
        "wcag21a",
        "wcag21aa",
        "wcag22aa",
        "best-practice",
    ]
    # Except for the color-contrast-enhanced rule
    axe_rules = {
        "color-contrast-enhanced": {"enabled": False},
    }

    def get_axe_run_only(self, request):
        if env.bool('DEBUG', default=False):
            return self.axe_rules_in_dev
        else:
            # In production, run Wagtail's default accessibility rules for authored content only
            return self.axe_run_only


@hooks.register('construct_wagtail_userbar')
def replace_userbar_accessibility_item(request, items, page):
    items[:] = [CustomAccessibilityItem() if isinstance(item, AccessibilityItem) else item for item in items]
```

#### AccessibilityItem reference

The following is the reference documentation for the `AccessibilityItem` class:

```{eval-rst}
.. autoclass:: wagtail.admin.userbar.AccessibilityItem

    .. autoattribute:: axe_include
    .. autoattribute:: axe_exclude
    .. autoattribute:: axe_run_only
       :no-value:
    .. autoattribute:: axe_rules
    .. autoattribute:: axe_custom_rules
       :no-value:
    .. autoattribute:: axe_custom_checks
       :no-value:
    .. autoattribute:: axe_messages
       :no-value:

    The above attributes can also be overridden via the following methods to allow per-request customization.
    When overriding these methods, be mindful of the mutability of the class attributes above.
    To avoid unexpected behavior, you should always return a new object instead of modifying the attributes
    directly in the methods.

    .. method:: get_axe_include(request)
    .. method:: get_axe_exclude(request)
    .. method:: get_axe_run_only(request)
    .. method:: get_axe_rules(request)
    .. method:: get_axe_custom_rules(request)
    .. method:: get_axe_custom_checks(request)
    .. method:: get_axe_messages(request)

    For more advanced customization, you can also override the following methods:

    .. automethod:: get_axe_context
    .. automethod:: get_axe_options
    .. automethod:: get_axe_spec
```

### wagtail-accessibility

[wagtail-accessibility](https://github.com/neon-jungle/wagtail-accessibility) is a third-party package which adds [tota11y](https://blog.khanacademy.org/tota11y-an-accessibility-visualization-toolkit/) to Wagtail previews.
This makes it easy for authors to run basic accessibility checks – validating the page’s heading outline, or link text.

### help_text and HelpPanel

Occasional Wagtail users may not be aware of your site’s content guidelines, or best practices of writing for the web. Use fields’ `help_text` and `HelpPanel` (see [Panel types](../reference/panels)).

### Readability

Readability is fundamental to accessibility. One of the ways to improve text content is to have a clear target for reading level / reading age, which can be assessed with [wagtail-readinglevel](https://github.com/torchbox-forks/wagtail-readinglevel) as a score displayed in rich text fields.

(accessibility_resources)=

### prefers-reduced-motion

Some users, such as those with vestibular disorders, may prefer a more static version of your site. You can respect this preference by using the `prefers-reduced-motion` media query in your CSS.

```css
@media (prefers-reduced-motion) {
    /* styles to apply if a user's device settings are set to reduced motion */
    /* for example, disable animations */
    * {
        animation: none !important;
        transition: none !important;
    }
}
```

Note that `prefers-reduced-motion` is only applied for users who enabled this setting in their operating system or browser. This feature is supported by Chrome, Safari and Firefox. For more information on reduced motion, see the [MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion).

## Accessibility resources

We focus on considerations specific to Wagtail websites, but there is much more to accessibility. Here are valuable resources to learn more, for developers but also designers and authors:

-   [W3C Accessibility Fundamentals](https://www.w3.org/WAI/fundamentals/)
-   [The A11Y Project](https://www.a11yproject.com/)
-   [US GSA – Accessibility for Teams](https://accessibility.digital.gov/)
-   [UK GDS – Dos and don’ts on designing for accessibility](https://accessibility.blog.gov.uk/2016/09/02/dos-and-donts-on-designing-for-accessibility/)
-   [Accessibility Developer Guide](https://www.accessibility-developer-guide.com/)
