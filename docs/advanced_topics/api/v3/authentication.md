(api_v3_authentication)=

# v3 API authentication & tokens

The v3 API authenticates requests with bearer tokens. Tokens are tied to a user account, and API requests act as that user with exactly their Wagtail permissions — the same permissions system as the admin UI.

```{note}
v3 does not use Django session authentication. Browser session cookies are ignored by API requests; only a valid bearer token authenticates a caller.
```

## Authenticating requests

Send the token in the `Authorization` header of every request:

```bash
curl -H "Authorization: Bearer wagtail_…" https://example.com/api/v3/whoami/
```

`GET /api/v3/whoami/` returns the authenticated user, profile, groups, and permission summary — useful to validate a token and configuration.

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

A token grants exactly the permissions of its user. We recommend dedicated service accounts with minimal group permissions for integrations.

Token management itself is permission-gated:

- Users need the `wagtailcore` `add` / `change` / `delete` permissions for API tokens (assignable via **Settings → Groups**) to manage their own tokens.
- Managing **other users'** tokens additionally requires the user model's `change` permission.
- Tokens owned by superusers can only be managed by superusers.

## Custom authentication

Projects can subclass `wagtail.api.v3.auth.BearerTokenAuth` (or stack additional [Django Ninja authentication classes](https://django-ninja.dev/guides/authentication/)) and apply them per router or per endpoint. Authorization in v3 derives from `request.auth` only — see `wagtail.api.v3.auth.get_api_user`.

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
