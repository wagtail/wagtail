# Security considerations

Wagtail is built on Django, and supports all Django 's security features. However, being a CMS, there are some beneficial features that might not ordinarily come to mind when using Django as is, but should be given some thought. For more context, here's Django's [documentation on security.](inv:django#topics/security)

```{contents}
---
local:
depth: 1
---
```

## Content Security Policy (CSP)

Content Security Policy (CSP) is an important security mechanism that helps protect your site from cross-site scripting (XSS) attacks, clickjacking, and other code injection actions. CSP works by allowing you define allowed sources for content like scripts, styles, images, and other resources. To get a more thorough understanding of CSS, here's a [Mozilla article about CSP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP)

```{contents}
---
local:
depth: 2
---
```

### Enabling Django's built-in CSP feature

Django 6.0+ includes built-in CSP support through middleware and settings. To enable CSP in your Wagtail project:

1. Add the CSP middleware to your `MIDDLEWARE` setting:

```python
MIDDLEWARE = [
    # ...other middleware,
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    # ...
]
```

2. Configure your CSP directives in `settings.py`.

```python
from django.utils.csp import CSP

# To enforce a CSP policy:
SECURE_CSP = {
    "default-src": [CSP.SELF],
    # Add more directives to be enforced.
}

# Or for report-only mode:
SECURE_CSP_REPORT_ONLY = {
    "default-src": [CSP.SELF],
    # Add more directives as needed.
    "report-uri": "/path/to/reports-endpoint/",
}
```

For more advanced usage like Nonce usage or additional directives you can use, the [Django documentation](https://docs.djangoproject.com/en/dev/howto/csp/) covers this.

### Legacy Django-csp Support (Pre Django 6.0)

If you're using anything earlier than Django 6.0, you will need to use the [django-csp](https://django-csp.readthedocs.io/) package instead. The django-csp documentation will guide you on the exact settings and setup instructions.

### Wagtail features that need CSP considerations

Some Wagtail features require specific CSP directives to function properly. Below are the main considerations

```{contents}
---
local:
depth: 3
---
```

#### Gravatar images

If you're using Gravatar for user profile images in the Wagtail admin, you will need to allow images from Gravatar's CDN

```python
SECURE_CSP = {
  'img-src' = (CSP.SELF, "https://gravatar.com",)
}
```

However, for a stronger security policy, you should choose to allow only sources you have control over. To disable Gravatar support and avoid this requirement, set `WAGTAIL_GRAVATAR_PROVIDER_URL = None` in your settings.

#### Responsive image backgrounds (Image background styles)

When setting client-side image background styles, inline styles may be generated. This will trigger CSP violations. To support this, you have two options:

1. Use nonces (recommended).
2. Allow `unsafe-inline` in the `CSP_STYLE_SRC` directives (less secure).

#### Responsive embeds

Just as with Responsive image backgrounds, inline styles may also be generated when embedding content. To prevent CSP violations, you also have two options:

1. Use nonces (recommended).
2. Allow `unsafe-inline` in the `CSP_STYLE_SRC` directives (less secure).

#### Custom code or third-party packages

When developing custom functionality for your Wagtail site or integrating third-party packages, some CSP tips to keep in mind are:

1. Avoid inline scripts and styles. Opt to move JavaScript and CSS to external files.
2. Use nonces for dynamic content. If you must generate inline styles or scripts, use CSP nonces to allow them securely.
3. Test with CSP enabled. In the case of third-party packages, check that the packages work correctly with your CSP policy in place.

#### Images and docs

In the case of SVG images, users navigating directly to the URL of the SVG file may allow embedded scripts be executed, depending on the server/storage configuration. An appropriate Content Security Policy will help mitigate this. For more context, see the section on [security considerations in images](svg_security_considerations)

In the case of docs, you can configure the server to return a `Content-Security-Policy: default-src 'none'` header for files within the `documents` subdirectory, to prevent execution of scripts in those files. A recommended reading would be [security considerations in serving documents](documents_security_considerations)