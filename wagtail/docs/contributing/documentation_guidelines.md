# Documentation guidelines

```{contents}
---
local:
depth: 1
---
```

(writing_style_guide)=

## Writing style guide

To ensure consistency in tone and language, follow the [Google developer documentation style guide](https://developers.google.com/style) when writing the Wagtail documentation.

## Formatting recommendations

Wagtail’s documentation uses a mixture of [Markdown (with MyST)](inv:myst#syntax/core) and [reStructuredText](inv:sphinx#rst-primer). We encourage writing documentation in Markdown first, and only reaching for more advanced reStructuredText formatting if there is a compelling reason. Docstrings in Python code must be written in reStructuredText, as using Markdown is not yet supported.

Here are formats we encourage using when writing documentation for Wagtail.

### Paragraphs

It all starts here.
Keep your sentences short, varied in length.

Separate text with an empty line to create a new paragraph.

### Latin phrases and abbreviations

Try to avoid Latin phrases (such as `ergo` or `de facto`) and abbreviations (such as `i.e.` or `e.g.`), and use common English phrases instead. Alternatively, find a simpler way to communicate the concept or idea to the reader. The exception is `etc.` which can be used when space is limited.

Examples:

| Don't use this | Use this instead     |
| -------------- | -------------------- |
| e.g.           | for example, such as |
| i.e.           | that is              |
| viz.           | namely               |
| ergo           | therefore            |

### Heading levels

Use heading levels to create sections, and allow users to link straight to a specific section. Start documents with an `# h1`, and proceed with `## h2` and further sub-sections without skipping levels.

```md
# Heading level 1

## Heading level 2

### Heading level 3
```

### Lists

Use bullets for unordered lists, numbers when ordered. Prefer dashes `-` for bullets. Nest by indenting with 4 spaces.

```md
-   Bullet 1
-   Bullet 2
    -   Nested bullet 2
-   Bullet 3

1. Numbered list 1
2. Numbered list 2
3. Numbered list 3
```

<details>

<summary>Rendered output</summary>

-   Bullet 1
-   Bullet 2
    -   Nested bullet 2
-   Bullet 3

1. Numbered list 1
2. Numbered list 2
3. Numbered list 3

</details>

### Inline styles

Use **bold** and _italic_ sparingly and inline `code` when relevant.

```md
Use **bold** and _italic_ sparingly and inline `code` when relevant.
```

Keep in mind that in reStructuredText, italic is written with `*`, and inline code must be written with double backticks, like ` ``code`` `.

```rst
Use **bold** and *italic* sparingly and inline ``code`` when relevant.
```

### Code blocks

Make sure to include the correct language code for syntax highlighting, and to format your code according to our coding guidelines. Frequently used: `python`, `css`, `html`, `html+django`, `javascript`, `sh`.

````md
```python
INSTALLED_APPS = [
    ...
    "wagtail",
    ...
]
```
````

<details>

<summary>Rendered output</summary>

```python
INSTALLED_APPS = [
    ...
    "wagtail",
    ...
]
```

</details>

#### When using console (terminal) code blocks

```{note}
`$` or `>` prompts are not needed, this makes it harder to copy and paste the lines and can be difficult to consistently add in every single code snippet.
```

Use `sh` as it has better support for comment and code syntax highlighting in MyST's parser, plus is more compatible with GitHub and VSCode.

````md
```sh
# some comment
some command
```
````

<details>

<summary>Rendered output</summary>

```sh
# some comment
some command
```

</details>

Use `doscon` (DOS Console) only if explicitly calling out Windows commands alongside their bash equivalent.

````md
```doscon
# some comment
some command
```
````

<details>

<summary>Rendered output</summary>

```doscon
# some comment
some command
```

</details>

#### Code blocks that contain triple backticks

You can use three or more backticks to create code blocks. If you need to include triple backticks in a code block, you can use a different number of backticks to wrap the code block. This is useful when you need to demonstrate a Markdown code block, such as in the examples above.

`````md
````md
```python
print("Hello, world!")
```
````
`````

<details>

<summary>Rendered output</summary>

````md
```python
print("Hello, world!")
```
````

</details>

### Links

Links are fundamental in documentation. Use internal links to tie your content to other docs, and external links as needed. Pick relevant text for links, so readers know where they will land.

Do not let external links hide critical context for the reader. Instead, provide the core information on the page and use links for added context.

```md
An [external link](https://wwww.example.com).
An [internal link to another document](/reference/contrib/legacy_richtext).
An auto generated link label to a page [](/getting_started/tutorial).
A [link to a target](register_reports_menu_item).
Do not use [click here](https://www.example.com) as the link's text, use a more descriptive label.
Do not rely on links for critical context, like [why it is important](https://www.example.com).
```

<details>

<summary>Rendered output</summary>

An [external link](https://wwww.example.com).
An [internal link to another document](/reference/contrib/legacy_richtext).
An auto generated link label to a page [](/getting_started/tutorial).
A [link to a target](register_reports_menu_item).
Do not use [click here](https://www.example.com) as the link's text, use a more descriptive label.
Do not rely on links for critical context, like [why it is important](https://www.example.com).

</details>

#### Anchor links

Anchor links point to a specific target on a page. They rely on the page having the target created. Each target must have a unique name and should use the `lower_snake_case` format. A target can be added as follows:

```md
(my_awesome_section)=

##### Some awesome section title

...
```

The target can be linked to, with an optional label, using the Markdown link syntax as follows:

```md
-   Auto generated label (preferred) [](my_awesome_section)
-   [label for section](my_awesome_section)
```

Rendered output:

(my_awesome_section)=

##### Some awesome section title

...

-   Auto generated label (preferred) [](my_awesome_section)
-   [label for section](my_awesome_section)

You can read more about other methods of linking to, and creating references in the MyST-Parser docs section on [](inv:myst#syntax/cross-referencing).

#### Intersphinx links (external docs)

Due to the large amount of links to external documentation (especially Django), we have added the integration via intersphinx references. This is configured via [](inv:sphinx:std:confval#intersphinx_mapping) in the `docs/conf.py` file. This allows you to link to specific sections of a project's documentation and catch warnings when the target is no longer available.

Markdown example:

```md
You can select widgets from [Django's form widgets](inv:django#ref/forms/widgets).
```

reStructuredText example:

```rst
You can select widgets from :doc:`Django form widget <django:ref/forms/widgets>`.
```

The format for a Sphinx link in Markdown is `inv:key:domain:type#name`. The `key`, `domain`, and `type` are optional, but are recommended to avoid ambiguity when there are multiple targets with the same `name`.

If the `name` contains a space, you need to wrap the whole link in angle brackets `<>`.

```md
See Django's docs on [](<inv:django:std:label#topics/cache:template fragment caching>).
```

<details>

<summary>Rendered output</summary>

See Django's docs on [](<inv:django:std:label#topics/cache:template fragment caching>).

</details>

##### Find the right intersphinx target

The intersphinx target for a specific anchor you want to link to may not be obvious. You can use the `myst-inv` command line tool from MyST-Parser and save the output as a JSON or YAML file to get a visual representation of the available targets.

```sh
myst-inv https://docs.djangoproject.com/en/stable/_objects/ --format=json > django-inv.json
```

Using the output from `myst-inv`, you can follow the tree structure under the `objects` key to build the link target. Some text editors such as VSCode can show you the breadcrumbs to the target as you navigate the file.

Other tools are also available to help you explore Sphinx inventories, such as [sphobjinv](https://github.com/bskinn/sphobjinv) and Sphinx's built-in `sphinx.ext.intersphinx` extension.

```sh
sphobjinv suggest "https://docs.djangoproject.com/en/stable/_objects/" 'template fragment caching' -su

python -m sphinx.ext.intersphinx https://docs.djangoproject.com/en/stable/_objects/
```

In some cases, a more specific target may be available in the documentation. However, you may need to inspect the source code of the page to find it.

For example, the above section on Django's docs can also be linked via the type `templatetag` and the name `cache`.

```md
See Django's docs on the [](inv:django:std:templatetag#cache) tag.
```

<details>

<summary>Rendered output</summary>

See Django's docs on the [](inv:django:std:templatetag#cache) tag.

</details>

Note that while the link takes you to the same section, the URL hash and the default text will be different. If you use a custom text, this may not make a difference to the reader. However, they are semantically different.

Use the first approach (with the `label` type) when you are linking in the context of documentation in general, such as a guide on how to do caching. Use the second approach (with the `templatetag` type) when you are linking in the context of writing code, such as the use of the `{% cache %}` template tag. The second approach is generally preferred when writing docstrings.

#### Absolute links

Sometimes, there are sections in external docs that do not have a Sphinx target target attached at all. Before linking to such sections, consider linking to the nearest target before that section. If there is one available that is close enough such that your intended section is immediately visible upon clicking the link, use that. Otherwise, you can write it as a full URL. Remember to use the `stable` URL and not a specific version.

A common example of using full URLs over intersphinx links is when linking to sections in Django's release notes.

```md
`DeleteView` has been updated to align with [Django 4.0's `DeleteView` implementation](https://docs.djangoproject.com/en/stable/releases/4.0/#deleteview-changes).
```

<details>

<summary>Rendered output</summary>

`DeleteView` has been updated to align with [Django 4.0's `DeleteView` implementation](https://docs.djangoproject.com/en/stable/releases/4.0/#deleteview-changes).

</details>

For external links to websites with no intersphinx mapping, always use the `https://` scheme.

Absolute links are also preferred for one-off links to external docs, even if they have a Sphinx object inventory. Once there are three or more links to the same project, consider adding an intersphinx mapping if possible.

#### Code references

When linking to code references, you can use Sphinx's [reference roles](inv:sphinx#usage/restructuredtext/roles).

Markdown example:

```md
The {class}`~django.db.models.JSONField` class lives in the {mod}`django.db.models.fields.json` module,
but it can be imported from the {mod}`models <django.db.models>` module directly.
For more info, see {ref}`querying-jsonfield`.
```

reStructuredText example:

```rst
The :class:`~django.db.models.JSONField` class lives in the :mod:`django.db.models.fields.json` module,
but it can be imported from the :mod:`models <django.db.models>` module directly.
For more info, see :ref:`querying-jsonfield`.
```

<details>

<summary>Rendered output</summary>

The {class}`~django.db.models.JSONField` class lives in the {mod}`django.db.models.fields.json` module,
but it can be imported from the {mod}`models <django.db.models>` module directly.
For more info, see {ref}`querying-jsonfield`.

</details>

Adding `~` before the dotted path will shorten the link text to just the final part (the object name). This can be useful when the full path is already mentioned in the text. You can also set the current scope of the documentation with a [`module`](inv:sphinx:rst:directive#py:module) or [`currentmodule`](inv:sphinx:rst:directive#py:currentmodule) directive to avoid writing the full path to every object.

````md
```{currentmodule} wagtail.admin.viewsets.model

```

The {class}`ModelViewSet` class extends the {class}`~wagtail.admin.viewsets.base.ViewSet` class.
````

<details>

<summary>Rendered output</summary>

```{currentmodule} wagtail.admin.viewsets.model

```

The {class}`ModelViewSet` class extends the {class}`~wagtail.admin.viewsets.base.ViewSet` class.

</details>

```{currentmodule} None

```

A reference role can also define how it renders itself. In the above examples, the [`class`](inv:sphinx:rst:role#py:class) and [`mod`](inv:sphinx:rst:role#py:mod) roles are rendered as an inline code with link, but the [`ref`](inv:sphinx:rst:role#ref) role is rendered as a plain link.

These features make reference roles particularly useful when writing reference-type documentation and docstrings.

Aside from using reference roles, you can also use the link syntax. Unlike reference roles, the link syntax requires the full path to the object and it allows you to customize the link label. This can be useful when you want to avoid the reference role's default rendering, for example to mix inline code and plain text as the link label.

```md
For more details on how to query the [`JSONField` model field](django.db.models.JSONField),
see [the section about querying `JSONField`](inv:django#querying-jsonfield).
```

<details>

<summary>Rendered output</summary>

For more details on how to query the [`JSONField` model field](django.db.models.JSONField),
see [the section about querying `JSONField`](inv:django#querying-jsonfield).

</details>

### Note and warning call-outs

Use notes and warnings sparingly to get the reader's attention when needed. These can be used to provide additional context or to warn about potential issues.

    ```{note}
    Notes can provide complementary information.
    ```

    ```{warning}
    Warnings can be scary.
    ```

<details>

<summary>Rendered output</summary>

```{note}
Notes can provide complementary information.
```

```{warning}
Warnings can be scary.
```

</details>

These call-outs do not support titles, so be careful not to include them, titles will just be moved to the body of the call-out.

    ```{note} Title's here will not work correctly
    Notes can provide complementary information.
    ```

### Images

Images are hard to keep up-to-date as documentation evolves, but can be worthwhile nonetheless. Here are guidelines when adding images:

-   All images should have meaningful [alt text](https://axesslab.com/alt-texts/) unless they are decorative.
-   Images are served as-is – pick the correct format, and losslessly compress all images.
-   Use absolute paths for image files so they are more portable.

```md
![The TableBlock component in StreamField, with row header, column header, caption fields - and then the editable table](/_static/images/screen40_table_block.png)
```

<details>

<summary>Rendered output</summary>

![The TableBlock component in StreamField, with row header, column header, caption fields - and then the editable table](/_static/images/screen40_table_block.png)

</details>

### Docstrings and API reference (autodoc)

With its [autodoc](inv:sphinx#ext-autodoc) feature, Sphinx supports writing documentation in Python docstrings for subsequent integration in the project’s documentation pages. This is a very powerful feature that we highly recommend using to document Wagtail’s APIs.

Modules, classes, and functions can be documented with docstrings. Class and instance attributes can be documented with docstrings (with triple quotes `"""`) or doc comments (with hash-colon `#:`). Docstrings are preferred, as they have better integration with code editors. Docstrings in Python code must be written in reStructuredText syntax.

```py
SLUG_REGEX = r'^[-a-zA-Z0-9_]+$'
"""Docstring for module-level variable ``SLUG_REGEX``."""

class Foo:
    """Docstring for class ``Foo``."""

    bar = 1
    """Docstring for class attribute ``Foo.bar``."""

    #: Doc comment for class attribute ``Foo.baz``.
    #: It can have multiple lines, and each line must start with ``#:``.
    #: Note that it is written before the attribute.
    #: While Sphinx supports this, it is not recommended.
    baz = 2

    def __init__(self):
        self.spam = 4
        """Docstring for instance attribute ``spam``."""
```

The autodoc extension provides many directives to document Python code, such as [`autoclass`](inv:sphinx#autoclass), [`autofunction`](inv:sphinx#autofunction), [`automodule`](inv:sphinx#automodule), along with different options to customize the output. In Markdown files, these directives need to be wrapped in an `eval-rst` directive. As with docstrings, everything inside the `eval-rst` block must be written in reStructuredText syntax.

You can mix automatic and non-automatic documentation. For example, you can use [`module`](inv:sphinx#py:module) instead of `automodule` and write the module's documentation in the `eval-rst` block, but still use `autoclass` and `autofunction` for classes and functions. Using automatic documentation is recommended, as it reduces the risk of inconsistencies between the code and the documentation, and it provides better integration with code editors.

    ```{eval-rst}
    .. module:: wagtail.coreutils

        Wagtail's core utilities.

        .. autofunction:: cautious_slugify
            :no-index:
    ```

<details>
<summary>Rendered output</summary>

```{eval-rst}
.. module:: wagtail.coreutils
    :no-index:

    Wagtail's core utilities.

    .. autofunction:: cautious_slugify
        :no-index:
```

</details>

For more details on the available directives and options, refer to [](inv:sphinx#autodoc-directives) and [](inv:sphinx#usage/domains/python) in Sphinx's documentation.

### Tables

Only use tables when needed, using the [GitHub Flavored Markdown table syntax](https://github.github.com/gfm/#tables-extension-).

```md
| Browser       | Device/OS |
| ------------- | --------- |
| Stock browser | Android   |
| IE            | Desktop   |
| Safari        | Windows   |
```

<details>

<summary>Rendered output</summary>

| Browser       | Device/OS |
| ------------- | --------- |
| Stock browser | Android   |
| IE            | Desktop   |
| Safari        | Windows   |

</details>

### Tables of contents

The [`toctree` and `contents` directives](inv:myst#organising-content) can be used to render tables of contents.

    ```{toctree}
    ---
    maxdepth: 2
    titlesonly:
    ---
    getting_started/index
    topics/index
    ```

    ```{contents}
    ---
    local:
    depth: 1
    ---
    ```

### Version added, changed, deprecations

Sphinx offers release-metadata directives to present information about new or updated features in a consistent manner.

    ```{versionadded} 2.15
    The `WAGTAIL_NEW_SETTING` setting was added.
    ```

    ```{versionchanged} 2.15
    The `WAGTAIL_OLD_SETTING` setting was deprecated.
    ```

<details>

<summary>Rendered output</summary>

```{versionadded} 2.15
The `WAGTAIL_NEW_SETTING` setting was added.
```

```{versionchanged} 2.15
The `WAGTAIL_OLD_SETTING` setting was deprecated.
```

</details>

These directives will typically be removed two releases after they are added, so should only be used for short-lived information, such as "The `WAGTAILIMAGES_CACHE_DURATION` setting was added". Detailed documentation about the feature should be in the main body of the text, outside of the directive.

### Progressive disclosure

We can add supplementary information in documentation with the HTML `<details>` element. This relies on HTML syntax, which can be hard to author consistently, so keep this type of formatting to a minimum.

```html
<details>
    <summary>Supplementary information</summary>

    This will be visible when expanding the content.
</details>
```

Example:

<details>

<summary>Supplementary information</summary>

This will be visible when expanding the content.

</details>

## Formatting to avoid

There is some formatting in the documentation which is technically supported, but we recommend avoiding unless there is a clear necessity.

### Call-outs

We only use `{note}` and `{warning}` call-outs. Avoid `{admonition}`, `{important}`, `{topic}`, and `{tip}`. If you find one of these, please replace it with `{note}`.

### Glossary

Sphinx glossaries (`.. glossary::`) generate definition lists. Use plain bullet or number lists instead, or sections with headings, or a table.

### Comments

Avoid documentation source comments in committed documentation.

### Figure

reStructuredText figures (`.. figure::`) only offer very marginal improvements over vanilla images. If your figure has a caption, add it as an italicized paragraph underneath the image.

### Other reStructuredText syntax and Sphinx directives

We generally want to favor Markdown over reStructuredText, to make it as simple as possible for newcomers to make documentation contributions to Wagtail. Always prefer Markdown, unless the document’s formatting highly depends on reStructuredText syntax.

If you want to use a specific Sphinx directive, consult with core contributors to see whether its usage is justified, and document its expected usage on this page.

### Markdown in reStructuredText

Conversely, do not use Markdown syntax in places where reStructuredText is required. A common mistake is writing Markdown-style inline `` `code` `` (with single backticks) inside Python code docstrings and inside `eval-rst` directives. This is not supported and will not render correctly.

### Arbitrary HTML

While our documentation tooling offers some support for embedding arbitrary HTML, this is frowned upon. Only do so if there is a necessity, and if the formatting is unlikely to need updates.

(documentation_code_example_considerations)=

## Code example considerations

When including code examples, particularly JavaScript or embedded HTML, it's important to follow best practices for security, accessibility and approaches that make it easier to understand the example.

These are not hard rules but rather considerations to make when writing example code.

### Reference example filename

At the start of a code snippet, it can be helpful to reference an example filename at the top. For example: `# wagtail_hooks.py` or `// js/my-custom.js`.

### CSP (Content Security Policy) compliance

When adding JavaScript from external sources or custom scripts, ensure CSP compliance to prevent security vulnerabilities like cross-site scripting (XSS).

Avoid `mark_safe` where possible, and use `format_html` and use examples that load external files to manage scripts securely instead of inline `<script>` usage.

### Accessibility compliance

Make sure that all examples are accessible and adhere to accessibility standards (for example: WCAG, ATAG).

For interactive components, ensure proper keyboard navigation and screen reader support. When creating dynamic content or effects (such as animations or notifications), provide options for users to pause, stop, or adjust these features as needed.

If needed, call out explicitly that the example is not compliant with accessibility and would need additional considerations before adoption.
