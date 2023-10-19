(extending_client_side)=

# Extending client-side behaviour

Many kinds of common customisations can be done without reaching into JavaScript, but depending on what parts of the client-side interaction you want to leverage or customise, you may need to employ React, Stimulus, or plain (vanilla) JS.

[React](https://reactjs.org/) is used for more complex parts of Wagtail, such as the sidebar, commenting system, and the Draftail rich-text editor.
For basic JavaScript-driven interaction, Wagtail is migrating towards [Stimulus](https://stimulus.hotwired.dev/).

You don't need to know or use these libraries to add your custom behaviour to elements, and in many cases, simple JavaScript will work fine, but Stimulus is the recommended approach for more complex use cases.

You don't need to have Node.js tooling running for your custom Wagtail installation for many customisations built on these libraries, but in some cases, such as building packages, it may make more complex development easier.

```{note}
Avoid using jQuery and undocumented jQuery plugins, as they will be removed in a future version of Wagtail.
```

(extending_client_side_injecting_javascript)=

## Adding custom JavaScript

Within Wagtail's admin interface, there are a few ways to add JavaScript.

The simplest way is to add global JavaScript files via hooks, see [](insert_editor_js) and [](insert_global_admin_js).

For JavaScript added when a specific Widget is used you can add an inner `Media` class to ensure that the file is loaded when the widget is used, see [Django's docs on their form `Media` class](https://docs.djangoproject.com/en/stable/topics/forms/media/#assets-as-a-static-definition).

In a similar way, Wagtail's [template components](template_components) provide a `media` property or `Media` class to add scripts when rendered.

These will ensure the added files are used in the admin after the core JavaScript admin files are already loaded.

(extending_client_side_using_events)=

## Extending with DOM events

When approaching client-side customisations or adopting new components, try to keep the implementation simple first, you may not need any knowledge of Stimulus, React, JavaScript Modules or a build system to achieve your goals.

The simplest way to attach behaviour to the browser is via [DOM Events](https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Building_blocks/Events) and plain (vanilla) JavaScript.

### Wagtail's custom DOM events

Wagtail supports some custom behaviour via listening or dispatching custom DOM events.

-   See [Images title generation on upload](images_title_generation_on_upload).
-   See [Documents title generation on upload](docs_title_generation_on_upload).

(extending_client_side_stimulus)=

## Extending with Stimulus

Wagtail uses [Stimulus](https://stimulus.hotwired.dev/) as a way to provide lightweight client-side interactivity or custom JavaScript widgets within the admin interface.

The key benefit of using Stimulus is that your code can avoid the need for manual initialisation when widgets appear dynamically, such as within modals, `InlinePanel`, or `StreamField` panels.

The [Stimulus handbook](https://stimulus.hotwired.dev/handbook/introduction) is the best source on how to work with and understand Stimulus.

### Adding a custom Stimulus controller

Wagtail exposes two client-side globals for using Stimulus.

1. `window.wagtail.app` the core admin Stimulus application instance.
2. `window.StimulusModule` Stimulus module as exported from `@hotwired/stimulus`.

First, create a custom [Stimulus controller](https://stimulus.hotwired.dev/reference/controllers) that extends the base `window.StimulusModule.Controller` using [JavaScript class inheritance](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Classes). If you are using a build tool you can import your base controller via `import { Controller } from '@hotwired/stimulus';`.

Once you have created your custom controller, you will need to [register your Stimulus controllers manually](https://stimulus.hotwired.dev/reference/controllers#registering-controllers-manually) via the `window.wagtail.app.register` method.

#### A simple controller example

First, create your HTML so that appears somewhere within the Wagtail admin.

```html
<!-- Will log 'My controller has connected: hi' to the console -->
<div data-controller="my-controller">Hi</div>
<!-- Will log 'My controller has connected: hello' to the console, with the span element-->
<div data-controller="my-controller">
    Hello <span data-my-controller-target="label"></span>
</div>
```

Second, create a JavaScript file that will contain your controller code. This controller logs a simple message on `connect`, which is once the controller has been created and connected to an HTML element with the matching `data-controller` attribute.

```javascript
// myapp/static/js/example.js

class MyController extends window.StimulusModule.Controller {
    static targets = ['label'];
    connect() {
        console.log(
            'My controller has connected:',
            this.element.innerText,
            this.labelTargets,
        );
    }
}

window.wagtail.app.register('my-controller', MyController);
```

Finally, load the JavaScript file into Wagtail's admin with a hook.

```python
# myapp/wagtail_hooks.py
from django.templatetags.static import static
from django.utils.safestring import mark_safe

from wagtail import hooks

@hooks.register('insert_global_admin_js')
def global_admin_js():
    return mark_safe(
        f'<script src="{static("js/example.js")}"></script>',
    )
```

You should now be able to refresh your admin that was showing the HTML and see two logs in the console.

#### A more complex controller example

Now we will create a `WordCountController` that adds a small `output` element next to the controlled `input` element that shows a count of how many words have been entered.

```javascript
// myapp/static/js/word-count-controller.js
class WordCountController extends window.StimulusModule.Controller {
    static values = { max: { default: 10, type: Number } };

    connect() {
        this.setupOutput();
        this.updateCount();
    }

    setupOutput() {
        if (this.output) return;
        const template = document.createElement('template');
        template.innerHTML = `<output name='word-count' for='${this.element.id}' class='output-label'></output>`;
        const output = template.content.firstChild;
        this.element.insertAdjacentElement('beforebegin', output);
        this.output = output;
    }

    updateCount(event) {
        const value = event ? event.target.value : this.element.value;
        const words = (value || '').split(' ');
        this.output.textContent = `${words.length} / ${this.maxValue} words`;
    }

    disconnect() {
        this.output && this.output.remove();
    }
}
window.wagtail.app.register('word-count', WordCountController);
```

This lets the data attribute `data-word-count-max-value` determine the 'configuration' of this controller and the data attribute actions to determine the 'triggers' for the updates to the output element.

```python
# models.py
from django import forms

from wagtail.admin.panels import FieldPanel
from wagtail.models import Page


class BlogPage(Page):
    # ...
    content_panels = Page.content_panels + [
        FieldPanel('subtitle', classname="full"),
        FieldPanel(
            'introduction',
            classname="full",
            widget=forms.TextInput(
                attrs={
                    'data-controller': 'word-count',
                    # allow the max number to be determined with attributes
                    # note we can use Python values here, Django will handle the string conversion (including escaping if applicable)
                    'data-word-count-max-value': 5,
                    # decide when you want the count to update with data-action
                    # (e.g. 'blur->word-count#updateCount' will only update when field loses focus)
                    'data-action': 'word-count#updateCount paste->word-count#updateCount',
                }
            )
        ),
    #...
```

This next code snippet shows a more advanced version of the `insert_editor_js` hook usage which is set up to append additional scripts for future controllers.

```python
# wagtail_hooks.py
from django.utils.html import format_html_join
from django.templatetags.static import static

from wagtail import hooks


@hooks.register('insert_editor_js')
def editor_js():
    # add more controller code as needed
    js_files = ['js/word-count-controller.js',]
    return format_html_join('\n', '<script src="{0}"></script>',
        ((static(filename),) for filename in js_files)
    )
```

You should be able to see that on your Blog Pages, the introduction field will now have a small `output` element showing the count and max words being used.

#### Using a build system

You will need ensure your build output is ES6/ES2015 or higher. You can use the exposed global module at `window.StimulusModule` or provide your own using the npm module `@hotwired/stimulus`.

```javascript
// myapp/static/js/word-count-controller.js
import { Controller } from '@hotwired/stimulus';

class WordCountController extends Controller {
    // ... the same as above
}

window.wagtail.app.register('word-count', WordCountController);
```

You may want to avoid bundling Stimulus with your JavaScript output and treat the global as an external/alias module, refer to your build system documentation for instructions on how to do this.

## Extending with React

To customise or extend the [React](https://reactjs.org/) components, you may need to use React too, as well as other related libraries.

To make this easier, Wagtail exposes its React-related dependencies as global variables within the admin. Here are the available packages:

```javascript
// 'focus-trap-react'
window.FocusTrapReact;
// 'react'
window.React;
// 'react-dom'
window.ReactDOM;
// 'react-transition-group/CSSTransitionGroup'
window.CSSTransitionGroup;
```

Wagtail also exposes some of its own React components. You can reuse:

```javascript
window.wagtail.components.Icon;
window.wagtail.components.Portal;
```

Pages containing rich text editors also have access to:

```javascript
// 'draft-js'
window.DraftJS;
// 'draftail'
window.Draftail;

// Wagtail’s Draftail-related APIs and components.
window.draftail;
window.draftail.DraftUtils;
window.draftail.ModalWorkflowSource;
window.draftail.ImageModalWorkflowSource;
window.draftail.EmbedModalWorkflowSource;
window.draftail.LinkModalWorkflowSource;
window.draftail.DocumentModalWorkflowSource;
window.draftail.Tooltip;
window.draftail.TooltipEntity;
```

## Extending Draftail

-   [](extending_the_draftail_editor)

## Extending StreamField

-   [](streamfield_widget_api)
-   [](custom_streamfield_blocks_media)

(extending_client_side_react)=
