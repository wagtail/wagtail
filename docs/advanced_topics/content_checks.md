(content_checks)=

# Content checks

Wagtail ships a built-in content checker, available in the page editor's **Checks** side panel and in the userbar's **Checks** dialog on the front-end site. It reports content metrics, the page's SEO metadata (title, description and meta tags) with their lengths, and content issues found by [Axe](https://github.com/dequelabs/axe-core).

```{contents}
---
local:
---
```

## How it works

The content checker combines three pieces:

1. **Server-side configuration** – `wagtail.admin.userbar.ContentCheckerItem` renders the Axe configuration as a JSON `script` tag on every page with the userbar, and in the page editor's Checks panel. This includes which rules to run, custom rules, and human-readable messages.
2. **Client-side extraction** – the userbar running inside a page registers an Axe plugin ("extractor") that collects the page's main content and its `<head>` metadata (title, `meta` tags with a `name` or `property` attribute, `link` tags with a `rel` attribute, and JSON-LD scripts).
3. **Rendering** – shared Django templates (`wagtailadmin/shared/content_checks/`) provide the markup for the metrics and metadata sections; client-side modules (`client/src/includes/contentMetrics.ts`, `metadataExtraction.ts`, `metadataPreview.ts`) populate them with live data.

In the page editor, the checks panel needs the *rendered* page content, which lives in the preview `iframe` – possibly cross-origin in [headless setups](headless.md). The Axe plugin runs inside the iframe's own copy of the userbar, and communicates with the editor window through Axe's [plugin API](https://github.com/dequelabs/axe-core/blob/master/doc/API.md#plugins-registering-plugins). This is why the extraction runs "inside" the page rather than reading the iframe from the editor window directly.

On front-end pages, the userbar runs the same extraction locally in the page's window, so the userbar's Checks dialog can show the same information as the editor's Checks panel.

All of the rendering logic is shared between the two surfaces: the same metric definitions, metadata extraction, and metadata rendering code runs in both, against the same template partials.

## Configuring the checks

The checks are configured through a custom `ContentCheckerItem`, registered with the `construct_wagtail_userbar` hook. See {ref}`custom content checks <custom_content_checks>` for the hook setup and the full list of Axe configuration attributes (`axe_include`, `axe_exclude`, `axe_run_only`, `axe_rules`, custom rules, and messages).

To load additional JavaScript (for example to register a custom metric, as below), add it to the item's `Media`:

```python
class CustomContentCheckerItem(ContentCheckerItem):
    class Media:
        js = ("js/custom-metrics.js",)
```

## Custom content metrics

Content metrics are defined declaratively in `client/src/includes/contentMetrics.ts` and rendered into slots of the shared metrics template. Sites can add their own metrics with the `window.wagtail.userbar.registerMetric` API – mirroring {ref}`registerCheck <custom_content_checks>` for custom Axe checks.

A metric is a plain object:

```ts
interface RegisteredMetric {
  id: string;                               // unique, used as the value slot's data attribute
  getLabel: () => string;                   // the metric's label (rendered client-side)
  compute: (data: ExtractedContent) => string;  // the metric's value
}
```

`compute` receives the full extracted content: `lang`, `innerText` and `innerHTML` of the page's main content, and `metadata` – the page's head metadata (see below).

### Example: text-to-HTML ratio

The text-to-HTML ratio is a page-bloat / thin-content diagnostic: the proportion of the page's response that is visible text rather than markup. The usual approach fetches the raw server HTML and strips tags from it – but note that raw server HTML is invisible to client-rendered content, whereas Wagtail's extraction reads the *rendered* page, so the metric sees exactly what users see.

Within Wagtail's content checks, the rendered HTML and text are already available in the extraction payload, so the metric is a one-liner:

```javascript
// static/js/custom-metrics.js

window.wagtail.userbar.registerMetric({
    id: 'text-to-html-ratio',
    getLabel: () => 'Text / HTML ratio',
    compute: (content) => {
        const textLength = content.innerText.length;
        const htmlLength = content.innerHTML.length;
        if (!htmlLength) return '-';
        return `${Math.round((textLength / htmlLength) * 100)}%`;
    },
});
```

This renders a "Text / HTML ratio" row in the content metrics section of both the Checks panel and the userbar's Checks dialog. Treat the value purely as a diagnostic: a very low ratio generally means markup bloat (inlined styles, scripts, or deeply nested templates) rather than an SEO problem in itself.

## Page metadata

The extracted metadata is available to custom code as `content.metadata`:

```ts
interface PageMetadata {
  title: string;            // <title> text, untruncated
  url: string;              // the document's URL
  metaTags: MetaTagData[];  // all meta tags with name= or property= and content
  linkTags: LinkTagData[];  // all link tags with rel= (canonical, alternate, ...)
  jsonLdScripts: string[];  // raw text of all JSON-LD scripts
}
```

The "Page metadata" section displays the page's title and meta description,
with their lengths: the title length is measured in pixels with an offscreen
canvas at the desktop search results font size (`20px Arial`), against a
~580px reference budget, and the description is measured in characters
against a ~160 character budget. These are approximations of documented
search engine behaviour, not hard limits – search engines truncate titles
and snippets as needed.

The "View more meta tags" viewer lists every extracted tag and its content:
all `meta` tags (with `name` or `property`), and `link` tags holding a
metadata-relevant `rel` value – `canonical`, `alternate`, `shortlink`,
`amphtml`, `prev` and `next` (allowlisted in `metadataPreview.ts`; other
relations, such as stylesheets and resource hints, are page plumbing rather
than metadata). It lives in `client/src/includes/metadataPreview.ts`, as
do the length measurements.

## Extending the checks

The extraction pipeline is designed to be extended:

- Additional head data can be collected in `client/src/includes/metadataExtraction.ts` – for example, JSON-LD scripts are already captured in `jsonLdScripts` but not yet displayed.
- Additional metrics can be registered by sites with `registerMetric`, as shown above.
- New built-in metrics (such as Core Web Vitals) would follow the same registry pattern as the existing word count / reading time / readability metrics.

For user-facing documentation of the content checks, see the [content checks guide](https://guide.wagtail.org/en/reference/content-checks/) and the [page metadata guide](https://guide.wagtail.org/en/reference/content-checks/page-metadata/).
