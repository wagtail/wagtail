(deployment_guide)=

# Deploying Wagtail

Once you've built your Wagtail site, it's time to release it upon the rest of the internet.

Wagtail is built on Django, and so the vast majority of the deployment steps and considerations for deploying Django are also true for Wagtail. We recommend reading Django's ["How to deploy Django"](django:howto/deployment/index) documentation.

## Infrastructure Requirements

When designing infrastructure for hosting a Wagtail site, there are a few basic requirements:

### WSGI / ASGI server

> Django, being a web framework, needs a web server in order to operate. Since most web servers don’t natively speak Python, we need an interface to make that communication happen.

Wagtail can be deployed using either [WSGI](django:howto/deployment/wsgi/index) or [ASGI](django:howto/deployment/asgi/index), however Wagtail doesn't natively implement any async views or middleware, so we recommend WSGI.

### Static files

As with all Django projects, static files are only served by the Django application server during development, when running through the `manage.py runserver` command. In production, these need to be handled separately at the web server level.
See [Django's documentation on deploying static files](django:howto/static-files/deployment).

The JavaScript and CSS files used by the Wagtail admin frequently change between releases of Wagtail - it's important to avoid serving outdated versions of these files due to browser or server-side caching, as this can cause hard-to-diagnose issues.
We recommend enabling [ManifestStaticFilesStorage](django.contrib.staticfiles.storage.ManifestStaticFilesStorage) in the `STATICFILES_STORAGE` setting - this ensures that different versions of files are assigned distinct URLs.

### User Uploaded Files

Wagtail follows [Django's conventions for managing uploaded files](django:topics/files).
So by default, Wagtail uses Django's built-in `FileSystemStorage` class which stores files on your site's server, in the directory specified by the `MEDIA_ROOT` setting.
Alternatively, Wagtail can be configured to store uploaded images and documents on a cloud storage service such as Amazon S3;
this is done through the [DEFAULT_FILE_STORAGE](https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-DEFAULT_FILE_STORAGE)
setting in conjunction with an add-on package such as [django-storages](https://django-storages.readthedocs.io/).

When using `FileSystemStorage`, image urls are constructed starting from the path specified by the `MEDIA_URL`.
In most cases, you should configure your web server to serve image files directly (without passing through Django/Wagtail).
When using one of the cloud storage backends, images urls go directly to the cloud storage file url.
If you would like to serve your images from a separate asset server or CDN, you can [configure the image serve view](image_serve_view_redirect_action) to redirect instead.

Document serving is controlled by the [WAGTAILDOCS_SERVE_METHOD](wagtaildocs_serve_method) method.
When using `FileSystemStorage`, documents are stored in a `documents` subdirectory within your site's `MEDIA_ROOT`.
If all your documents are public, you can set the `WAGTAILDOCS_SERVE_METHOD` to `direct` and configure your web server to serve the files itself.
However, if you use Wagtail's [Collection Privacy settings](https://guide.wagtail.org/en-latest/how-to-guides/manage-collections/#privacy-settings) to restrict access to some or all of your documents, you may or may not want to configure your web server to serve the documents directly.
The default setting is `redirect` which allows Wagtail to perform any configured privacy checks before offloading serving the actual document to your web server or CDN.
This means that Wagtail constructs document links that pass through Wagtail, but the final url in the user's browser is served directly by your web server.
If a user bookmarks this url, they will be able to access the file without passing through Wagtail's privacy checks.
If this is not acceptable, you may want to set the `WAGTAILDOCS_SERVE_METHOD` to `serve_view` and configure your web server so it will not serve document files itself.
If you are serving documents from the cloud and need to enforce privacy settings, you should make sure the documents are not publicly accessible using the cloud service's file url.

#### Cloud storage

Be aware that setting up remote storage will not entirely offload file handling tasks from the application server - some Wagtail functionality requires files to be read back by the application server.
In particular, original image files need to be read back whenever a new resized rendition is created, and documents may be configured to be served through a Django view in order to enforce permission checks (see [WAGTAILDOCS_SERVE_METHOD](wagtaildocs_serve_method)).

```{note}
The django-storages Amazon S3 backends (`storages.backends.s3boto.S3BotoStorage` and `storages.backends.s3boto3.S3Boto3Storage`) **do not correctly handle duplicate filenames** in their default configuration. When using these backends, `AWS_S3_FILE_OVERWRITE` must be set to `False`.
```

### Cache

Wagtail is designed to make huge advantage of Django's [cache framework](django:topics/cache/index) when available to accelerate page loads. The cache is especially useful for the Wagtail admin, which can't take advantage of conventional CDN caching.

Wagtail supports any of Django's cache backend, however we recommend against using one tied to the specific process or environment Django is running (eg `FileBasedCache` or `LocMemCache`).

## Deployment tips

Wagtail, and by extension Django, can be deployed in many different ways on many different platforms. There is no "best" way to deploy it, however here are some tips to ensure your site is as stable and maintainable as possible:

### Use Django's deployment checklist

Django has a [deployment checklist](django:howto/deployment/checklist) which runs through everything you should have done or should be aware of before deploying a Django application.

### Performance optimisation

Your production site should be as fast and performant as possible. For tips on how to ensure Wagtail performs as well as possible, take a look at our [performance tips](performance_overview).

(deployment_examples)=

## Deployment examples

Some examples for deployments on a few hosting platforms can be found in [](./third_party_tutorials). This is not a complete list of platforms where Wagtail can run, nor is it necessarily the only way to run Wagtail there.

An example of a production Wagtail site is [guide.wagail.org](https://guide.wagtail.org/), which is [open-source](https://github.com/wagtail/guide) and run on Heroku. More information on its hosting environment can be found in [its documentation](https://github.com/wagtail/guide/blob/main/docs/hosting-environment.md).

If you have successfully installed Wagtail on your platform or infrastructure, please [contribute](../contributing/index) your notes to this documentation!
