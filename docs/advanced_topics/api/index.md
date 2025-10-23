(api)=

# Wagtail API

Wagtail includes a built-in API module that provides a public-facing, JSON-formatted API to allow retrieving
content as raw field data. This is useful for cases like serving content to
non-web clients (such as a mobile phone app) or pulling content out of Wagtail
for use in another site.

See [RFC 8: Wagtail API](https://github.com/wagtail/rfcs/blob/main/text/008-wagtail-api.md#12---stable-and-unstable-versions)
for full details on our stabilization policy.

Wagtail is built on Django, so you can also use other Django solutions for building APIs such as [with Django Ninja](api_ninja) or [with GraphQL](https://github.com/torchbox/wagtail-grapple).

```{toctree}
---
maxdepth: 2
---
v2/configuration
v2/usage
django-ninja
```
