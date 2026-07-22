---
name: draftjs-exporter
description: Use when working with the Draft.js exporter library. Manipulating and rendering Draft.js ContentState to HTML or Markdown, parsing Markdown back into ContentState, writing custom block/entity/style components, configuring block/style/entity maps, picking or building DOM, or extending the exporter with fallbacks and composite decorators. Trigger on imports from `draftjs_exporter`, `DOM.create_element`, `block_map` / `style_map` / `entity_decorators` / `composite_decorators`, `build_markdown_config`, `markdown_to_content_state`, or Draft.js `ContentState` / `entityMap` JSON.
license: MIT
metadata:
  version: "6.0.0"
---

# Draft.js exporter

Python library converting Draft.js raw [ContentState](https://wagtail.github.io/draftjs_exporter/content-state/) JSON into HTML or Markdown. Maintained by [Wagtail](https://wagtail.org/) contributors, developed alongside the [Draftail](https://www.draftail.org/) rich text editor.

The public API is small: an `HTML` exporter class, a `DOM` namespace with a React-like `create_element`, default config maps (`BLOCK_MAP`, `STYLE_MAP`), constants (`BLOCK_TYPES`, `ENTITY_TYPES`, `INLINE_STYLES`), and type aliases (`Props`, `Element`, `Component`, `ContentState`). Almost everything else is configuration.

## Quick reference

You can access a Markdown-native version of every documentation page by adding `index.md` at the end of the URL.

| Task                                          | Solution                                                                  | Docs                                                                                                    |
| --------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Render ContentState to HTML                   | `HTML({}).render(content_state)`                                          | [getting-started](https://wagtail.github.io/draftjs_exporter/getting-started/)                          |
| Override default blocks / styles              | `**BLOCK_MAP`, `**STYLE_MAP` then override keys                           | [block map](https://wagtail.github.io/draftjs_exporter/configuration/#block-map)                        |
| Add HTML attributes to a block                | `BLOCK_TYPES.X: {"element": "h3", "props": {"class": "…"}}`               | [block map](https://wagtail.github.io/draftjs_exporter/configuration/#block-map)                        |
| Wrap adjacent blocks (lists)                  | `"wrapper": "ul", "wrapper_props": {"class": "…"}`                        | [block map](https://wagtail.github.io/draftjs_exporter/configuration/#block-map)                        |
| Render entity data (image, link)              | `"entity_decorators": {ENTITY_TYPES.LINK: link}`                          | [entity components](https://wagtail.github.io/draftjs_exporter/custom-components/#entity-components)    |
| Read block data / depth in a component        | `props["block"]["data"]`, `props["block"]["depth"]`                       | [block components](https://wagtail.github.io/draftjs_exporter/custom-components/#block-components)      |
| Compose components / pass children            | `DOM.create_element(type, props, *children)`                              | [nesting](https://wagtail.github.io/draftjs_exporter/custom-components/#nesting-and-reusing-components) |
| Replace text by regex (line breaks, mentions) | `"composite_decorators": [{"strategy": rx, "component": fn}]`             | [composite decorators](https://wagtail.github.io/draftjs_exporter/configuration/#composite-decorators)  |
| Handle missing block / style / entity types   | `BLOCK_TYPES.FALLBACK`, `INLINE_STYLES.FALLBACK`, `ENTITY_TYPES.FALLBACK` | [fallbacks](https://wagtail.github.io/draftjs_exporter/fallback-components/)                            |
| Discard an entity type                        | `ENTITY_TYPES.EMBED: None`                                                | [entity decorators](https://wagtail.github.io/draftjs_exporter/configuration/#entity-decorators)        |
| Switch DOM engine                             | `"engine": DOM.HTML5LIB` (or `DOM.LXML`, `DOM.STRING_COMPAT`)             | [alternative engines](https://wagtail.github.io/draftjs_exporter/alternative-engines/)                  |
| Render Markdown instead of HTML               | `HTML(MARKDOWN_CONFIG).render(content_state)`                             | [Markdown](https://wagtail.github.io/draftjs_exporter/markdown/)                                        |
| Customize Markdown characters                 | `build_markdown_config({"bold": "__", "italic": "*", ...})`               | [Markdown chars](https://wagtail.github.io/draftjs_exporter/markdown/#configuring-output-characters)    |
| Parse Markdown back into ContentState         | `markdown_to_content_state(markdown, options=None)`                       | [Markdown importer](https://wagtail.github.io/draftjs_exporter/markdown/#importer)                      |
| Debug output                                  | `DOM.render_debug(elt)`, `echo '{...}' \| python example.py -`            | [API](https://wagtail.github.io/draftjs_exporter/api/)                                                  |
| Migrate between major versions                | `DOM.STRING_COMPAT` for old `string` output; per-version notes            | [migration guide](https://wagtail.github.io/draftjs_exporter/migration-guide/)                          |
| Full public API (constants, types, defaults)  | `draftjs_exporter.constants`, `types`, `defaults`                         | [API reference](https://wagtail.github.io/draftjs_exporter/api/)                                        |

## Quick start

Install `draftjs_exporter` from PyPI.

```python
from draftjs_exporter import HTML

exporter = HTML({})  # empty config = use default block/style/entity maps

html = exporter.render({
    "entityMap": {},
    "blocks": [{
        "key": "6m5fh",
        "text": "Hello, world!",
        "type": "unstyled",
        "depth": 0,
        "inlineStyleRanges": [],
        "entityRanges": [],
    }],
})
```

Debug with real JSON: `echo '{"json": "contents"}' | python example.py -`. See [getting-started](https://wagtail.github.io/draftjs_exporter/getting-started/).

## Configuration

The config is a single dict passed to `HTML()` with four optional keys plus `engine`. Each map extends the built-in defaults (`BLOCK_MAP`, `STYLE_MAP`) — spread them with `**` and override individual keys.

```python
from draftjs_exporter import BLOCK_MAP, BLOCK_TYPES, DOM, ENTITY_TYPES, HTML, STYLE_MAP
import re

config = {
    "block_map": {
        **BLOCK_MAP,
        BLOCK_TYPES.HEADER_TWO: "h2",                                  # string: tag name
        BLOCK_TYPES.HEADER_THREE: {"element": "h3", "props": {"class": "u-text-center"}},
        BLOCK_TYPES.UNORDERED_LIST_ITEM: {                             # wrapper for adjacent blocks
            "element": "li", "wrapper": "ul", "wrapper_props": {"class": "bullet-list"},
        },
    },
    "style_map": {
        **STYLE_MAP,
        "KBD": "kbd",
        "HIGHLIGHT": {"element": "strong", "props": {"style": {"textDecoration": "underline"}}},
    },
    "entity_decorators": {
        ENTITY_TYPES.LINK: lambda props: DOM.create_element("a", {"href": props["url"]}, props["children"]),
        ENTITY_TYPES.EMBED: None,  # None discards this entity type
    },
    "composite_decorators": [
        {"strategy": re.compile(r"\n"), "component": br},              # text transformations by regex
    ],
    "engine": DOM.STRING,  # default; see Engines below
}

exporter = HTML(config)
```

See [configuration reference](https://wagtail.github.io/draftjs_exporter/configuration/) for the full shape.

### Conventions

- **Extend `BLOCK_MAP` and `STYLE_MAP` with `**`** spread instead of rebuilding from scratch — they cover the common Draft.js types and styles.
- **Use `BLOCK_TYPES` / `INLINE_STYLES` / `ENTITY_TYPES` constants** instead of raw strings, so renames surface as test failures. They also expose `FALLBACK`.
- **Pick a component function only when you need block data, depth, or children composition.** A plain string or dict covers most cases.
- **Stick with the default `string` engine** unless you need HTML sanitization (`html5lib`/`lxml`).

## Custom components

The component API mirrors React's `createElement`: a function takes a `props` dict and returns an `Element`. The `props` shape differs between entities, blocks, and styles. Reference components from `entity_decorators` (entities) or `block_map` / `style_map` (blocks and styles).

```python
from draftjs_exporter import DOM, Element, Props


# Entity component: receives the entity's `data` dict as props.
def image(props: Props) -> Element:
    """Render an image element from entity data."""
    return DOM.create_element("img", {
        "src": props.get("src"),
        "width": props.get("width"),
        "height": props.get("height"),
        "alt": props.get("alt"),
    })


# Block component: receives `block` (Draft.js block object) and `children`.
def blockquote(props: Props) -> Element:
    """Render a blockquote with an optional cite attribute."""
    block_data = props["block"]["data"]
    return DOM.create_element(
        "blockquote", {"cite": block_data.get("cite")}, props["children"]
    )
```

Compose by passing extra positional children to `DOM.create_element(type, props, *children)`. Children can be strings, DOM elements, other components, or `None` (renders nothing). Pass `props["children"]` as the last argument so the block's content renders inside the wrapping element. See [custom components](https://wagtail.github.io/draftjs_exporter/custom-components/).

### Fallbacks

Each map accepts a `FALLBACK` key (`BLOCK_TYPES.FALLBACK`, `INLINE_STYLES.FALLBACK`, `ENTITY_TYPES.FALLBACK`) triggered when the exporter hits a type with no explicit mapping. A fallback can return `props["children"]` (keep content, drop wrapper), `None` (remove entirely), or any DOM element (alternative rendering). Useful during development and migrations. See [fallback components](https://wagtail.github.io/draftjs_exporter/fallback-components/).

## Engines

Engines are pluggable serialization strategies selected at runtime via the `engine` config key. Use the `DOM` class constants:

| Constant            | Extra install                                          | Notes                                             |
| ------------------- | ------------------------------------------------------ | ------------------------------------------------- |
| `DOM.STRING`        | none (default)                                         | Fast, dependency-free, no text escaping           |
| `DOM.HTML5LIB`      | `pip install draftjs_exporter[html5lib]`               | Escapes/sanitizes HTML                            |
| `DOM.LXML`          | `pip install draftjs_exporter[lxml]` + libxml2/libxslt | Escapes/sanitizes, alphabetical attrs             |
| `DOM.STRING_COMPAT` | none                                                   | Byte-identical to first release of `string`       |
| `DOM.MARKDOWN`      | none                                                   | Produces Markdown — use `MARKDOWN_CONFIG` instead |

**Engines are not guaranteed to produce byte-identical output.** Real differences: attribute ordering (alphabetical for `lxml`/`html5lib`, insertion order for `string`), quote escaping in attributes, attribute-name validation. Expect minor output differences when switching engines — re-check tests that compare rendered HTML exactly. See [troubleshooting: exporter behavior](https://wagtail.github.io/draftjs_exporter/troubleshooting/#exporter-behavior).

To build a custom engine, subclass `DOMEngine` (`draftjs_exporter.engines.base`) and implement `create_tag`, `append_child`, `render`. Reference it by dotted path: `"engine": "my_project.example.DOMListTree"`. See [custom engines](https://wagtail.github.io/draftjs_exporter/custom-engines/).

## Markdown

Markdown output is **experimental**. Prefer `MARKDOWN_CONFIG` and `build_markdown_config` over hand-rolling a Markdown config.

```python
from draftjs_exporter import HTML, MARKDOWN_CONFIG

exporter = HTML(MARKDOWN_CONFIG)
markdown = exporter.render(content_state)
```

Customize characters and fallbacks with `build_markdown_config`:

````python
from draftjs_exporter import HTML, build_markdown_config

config = build_markdown_config({
    "bold": "__", "italic": "*", "unordered_list_marker": "*",
    "ordered_list_delimiter": ")", "horizontal_rule": "---", "code_fence": "```",
    "style_fallback": None,  # None disables fallback (raises instead)
})
exporter = HTML(config)
````

All defaults produce valid [CommonMark](https://commonmark.org/). Limitations: no underline/subscript/reference-style links/tables; no HTML escaping in text; partial bold/italic overlap can produce markers strict parsers reject. See [Markdown support](https://wagtail.github.io/draftjs_exporter/markdown/).

### Importer

The Markdown importer (`markdown_to_content_state`) parses Markdown back into Draft.js `ContentState`, enabling round-trip workflows (`ContentState → Markdown → ContentState`). It is dependency-free and recognizes the same Markdown subset the exporter produces.

```python
from draftjs_exporter import build_markdown_config, HTML, markdown_to_content_state

options = {"bold": "__", "italic": "*"}
config = build_markdown_config(options)
exporter = HTML(config)
markdown = exporter.render(content_state)
# Round-trip by passing the same options to the importer.
round_tripped = markdown_to_content_state(markdown, options)
```

Only inline style markers (`bold`, `italic`, `strikethrough`) and `html_style_tags` are configurable. Block-level syntax (list markers, horizontal rules, code fences, ordered-list delimiters) is recognized polymorphically. See [Markdown importer](https://wagtail.github.io/draftjs_exporter/markdown/#importer).

## Common gotchas

1. **`entity` and `children` are reserved `props` keys.** The exporter overrides them — `entity` becomes a dict with `type`/`mutability`, and `children` becomes the already-rendered content. Pick entity `data` keys that avoid them; there is no workaround. See [entity props override](https://wagtail.github.io/draftjs_exporter/troubleshooting/#entity-props-override).
2. **`string` engine does not escape HTML outside attributes.** Use `html5lib`/`lxml` if you need escaping/sanitization. `DOM.parse_html` also provides no sanitization.
3. **Engine output is not byte-identical across engines.** Switching engines produces real differences (attribute order, quote escaping, self-closing tags, attribute-name validation). Update snapshot tests when changing `engine`.
4. **Overlapping inline styles render with minimum tags** (e.g. `<strong>Bold <em>Italic</em></strong>` rather than reopening `<strong>`). Semantically equivalent but breaks tests asserting exact strings.
5. **`style` props accept a dict** (camelCase keys) converted to a CSS string. Properties keep insertion order — not sorted alphabetically. Pass `style` as a string for byte-stable output.
6. **`className` is not auto-converted to `class`.** Use `class` directly.
7. **Engine constants are dotted-path strings, not classes.** The exporter imports the class lazily at runtime via `import_string`.
8. **`unstyled` blocks without text render as empty elements** (`<p></p>`), not nothing.

## Public API

All imported from `draftjs_exporter` directly:

- **`HTML`** (alias: `Exporter`) — `HTML(config).render(content_state)`.
- **`DOM`** — facade over the active engine. `create_element`, `render`, `render_debug`, `parse_html`, `append_child`, `camel_to_dash`. Engine constants: `DOM.STRING`, `DOM.HTML5LIB`, `DOM.LXML`, `DOM.STRING_COMPAT`, `DOM.MARKDOWN`.
- **Default maps & configs**: `BLOCK_MAP`, `STYLE_MAP`, `HTML_CONFIG`, `MARKDOWN_CONFIG`.
- **Constants**: `BLOCK_TYPES`, `INLINE_STYLES`, `ENTITY_TYPES` (each with a `FALLBACK` member).
- **Markdown helpers**: `build_markdown_config(options)`, `markdown_to_content_state(markdown, options=None)`, plus option type aliases `MarkdownOptions` and `MarkdownImporterOptions`.
- **Type aliases**: `Props`, `Element`, `Component`, `ContentState`, `Block`, `Entity`, `EntityMap`, `EntityRange`, `InlineStyleRange`, `RenderableConfig`, `ExporterConfig`, plus internals (`CompositeDecorators`, `ConfigMap`, `Decorator`, `EntityKey`, `Mutability`, `RenderableType`, `Tag`).
- **`DOMEngine`** — abstract base for custom engines. Import from `draftjs_exporter.engines.base` (not re-exported at top level).

For every `BLOCK_TYPES.*`, `INLINE_STYLES.*`, `ENTITY_TYPES.*` value, see [the API reference](https://wagtail.github.io/draftjs_exporter/api/) or [`constants.py`](https://github.com/wagtail/draftjs_exporter/blob/main/draftjs_exporter/constants.py).

## Resources

- [Full docs site](https://wagtail.github.io/draftjs_exporter/)
- [llms-full.txt](https://wagtail.github.io/draftjs_exporter/llms-full.txt)
- [GitHub](https://github.com/wagtail/draftjs_exporter)
