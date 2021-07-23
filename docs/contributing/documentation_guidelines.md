# Documentation guidelines

```eval_rst
.. contents::
    :local:
    :depth: 1
```

## Formatting recommendations

Wagtail’s documentation uses a mixture of [Markdown](https://commonmark.org/help/) and [reStructuredText](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html). We encourage writing documentation in Markdown first, and only reaching for more advanced reStructuredText formatting if there is a compelling reason.

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
- Bullet 1
- Bullet 2
    - Nested bullet 2
- Bullet 3

1. Numbered list 1
2. Numbered list 2
3. Numbered list 3
```

<details>

<summary>Rendered output</summary>

- Bullet 1
- Bullet 2
    - Nested bullet 2
- Bullet 3

1. Numbered list 1
2. Numbered list 2
3. Numbered list 3

</details>

### Inline styles

Use **bold** and _italic_ sparingly, inline `code` when relevant.

```md
Use **bold** and _italic_ sparingly, inline `code` when relevant.
```

### Code blocks

Make sure to include the correct language code for syntax highlighting, and to format your code according to our coding guidelines. Frequently used: `python`, `css`, `html`, `html+django`, `javascript`, `console`.

    ```python
    INSTALLED_APPS = [
        ...
        "wagtail.core",
        ...
    ]
    ```

### Links

Links are fundamental in documentation. Use internal links to tie your content to other docs, and external links as needed. Pick relevant text for links, so readers know where they will land.

Don’t rely on [`links over code`](https://www.example.com/), as they are impossible to spot.

```md
An [external link](https://wwww.example.com).
An [internal link to another document](/reference/contrib/legacy_richtext.md).
A [link to a reference](register_reports_menu_item).
```

<details>

<summary>Rendered output</summary>

An [external link](https://wwww.example.com).
An [internal link to another document](/reference/contrib/legacy_richtext.md).
A [link to a reference](register_reports_menu_item).

</details>

Reference links rely on creating a reference in reStructuredText. Prefer linking to the whole document if at all possible, otherwise create a reference by embedding reStructuredText with `eval_rst`:

    ```eval_rst
    .. _register_reports_menu_item:
    ```

### Note and warning call-outs

Use notes and warnings sparingly, as they rely on reStructuredText syntax which is more complicated for future editors.

    ```eval_rst note:: Notes can provide complementary information.
    ```

    ```eval_rst warning:: Warnings can be scary.
    ```

<details>

<summary>Rendered output</summary>

```eval_rst note:: Notes can provide complementary information.
```

```eval_rst warning:: Warnings can be scary.
```

</details>

### Images

Images are hard to keep up-to-date as documentation evolves, but can be worthwhile nonetheless. Here are guidelines when adding images:

- All images should have meaningful [alt text](https://axesslab.com/alt-texts/) unless they are decorative.
- Images are served as-is – pick the correct format, and losslessly compress all images.
- Use absolute paths for image files so they are more portable.

```md
![Screenshot of the workflow editing interface, with fields to change the workflow name, tasks, and assigned pages](/_static/images/screen44_workflow_edit.png)
```

<details>

<summary>Rendered output</summary>

![Screenshot of the workflow editing interface, with fields to change the workflow name, tasks, and assigned pages](/_static/images/screen44_workflow_edit.png)

</details>

### Autodoc

With its [autodoc](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html) feature, Sphinx supports writing documentation in Python docstrings for subsequent integration in the project’s documentation pages. This is a very powerful feature which we highly recommend using to document Wagtail’s APIs.

    ```eval_rst
    .. module:: wagtail.core.utils

    .. autofunction:: cautious_slugify
    ```

<details>
<summary>Rendered output</summary>

```eval_rst
.. module:: wagtail.core.utils

.. autofunction:: cautious_slugify
```

</details>

### Tables

Only use tables when needed, with the “simple” reStructuredText syntax, which is hard enough to format as it is.

    ```eval_rst
    =============  =============
    Browser        Device/OS    
    =============  =============
    Stock browser  Android      
    IE             Desktop      
    Safari         Windows      
    =============  =============
    ```

<details>

<summary>Rendered output</summary>

```eval_rst
=============  =============
Browser        Device/OS    
=============  =============
Stock browser  Android      
IE             Desktop      
Safari         Windows      
=============  =============
```

</details>

### Tables of content

`toctree` and `contents` can be used as reStructuredText embeds.

    ```eval_rst
    .. toctree::
        :maxdepth: 2
        :titlesonly:

        getting_started/index
        topics/index
    ```

    ```eval_rst
    .. contents::
    ```

### Version added, changed, deprecations

Sphinx offers release-metadata directives to generate this information consistently. Use as appropriate.

    ```eval_rst
    .. versionadded:: 2.15
    ```

    ```eval_rst
    .. versionchanged:: 2.15
    ```

<details>

<summary>Rendered output</summary>

```eval_rst
.. versionadded:: 2.15
```

```eval_rst
.. versionchanged:: 2.15
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

We only use `note::` and `warning::` call-outs. Avoid `important::`, `topic::`, and `tip::`. If you find one of these, please replace it with `note::`.

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
