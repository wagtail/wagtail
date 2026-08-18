(api_v3_authentication)=

# v3 API authentication & tokens

The v3 API authenticates requests with bearer tokens. Tokens are tied to a user account, and API requests act as that user with their Wagtail permissions — the same permissions system as the admin UI. Edge cases are covered in the Permissions section below.

```{note}
v3 does not use Django session authentication. Browser session cookies are ignored by API requests; only a valid bearer token authenticates a caller.
```

## Authenticating requests

Send the token in the `Authorization` header of every request:

```bash
curl -H "Authorization: Bearer wagtail_…" https://example.com/api/v3/whoami/
```

`GET /api/v3/whoami/` returns the authenticated user, profile, and groups — useful to validate a token and configuration.

## Anonymous requests and failed tokens

Public read endpoints (for example pages, images, documents, and redirects) allow both anonymous and bearer access, declared as `auth=[BearerTokenAuth(), AllowAnonymous()]`. On these endpoints a missing, invalid, or revoked token does **not** reject the request: authentication falls through to `AllowAnonymous`, which marks the request anonymous and normalizes `request.user` so a Django session cookie cannot elevate it, and the request is served with anonymous visibility.

This has an important consequence: a successful public response does not prove that a credential was accepted. For example, `GET /pages/{id}/?version=draft` with an invalid token returns the live public page with HTTP 200, because `version=draft` only returns the latest revision when the caller is authenticated. Clients must not treat a successful public response as proof that their token was valid — confirm with `GET /whoami/` if that matters.

## Creating tokens

### In the admin

Users with the relevant permission can manage tokens under **Settings → API tokens** (shown when `wagtail.api.v3` is in `INSTALLED_APPS`). The token secret is displayed exactly once at creation — copy it somewhere safe. It cannot be retrieved later.

### On the command line

```bash
./manage.py api_tokens create --user=deploy --name="deploy bot"
```

The command prints the bare token, suitable for scripting:

```bash
TOKEN=$(./manage.py api_tokens create --user=deploy --name="ci")
```

Use `--json` for structured output. `api_tokens list` shows tokens (prefix, name, owner, timestamps — never the secret), and `api_tokens revoke` revokes by `--id` or by `--user` and `--prefix`.

## Token security model

- Only an HMAC-SHA-256 **digest** of each token is stored, bound to your `SECRET_KEY`. The plaintext exists only at creation time.
- Token strings carry a `wagtail_` prefix and a checksum, so clients and secret scanners can recognize them.
- **Rotating `SECRET_KEY`:** tokens created under a key listed in [`SECRET_KEY_FALLBACKS`](https://docs.djangoproject.com/en/stable/ref/settings/#secret-key-fallbacks) keep working until the fallback is removed — the same rotation window semantics as Django sessions. Rotating without fallbacks revokes all tokens at once, which is the recommended incident-response path for a suspected leak.

## Token lifecycle

Revoking a token (admin UI or `api_tokens revoke`) sets a revocation timestamp rather than deleting the row, so the audit trail is preserved. Token creation and revocation are recorded in the [audit log](audit_log).

Each successful request updates the token's `last_used_at`, throttled to at most one write per `WAGTAILAPI_TOKEN_LAST_USED_INTERVAL` seconds (default `60`). Set the setting to `None` to disable these writes entirely — for example on sites running with a read-only production database.

## Permissions

A token acts as its user, so it grants exactly the permissions the user has. We recommend dedicated service accounts with minimal group permissions for integrations.

```{note}
Most writes route through Wagtail's forms and actions, so they enforce the same per-object policies as the admin UI. One caveat: snippet list and detail endpoints gate on a model-wide "any permission" check and start from the model's unfiltered default manager, so object-level snippet visibility policies are not applied automatically. See [the permissions and visibility guide](api_v3_permissions) for how visibility differs by resource and access tier.
```

Token management itself is permission-gated:

- Users need the `wagtailcore` `add` / `change` / `delete` permissions for API tokens (assignable via **Settings → Groups**) to manage their own tokens.
- Managing **other users'** tokens additionally requires the user model's `change` permission.
- Tokens owned by superusers can only be managed by superusers.

## Custom authentication

Projects can subclass `wagtail.api.v3.auth.BearerTokenAuth` to customize token resolution, or stack additional [Django Ninja authentication classes](https://django-ninja.dev/guides/authentication/) per router or per endpoint. Public read endpoints use `auth=[BearerTokenAuth(), AllowAnonymous()]`. Authorization in v3 derives from `request.auth`, which Ninja sets to the authenticated `APIToken`.

## Throttling

No throttling is applied by default. v3 is built on Django Ninja, which provides DRF-style rate throttling via the `NINJA_DEFAULT_THROTTLE_RATES` setting and the `throttle=` argument on routers and operations — see the [Django Ninja throttling docs](https://django-ninja.dev/guides/throttling/).

Ninja's throttling state is stored in Django's cache: the default local-memory cache does not coordinate across processes. For production rate limiting, use a shared cache backend or — recommended for high-traffic sites — rate limiting at the reverse proxy (nginx, CDN, etc.).

## CORS

The API allows no cross-origin browser access by default. If browser-based clients need access, use [`django-cors-headers`](https://github.com/adamchainz/django-cors-headers) with an explicit allowlist:

```python
CORS_ALLOWED_ORIGINS = [
    "https://editor.example.com",
]
```

Never use `CORS_ALLOW_ALL_ORIGINS = True` with a write-capable API.
