# Deploying Wagtail

## On your server

Wagtail is straightforward to deploy on modern Linux-based distributions, and should run with any of the combinations detailed in Django's [deployment documentation](django:howto/deployment/index).
See the section on [performance](performance) for the non-Python services we recommend.

## On Divio Cloud

[Divio Cloud](https://divio.com/) is a Dockerised cloud hosting platform for Python/Django that allows you to launch and deploy Wagtail projects in minutes.
With a free account, you can create a Wagtail project. Choose from a:

-   [site based on the Wagtail Bakery project](https://divio.com/wagtail), or
-   [brand new Wagtail project](https://control.divio.com/control/project/create) (see the [how to get started notes](https://docs.divio.com/en/latest/introduction/wagtail/)).

Divio Cloud also hosts a [live Wagtail Bakery demo](https://divio.com/wagtail) (no account required).

## On PythonAnywhere

[PythonAnywhere](https://www.pythonanywhere.com/) is a Platform-as-a-Service (PaaS) focused on Python hosting and development.
It allows developers to quickly develop, host, and scale applications in a cloud environment.
Starting with a free plan they also provide MySQL and PostgreSQL databases as well as very flexible and affordable paid plans, so there's all you need to host a Wagtail site.
To get quickly up and running you may use the [wagtail-pythonanywhere-quickstart](https://github.com/texperience/wagtail-pythonanywhere-quickstart).

## On Google Cloud

[Google Cloud](https://cloud.google.com) is an Infrastructure-as-a-Service (IaaS) that offers multiple managed products, supported by Python client libraries, to help you build, deploy, and monitor your applications.
You can deploy Wagtail, or any Django application, in a number of ways, including on [App Engine](https://www.youtube.com/watch?v=uD9PTag2-PQ) or [Cloud Run](https://codelabs.developers.google.com/codelabs/cloud-run-wagtail/#0).

## On alwaysdata

[alwaysdata](https://www.alwaysdata.com/) is a Platform-as-a-Service (PaaS) providing Public and Private Cloud offers.
Starting with a free plan they provide MySQL/PostgreSQL databases, emails, free SSL certificates, included backups, etc.

To get your Wagtail application running you may:

-   [Install Wagtail from alwaysdata Marketplace](https://www.alwaysdata.com/en/marketplace/wagtail/)
-   [Configure a Django application](https://help.alwaysdata.com/en/languages/python/django/)

## On other PAASs and IAASs

We know of Wagtail sites running on [Heroku](https://spapas.github.io/2014/02/13/wagtail-tutorial/), Digital Ocean and elsewhere.
If you have successfully installed Wagtail on your platform or infrastructure, please [contribute](../contributing/index) your notes to this documentation!

(deployment_tips)=

## Deployment tips

### Static files

As with all Django projects, static files are not served by the Django application server in production
(i.e. outside of the `manage.py runserver` command); these need to be handled separately at the web server level.
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
However, if you use Wagtail's [Collection Privacy settings](collection_privacy_settings) to restrict access to some or all of your documents, you may or may not want to configure your web server to serve the documents directly.
The default setting is `redirect` which allows Wagtail to perform any configured privacy checks before offloading serving the actual document to your web server or CDN.
This means that Wagtail constructs document links that pass through Wagtail, but the final url in the user's browser is served directly by your web server.
If a user bookmarks this url, they will be able to access the file without passing through Wagtail's privacy checks.
If this is not acceptable, you may want to set the `WAGTAILDOCS_SERVE_METHOD` to `serve_view` and configure your web server so it will not serve document files itself.
If you are serving documents from the cloud and need to enforce privacy settings, you should make sure the documents are not publicly accessible using the cloud service's file url.

### Cloud storage

Be aware that setting up remote storage will not entirely offload file handling tasks from the application server - some Wagtail functionality requires files to be read back by the application server.
In particular, original image files need to be read back whenever a new resized rendition is created, and documents may be configured to be served through a Django view in order to enforce permission checks (see [WAGTAILDOCS_SERVE_METHOD](wagtaildocs_serve_method)).

Note that the django-storages Amazon S3 backends (`storages.backends.s3boto.S3BotoStorage` and `storages.backends.s3boto3.S3Boto3Storage`) **do not correctly handle duplicate filenames** in their default configuration. When using these backends, `AWS_S3_FILE_OVERWRITE` must be set to `False`.

If you are also serving Wagtail's static files from remote storage (using Django's [STATICFILES_STORAGE](https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-STATICFILES_STORAGE) setting), you'll need to ensure that it is configured to serve [CORS HTTP headers](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS), as current browsers will reject remotely-hosted font files that lack a valid header. For Amazon S3, refer to the documentation [Setting Bucket and Object Access Permissions](https://docs.aws.amazon.com/AmazonS3/latest/user-guide/set-permissions.html), or (for the `storages.backends.s3boto.S3Boto3Storage` backend only) add the following to your Django settings:

```python
AWS_S3_OBJECT_PARAMETERS = {
    "ACL": "public-read"
}
```

The `ACL` parameter accepts a list of predefined configurations for Amazon S3. For more information, refer to the documentation [Canned ACL](https://docs.aws.amazon.com/AmazonS3/latest/dev/acl-overview.html#canned-acl).

For Google Cloud Storage, create a `cors.json` configuration:

```json
[
    {
        "origin": ["*"],
        "responseHeader": ["Content-Type"],
        "method": ["GET"],
        "maxAgeSeconds": 3600
    }
]
```

Then, apply this CORS configuration to the storage bucket:

```sh
gsutil cors set cors.json gs://$GS_BUCKET_NAME
```

For other storage services, refer to your provider's documentation, or the documentation for the Django storage backend library you're using.
