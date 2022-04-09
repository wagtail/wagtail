# Title generation on upload

When uploading a file (document), Wagtail takes the filename, removes the file extension, and populates the title field. This section is about how to customise this filename to title conversion.

The filename to title conversion is used on the single file widget, multiple upload widget, and within chooser modals.

You can also customise this [same behaviour for images](../images/title_generation_on_upload).

You can customise the resolved value of this title using a JavaScript [event listener](https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener) which will listen to the `'wagtail:documents-upload'` event.

The simplest way to add JavaScript to the editor is via the [`insert_global_admin_js` hook](insert_global_admin_js), however any JavaScript that adds the event listener will work.

## DOM Event

The event name to listen for is `'wagtail:documents-upload'`. It will be dispatched on the document upload `form`. The event's `detail` attribute will contain:

-   `data` - An object which includes the `title` to be used. It is the filename with the extension removed.
-   `maxTitleLength` - An integer (or `null`) which is the maximum length of the `Document` model title field.
-   `filename` - The original filename without the extension removed.

To modify the generated `Document` title, access and update `event.detail.data.title`, no return value is needed.

For single document uploads, the custom event will only run if the title does not already have a value so that we do not overwrite whatever the user has typed.

You can prevent the default behaviour by calling `event.preventDefault()`. For the single upload page or modals, this will not pre-fill any value into the title. For multiple uploads, this will avoid any title submission and use the filename title only (with file extension) as a title is required to save the document.

The event will 'bubble' up so that you can simply add a global `document` listener to capture all of these events, or you can scope your listener or handler logic as needed to ensure you only adjust titles in some specific scenarios.

See MDN for more information about [custom JavasScript events](https://developer.mozilla.org/en-US/docs/Web/Events/Creating_and_triggering_events).

## Code Examples

### Adding the file extension to the start of the title

```python
# wagtail_hooks.py
from django.utils.safestring import mark_safe

from wagtail import hooks


@hooks.register("insert_global_admin_js")
def get_global_admin_js():
    return mark_safe(
    """
    <script>
    window.addEventListener('DOMContentLoaded', function () {
        document.addEventListener('wagtail:documents-upload', function(event) {
            var extension = (event.detail.filename.match(/\.([^.]*?)(?=\?|#|$)/) || [''])[1];
            var newTitle = '(' + extension.toUpperCase() + ') ' + (event.detail.data.title || '');
            event.detail.data.title = newTitle;
        });
    });
    </script>
    """
    )
```

### Changing generated titles on the page editor only to remove dashes/underscores

Using the [`insert_editor_js` hook](insert_editor_js) instead so that this script will not run on the `Document` upload page, only on page editors.

```python
# wagtail_hooks.py
from django.utils.safestring import mark_safe

from wagtail import hooks


@hooks.register("insert_editor_js")
def get_global_admin_js():
    return mark_safe(
    """
    <script>
    window.addEventListener('DOMContentLoaded', function () {
        document.addEventListener('wagtail:documents-upload', function(event) {
            // replace dashes/underscores with a space
            var newTitle = (event.detail.data.title || '').replace(/(\s|_|-)/g, " ");
            event.detail.data.title = newTitle;
        });
    });
    </script>
    """
    )
```

### Stopping pre-filling of title based on filename

```python
# wagtail_hooks.py
from django.utils.safestring import mark_safe

from wagtail import hooks


@hooks.register("insert_global_admin_js")
def get_global_admin_js():
    return mark_safe(
    """
    <script>
    window.addEventListener('DOMContentLoaded', function () {
        document.addEventListener('wagtail:documents-upload', function(event) {
            // will stop title pre-fill on single file uploads
            // will set the multiple upload title to the filename (with extension)
            event.preventDefault();
        });
    });
    </script>
    """
    )
```
