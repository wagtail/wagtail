# Documentation guidelines

```{contents}
---
local:
depth: 1
---
```

## Formatting recommendations

Wagtail’s documentation uses a mixture of [Markdown](https://myst-parser.readthedocs.io/en/stable/syntax/syntax.html) and [reStructuredText](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html). We encourage writing documentation in Markdown first, and only reaching for more advanced reStructuredText formatting if there is a compelling reason.

Here are formats we encourage using when writing documentation for Wagtail.

### Paragraphs

It all starts here.
Keep your sentences short, varied in length.

Separate text with an empty line to create a new paragraph.

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

### Code blocks

Make sure to include the correct language code for syntax highlighting, and to format your code according to our coding guidelines. Frequently used: `python`, `css`, `html`, `html+django`, `javascript`, `sh`.

    ```python
    INSTALLED_APPS = [
        ...
        "wagtail",
        ...
    ]
    ```

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

    ```sh
    # some comment
    some command
    ```
    
<details>

<summary>Rendered output</summary>

```sh
# some comment
some command
```

</details>

Use `doscon` (DOS Console) only if explicitly calling out Windows commands alongside their bash equivalent.

    ```doscon
    # some comment
    some command
    ```

<details>

<summary>Rendered output</summary>

```doscon
# some comment
some command
```

</details>

### Links

Links are fundamental in documentation. Use internal links to tie your content to other docs, and external links as needed. Pick relevant text for links, so readers know where they will land.

Don’t rely on [`links over code`](https://www.example.com/), as they are impossible to spot.

```md
An [external link](https://wwww.example.com).
An [internal link to another document](/reference/contrib/legacy_richtext).
An auto generated link label to a page [](/getting_started/tutorial).
A [link to a reference](register_reports_menu_item).
```

<details>

<summary>Rendered output</summary>

An [external link](https://wwww.example.com).
An [internal link to another document](/reference/contrib/legacy_richtext).
An auto generated link label to a page [](/getting_started/tutorial).
A [link to a reference](register_reports_menu_item).

</details>

#### Reference links

Reference links (links to a target within a page) rely on the page having a reference created. Each reference must have a unique name and should use the `lower_snake_case` format. A reference can be added as follows:

```md
(my_awesome_section)=

##### Some awesome section title

...
```

The reference can be linked to, with an optional label, using the Markdown link syntax as follows:

```md
-   Auto generated label (preferred) [](my_awesome_section)
-   [label for section](my_awesome_section)
```

<details>

<summary>Rendered output</summary>

(my_awesome_section)=

##### Some awesome section title

...

-   Auto generated label (preferred) [](my_awesome_section)
-   [label for section](my_awesome_section)

</details>

You can read more about other methods of linking to, and creating references in the MyST parser docs section on [Targets and cross-referencing](https://myst-parser.readthedocs.io/en/stable/syntax/syntax.html#targets-and-cross-referencing).

### Note and warning call-outs

Use notes and warnings sparingly, as they rely on reStructuredText syntax which is more complicated for future editors.

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
![Screenshot of the workflow editing interface, with fields to change the workflow name, tasks, and assigned pages](/_static/images/screen44_workflow_edit.png)
```

<details>

<summary>Rendered output</summary>

![Screenshot of the workflow editing interface, with fields to change the workflow name, tasks, and assigned pages](/_static/images/screen44_workflow_edit.png)

</details>

### Autodoc

With its [autodoc](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html) feature, Sphinx supports writing documentation in Python docstrings for subsequent integration in the project’s documentation pages. This is a very powerful feature that we highly recommend using to document Wagtail’s APIs.

    ```{eval-rst}
    .. module:: wagtail.coreutils

    .. autofunction:: cautious_slugify
    ```

<details>
<summary>Rendered output</summary>

```{eval-rst}
.. module:: wagtail.coreutils

.. autofunction:: cautious_slugify
```

</details>

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

`toctree` and `contents` can be used as reStructuredText directives.

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

Sphinx offers release-metadata directives to generate this information consistently. Use as appropriate.

    ```{versionadded} 2.15
    ```

    ```{versionchanged} 2.15
    ```

<details>

<summary>Rendered output</summary>

```{versionadded} 2.15

```

```{versionchanged} 2.15

```

</details>

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

reStructuredText figures (`.. figure::`) only offer very marginal improvements over vanilla images. If your figure has a caption, add it as an italicised paragraph underneath the image.

### Other reStructuredText syntax and Sphinx directives

We generally want to favour Markdown over reStructuredText, to make it as simple as possible for newcomers to make documentation contributions to Wagtail. Always prefer Markdown, unless the document’s formatting highly depends on reStructuredText syntax.

If you want to use a specific Sphinx directive, consult with core contributors to see whether its usage is justified, and document its expected usage on this page.

### Arbitrary HTML

While our documentation tooling offers some support for embedding arbitrary HTML, this is frowned upon. Only do so if there is a necessity, and if the formatting is unlikely to need updates.
