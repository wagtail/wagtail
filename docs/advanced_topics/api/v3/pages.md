(api_v3_pages)=

# Pages

Pages are the core resource of the v3 API. You can list, find, read, create, edit, delete, and act on pages, including drafts, revisions, and page actions.

```{note}
Most page "read" endpoints support both anonymous and authenticated access. Writes (creating, editing, deleting, and page actions) always require an authenticated request with the relevant page permission. See [](api_v3_authentication).
```

## Listing pages

The `/pages/` endpoint returns a paginated list of pages using the compact base page schema:

```json
{
    "id": 3,
    "title": "Example",
    "meta": {
        "type": "tests.BlogPage",
        "detail_url": "/api/v3/pages/3/",
        "html_url": "/blog/example/",
        "locale": "en",
        "slug": "example",
        "first_published_at": "2026-08-01T10:00:00Z"
    }
}
```

The list uses the same pagination envelope as every list endpoint, with `count` for the total number of results and `?limit` / `?offset` for paging — see [](api_v3) for details.

Which pages appear depends on the access tier:

-   **Anonymous requests** see only publicly accessible pages: live, scoped to the request's site, and without any page view restrictions.
-   **Authenticated requests** see the pages the current user can explore in the admin, which includes draft-only pages.

### Filters

The list endpoint supports filtering, ordering, and searching through query parameters:

-   **`type`**: restrict to one or more page types, given as their Django model labels (for example `tests.BlogPage`). Repeat the parameter to request several types. Selecting exactly one type allows field filtering and ordering on that type's own fields, while multiple types filter by content type. List responses always use the compact base shape regardless of type.
-   **`ancestor_of`**: only pages that are ancestors of the given page.
-   **`child_of`**: only direct children of the given page. Pass `child_of=root` to filter relative to the site root.
-   **`descendant_of`**: only descendants of the given page. Pass `descendant_of=root` to filter to the whole tree under the root. `child_of` and `descendant_of` cannot be combined.
-   **`translation_of`**: only pages that are translations of the given page; the source page itself is excluded.
-   **`locale`**: a language code, for example `en` or `fr`, to restrict to a single locale.
-   **`site`**: restrict to a site, given by its hostname, port, site name, or ID.

These tree-relative and translation parameters reference other pages. The referenced page must be visible in the current access tier (anonymous or authenticated).

Here are two examples:

```sh
# Direct children of page 10, most recent first
curl "https://example.com/api/v3/pages/?child_of=10&order=-first_published_at"

# All blog pages in French that mention "drafting"
curl "https://example.com/api/v3/pages/?type=tests.BlogPage&locale=fr&search=drafting"
```

### Field filters, ordering, and search

Beyond the structured filters above, you can filter on the page's own exposed database fields (any `api_fields` the project declares, such as `title` or `slug`) as exact-match query parameters, order by them, and run full-text search:

-   **Field filters**: for example `?title=Example` returns pages whose `title` equals the value.
-   **`order`**: order by a field, with a leading `-` for descending order (for example `?order=-first_published_at`). Repeat the parameter to order by several fields, or pass `?order=random` for random ordering. Random ordering cannot be combined with a non-zero `?offset`.
-   **`search`**: full-text search over the page content, with `?search_operator=and` (all terms) or `?search_operator=or` (any term). This only works when page search is enabled.

```sh
# Blog pages ordered by title
curl "https://example.com/api/v3/pages/?type=tests.BlogPage&order=title"
```

## Finding a page

The `/pages/find/` endpoint resolves a page by its public HTML path (or by ID) to the canonical detail URL. It accepts `id` and/or `html_path`, plus optional `site` and `version`. When a page matches, the endpoint responds with an HTTP redirect (302) to `GET /pages/{page_id}/`.

```sh
curl "https://example.com/api/v3/pages/find/?html_path=/blog/example/"
```

When no page matches, it returns `404`. Path resolution always uses normal live routing, so a draft-only page returns `404` for an `html_path` lookup even for an authenticated request; only an authenticated `id` lookup can resolve a draft-only page.

## Page detail

The `/pages/{page_id}/` endpoint returns a single page, with the base fields plus any readable custom `api_fields` the page type declares. The `meta` block includes the page's type, URLs, locale, slug, and, where available, its SEO settings, menu fields, parent, and alias source.

Two query parameters control the response:

-   **`version`**: `live` (the default) returns the currently live page. `draft` returns the latest revision for an authenticated request.
-   **`rich_text_format`**: the output format for rich text fields, as described in [](api_v3_rich_text).

## Creating a page

The `/pages/` endpoint creates a new page under a parent. It requires an authenticated request and the page `add` (create) permission for the relevant page type.

The request body is a discriminated union: `meta.type` selects the concrete page type, and the remaining fields are that type's writable fields. A minimal create request looks like:

```json
{
    "meta": {
        "type": "blog.BlogPage",
        "parent_id": 3,
        "action": "publish"
    },
    "title": "Example",
    "slug": "example"
}
```

-   **`meta.type`**: the concrete page type, as its Django model label (for example `blog.BlogPage`).
-   **`meta.parent_id`**: the ID of the parent page, required to place the new page in the tree.
-   **`meta.action`**: optional. The only currently supported value is `publish`, which publishes the page as part of creation. Without it, the page is saved as a draft.
-   **`title`**: required.
-   **`slug`**: optional. When omitted, Wagtail generates a slug from the title, de-duplicating it against the page's siblings.

```sh
curl -X POST "https://example.com/api/v3/pages/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {"type": "blog.BlogPage", "parent_id": 3, "action": "publish"},
    "title": "Example",
    "slug": "example"
  }'
```

A successful create returns `201` with the type-specific page detail. The creating user is also subscribed to comment notifications for the page, matching the admin create flow.

### Writable fields

Beyond `title`, `slug`, and the `meta` envelope, you can submit any of the following, subject to the page type's declared `api_fields`:

-   Built-in writable page fields where present, for example `seo_title`, `search_description`, and `show_in_menus`;
-   Custom model fields the project exposes as writable API fields (declared `APIField(..., writable=True)` — see [](api_v3_schema));
-   StreamField values, as the internal list of blocks;
-   Rich text field values, using the input formats described in [](api_v3);
-   `ForeignKey` relations;
-   `ParentalManyToMany` fields;
-   InlinePanel / `ParentalKey` child relations whose child fields are also writable.

Each submitted field is validated against the page type's generated schema and its admin form, so the same validation, permission, revision, and audit behaviour as the editor applies.

## Editing a page

The `/pages/{page_id}/` endpoint updates an existing page. It requires an authenticated request and the page `change` (edit) permission.

`PATCH` is a partial update:

-   **`meta.type`**: optional. When omitted, the page's actual type is used. You only need to specify it when the payload must bind against a particular type.
-   Omitted fields and child relations are left unchanged.

```sh
curl -X PATCH "https://example.com/api/v3/pages/3/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated example"}'
```

Editing a live page without `meta.action=publish` creates a revision while preserving the currently-live database representation. With `action=publish`, the new revision is published, applying it to the live page.

```{note}
StreamField and child-relation values are replaced as a whole: a `PATCH` that supplies a StreamField or a child relation overwrites the full existing value rather than merging individual blocks or rows.
```

## Deleting a page

The `/pages/{page_id}/` endpoint deletes a page. It requires an authenticated request and the page `change` permission.

```{warning}
Deletion is a hard delete. There is no trash or undo. Descendants are deleted too, according to the delete action's permissions.
```

```sh
curl -X DELETE "https://example.com/api/v3/pages/3/" \
  -H "Authorization: Bearer $TOKEN"
```

## Revisions

Page revisions record every save as the current API user, so edits made over the API produce the same revision history as changes done in the admin. Accessing revisions requires access to the page's edit or publish capability.

### Listing revisions

The `/pages/{page_id}/revisions/` endpoint returns a paginated list of the page's revisions, newest first:

```json
{
    "id": 41,
    "object_id": "3",
    "created_at": "2026-08-05T14:22:00Z",
    "user_id": 2,
    "object_str": "Example",
    "approved_go_live_at": null
}
```

Each entry includes the revision ID, object ID, creation time, authoring user ID, object string, and approved go-live time. The list can be filtered with query parameters:

-   `created_at_from` / `created_at_to`: restrict to revisions created within a time range.
-   `user_id`: revisions authored by a given user.
-   `approved_go_live_at_from` / `approved_go_live_at_to`: revisions with an approved go-live time in a range.
-   `object_str`: a substring match on the revision's object string.

### Revision detail

The `/pages/{page_id}/revisions/{revision_id}/` endpoint returns a single revision's metadata, its content and base content types, and a `content_object` reconstructed from the revision. Revision IDs are scoped to the page: a revision belonging to another page returns `404`.

## Page actions

Page actions are operations Wagtail applies to a page as a whole, each exposed as a `POST /pages/{page_id}/actions/<name>/` endpoint. Each action requires an authenticated request and the permission indicated below, and runs through the same Wagtail action layer as the admin UI, so permissions, revisions, audit logs, hooks, and signals are preserved.

### Publish

`/pages/{page_id}/actions/publish/` requires the page `publish` permission. It publishes the page's latest revision. If that revision already has a future `go_live_at`, publishing schedules it for that time instead of publishing immediately. If the page has no revision yet, one is created first when the caller has permission:

```sh
curl -X POST "https://example.com/api/v3/pages/3/actions/publish/" \
  -H "Authorization: Bearer $TOKEN"
```

```{note}
There is no separate endpoint to set or cancel a publication schedule; the publish action only honours a `go_live_at` already present on a revision.
```

### Unpublish

`/pages/{page_id}/actions/unpublish/` requires the page `publish` permission. By default it unpublishes only the page; pass `recursive` as `true` to also unpublish its descendants.

### Copy

`/pages/{page_id}/actions/copy/` copies the page and requires the page `add` permission. It accepts:

-   `destination_id`: where to place the copy; defaults to the page's current parent.
-   `recursive`: copy descendants too.
-   `keep_live`: whether the copy stays live (default `true`).
-   `slug` / `title`: overrides for the copy; a slug is otherwise generated to be collision-safe.

```json
{
    "destination_id": 12,
    "recursive": true,
    "slug": "example-2"
}
```

A successful copy returns `201` with the new page's detail.

### Move

`/pages/{page_id}/actions/move/` moves the page and requires the page `change` permission. It needs `destination_id` and an optional `position`, one of `first-child`, `last-child`, `left`, `right`, `first-sibling`, or `last-sibling`:

```json
{"destination_id": 12, "position": "last-child"}
```

### Revert

`/pages/{page_id}/actions/revert/` reverts the page to a previous revision, given by `revision_id`, and requires the page `change` permission:

```json
{"revision_id": 41}
```

Reverting creates a new draft revision based on the given one, without publishing. To make the reverted content live, publish afterwards.

### Create an alias

`/pages/{page_id}/actions/create_alias/` creates an alias of the page and requires the page `add` permission. It accepts `destination_id` (defaults to the current parent), `recursive`, and an optional `slug` (otherwise generated to be collision-safe). A successful call returns `201` with the new alias's detail.

### Convert an alias

`/pages/{page_id}/actions/convert_alias/` converts an alias page into a regular page and requires the page `change` permission. It takes no request body.

### Copy for translation

`/pages/{page_id}/actions/copy_for_translation/` copies the page into another locale and requires i18n to be enabled and the translation submit permission. It accepts:

-   `locale`: the target language code, for example `fr` (required).
-   `copy_parents`: also copy the page's ancestor pages.
-   `alias`: create aliases rather than full copies.
-   `recursive`: include the page's subtree.

```json
{"locale": "fr", "recursive": true}
```

A successful call returns `201` with the new translated page's detail.

```{note}
Ongoing translation synchronization and [`wagtail-localize`](https://wagtail-localize.org/) workflows are not yet available through the v3 API. `copy_for_translation` creates the initial translated copy only.
```

## Pages API reference

We document the full generated OpenAPI reference for every page endpoint from Wagtail's own OpenAPI snapshot, see [](api_v3_reference).
