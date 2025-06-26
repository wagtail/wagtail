(storing_and_serving)=

# Storing and serving

Wagtail follows [Django’s conventions for managing uploaded files](inv:django#topics/files). For configuration of `FileSystemStorage` and more information on handling user uploaded files, see [](user_uploaded_files).

## File storage location

Wagtail uses the [`STORAGES["default"]`](inv:django#STORAGES) setting to determine where and how user-uploaded files are stored. By default, Wagtail stores files in the local filesystem.

## Serving documents

Document serving is controlled by the [WAGTAILDOCS_SERVE_METHOD](wagtaildocs_serve_method) method. It provides a number of serving methods which trade some of the strictness of the permission check that occurs when normally handling a document request for performance.

The serving methods provided are `direct`, `redirect` and `serve_view`, with `redirect` method being the default when `WAGTAILDOCS_SERVE_METHOD` is unspecified or set to `None`. For example:

```python
WAGTAILDOCS_SERVE_METHOD = "redirect"
```

(documents_security_considerations)=

### Security considerations

```{warning}
Any system that allows user-uploaded files is a potential security risk.
```

When using `FileSystemStorage`, documents are stored in a `documents` subdirectory within your site's `MEDIA_ROOT`. In this case, `WAGTAILDOCS_SERVE_METHOD` defaults to `serve_view`, where Wagtail serves the document through a Django view that enforces privacy checks.

When using the `serve_view` method:

-   You must block direct access to the `documents` subdirectory of `MEDIA_ROOT` within your web server configuration. This prevents users from bypassing [collection privacy settings](https://guide.wagtail.org/en-latest/how-to-guides/manage-collections/#privacy-settings) by accessing documents at their direct URL.
-   Documents are served as downloads rather than displayed in the browser (unless specified explicitly via [](wagtaildocs_inline_content_types)) - this ensures that if the document is a type that can contain scripts (such as HTML or SVG), the browser is prevented from executing them.
-   However, since the document is served through the Django application server, this may consume more server resources than serving the document directly from the web server.

The alternative serve methods `'direct'` and `'redirect'` work by serving the documents directly from `MEDIA_ROOT`. This means it is not possible to block direct access to the `documents` subdirectory, and so users may bypass permission checks by accessing the direct URL. Also, in the case that users with access to the Wagtail admin are not fully trusted, you will need to take additional steps to prevent the execution of scripts in documents:

-   The [](wagtaildocs_extensions) setting may be used to restrict uploaded documents to an "allow list" of safe types.
-   The web server can be configured to return a `Content-Security-Policy: default-src 'none'` header for files within the `documents` subdirectory, which will prevent the execution of scripts in those files.
-   The web server can be configured to return a `Content-Disposition: attachment` header for files within the `documents` subdirectory, which will force the browser to download the file rather than displaying it inline.

If a remote ("cloud") storage backend is used, the serve method will default to `'redirect'` and the document will be served directly from the cloud storage file url. In this case (as with `'direct'`), Wagtail has less control over how the file is served and users may be able to bypass permission checks, and scripts within documents may be executed (depending on the cloud storage service's configuration). However, whilst cross-site scripts attacks are still possible, the impact is reduced as the document is usually served from a different domain to the main site.

If these limitations are not acceptable, you may set the `WAGTAILDOCS_SERVE_METHOD` to `serve_view` and ensure that the documents are not publicly accessible using the cloud service's file url.

The steps required to set headers for specific responses will vary, depending on how your Wagtail application is deployed and which storage backend is used. For the `serve_view` method, a `Content-Security-Policy` header is automatically set for you (unless disabled via [](wagtaildocs_block_embedded_content)) to prevent the execution of scripts embedded in documents.

## Content types

Wagtail provides the [WAGTAILDOCS_CONTENT_TYPES](wagtaildocs_content_types) setting to specify which document content types are allowed to be uploaded. For example:

```python
WAGTAILDOCS_CONTENT_TYPES = {
    'pdf': 'application/pdf',
    'txt': 'text/plain',
}
```

## Inline content types

Inline content types can be specified using [WAGTAILDOCS_INLINE_CONTENT_TYPES](wagtaildocs_inline_content_types), are displayed within the rich text editor.

For example:

```python
WAGTAILDOCS_INLINE_CONTENT_TYPES = ['application/pdf', 'text/plain']
```

## File extensions

Wagtail allows you to specify the permitted file extensions for document uploads using the [WAGTAILDOCS_EXTENSIONS](wagtaildocs_extensions) setting.

It also validates the extensions using Django's {class}`~django.core.validators.FileExtensionValidator`. For example:

```python
WAGTAILDOCS_EXTENSIONS = ['pdf', 'docx']
```

## Document password required template

Wagtail provides the `WAGTAILDOCS_PASSWORD_REQUIRED_TEMPLATE` setting to use a custom template when a password is required to access a protected document. Read more about [](private_pages).

Here's an example:

```python
WAGTAILDOCS_PASSWORD_REQUIRED_TEMPLATE = 'myapp/document_password_required.html'
```
