# Deployment: Under the hood

This doc provides a technical deep-dive into Wagtail hosting concepts. Most likely, you'll want to [choose a hosting provider](index.md) instead.

Wagtail is built on Django, and so the vast majority of the deployment steps and considerations for deploying Django are also true for Wagtail. We recommend reading Django's ["How to deploy Django"](inv:django#howto/deployment/index) documentation.

## Infrastructure Requirements

When designing infrastructure for hosting a Wagtail site, there are a few basic requirements:

### WSGI / ASGI server

> Django, being a web framework, needs a web server in order to operate. Since most web servers don’t natively speak Python, we need an interface to make that communication happen.

Wagtail can be deployed using either [WSGI](inv:django#howto/deployment/wsgi/index) or [ASGI](inv:django#howto/deployment/asgi/index), however Wagtail doesn't natively implement any async views or middleware, so we recommend WSGI.

### Static files

As with all Django projects, static files are only served by the Django application server during development, when running through the `manage.py runserver` command. In production, these need to be handled separately at the web server level.
See [Django's documentation on deploying static files](inv:django#howto/static-files/deployment).

The JavaScript and CSS files used by the Wagtail admin frequently change between releases of Wagtail - it's important to avoid serving outdated versions of these files due to browser or server-side caching, as this can cause hard-to-diagnose issues.
We recommend enabling [ManifestStaticFilesStorage](django.contrib.staticfiles.storage.ManifestStaticFilesStorage) in the `STORAGES["staticfiles"]` setting - this ensures that different versions of files are assigned distinct URLs.

(user_uploaded_files)=

### User Uploaded Files

Wagtail follows [Django's conventions for managing uploaded files](inv:django#topics/files).
So by default, Wagtail uses Django's built-in `FileSystemStorage` class which stores files on your site's server, in the directory specified by the `MEDIA_ROOT` setting.
Alternatively, Wagtail can be configured to store uploaded images and documents on a cloud storage service such as Amazon S3;
this is done through the [`STORAGES["default"]`](inv:django#STORAGES)
setting in conjunction with an add-on package such as [django-storages](https://django-storages.readthedocs.io/).

#### Security

Any system that allows user-uploaded files is a potential security risk. For example, a user with the ability to upload HTML files could potentially launch a [cross-site scripting attack](https://owasp.org/www-community/attacks/xss/) against a user viewing that file. This may not be a concern if all users with access to the Wagtail admin are fully trusted - for example, a personal site where you are the only editor. With this in mind, Wagtail aims to provide a secure configuration by default, but developers may choose a more permissive setup if they understand the risks, as detailed below.

#### Images

When using `FileSystemStorage`, image urls are constructed starting from the path specified by the `MEDIA_URL`.
In most cases, you should configure your web server to serve image files directly from the `images` subdirectory of `MEDIA_ROOT` (without passing through Django/Wagtail).
If [](svg_images) are enabled, it is possible for a user to upload an SVG file containing scripts that execute when the file is viewed directly; if this is a concern, several approaches for avoiding this are detailed under [](svg_security_considerations).

When using one of the cloud storage backends, images urls go directly to the cloud storage file url.
If you would like to serve your images from a separate asset server or CDN, you can [configure the image serve view](image_serve_view_redirect_action) to redirect instead.

#### Documents

Document serving is controlled by the [WAGTAILDOCS_SERVE_METHOD](wagtaildocs_serve_method) method.
When using `FileSystemStorage`, documents are stored in a `documents` subdirectory within your site's `MEDIA_ROOT`. In this case, `WAGTAILDOCS_SERVE_METHOD` defaults to `serve_view`, where Wagtail serves the document through a Django view that enforces privacy checks. This has the following implications:

-   **You should block direct access to the `documents` subdirectory of `MEDIA_ROOT` within your web server configuration.** This prevents users from bypassing [collection privacy settings](https://guide.wagtail.org/en-latest/how-to-guides/manage-collections/#privacy-settings) by accessing documents at their direct URL.
-   Documents are served as downloads rather than displayed in the browser (unless specified explicitly via [](wagtaildocs_inline_content_types)) - this ensures that if the document is a type that can contain scripts (such as HTML or SVG), the browser is prevented from executing them.
-   However, since the document is served through the Django application server, this may consume more server resources than serving the document directly from the web server.

The alternative serve methods `'direct'` and `'redirect'` work by serving the documents directly from `MEDIA_ROOT`. This means it is not possible to block direct access to the `documents` subdirectory, and so users may bypass permission checks by accessing the direct URL. Also, in the case that users with access to the Wagtail admin are not fully trusted, you will need to take additional steps to prevent the execution of scripts in documents:

-   The `WAGTAILDOCS_EXTENSIONS` setting may be used to restrict uploaded documents to an "allow list" of safe types.
-   The web server can be configured to return a `Content-Security-Policy: default-src 'none'` header for files within the `documents` subdirectory, which will prevent the execution of scripts in those files.
-   The web server can be configured to return a `Content-Disposition: attachment` header for files within the `documents` subdirectory, which will force the browser to download the file rather than displaying it inline.

If a remote ("cloud") storage backend is used, the serve method will default to `'redirect'` and the document will be served directly from the cloud storage file url. In this case, users may be able to bypass permission checks, and scripts within documents may be executed (depending on the cloud storage service's configuration). However, the impact of cross-site scripting attacks is reduced, as the document is served from a different domain to the main site.

If these limitations are not acceptable, you may set the `WAGTAILDOCS_SERVE_METHOD` to `serve_view` and ensure that the documents are not publicly accessible using the cloud service's file url.

The steps required to set headers for specific responses will vary, depending on how your Wagtail application is deployed and which storage backend is used. For the `'serve_view` method, a `Content-Security-Policy` header is automatically set for you (unless disabled via [](wagtaildocs_block_embedded_content)) to prevent the execution of scripts embedded in documents.

#### Cloud storage

Be aware that setting up remote storage will not entirely offload file handling tasks from the application server - some Wagtail functionality requires files to be read back by the application server.
In particular, original image files need to be read back whenever a new resized rendition is created, and documents may be configured to be served through a Django view in order to enforce permission checks (see [WAGTAILDOCS_SERVE_METHOD](wagtaildocs_serve_method)).

```{note}
The django-storages Amazon S3 backends (`storages.backends.s3boto.S3BotoStorage` and `storages.backends.s3boto3.S3Boto3Storage`) **do not correctly handle duplicate filenames** in their default configuration. When using these backends, `AWS_S3_FILE_OVERWRITE` must be set to `False`.
```

### Cache

Wagtail is designed to take advantage of Django's [cache framework](inv:django#topics/cache) when available to accelerate page loads. The cache is especially useful for the Wagtail admin, which can't take advantage of conventional CDN caching.

Wagtail supports any of Django's cache backend, however we recommend against using one tied to the specific process or environment Django is running (eg `FileBasedCache` or `LocMemCache`).

## Deployment tips

Wagtail, and by extension Django, can be deployed in many different ways on many different platforms. There is no "best" way to deploy it, however here are some tips to ensure your site is as stable and maintainable as possible:

### Use Django's deployment checklist

Django has a [deployment checklist](inv:django#howto/deployment/checklist) which runs through everything you should have done or should be aware of before deploying a Django application.

### Performance optimization

Your production site should be as fast and performant as possible. For tips on how to ensure Wagtail performs as well as possible, take a look at our [performance tips](performance_overview).

(deployment_examples)=

## Deployment examples

Some examples of deployments on a few hosting platforms can be found in [](/advanced_topics/third_party_tutorials). This is not a complete list of platforms where Wagtail can run, nor is it necessarily the only way to run Wagtail there.

An example of a production Wagtail site is [guide.wagail.org](https://guide.wagtail.org/), which is [open-source](https://github.com/wagtail/guide) and runs on Heroku. More information on its hosting environment can be found in [its documentation](https://github.com/wagtail/guide/blob/main/docs/hosting-environment.md).

If you have successfully installed Wagtail on your platform or infrastructure, please [contribute](../contributing/index) your notes to this documentation!
