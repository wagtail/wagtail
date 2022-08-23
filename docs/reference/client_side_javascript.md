(client_side_javascript_reference)=

# Client-side JavaScript reference

(stimulus_reference)=

## Stimulus

Wagtail uses [Stimulus](https://stimulus.hotwired.dev/) as a way to attach interactive behaviour to DOM elements throughout Wagtail.

Wagtail does not, currently, make the Stimulus application instance available officially. This is so that a clean and supported API can be provided by events.

### Interacting with the Stimulus application via events

Wagtail uses [event listeners and event dispatching](https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Building_blocks/Events) to provide the ability to interact with Stimulus.

#### Dispatched - `'wagtail:stimulus-init'`

-   Called once the Stimulus application has been initialised, most Wagtail code will not be able to listen to this event, however, if more complex JavaScript is injected to run before Wagtail's code it may be useful.
-   It will be dispatched just before `stimulus-ready`
-   **Cancellable** - No

#### Dispatched - `'wagtail:stimulus-ready'`

-   Dispatched on `DOMContentLoaded` and DOM ready state changes to indicate that Stimulus is ready.
-   `detail.createController` a function that accepts an object with `STATIC` and other values which will be built into a Stimulus Controller class.
-   `detail.register` a function that accepts an `identifier` (kebab-case string) as the first arg and a controller class as the second, used to register a controller class to the Stimulus application.
-   **Cancellable** - No

#### Listened to - `'wagtail:stimulus-enable-debug'`

-   Must only be fired after the Stimulus application is ready.
-   Will enable the debug mode for Stimulus, useful when working in local development mode.
-   To revert behaviour, simply refresh the browser.

```javascript
document.dispatch(new CustomEvent('wagtail:stimulus-enable-debug'));
```

#### Listened to - `'wagtail:stimulus-register-controller'`

-   Must only be fired after the Stimulus application is ready.
-   Provides an ad-hoc way to register controllers.
-   The event dispatched must provide two values within its `detail`;
-   `detail.identifier` a kebab-case string to use as the identifier.
-   `detail.controller` a controller class OR a suitable object for the `createController` function.

## Further debugging interaction

If you are finding that there are Stimulus controller issues you cannot debug with the `wagtail:stimulus-enable-debug` approach, you can use the built in [Stimulus error callback](https://stimulus.hotwired.dev/handbook/installing#error-handling).

```javascript
window.onerror = console.error;
```

The above code will simply log any errors to the console.

### About ES6 Modules vs ES5 compile targets

Currently, Wagtail compiles to ES5 code, which means that the classes (Stimulus base controller and applications) are not native ES6 classes but rather ES5 classes.

This is fine in most cases, except for calling `new` on classes that extend the ES5 classes while in ES6 code.

Due to this problem, the base controller from Stimulus will not be provided by any shared API, instead you will need to 'bring your own' controller.

This may change at some point in the future, for now you can import Stimulus via your own package or leverage the object approach for simple class generation.

See [](custom_stimulus_controllers) for examples on how to register your own Controller without needing access to the Wagtail core base Controller.
