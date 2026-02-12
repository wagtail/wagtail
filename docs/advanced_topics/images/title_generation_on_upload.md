(images_title_generation_on_upload)=

# Title generation on upload

When uploading an image, Wagtail takes the filename, removes the file extension, and populates the title field. This section is about how to customize this filename to title conversion.

The filename to title conversion is used on the single file widget, multiple upload widget, and within chooser modals.

You can also customize this [same behavior for documents](../documents/title_generation_on_upload).

You can customize the resolved value of this title using a JavaScript [event listener](https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener) which will listen to the `'wagtail:images-upload'` event.

The simplest way to add JavaScript to the editor is via the [`insert_global_admin_js` hook](insert_global_admin_js), however, any JavaScript that adds the event listener will work.

## DOM event

The event name to listen for is `'wagtail:images-upload'`. It will be dispatched on the image upload `form`. The event's `detail` attribute will contain:

-   `data` - An object which includes the `title` to be used. It is the filename with the extension removed.
-   `maxTitleLength` - An integer (or `null`) which is the maximum length of the `Image` model title field.
-   `filename` - The original filename without the extension removed.

To modify the generated `Image` title, access and update `event.detail.data.title`, no return value is needed.

For single image uploads, the custom event will only run if the title does not already have a value so that we do not overwrite whatever the user has typed.

You can prevent the default behavior by calling `event.preventDefault()`. For the single upload page or modals, this will not pre-fill any value into the title. For multiple uploads, this will avoid any title submission and use the filename title only (with file extension) as a title is required to save the image.

The event will 'bubble' up so that you can simply add a global `document` listener to capture all of these events, or you can scope your listener or handler logic as needed to ensure you only adjust titles in some specific scenarios.

See MDN for more information about [custom JavaScript events](https://developer.mozilla.org/en-US/docs/Web/Events/Creating_and_triggering_events).

## Code examples

For each example below, create the specified external JavaScript file in your app’s static directory, such as `static/js/`, and reference it in the `wagtail_hooks.py` file.

### Removing any url unsafe characters from the title

```python
# wagtail_hooks.py
from django.templatetags.static import static
from django.utils.html import format_html

from wagtail import hooks

@hooks.register("insert_global_admin_js")
def get_global_admin_js():
    script_url = static('js/wagtail_admin.js')
    return format_html('<script src="{}"></script>', script_url)
```

```javascript
window.addEventListener('DOMContentLoaded', function () {
    document.addEventListener('wagtail:images-upload', function (event) {
        const newTitle = (event.detail.data.title || '').replace(
            /[^a-zA-Z0-9\s-]/g,
            '',
        );
        event.detail.data.title = newTitle;
    });
});
```

### Changing generated titles on the page editor only to remove dashes/underscores

Use the [`insert_editor_js` hook](insert_editor_js) instead so that this script will not run on the `Image` upload page, only on page editors.

```python
# wagtail_hooks.py
from django.templatetags.static import static
from django.utils.html import format_html

from wagtail import hooks

@hooks.register("insert_editor_js")
def get_global_admin_js():
def insert_remove_dashes_underscores_js():
    script_url = static('js/remove_dashes_underscores.js')
    return format_html('<script src="{}"></script>', script_url)
```

```javascript
window.addEventListener('DOMContentLoaded', function () {
    document.addEventListener('wagtail:images-upload', function (event) {
        // Replace dashes/underscores with a space
        const newTitle = (event.detail.data.title || '').replace(
            /(\s|_|-)/g,
            ' ',
        );
        event.detail.data.title = newTitle;
    });
});
```

### Stopping pre-filling of title based on filename

```python
# wagtail_hooks.py
from django.templatetags.static import static
from django.utils.html import format_html

from wagtail import hooks

@hooks.register("insert_global_admin_js")
def get_global_admin_js():
    script_url = static('js/stop_prefill.js')
    return format_html('<script src="{}"></script>', script_url)
```

```javascript
window.addEventListener('DOMContentLoaded', function () {
    document.addEventListener('wagtail:images-upload', function (event) {
        // Stop title pre-fill on single file uploads
        // Set the multiple upload title to the filename (with extension)
        event.preventDefault();
    });
});
```
