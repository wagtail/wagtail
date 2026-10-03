(api_v3_snippets)=

# Snippets

Snippets are small pieces of content to reuse between pages. The v3 API exposes registered snippet models data for reading, writing. And where the model is configured: revisions, drafts, and translations.

```{note}
Every snippet endpoint requires an authenticated request with the relevant model permission. See [](api_v3_authentication) for how permissions work in the API.
```

## Registering snippets

A snippet model is exposed through the v3 API only if it declares at least one `APIField`. Its routes use the exact Django model label as the path segment, for example `mymodels.Advert`. Primary keys are accepted as string path input, supporting integer, UUID, and other string primary keys.

The per-type operations are:

-   `GET /snippets/{type}/`: list snippets of the model.
-   `GET /snippets/{type}/{pk}/`: return one snippet.
-   `POST /snippets/{type}/`: create a snippet.
-   `PATCH /snippets/{type}/{pk}/`: update a snippet.
-   `DELETE /snippets/{type}/{pk}/`: delete a snippet.

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
| `LockableMixin` | lock respected but no locking/unlocking via the API |
| `WorkflowMixin` | not supported |

A `RevisionMixin` model gains `GET /snippets/{type}/{pk}/revisions/` and `.../revisions/{revision_id}/`, plus a `revert` action. A `DraftStateMixin` model gains draft reads, an optional `meta.action=publish` on create/update, and `publish` / `unpublish` actions. A `TranslatableMixin` model gains locale and translation filtering and a `copy_for_translation` action.

## Draft state and revisions

On a `DraftStateMixin` model, create and update produce a revision while keeping the live database representation unchanged until publication. `?version=draft` returns the latest revision for a draft-state model.

`meta.action` is optional on create/update. On a draft-state model it currently only accepts `publish` (which publishes the just-written revision); an invalid action value is rejected with `422`. On a model without `DraftStateMixin`, `meta.action` is silently ignored.

Several actions are available on the relevant mixins: `publish`, `unpublish`, `revert`, `copy_for_translation`, and `delete`. This follows the same action pattern as pages.

## Schema discovery

To learn a snippet model's exact fields and required input for a request, look it up by type through the schema discovery endpoints: `GET /schema/` lists registered content types and `GET /schema/mymodels.Advert/` returns its read, create, and patch JSON schemas. Both discovery endpoints require bearer authentication. See the [schema discovery guide](api_v3_schema) for how these are generated.


The full, generated OpenAPI reference for every snippet endpoint — including the revision and action routes above — is rendered from Wagtail's own OpenAPI snapshot, see [](api_v3_reference).

## ## Snippets API reference

We document the full generated OpenAPI reference for snippet endpoints from Wagtail's own OpenAPI snapshot, see [](api_v3_reference).
