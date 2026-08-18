(api_v3_migration)=

# Migrating from the v2 API

The v3 API is a new and significantly broader API, not an in-place upgrade of the v2 read API. It adds write CMS operations, fixed generated schemas, bearer-token authentication, and new resources, using a different transport. Treat moving to it as a migration to a new API: audit each client against the v3 behaviour described in this reference, rather than assuming a v2 request will behave the same way.

The v2 read API remains **available, unchanged, and supported** in this release. Wagtail 8.0 does not deprecate, remove, or otherwise change v2, so existing headless integrations can keep running on v2 untouched. There is no need to migrate unless you want v3's write operations, authenticated access, or OpenAPI schema discovery. The migration path is planned (see the compatibility notes below), but no parity or deprecation tooling has shipped yet.

## Crosswalk at a glance

The table below compares the v2 and v3 APIs across the areas that matter when migrating. It is a crosswalk, not a complete parity audit, and it assumes the standard `/api/v3/` mount.

| Area | v2 | v3 |
| --- | --- | --- |
| Framework | Django REST Framework | Django Ninja and Pydantic |
| Mounting | Project-created `WagtailAPIRouter` and explicit endpoint classes | Singleton plus app-contributed routers |
| Operations | Read-only lists, detail, and find | Read/write, actions, and revisions |
| Resources | Pages, images, documents, redirects, by registered endpoints | Adds sites, locales, snippets, schema, and whoami; resources map one-to-many |
| Authentication | Project/DRF-configurable; built-in defaults are public | Wagtail bearer tokens; selected anonymous reads; sessions ignored |
| Page visibility | Public/live queryset by default | Public/live anonymously; explorable drafts when authenticated |
| Pagination envelope | `{"meta": {"total_count": N}, "items": [...]}` | `{"count": N, "items": [...]}` |
| Zero limit | Permitted | Rejected (`limit` must be at least `1`) |
| Field projection | Rich `?fields=` grammar with nested selection | No projection query; fixed generated schemas |
| API fields | DRF serializers, sources, computed fields | Read compatibility plus typed Pydantic schemas and explicit writable real fields |
| Unknown queries | Rejected | Unknown arbitrary field filters are often skipped |
| Ordering encoding | Comma-oriented v2 filters | Repeated/list query parameters |
| Find | Generic for registered endpoints | Pages and redirects only |
| Rich text | All four output formats | Same four outputs, plus typed write input and sanitisation |
| StreamField | Read representation | Read and full-field write |
| Errors | DRF message dictionaries | Problem Details, often `422` |
| OpenAPI / discovery | No built-in OpenAPI or schema route | OpenAPI 3.1 and authenticated schema discovery |
| Frontend cache | v2-specific signal handlers and URL names | No equivalent handlers yet |

See [the v3 reference](api_v3_reference) for the definitive per-endpoint details, and the [schema discovery guide](api_v3_schema) for how v3 fields and write schemas are generated.

## High-risk migration seams

Some v2 capabilities have no direct v3 equivalent, or behave differently enough to break a naive port. Pay particular attention to:

-   **`?fields=` projections have no v3 equivalent.** v3 exposes fixed, generated schemas rather than the v2 dynamic `?fields=` grammar, and does not support nested field selection or include/exclude projection. Clients that rely on `?fields=` cannot migrate without reworking how they select fields — see [](api_v3_schema).
-   **Arbitrary DRF `APIField(serializer=...)` behaviour is not a v3 input contract.** Such fields remain readable through a compatibility shim, but their output may differ and they define no input shape. Imports or writes that target these fields need review.
-   **Error responses differ.** v2 uses DRF message dictionaries; v3 uses Problem Details, often with different status codes. Error-handling code must be updated.
-   **The list envelope differs.** v2 returns `{"meta": {"total_count": ...}, ...}`; v3 returns `{"count": ..., "items": [...]}` and rejects a `limit` of `0`.
-   **Authenticated page visibility differs.** A v3 bearer-authenticated request sees the pages the user can explore in the admin, including draft-only pages, whereas v2 defaulted to the public live queryset. A request's readable surface changes with its credentials.
-   **v2 frontend-cache invalidation is hardcoded to v2 URL names.** v3 has no equivalent frontend-cache handlers yet, so cached v3 responses are not invalidated the same way.
-   **Internal admin explorer parameters** (for example `for_explorer`, `has_children`, and other special fields) are not present in v3.
-   **Custom v2 endpoints cannot be inferred from core.** Anything you subclassed or registered against a v2 `WagtailAPIRouter` — endpoint classes, auth, renderers, serializers, resources — is project-specific and needs to be re-expressed for v3.

## Not yet available for migration

Several capabilities you might expect from a full migration have not yet shipped for v3:

-   There is **no v2 deprecation timeline, warning, or parity test suite** — v2 remains fully supported, and no extraction into a legacy package has been announced.
-   There is **no official API client CLI** shipped in core (only the server-side `api_tokens` management command for token administration).
-   **Workflow and moderation operations** (submitting, approving, rejecting, resuming, or cancelling a workflow) do not have v3 routes.
-   The internal **admin API has not been replaced**; existing admin console consumers remain on their own endpoints.

These are stated so a migration plan does not assume they exist. They are separate from the v3 API surface documented on this site.

```{warning}
The earlier `wagtail-write-api` package is **not** a migration baseline. Core v3 is not wire- or behaviour-compatible with it, and the package has a critical authorization gap: its endpoints generally authenticate and then mutate models directly, without Wagtail's permission policies, admin forms, or actions. Its page permission helper populated response metadata but did not authorize operations, so a package token could act beyond the user's Wagtail permissions. Core v3 reconstructs the correct behaviour through permission-policy querysets, admin forms, registered actions, and broad permission tests, but nothing from the package should be carried forward as a compatibility contract.
```
