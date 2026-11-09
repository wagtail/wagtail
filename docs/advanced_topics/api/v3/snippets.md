(api_v3_snippets)=

# Snippets

Snippets are small pieces of content to reuse between pages. The v3 API exposes registered snippet models data for reading, writing, and where the model is configured: revisions, drafts, and translations.

```{note}
Every snippet endpoint requires an authenticated request with the relevant model permission. See [](api_v3_authentication) for how permissions work in the API.
```

## Registering snippets

A snippet model is exposed through the v3 API only if it declares at least one `APIField`. The schema for a snippet model is generated similarly to pages and can be inspected via [schema discovery](api_v3_schema). The main difference is that snippets use the same schema for both the listing and detail endpoints.

The routes for a snippet model use the exact Django model label as the path segment, for example `mymodels.Advert`. Primary keys are accepted as string path input, supporting integer, UUID, and other string primary keys.

Each registered snippet model has the following operations:

-   `GET /snippets/{type}/`: list snippets of the model.
-   `GET /snippets/{type}/{pk}/`: return one snippet.
-   `POST /snippets/{type}/`: create a snippet.
-   `PATCH /snippets/{type}/{pk}/`: update a snippet.
-   `DELETE /snippets/{type}/{pk}/`: delete a snippet.

## Listing and viewing snippets

The `/snippets/{type}/` endpoint returns a paginated list of a snippet model's instances. It supports pagination with `?limit` / `?offset` (see [](api_v3_pagination)), plus exact filtering on the model's API fields and primary key, ordering, and full-text search. For translatable snippet models, `locale` and `translation_of` filters are also available.

```sh
# Adverts in French, most recently created first
curl -H "Authorization: Bearer $TOKEN" \
  "https://example.com/api/v3/snippets/mymodels.Advert/?locale=fr&order=-pk"
```

To retrieve a single snippet, you can use the `/snippets/{type}/{pk}/` endpoint.

```sh
# Retrieve an Advert snippet with ID 123
curl -H "Authorization: Bearer $TOKEN" \
  "https://example.com/api/v3/snippets/mymodels.Advert/123/"
```

## Write operations

The create, update, and delete endpoints work similarly to [how they work for pages](api_v3_pages_create). Each submitted field is validated against the snippet type's generated schema and its admin form. This means the same validation, permission, revision, and audit behavior as the admin interface applies.

### Draft state and revisions

If a snippet model has [`DraftStateMixin`](wagtailsnippets_saving_draft_changes_of_snippets) enabled, the create and update operations produce a revision while keeping the live database representation unchanged until publication.

Similar to pages, the `meta.action` field for these operations can be set to `publish` to immediately publish the new revision. Using `?version=draft` on the detail endpoint returns the latest revision for a draft-state model.

## Mixin capabilities

In addition to the default operations above, the capabilities a snippet exposes depend on the mixins its model uses:

| Mixin | Added capability |
| --- | --- |
| `RevisionMixin` | revision list/detail + revert action |
| `DraftStateMixin` | draft reads, `meta.action=publish`, publish/unpublish actions |
| `TranslatableMixin` | locale/translation filtering + copy-for-translation |
| `LockableMixin` | lock respected but no locking/unlocking via the API |
| `WorkflowMixin` | workflow actions, status and history reads, see [](api_v3_workflows) |

Enabling each mixin will automatically register the endpoints for their relevant actions, such as: `publish`, `unpublish`, `revert`, `copy_for_translation`, `delete`, and the workflow transitions. This follows the [same action pattern as pages](api_v3_pages_actions).

## Snippets API reference

We document the full generated OpenAPI reference for snippet endpoints from Wagtail's own OpenAPI snapshot, see [](api_v3_reference).
