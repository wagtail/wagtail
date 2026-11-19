(api)=

# Wagtail API

Wagtail includes a built-in API module, currently with two coexisting versions for programmatic access to your content:

-   **v2**: a battle-tested read-only API, built on [Django REST Framework](https://www.django-rest-framework.org/). It exposes content as raw field data for serving content to non-web clients (such as a mobile phone app), or pulling content out of Wagtail for use in another site. It’s widely used for headless projects.
-   **v3**: [Wagtail 8.0's new API](api_v3), built on [Django Ninja](https://django-ninja.dev/). Beyond reading content, it supports a wide range of authenticated CMS operations such as creating and editing pages, media, documents, and snippets, plus revisions, rich text, and StreamField. It offers OpenAPI 3.1 schema output and RFC 7807 errors.

The v2 read API remains available, but is planned for deprecation in favor of v3. See the [deprecation timeline](api_v2_deprecation) and [](api_v3_migration). See the configuration guides below for more usage information.

Wagtail is built on Django, so you can also use other Django solutions for building APIs such as [with GraphQL](https://github.com/torchbox/wagtail-grapple) or [rolling your own API with Django Ninja](api_ninja).

```{toctree}
---
maxdepth: 2
---
v2/configuration
v2/usage
v3/index
django-ninja
```
