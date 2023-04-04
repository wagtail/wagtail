(extending_client_side)=

# Extending client-side behaviour

Some of Wagtail’s admin interface is written as client-side JavaScript with [Stimulus](https://stimulus.hotwired.dev/) and [React](https://reactjs.org/).

## Overview

Depending on what parts of the client-side interaction you want to leverage or customise you may need to understand these libraries. React is used for more complex parts of Wagtail such as the sidebar, commenting system and Draftail (rich text editor), for basic JavaScript driven interaction Wagtail is migrating towards Stimulus.

You do not need to know or use these libraries to add your own custom behaviour to elements and in many cases vanilla (plain) JavaScript will work fine. However, Stimulus is the recommended approach for anything that vanilla JavaScript cannot do. You do not need to have Node.js tooling running for your custom Wagtail installation for many customisations built on these libraries. In some cases, such as building packages, it may make more complex development easier though.

Finally, many kinds of common customisations can be done without reaching into JavaScript. Even the Stimulus approach aligns with this philosophy by relying on data attributes that can be often set when declaring Django Widgets and Wagtail Panels in Python or in the HTML templates.

```{note}
It is recommended that you avoid using jQuery as this will be removed in a future version of Wagtail.
```

(extending_client_side_injecting_javascript)=

## Adding custom JavaScript

Within Wagtail's admin interface, there are a few ways to add JavaScript.

For JavaScript added when a specific Widget is used you can add a an inner `Media` class to ensure that file is loaded when the widget is used, see [Django form Media](topics:forms/media/#assets-as-a-static-definition).

If you need the JavaScript files loaded globally, the recommended approach is via hooks such as the [](insert_editor_js) and [](insert_global_admin_js) hooks.

These will ensure the added files are used in the admin after the core JavaScript admin files are already loaded.

(extending_client_side_using_events)=

## Using Browser DOM Events

When approaching client-side customisations or adopting new components, try to keep the implementation simple first, you may not need any knowledge of Stimulus, React, ECMA 2015 Modules or a build system to achieve your goals.

The simplest way to attach behaviour to the browser is via DOM Events.

For example, you if you want to attach some logic to a field value change in Wagtail you can add an event listener, check if it is the correct element and change what you need.

```javascript
document.addEventListener('change', function (event) {
    if (event.currentTarget) {
        console.log('field has changed', event.currentTarget);
    }
});
```

Or you could write some JavaScript logic that does something when the sidebar panel is toggled by listening to all click events and determining if the one clicked was the sidebar.

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

### Wagtail's custom DOM events

-   Wagtail supports some custom behaviour to via listening or dispatching custom DOM events, usually with the prefix `wagtail:` or `w-` for specific Stimulus controllers.
-   See [](images_title_generation_on_upload)
-   See [](docs_title_generation_on_upload)

(extending_client_side_stimulus)=

## Using Stimulus

Wagtail uses [Stimulus](https://stimulus.hotwired.dev/) as a way to provide lightweight client-side interactivity where React is not required. Stimulus can be used to easily build custom JavaScript widgets within the admin interface. The key benefit of using Stimulus is that your code does not have to manually be initialised when widgets appear dynamically in the browser (such as within modals, InlinePanels StreamField panels).

Below are a series of examples on how to use Stimulus within the Wagtail admin interface.

### Understanding the basics of Stimulus

The [Stimulus documentation](https://stimulus.hotwired.dev/) is the best source on how to work with and understand Stimulus, here is a basic overview though.

1. HTML first - Consider the HTML structure of your components first, especially accessibility.
2. Controllers - Try to create Controllers that are small in scope, remember that there are a few callback methods (`connect`, `disconnect`).
3. Targets - Simple Controllers can use the `this.element` to get the controlled element, reach for targets if you need to have access to other DOM elements in your Controller code and avoid using DOM selectors within the JavaScript.
4. Values - Using `data-...-value` attributes allows values to be declared within your HTML and these values are also dynamic based on changes triggered within the Controller.
5. Actions - To avoid using manually adding and removing DOM event listeners you can leverage the `data-action` attributes for triggering Controller methods based on DOM events such as `click`.

### Adding a custom Stimulus controller

Wagtail exposes a single client-side global (`window.Stimulus`), which is an instance of the core admin Stimulus application.

To you need to first create a custom [Stimulus Controller](https://stimulus.hotwired.dev/reference/controllers). This can be done in two main ways;

1. `window.Stimulus.base.createController` accepts an object using the [method definitions](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/Method_definitions) approach, with a special `STATIC` property for static properties. This is the simplest way to work with Stimulus and does not require any knowledge of JavaScript classes.
2. Create a custom class that extends the base `window.Stimulus.base.Controller` using ES2015 JavaScript class inheritance.

Once you have created your custom controller, you will need to [register your Stimulus controllers manually](https://stimulus.hotwired.dev/reference/controllers#registering-controllers-manually) via the `window.Stimulus.register` method.

For additional guidance on building Stimulus controllers you can view the [](ui_guidelines_stimulus) aimed at Wagtail contributors.

#### A simple example

```javascript
window.Stimulus.register(
    'my-controller',
    window.Stimulus.base.createController({
        connect: function () {
            console.log(
                'My controller has connected: %s',
                this.element.innerText,
            );
        },
    }),
);
```

```html
<div data-controller="my-controller">Hi</div>
<!-- will log 'My controller has connected: hi' to the console -->
<div data-controller="my-controller">Hello</div>
<!-- will log 'My controller has connected: hello' to the console -->
```

#### A word count controller (without a build system)

```javascript
// myapp/static/js/word-count-controller.js
window.Stimulus.register(
    'word-count',
    window.Stimulus.base.createController({
        STATIC: {
            values: { max: { default: 10, type: Number } },
        },
        connect: function () {
            this.setupOutput();
            this.updateCount();
        },
        setupOutput: function () {
            if (this.output) return;
            const template = document.createElement('template');
            template.innerHTML = `<output name='word-count' for='${this.element.id}' style='float: right;'></output>`;
            const output = template.content.firstChild;
            this.element.insertAdjacentElement('beforebegin', output);
            this.output = output;
        },
        updateCount: function (event) {
            const value = event ? event.target.value : this.element.value;
            const words = (value || '').split(' ');
            this.output.textContent = `${words.length} / ${this.maxValue} words`;
        },
        disconnect: function () {
            this.element && this.element.remove();
        },
    }),
);
```

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
                    'data-word-count-max-value': '5',
                    'data-action': 'word-count#updateCount paste->word-count#updateCount',
                }
            )
        ),
    #...
```

```python
# wagtail_hooks.py
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

#### A word count controller (with a build system or ES2015 modules)

You can import the base controller from the global Stimulus application or if you have a build tooling set up you can install `@hotwired/stimulus` using `npm install @hotwired/stimulus --save`.

```{warning}
Usage of `class ... extends` from the globally provided `window.Stimulus.base.Controller` cannot be done outside of code that is also bundled to ES5.
```

```javascript
// myapp/static/js/word-count-controller.js
// const { Controller } = window.Stimulus.base; // if you do not want to use an alias or import your own package
import { Controller } from '@hotwired/stimulus'; // if using a build tool (see notes below about bundling)

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
        this.element && this.element.remove();
    }
}

window.Stimulus.register('word-count', WordCountController);
```

```python
# wagtail_hooks.py
from django.utils.html import format_html_join
from django.templatetags.static import static

from wagtail import hooks

# IMPORTANT _ THIS IS NOT FUNCTIONAL _ NEED TO MAKE MODULE SYNTAX
@hooks.register('insert_editor_js')
def editor_js():
    js_files = ['js/word-count-controller.js',]
    return format_html_join('\n', '<script src="{0}"></script>',
        ((static(filename),) for filename in js_files)
    )
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

##### Additional tips for bundling

You may want to avoid bundling Stimulus with your JavaScript output, you will need to look at how your build system can support this. You may also need to ensure your target bundle is ES2015 or above to be able to correctly extend the global base Controller class.

For bundler specific handling of external dependencies or aliasing, see the following links.

-   [Vite library mode](https://vitejs.dev/guide/build.html#library-mode), which uses rollup configuration
-   [Rollup external](https://rollupjs.org/configuration-options/#external) and [Rollup output globals](https://rollupjs.org/configuration-options/#output-globals)
-   [Webpack externals](https://webpack.js.org/configuration/externals/)
-   [Parcel aliases](https://parceljs.org/features/dependency-resolution/#aliases)

### Using an existing Stimulus controller in HTML

```{warning}
While many Stimulus controllers are in use, this does not imply stable and documented usage is supported for all.
```

Any built in admin Stimulus Controller can be used via the Stimulus data attributes. These attributes can be declared in the HTML template for the content being used.

-   `data-controller` - The registered Controller's identifier (prefixed with `w-`).
-   `data-action` - Mapping DOM events to the Controller's supported methods.
-   `data-...-target` - Mapping DOM elements to the Controller's supported targets.
-   `data-...-value` - Must be added on the controlled element (the one with the `data-controller` attribute), used to declare values based on what the Controller supports.

#### Examples of using the `w-progress` Controller

The `w-progress` Controller is used to help the user avoid clicking the same button multiple times when there may be some delayed behaviour required. Custom usage of this is supported for usage within the admin interface.

-   `<button ... data-w-progress-duration-value="500" ...>` - custom duration can be declared on the element
-   `<button ... class="custom-button" data-w-progress-active-class="custom-button--busy" ...>` - custom 'active' class to replace the default `button-longrunning-active` (must be a single string without spaces)
-   `<button ... ><strong data-w-progress-target="label">{% trans 'Create' %}</strong></button>` - any element can be the button label (not just `em`)
-   `<button ... data-action="w-progress#activate focus->w-progress#activate" ...>` - any event can be used to trigger the in progress behaviour
-   `<button ... data-action="w-progress#activate:once" ...>` - only trigger the progress behaviour once
-   `<button ... data-action="readystatechange@document->w-progress#activate:once" data-w-progress-duration-value="5000" disabled ...>` - disabled on load (once JS starts) and becomes enabled after 5s duration

### Debugging & Error Handling

For simple debugging, you can enable the [Stimulus debug mode](https://stimulus.hotwired.dev/handbook/installing#debugging).

```javascript
window.Stimulus.debug = true;
```

You can use also the built in [Stimulus error callback](https://stimulus.hotwired.dev/handbook/installing#error-handling) for more robust error handling.

```javascript
window.onerror = console.error;
```

### Advanced Stimulus overrides

While these kinds of overrides are supported as a last ditch method to fully customise behaviour, writing this knd of code will require you to understand the existing implementations and support the JavaScript on your own. It is also important to note that the maintenance burden will be on your project to ensure that any functionality added or changes to controller identifiers are supported.

If you find yourself reaching for this to fix a bug, please ensure an issue is raised on the Wagtail repository with your functional work around.

Similarly, if some common Stimulus Controller usage would be helpful for the community, such as additional values, targets, DOM events or methods, please raise an issue with the suggestion.

```{warning}
Usage of `class ... extends` from the globally provided `window.Stimulus.base.Controller` cannot be done outside of code that is also bundled to ES5.
```

#### Registering a custom Stimulus application instance

One of the simplest ways to add behaviour on top of Wagtail's existing Controllers is to create your own Stimulus application.
This is useful if you want to append to existing behaviour of known Controllers.
Please note that non-blocking (async) errors will be thrown and shown in the console if methods are triggered by Stimulus actions if the method does not exist.

In the example below we can attach, but not override, custom behaviour to the `w-dismissible` methods.

```javascript
(() => {
    const StimulusExtra = window.Stimulus.start(); // start will instantiate the class and return its new instance
    class SlugCheckController extends window.Stimulus.base.Controller {
        compare() {
            // noop
        }
        slugify() {
            window.myCustomChecks.validate(this.element);
        }
        urlify() {
            window.myCustomChecks.validate(this.element);
        }
    }
    StimulusExtra.register('w-slug', SlugCheckController);
})();
```

#### Extending an existing Stimulus controller

For more extreme customisations it is possible to retrieve an existing registered Controller from the Stimulus application instance. This can be extended (using ES2015 class inheritance) and this extended controller registered again with the same identifier.

There may also be some side effects of built in controllers being registered, depending on the timing of your JavaScript code event firing.

The example below is a basic functional way to extend and override an existing controller.
Stimulus' only documented way of retrieving a Controller constructor is via the [`getControllerForElementAndIdentifier`](https://stimulus.hotwired.dev/reference/controllers#directly-invoking-other-controllers) method on the application.
You can also retrieve all registered Controllers via `window.Stimulus.controllers`, but this approach is not officially supported by Stimulus.

Once you have the Controller class, you can use `window.Stimulus.unload` to remove the registration of the existing one and then replace it with your custom Controller class using `window.Stimulus.register`.

Here is a basic example of this override.

```javascript
(() => {
    const identifier = 'w-slug';
    const element = document.querySelector(`[data-controller="${identifier}"]`);

    if (!element) return;

    const SlugController = window.Stimulus.getControllerForElementAndIdentifier(
        element,
        identifier,
    );

    class CustomSlugController extends SlugController {
        slugify() {
            // custom url slug
        }
        urlify() {
            // custom url slug
        }
    }
    Stimulus.register('w-slug', CustomSlugController);
})();
```

#### Completely overriding existing admin behaviour of Stimulus controllers

Wagtail also allows you to register a controller against its main application instance, see the examples above or the events reference for these events.

You can completely override the built in controllers via using the same `identifier` (usually starts with `w-`) and registering your own controller with that identifier.

It is important to note that your custom controller will need to re-implement the existing methods or you will get console errors when these are called.

There may also be some side effects of built in controllers being registered, depending on the timing of your JavaScript code event firing.

```javascript
(() => {
    class CustomSlugController extends window.Stimulus.base.Controller {
        slugify() {
            // custom url slug
        }
        urlify() {
            // custom url slug
        }
    }
    Stimulus.register('w-slug', CustomSlugController);
})();
```

(extending_client_side_react)=

## Extending with React

In order to customise or extend the [React](https://reactjs.org/) components, you may need to use React too, as well as other related libraries.

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

See [](extending_the_draftail_editor)
