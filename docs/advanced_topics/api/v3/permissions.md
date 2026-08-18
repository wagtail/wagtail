(api_v3_permissions)=

# Permissions and visibility

The v3 API grants access to different content depending on how a request is authenticated. This page explains how requests are authorized, what an anonymous request can see compared with a bearer-authenticated one, and the operational and security considerations to review before exposing the API.

```{warning}
Mounting the v3 API enables write, publish, and destructive operations on your content. Read this page and [](api_v3_authentication) before exposing it, and review what each resource makes visible to anonymous and authenticated callers.
```

## How requests are authorized

A request to the v3 API is checked in layers, so an endpoint is only reachable after each gate passes:

1. **Route permission gate** — `require_any_permission()` performs a coarse gate through the global permission-policy registry, so a caller must hold any relevant permission for the route.
2. **Queryset restriction** — list and detail endpoints restrict the objects a caller can read, through permission-policy querysets and, for authenticated requests, the pages a user can explore.
3. **Form and action checks** — writes route through Wagtail's admin forms and action classes, which enforce operation- and object-level permission checks the same way the editor does.
4. **Explicit object checks** — some domains add further object-level checks, notably page and snippet revision reads.

Because most writes flow through Wagtail's forms and actions, they inherit the same validation, permission, revision, audit-log, hook, and signal behaviour as the admin. Writes always require an authenticated bearer token.

## What an anonymous request can see

Anonymous requests are served without a token. Public endpoints allow anonymous access as well as bearer access; on a public endpoint, a missing or invalid token does not reject the request but falls through to anonymous visibility instead (see [](api_v3_authentication)).

```{note}
Because a failed token falls through to anonymous access, a successful public response is not proof that a credential was accepted. For example, `GET /pages/{id}/?version=draft` with an invalid token returns the live public page with HTTP 200 rather than an error, because `version=draft` only returns a draft for an authenticated request. Confirm with `GET /whoami/` when it matters.
```

The visibility matrix below summarises which resources allow anonymous reads and how authenticated reads differ.

## Visibility by access tier

| Resource | Anonymous read | Authenticated read | Writes |
| --- | --- | --- | --- |
| **Pages** | Live, public, site-scoped pages (plus view restrictions) | Pages the user can explore in the admin, including draft-only pages | Bearer |
| **Images** | All, excluding images in a directly restricted collection whose restriction is not satisfied | Same, with the request able to satisfy restrictions via user/groups and password-restriction session state | Bearer |
| **Documents** | All, excluding documents whose own collection is restricted | Same (restriction-aware) | Bearer |
| **Redirects** | Public | Public | Bearer |
| **Sites** | — | Bearer + site permission | Bearer |
| **Locales** | — | Bearer + locale permission | Bearer |
| **Snippets** | — | Bearer + model permission | Bearer |
| **Schema** | — | Bearer | — |
| **Whoami** | — | Bearer | — |

Two behaviours are worth calling out:

- **Pages.** An anonymous request sees the shared public, live, site-scoped queryset, subject to page view restrictions. An authenticated request instead uses the pages the user can explore in the admin, which includes draft-only pages and is not scoped to a site in the same way. `?version=draft` returns the latest revision only for authenticated users.
- **Snippets and collection restrictions.** Snippet list and detail require any relevant model permission but start from the model's unfiltered default manager, so object-level snippet visibility policies are not applied automatically to the queryset — if your project relies on them, do not assume the API filters to the instances a user can see. Images and documents exclude an object when a view restriction attached to its collection is not satisfied by the request; restrictions inherited from an ancestor collection do not hide a document in a descendant collection.

## The token user model

A token acts as its user, so API requests made with it grant exactly the permissions that user has. Recommend dedicated service accounts with minimal group permissions for integrations, rather than sharing a full-privilege account.

Token management itself is permission-gated, and token lifecycle, security, and administration are covered in [](api_v3_authentication):

- Token creators need the `wagtailcore` add / change / delete permissions for API tokens.
- Managing other users' tokens additionally requires the user model's change permission.
- Tokens owned by superusers can only be managed by superusers.

## Security and operations

Review these before going to production with the v3 API:

- **Attack surface.** Mounting v3 expands the exposed surface with write, publish, and delete operations. Only mount it where it is needed, and keep tokens restricted to dedicated service accounts.
- **Public read visibility varies by resource.** What an anonymous caller can see (and what a bearer-authenticated caller sees) differs per resource, as shown above. Review this per resource during deployment.
- **Snippet object-level visibility.** Custom snippet permission policies that rely on object-level visibility are not reflected automatically in list/detail querysets; review this if you use such policies.
- **Throttling.** No throttling is applied by default. Use Django Ninja's throttling or rate limit at the reverse proxy for high-traffic deployments — see [](api_v3_authentication).
- **CORS.** Cross-origin browser access is denied by default. If browser clients need access, use [`django-cors-headers`](https://github.com/adamchainz/django-cors-headers) with an explicit allowlist, and never enable `CORS_ALLOW_ALL_ORIGINS = True` on a write-capable API — see [](api_v3_authentication).
- **Request and body limits.** Align reverse-proxy request and body size limits with the image and document upload limits the API enforces.
- **`SECRET_KEY` rotation.** Token digests are bound to `SECRET_KEY`; rotating it without `SECRET_KEY_FALLBACKS` revokes all tokens. See [](api_v3_authentication) for the rotation window.
- **Rich text sanitization is silent.** Rich text input is sanitised against the field's declared features, and unsupported content is stripped without being reported back, so a stored or returned value can contain less than what was submitted. This matters for automation and AI-generated content.
- **Content quality checks are not run.** The API routes content through Wagtail's actions but bypasses the editor's built-in content checker, so accessibility and content-quality checks are not run by these endpoints on the content they write.

## Operations not available in v3

The following admin operations are not currently exposed over the v3 API:

- workflow and moderation operations (submitting, approving, rejecting, resuming, or cancelling a workflow);
- locking and unlocking objects;
- comments and comment replies;
- managing page view restrictions.
