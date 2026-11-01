(api_v3_migration)=

# Migrating from the v2 API

The v3 API has major differences with v2. We aim for all v2 capabilities to be present or replicable in v3, with exceptions. Treat moving to it as a migration to a new API: audit each client against the v3 behaviour described in this reference.

The v2 API is planned for deprecation in favor of v3. It currently remains available, but we recommend planning your migration now. See the [deprecation timeline](api_v2_deprecation) below.

(api_v2_deprecation)=

## Deprecation timeline for the v2 API

-   **Wagtail 8.1**: the v2 API remains available and supported, with no changes. We recommend trying v3 on your project, and [sharing feedback](https://github.com/wagtail/wagtail/discussions/14531) on anything that makes migrating difficult.
-   **Wagtail 8.2**: the v2 API is deprecated, and using it raises deprecation warnings. It is also published as a separate package for projects that need more time to migrate. We plan for the v3 API to be stable from this release.
-   **Wagtail 8.3 (LTS)**: the v2 API remains included, with deprecation warnings.
-   **Wagtail 9.0**: the v2 API is removed from Wagtail. Projects that still use it can switch to the separate package.

Only the v2 API's endpoints, views, and serializers are affected. [`APIField` and `api_fields`](api_v3_schema) are shared with the v3 API, and are not deprecated.

## Comparison of v2 and v3 APIs

Here is a comparison of the two versions across high-level areas relevant for compatibility.

| Area | v2 | v3 |
| --- | --- | --- |
| Framework | [Django REST Framework](https://www.django-rest-framework.org/) | [Django Ninja](https://django-ninja.dev/) and Pydantic |
| Operations | Read-only lists, detail, and find | Read/write, actions, and revisions |
| Resources | Pages, images, documents, redirects, by registered endpoints | All of v2 and sites, locales, snippets, schema, and whoami |
| Authentication | Public by default, DRF-configurable auth | Anonymous reads by default, Wagtail-provided bearer tokens |
| Page visibility | Public/live queryset by default | Public/live anonymously; drafts with change or publish permission when authenticated |
| Pagination envelope | `{"meta": {"total_count": N}, "items": [...]}` | `{"count": N, "items": [...]}` |
| Field projection | Rich `?fields=` with nested fields | Not supported. Fixed generated schemas |
| API fields | DRF serializers, sources, computed fields | Read compatibility plus typed Pydantic schemas and explicit writable fields |
| Unknown queries | Rejected | Unknown arbitrary field filters are often skipped |
| Ordering encoding | Comma-oriented v2 filters | Repeated/list query parameters |
| Find | Generic for registered endpoints | Pages and redirects only |
| Rich text | Multiple output formats | Multiple output formats and subset for input |
| StreamField | Read representation | Read and full-field write |
| Errors | DRF message dictionaries | Problem Details |
| OpenAPI / discovery | No schema support | OpenAPI 3.1 and authenticated schema discovery |
| Frontend cache | Pages, images, documents | Pages, images, documents, redirects |

See [the v3 reference](api_v3_reference) for the definitive per-endpoint details, and the [schema discovery guide](api_v3_schema) for how v3 fields and write schemas are generated.

## High-risk migration areas

Some v2 capabilities have no direct v3 equivalent, or behave differently enough to break a naive port. Pay particular attention to the following:

-   **Lack of `?fields=` support**. v3 exposes fixed schemas.
-   **DRF `APIField(serializer=...)` serializers support**. v3 has a temporary compatibility layer but the output may differ. Some fields have direct replacements, such as `wagtail.images.api.v3.fields.ImageRenditionField` replacing `wagtail.images.api.fields.ImageRenditionField` (see [the image renditions guide](api_v3_images)). Other fields can be reimplemented as a subclass of `wagtail.api.v3.fields.FieldSerializer`.
-   **Different error responses**. DRF messages vs. Problem Details. Different HTTP status codes for some errors.
-   **Different list envelope**. v2 returns `{"meta": {"total_count": ...}, ...}`; v3 returns `{"count": ..., "items": [...]}` and rejects a `limit` of `0`.
-   **Authenticated page visibility differs**. v2 defaulted to the public live queryset. A v3 bearer-authenticated request sees the pages the user has change or publish permission for, including draft-only pages.
-   **Custom v2 endpoints**. They may be replace-able with v3's generic endpoints, or require creation of new custom endpoints.
