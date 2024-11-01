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
