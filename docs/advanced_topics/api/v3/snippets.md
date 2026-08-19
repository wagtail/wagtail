(api_v3_snippets)=

# Snippets

Snippets are small pieces of reusable, non-page content that Wagtail manages through the admin. The v3 API exposes registered snippet models for reading, writing, and where the model supports it, revisions, drafts, and translations.

```{note}
Unlike pages, images, and documents, snippet endpoints are bearer-only: every snippet read and write requires an authenticated request with the relevant model permission. See [](api_v3_authentication) and the [permissions and visibility guide](api_v3_permissions) for how these grants work.
```

## Registering snippets

A snippet model is exposed through the v3 API only if it declares at least one `APIField`. Its routes use the exact Django model label as the path segment, for example `mymodels.Advert`, and primary keys are accepted as string path input, supporting integer, UUID, and string primary keys.

The per-type routes are:

-   `GET /snippets/{type}/` — list snippets of the model.
-   `GET /snippets/{type}/{pk}/` — return one snippet.
-   `POST /snippets/{type}/` — create a snippet.
-   `PATCH /snippets/{type}/{pk}/` — update a snippet.
-   `DELETE /snippets/{type}/{pk}/` — delete a snippet (a duplicate action-style delete route is also available).

Create and update use generated schemas and the model's own edit handler and admin form, so the same validation, permissions, revisions, and signals apply as in the editor.

## Listing snippets

The `/snippets/{type}/` endpoint returns a paginated list of a snippet model's instances. It supports pagination with `?limit` / `?offset` (see [](api_v3)), plus exact filtering on the model's API fields and primary key, ordering, and full-text search. For translatable snippet models, `locale` and `translation_of` filters are also available.

```sh
# Adverts in French, most recently created first
curl -H "Authorization: Bearer $TOKEN" \
  "https://example.com/api/v3/snippets/mymodels.Advert/?locale=fr&order=-pk"
```

## Mixin capabilities

The capabilities a snippet exposes depend on the mixins its model uses:

| Mixin | Added capability |
| --- | --- |
| `RevisionMixin` | revision list/detail + revert action |
| `DraftStateMixin` | draft reads, `meta.action=publish`, publish/unpublish actions |
| `TranslatableMixin` | locale/translation filtering + copy-for-translation |
| `WorkflowMixin` | none in v3 |
| `LockableMixin` | none in v3 |

A `RevisionMixin` model gains `GET /snippets/{type}/{pk}/revisions/` and `.../revisions/{revision_id}/`, plus a `revert` action. A `DraftStateMixin` model gains draft reads, an optional `meta.action=publish` on create/update, and `publish` / `unpublish` actions. A `TranslatableMixin` model gains locale and translation filtering and a `copy_for_translation` action.

## Draft state and revisions

On a `DraftStateMixin` model, create and update produce a revision while keeping the live database representation unchanged until publication. `?version=draft` returns the latest revision for a draft-state model.

`meta.action` is optional on create/update. On a draft-state model it currently only accepts `publish` (which publishes the just-written revision); an invalid action value is rejected with `422`. On a model without `DraftStateMixin`, `meta.action` is silently ignored.

Several actions are available on the relevant mixins — `publish`, `unpublish`, `revert`, `copy_for_translation`, and `delete` — following the same action pattern as pages. There are no workflow submit/approve/reject/resume/cancel routes.

## Permissions and visibility

Snippet list and detail require the caller to possess any relevant permission for the model, but they start from the model's unfiltered default manager rather than a per-object permission-filtered queryset. Revision reads add an instance-level change check. If your project relies on object-level snippet visibility policies, do not assume the API queryset is automatically filtered to the instances a user can see — see the [permissions and visibility guide](api_v3_permissions) for how this compares with pages and media.

## Schema discovery

To learn a snippet model's exact fields and required input for a request, look it up by type through the schema discovery endpoints: `GET /schema/` lists registered content types and `GET /schema/mymodels.Advert/` returns its read, create, and patch JSON schemas. Both discovery endpoints require bearer authentication. See the [schema discovery guide](api_v3_schema) for how these are generated.

## Example: create, publish, and revert an advert

This example discovers, creates, publishes, and then reverts an advert snippet. It assumes a `BASE` pointing at the mounted API and a bearer `TOKEN`, and that `mymodels.Advert` is a registered snippet using `DraftStateMixin` and `RevisionMixin`.

Create an advert as a draft. Because an advert is also translatable, include a locale; omit `meta.action` to save a draft rather than publish:

```sh
curl -X POST "$BASE/snippets/mymodels.Advert/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {"locale": "en"},
    "text": "Summer sale — 20% off"
  }'
```

The response returns the new snippet's `id`. Publish it with the `publish` action:

```sh
curl -X POST "$BASE/snippets/mymodels.Advert/1/actions/publish/" \
  -H "Authorization: Bearer $TOKEN"
```

Later edits create further revisions. To undo them, revert to an earlier revision ID:

```sh
curl -X POST "$BASE/snippets/mymodels.Advert/1/actions/revert/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"revision_id": 27}'
```

The full, generated OpenAPI reference for every snippet endpoint — including the revision and action routes above — is rendered from Wagtail's own OpenAPI snapshot, see [](api_v3_reference).
