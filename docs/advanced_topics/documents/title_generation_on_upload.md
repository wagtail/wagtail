(title_generation_on_upload)=

# Title generation on upload

When uploading files (such as documents or images), Wagtail automatically removes the file extension from the filename and uses the rest of the name as the title. This guide shows how to customize that default behavior for both documents and images.

The file name to title conversion is used on the single file widget, multiple upload widget, and within chooser modals.

The filename-to-title conversion applies across Wagtail's single file widget, multiple upload widget, and chooser modals. You can further customize this conversion by using JavaScript event listeners, which react to either the `'wagtail:documents-upload'` or `'wagtail:images-upload'` events.

The simplest way to add JavaScript to the editor is via the [`insert_global_admin_js` hook](insert_global_admin_js). However, any JavaScript that adds an event listener will work.

## DOM event

The event name to listen to is `'wagtail:documents-upload'` and `'wagtail:image-upload'`. It will be dispatched on the document upload `form`. The event's `detail` attribute will contain:

-   `data` - An object which includes the `title` to be used. It is the filename with the extension removed.
-   `maxTitleLength` - An integer (or `null`) which is the maximum length of the title field.
-   `filename` - The original filename without the extension removed.

To modify the generated title, access and update `event.detail.data.title`, no return value is needed.

For single document uploads, the custom event will only run if the title does not already have a value so that we do not overwrite whatever the user has typed.

You can prevent the default behavior by calling `event.preventDefault()`. For the single upload page or modals, this will not pre-fill any value into the title. For multiple uploads, this will avoid any title submission and use the filename title only (with file extension) as a title is required to save the document.

The event will 'bubble' up so that you can simply add a global `document` listener to capture all of these events, or you can scope your listener or handler logic as needed to ensure you only adjust titles in some specific scenarios.

See MDN for more information about [custom JavaScript events](https://developer.mozilla.org/en-US/docs/Web/Events/Creating_and_triggering_events).

## Code examples

For each example below, create the specified external JavaScript file in your app’s static directory, such as `static/js/`, and reference it in the `wagtail_hooks.py` file.

### Document specific methods:

### Adding the file extension to the start of the title

```python
# wagtail_hooks.py
from django.utils.safestring import mark_safe
from wagtail import hooks
from django.templatetags.static import static

@hooks.register("insert_global_admin_js")
def get_global_admin_js():
    static_url = static('js/title_with_extension.js')
    return mark_safe(f'<script src="{static_url}"></script>')
```

Save the following code as static/js/title_with_extension.js

```javascript
// title_with_extension.js
window.addEventListener('DOMContentLoaded', function () {
    document.addEventListener('wagtail:documents-upload', function(event) {
        var extension = (event.detail.filename.match(/\.([^.]*?)(?=\?|#|$)/) || [''])[1];
        var newTitle = '(' + extension.toUpperCase() + ') ' + (event.detail.data.title || '');
        event.detail.data.title = newTitle;
    });
});
```


### Changing generated titles on the page editor only to remove dashes/underscores

Use the [`insert_editor_js` hook](insert_editor_js) instead so that this script will run only on page editors and not on the `Document`.

```python
# wagtail_hooks.py
from django.utils.safestring import mark_safe
from wagtail import hooks
from django.templatetags.static import static

@hooks.register("insert_editor_js")
def get_editor_js():
    static_url = static('js/title_with_extension.js')
    return mark_safe(f'<script src="{static_url}"></script>')
```

Save the following code as static/js/remove_dashes_underscores.js

```javascript
// remove_dashes_underscores.js
window.addEventListener('DOMContentLoaded', function () {
    document.addEventListener('wagtail:documents-upload', function(event) {
        // Replace dashes/underscores with a space
        var newTitle = (event.detail.data.title || '').replace(/(\s|_|-)/g, " ");
        event.detail.data.title = newTitle;
    });
});
```

### Stopping pre-filling of title based on filename

```python
# wagtail_hooks.py
from django.utils.safestring import mark_safe
from wagtail import hooks
from django.templatetags.static import static

@hooks.register("insert_global_admin_js")
def get_global_admin_js():
    static_url = static('js/stop_title_prefill.js')
    return mark_safe(f'<script src="{static_url}"></script>')
```

Save the following code as static/js/stop_title_prefill.js

```javascript
// stop_title_prefill.js
window.addEventListener('DOMContentLoaded', function () {
    document.addEventListener('wagtail:documents-upload', function(event) {
        // Will stop title pre-fill on single file uploads
        // Will set the multiple upload title to the filename (with extension)
        event.preventDefault();
    });
});
```
### Image specific methods:

### Removing any url unsafe characters from the title

```python
# wagtail_hooks.py
from django.utils.safestring import mark_safe
from wagtail import hooks
from django.templatetags.static import static

@hooks.register("insert_global_admin_js")
def get_global_admin_js():
    static_url = static('js/clean_image_title.js')
    return mark_safe(f'<script src="{static_url}"></script>')
```

Save the following code as static/js/clean_image_title.js

```javascript
// clean_image_title.js
window.addEventListener('DOMContentLoaded', function () {
    document.addEventListener('wagtail:images-upload', function(event) {
        // Remove special characters from the title, keeping only alphanumeric characters, spaces, and hyphens
        var newTitle = (event.detail.data.title || '').replace(/[^a-zA-Z0-9\s-]/g, "");
        event.detail.data.title = newTitle;
    });
});
```

### Changing generated titles on the page editor only to remove dashes/underscores

Use the [`insert_editor_js` hook](insert_editor_js) instead so that this script will not run on the `Image` upload page, only on page editors.

```python
# wagtail_hooks.py
from django.utils.safestring import mark_safe
from wagtail import hooks
from django.templatetags.static import static

@hooks.register("insert_editor_js")
def get_editor_js():
    static_url = static('js/remove_dashes_underscores.js')
    return mark_safe(f'<script src="{static_url}"></script>')
```

Save the following as static/js/remove_dashes_underscores.js

```javascript
// remove_dashes_underscores.js
window.addEventListener('DOMContentLoaded', function () {
    document.addEventListener('wagtail:images-upload', function(event) {
        // Replace dashes/underscores with a space
        var newTitle = (event.detail.data.title || '').replace(/(\s|_|-)/g, " ");
        event.detail.data.title = newTitle;
    });
});
```

### Stopping pre-filling of title based on filename

```python
# wagtail_hooks.py
from django.utils.safestring import mark_safe
from wagtail import hooks
from django.templatetags.static import static

@hooks.register("insert_global_admin_js")
def get_global_admin_js():
    static_url = static('js/stop_title_prefill.js')
    return mark_safe(f'<script src="{static_url}"></script>')
```

Save the following as static/js/stop_title_prefill.js

```javascript
// stop_title_prefill.js
window.addEventListener('DOMContentLoaded', function () {
    document.addEventListener('wagtail:images-upload', function(event) {
        // Will stop title pre-fill on single file uploads
        // Will set the multiple upload title to the filename (with extension)
        event.preventDefault();
    });
});
```
