(api_v3_reference)=

# v3 API reference

For the best results, we recommend existing projects generate reference documentation from their own API exports, or use the interactive explorer at `/api/v3/docs`. The reference below is generated as part of Wagtail’s build pipelines, and will not contain project-specific changes. It is also fixed-schema and project-dependent: it is built from Wagtail’s own test OpenAPI snapshot via the `.. openapi::` directive, so it reflects only the models and endpoints in that snapshot rather than a given site’s custom models. For a real deployment, `/api/v3/openapi.json` (or your project’s own exported schema) is the source of truth.

Unlike the v2 API’s dynamic `?fields=` projection, v3 exposes fixed, generated schemas and does not support `?fields=` — see [](api_v3_schema) and the [migration guide](api_v3_migration). The domain pages (pages, images, documents, snippets, sites, locales, and redirects, along with schema discovery) cross-reference this generated reference with links and plain endpoint paths rather than embedding their own copies of these definitions.

```{eval-rst}
.. openapi:: ../../../../wagtail/api/v3/tests/snapshots/openapi.json
   :examples:
```
