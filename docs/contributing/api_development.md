(api_development)=

# API development

Guidance for Wagtail core contributors working on the v3 API transport layer first defined in [RFC 115](https://wagtail.org/rfc-115/).

## OpenAPI snapshot workflow

CI asserts that `api.get_openapi_schema()` matches `wagtail/api/v3/tests/snapshots/openapi.json`.

When you add or change endpoints intentionally, regenerate the snapshot and commit the changes:

```bash
just openapi-snapshot
```

## Type checking

The v3 API package is type-checked with [ty](https://docs.astral.sh/ty/) (configured in `[tool.ty]` in `pyproject.toml`). Checking is scoped to `wagtail/api/v3` only.

## Pagination

List endpoints use `@paginate` with `WagtailLimitOffsetPagination` (or a subclass such as `PageListingPagination` in `routers/pages.py`). Responses use Ninja's native envelope: `{"count": N, "items": [...]}`. `WAGTAILAPI_LIMIT_MAX` is enforced in the paginator.

## RFC 7807 errors

Register handlers via `register_exception_handlers(api)` in `wagtail/api/v3/errors.py`. Tests should use `assert_problem_response` from `wagtail.api.v3.tests.base`.
