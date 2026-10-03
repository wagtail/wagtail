(api_v3_authentication)=

# v3 API authentication

The v3 API authenticates requests with bearer tokens. Tokens are tied to a user account, and API requests act as that user with their Wagtail permissions. This is the same permissions system as for actions taken in the admin interface, with edge cases noted below.

## Authenticating requests

Send the token in the `Authorization` header of every request:

```bash
curl -H "Authorization: Bearer wagtail_…" https://example.com/api/v3/whoami/
```

`GET /api/v3/whoami/` returns the authenticated user, profile, and groups, so you can validate a token and its level of access.

## Anonymous requests and failed authentication.

Public read endpoints (for example pages, images, documents, and redirects) allow both anonymous and authenticated access. On these endpoints, a missing, invalid or revoked token will be treated as an anonymous request.

## Creating tokens

### In the admin

Users with the relevant permission can manage tokens under **Settings → API tokens** (shown when `wagtail.api.v3` is in `INSTALLED_APPS`). The token secret is displayed exactly once at creation, copy it somewhere safe.

### On the command line

```bash
./manage.py api_tokens create --user=deploy --name="deploy bot"
```

The command prints the bare token, suitable for scripting:

```bash
TOKEN=$(./manage.py api_tokens create --user=deploy --name="ci")
```

Use `--json` for structured output. `./manage.py api_tokens list` shows tokens (prefix, name, owner, timestamps), and `api_tokens revoke` revokes by `--id` or by `--user` and `--prefix`.

## Token security model

- Only an HMAC-SHA-256 **digest** of each token is stored, bound to your `SECRET_KEY`. The plaintext exists only at creation time.
- Token strings carry a `wagtail_` prefix and a checksum, so clients and secret scanners can recognize them.
- **Rotating `SECRET_KEY`:** tokens created under a key listed in [`SECRET_KEY_FALLBACKS`](https://docs.djangoproject.com/en/stable/ref/settings/#secret-key-fallbacks) keep working until the fallback is removed. This is the same rotation mechanism as session authentication. Rotating `SECRET_KEY` without fallbacks revokes all tokens at once.

## Token lifecycle

Revoking a token (admin UI or CLI) sets a revocation timestamp rather than deleting the row, to preserve an audit trail. Token creation and revocation are recorded in the [audit log](audit_log).

Tokens also track their usage via a `last_used_at` timestamp, throttled to at most one write per `WAGTAILAPI_TOKEN_LAST_USED_INTERVAL` interval in seconds (default `60`). Set the setting to `None` to disable these writes entirely, for example to run a site with a read-only database.

## Permissions

Tokens allow the same level of access as the user account they are attached to. Consider carefully whether to use real user accounts or introduce dedicated service accounts for API access. The latter can be created with a minimal set of permissions, and revoked without affecting a real user.

Token management itself is permission-gated:

- Users need the `wagtailcore` `add` / `change` / `delete` permissions for API tokens (assignable via **Settings → Groups**) to manage tokens associated with their account.
- Managing **other users'** tokens additionally requires the user model's `change` permission, which grants access to sensitive account management features (password resets, group membership).
- Tokens owned by superusers can only be managed by superusers.
