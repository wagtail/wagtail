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

The default behaviour for Wagtail images is to use the `title` field as the alt text ([#4945](https://github.com/wagtail/wagtail/issues/4945)).
This is inappropriate, as it’s not communicated in the CMS interface, and the image upload form uses the image’s filename as the title by default.

Ideally, always add an optional “alt text” field wherever an image is used, alongside the image field:

-   For normal fields, add an alt text field to your image’s panel.
-   For StreamField, add an extra field to your image block.
-   For rich text – Wagtail already makes it possible to customise alt text for rich text images.

When defining the alt text fields, make sure they are optional so editors can choose to not write any alt text for decorative images. Take the time to provide `help_text` with appropriate guidance.
For example, linking to [established resources on alt text](https://axesslab.com/alt-texts/).

```{note}
Should I add an alt text field on the Image model for my site?

It’s better than nothing to have a dedicated alt field on the Image model ([#5789](https://github.com/wagtail/wagtail/pull/5789)), and may be appropriate for some websites, but we recommend to have it inline with the content because ideally alt text should be written for the context the image is used in:

- If the alt text’s content is already part of the rest of the page, ideally the image should not repeat the same content.
- Ideally, the alt text should be written based on the context the image is displayed in.
- An image might be decorative in some cases but not in others. For example, thumbnails in page listings can often be considered decorative.
```

See [RFC 51: Contextual alt text](https://github.com/wagtail/rfcs/pull/51) for a long-term solution to this problem.

### Embeds title

Missing embed titles are common failures in accessibility audits of Wagtail websites. In some cases, Wagtail embeds’ iframe doesn’t have a `title` attribute set. This is generally a problem with OEmbed providers like YouTube ([#5982](https://github.com/wagtail/wagtail/issues/5982)).
This is very problematic for screen reader users, who rely on the title to understand what the embed is, and whether to interact with it or not.

If your website relies on embeds that have are missing titles, make sure to either:

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

The [TableBlock](../reference/contrib/table_block) default implementation makes it too easy for end-users to miss they need either row or column headers ([#5989](https://github.com/wagtail/wagtail/issues/5989>)). Make sure to always have either row headers or column headers set.
Always add a Caption, so screen reader users navigating the site’s tables know where they are.

(accessibility_in_templates)=

## Accessibility in templates

Here are common gotchas to be aware of to make the site’s templates as accessible as possible,

### Alt text in templates

See the [content modelling](content_modeling) section above. Additionally, make sure to [customise images’ alt text](image_tag_alt), either setting it to the relevant field, or to an empty string for decorative images, or images where the alt text would be a repeat of other content.
Even when your images have alt text coming directly from the image model, you still need to decide whether there should be alt text for the particular context the image is used in. For example, avoid alt text in listings where the alt text just repeats the listing items’ title.

### Empty heading tags

In both rich text and custom StreamField blocks, it’s sometimes easy for editors to create a heading block but not add any content to it. If this is a problem for your site,

-   Add validation rules to those fields, making sure the page can’t be saved with the empty headings, for example by using the [StreamField](../topics/streamfield) `CharBlock` which is required by default.
-   Consider adding similar validation rules for rich text fields ([#6526](https://github.com/wagtail/wagtail/issues/6526)).

Additionally, you can hide empty heading blocks with CSS:

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
-   For Number fields, consider whether `input type="number"` really is appropriate, or whether there may be [better alternatives such as inputmode](https://technology.blog.gov.uk/2020/02/24/why-the-gov-uk-design-system-team-changed-the-input-type-for-numbers).

Make sure to test your forms’ implementation with assistive technologies, and review [official W3C guidance on accessible forms development](https://www.w3.org/WAI/tutorials/forms) for further information.

(authoring_accessible_content)=

## Authoring accessible content

Here are things you can do to help authors create accessible content.

### wagtail-accessibility

[wagtail-accessibility](https://github.com/neon-jungle/wagtail-accessibility) is a third-party package which adds [tota11y](https://khan.github.io/tota11y/) to Wagtail previews.
This makes it easy for authors to run basic accessibility checks – validating the page’s heading outline, or link text.

### help_text and HelpPanel

Occasional Wagtail users may not be aware of your site’s content guidelines, or best practices of writing for the web. Use fields’ `help_text` and `HelpPanel` (see [Panel types](../reference/pages/panels)).

### Readability

Readability is fundamental to accessibility. One of the ways to improve text content is to have a clear target for reading level / reading age, which can be assessed with [wagtail-readinglevel](https://github.com/vixdigital/wagtail-readinglevel) as a score displayed in rich text fields.

(accessibility_resources)=

## Accessibility resources

We focus on considerations specific to Wagtail websites, but there is much more to accessibility. Here are valuable resources to learn more, for developers but also designers and authors:

-   [W3C Accessibility Fundamentals](https://www.w3.org/WAI/fundamentals/)
-   [The A11Y Project](https://www.a11yproject.com/)
-   [US GSA – Accessibility for Teams](https://accessibility.digital.gov/)
-   [UK GDS – Dos and don’ts on designing for accessibility](https://accessibility.blog.gov.uk/2016/09/02/dos-and-donts-on-designing-for-accessibility/)
-   [Accessibility Developer Guide](https://www.accessibility-developer-guide.com/)
