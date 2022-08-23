(client_side_javascript_customisation)=

# Client-side JavaScript customisation

Some of Wagtail’s admin interface is written as client-side JavaScript with [Stimulus](https://stimulus.hotwired.dev/) and [React](https://reactjs.org/).

Depending on what parts of the client-side interaction you want to leverage or customise you may need to understand these libraries. React is used for some more complex parts of Wagtail such as the sidebar, commenting system and Draftail (rich text editor), for basic JavaScript driven interaction Wagtail is migrating towards Stimulus.

You do not need to know or use these libraries to add your own custom behaviour to elements and in many cases vanilla (plain) JS will work fine. You do not need to have Node js tooling running for your custom Wagtail installation for many customisations built on these libraries, in some cases it may make complex development easier though.

```{note}
It is recommended that you avoid using jQuery as this will be removed in a future version of Wagtail.
```

## DOM Events

### Browser DOM Events

When approaching client-side customisations or adopting new components, try to keep the implementation simple first, you may not need any knowledge of Stimulus, React, ES6 Modules or a build system to achieve your goals.

The simplest way to attach behaviour to the browser is via DOM Events.

For example, you if you want to attach some logic to a field value change in Wagtail you can add an event listener, check if it is the correct element and change what you need.

```javascript
document.addEventListener('change', function (event) {
    if (event.currentTarget) {
        console.log('field has changed', event.currentTarget);
    }
});
```

Or you could write some simple JavaScript logic that does something when the sidebar panel is toggled.

```javascript
document.addEventListener('click', function (event) {
    if (event.currentTarget) {
        const isStatusSidebar =
            event.currentTarget.dataset.sidePanelToggle === 'status';
        if (isStatusSidebar) {
            console.log('status sidebar panel has been toggled');
        }
    }
});
```

### Custom DOM Events

-   Wagtail supports custom behaviour to via listening or dispatching custom DOM events, usually with the prefix `wagtail:`.
-   See [](../images/title_generation_on_upload.md)
-   See [](../documents/title_generation_on_upload.md)

(custom_stimulus_controllers)=

## Stimulus

Wagtail uses [Stimulus](https://stimulus.hotwired.dev/) as a way to provide client-side interactivity where React is not required. Stimulus can be used to easily build custom JavaScript widgets within the admin interface.

Below are a series of examples on how to use Stimulus within the Wagtail admin interface, you can also view the full [Stimulus reference](stimulus_reference) for more details.

### Adding a word count controller (without a build system)

Using JavaScript Method definition shorthand
https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/Method_definitions - should use this approach.

```javascript
// myapp/static/js/word-count-controller.js

const wordCountController = {
    STATIC: {
        values: { max: { default: 10, type: Number } },
    },
    connect() {
        this.setupOutput();
        this.updateCount();
    },
    setupOutput() {
        if (this.output) return;
        const template = document.createElement('template');
        template.innerHTML = `<output name='word-count' for='${this.element.id}' style='float: right;'></output>`;
        const output = template.content.firstChild;
        this.element.insertAdjacentElement('beforebegin', output);
        this.output = output;
    },
    updateCount(event) {
        const value = event ? event.target.value : this.element.value;
        const words = (value || '').split(' ');
        this.output.textContent = `${words.length} / ${this.maxValue} words`;
    },
    disconnect() {
        this.output && this.output.remove();
    },
};

document.addEventListener(
    'wagtail:stimulus-ready',
    ({ detail: { createController, register } }) => {
        register('word-count', createController(wordCountController));
    },
    // important: stimulus-ready may be called more than once, only run the registration once
    { once: true },
);
```

```python
# models.py
# https://docs.wagtail.org/en/stable/reference/pages/panels.html#fieldpanel
from django import forms

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
                    'data-word-count-max-value': '5',
                    'data-action': 'word-count#updateCount paste->word-count#updateCount',
                }
            )
        ),
    #...
```

```python
# wagtail_hooks.py
# https://docs.wagtail.org/en/stable/reference/hooks.html
from django.utils.html import format_html_join
from django.templatetags.static import static

from wagtail import hooks


@hooks.register('insert_editor_js')
def editor_js():
    js_files = ['js/word-count-controller.js',]
    return format_html_join('\n', '<script src="{0}"></script>',
        ((static(filename),) for filename in js_files)
    )

```

### Adding a word count controller (with a build system or ES6 modules)

-   Install `@hotwired/stimulus` using `npm install @hotwired/stimulus --save`
-   Alternatively, you can simply use ES6 modules with a path to the Stimulus module or a public URL.
-   Wagtail does not yet provide a controller to be imported, you will need to 'bring your own controller' class. This is due to conflicts with ES6 modules and the currently ES5 transpile target of Wagtail's JavaScript.

```javascript
// myapp/static/js/word-count-controller.js
// import { Controller } from "https://unpkg.com/@hotwired/stimulus/dist/stimulus.js"; // can be used as an ES6 module import
import { Controller } from '@hotwired/stimulus';

class WordCountController extends Controller {
    static values = { max: { default: 10, type: Number } };

    connect() {
        const output = document.createElement('output');
        output.setAttribute('name', 'word-count');
        output.setAttribute('for', this.element.id);
        output.style.float = 'right';
        this.element.insertAdjacentElement('beforebegin', output);
        this.output = output;
        this.updateCount();
    }

    setupOutput() {
        if (this.output) return;
        const template = document.createElement('template');
        template.innerHTML = `<output name='word-count' for='${this.element.id}' style='float: right;'></output>`;
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

document.addEventListener(
    'wagtail:stimulus-ready',
    ({ detail: { createController, register } }) => {
        register('word-count', WordCountController);
    },
    // important: stimulus-ready may be called more than once, only run the registration once
    { once: true },
);
```

```python
# models.py
# https://docs.wagtail.org/en/stable/reference/pages/panels.html#fieldpanel
from django import forms

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
                    'data-word-count-max-value': '40',
                    # decide when you want the count to update with data-action (e.g. 'blur->word-count#updateCount' will only update when field loses focus)
                    'data-action': 'word-count#updateCount paste->word-count#updateCount',
                }
            )
        ),
    #...
```

### Attaching additional behaviour to existing Stimulus usage

As Wagtail adopts Stimulus for client-side behaviour, you can attach your own Stimulus controllers to these same elements to attach custom behaviour.

This can be done via leveraging the same `identifier` (usually starts with `w-`) and registering your own controller with that identifier.

It is important to note that this does not modify existing controllers, but allows you to hook in extra behaviour.

```{note}
For many scenarios, using DOM Events will be more than sufficient for custom behaviour.
Only use additional controllers if you need to do more complex customisations.
```

```html
<script type="module">
    // note: It would be recommended to serve your own copy of the Stimulus library
    import {
        Application,
        Controller,
    } from 'https://unpkg.com/@hotwired/stimulus/dist/stimulus.js';
    window.Stimulus = Application.start();

    Stimulus.register(
        'w-clean-field',
        class extends Controller {
            clean(event) {
                console.log(
                    'Update some other field when the slug changes',
                    event,
                );
            }
        },
    );
</script>
```

### Completely overriding existing admin behaviour of Stimulus controllers

Wagtail also allows you to register a controller against its main application instance, see the examples above or the events reference for these events.

You can completely override the built in controllers via using the same `identifier` (usually starts with `w-`) and registering your own controller with that identifier.

It is important to note that your custom controller will need to re-implement the existing methods or you will get console errors when these are called.

There may also be some side effects of built in controllers being registered, depending on the timing of your JavaScript code event firing.

While these kinds of overrides are supported as a last ditch method to fully customise behaviour, writing this knd of code will require you to understand the existing implementations and support the JavaScript on your own.

```{note}
At this time, Wagtail does not provide an official way to extend existing controllers via class inheritance. If this is something useful, please share your use cases on the TODO _ ADD DISCUSSION.
```

(extending_client_side_react_components)=

## React

Some of Wagtail’s admin interface is written as client-side JavaScript with [React](https://reactjs.org/).

In order to customise or extend those components, you may need to use React too, as well as other related libraries.
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
