# UI Guidelines

Wagtail’s user interface is built with:

-   **HTML** using [Django templates](https://docs.djangoproject.com/en/stable/ref/templates/language/)
-   **CSS** using [Sass](https://sass-lang.com/) and [Tailwind](https://tailwindcss.com/)
-   **JavaScript** with [TypeScript](https://www.typescriptlang.org/)
-   **SVG** for our icons, minified with [SVGO](https://jakearchibald.github.io/svgomg/)

## Linting and formatting

Here are the available commands:

-   `make lint` will run all linting, `make lint-server` lints templates, `make lint-client` lints JS/CSS.
-   `make format` will run all formatting and fixing of linting issues. There is also `make format-server` and `make format-client`.

Have a look at our `Makefile` tasks and `package.json` scripts if you prefer more granular options.

## HTML guidelines

We use [djhtml](https://github.com/rtts/djhtml) for formatting and [Curlylint](https://www.curlylint.org/) for linting.

-   Write [valid](https://validator.w3.org/nu/), [semantic](https://html5doctor.com/element-index/) HTML.
-   Follow [ARIA authoring practices](https://w3c.github.io/aria-practices/), in particular [No ARIA is better than Bad ARIA](https://w3c.github.io/aria-practices/#no_aria_better_bad_aria).
-   Use classes for styling, `data-` attributes for JavaScript behaviour, IDs for semantics only.
-   For comments, use [Django template syntax](https://docs.djangoproject.com/en/stable/ref/templates/language/#comments) instead of HTML.

## CSS guidelines

We use [Prettier](https://prettier.io/) for formatting and [Stylelint](https://stylelint.io/) for linting.

-   We follow [BEM](http://getbem.com/) and [ITCSS](https://www.xfive.co/blog/itcss-scalable-maintainable-css-architecture/), with a large amount of utilities created with [Tailwind](https://tailwindcss.com/).
-   Familiarise yourself with our [stylelint-config-wagtail](https://github.com/wagtail/stylelint-config-wagtail) configuration, which details our preferred code style.
-   Use `rems` for `font-size`, because they offer absolute control over text. Additionally, unit-less `line-height` is preferred because it does not inherit a percentage value of its parent element, but instead is based on a multiplier of the `font-size`.
-   Always use variables for design tokens such as colours or font sizes, rather than hard-coding specific values.
-   We use the `w-` prefix for all styles intended to be reusable by Wagtail site implementers.

## JavaScript guidelines

We use [Prettier](https://prettier.io/) for formatting and [ESLint](https://eslint.org/) for linting.

-   We follow a somewhat relaxed version of the [Airbnb styleguide](https://github.com/airbnb/javascript).
-   Familiarise yourself with our [eslint-config-wagtail](https://github.com/wagtail/eslint-config-wagtail) configuration, which details our preferred code style.

## Multilingual support

This is an area of active improvement for Wagtail, with [ongoing discussions](https://github.com/wagtail/wagtail/discussions/8017).

-   Always use the `trimmed` attribute on `blocktrans` tags to prevent unnecessary whitespace from being added to the translation strings.

## Working with DOM Events

### Dispatching

-   Dispatch from the most suitable, lowest, target element.
-   Use the prefix `wagtail:` (for example, `wagtail:dialog-open`) when creating custom events so that these do not clash with other libraries or use the built inStimulus controller's prefixed event names `w-some-identifier` via `this.dispatch`.
-   `new CustomEvent('wagtail:some-behaviour', { bubbles: true, cancelable: false})` should be the default.
-   Use `event.preventDefault` to modify behaviour, but ensure that `cancelable` is set to `true` in this case.
-   Use `detail` on the event to provide detail to the listener, but do not pass through the DOM element as it will be available as `currentTarget`.
-   Prefer more event names instead of pushing things into detail, two events for open/close is better than one 'switched'.

### Adding Event listeners

-   Add `document` event listeners for global functionality, add event listeners to the nearest unique parent otherwise.
-   `formElement.addEventListener('wagtail:action', someFunction, { passive: true })` - use `passive` by default, unless potentially calling `event.preventDefault`.

## Stimulus usage within Wagtail

-   Wagtail uses [Stimulus](https://stimulus.hotwired.dev/) as a way to attach interactive behaviour to DOM elements throughout Wagtail.
-   This is a lightweight JavaScript framework that allows a JavaScript class to be attached to any DOM element that adheres to a specific usage of `data-` attributes on the element.

### When to use Stimulus

This is a migration in progress, any large refactors or new code should adopt this approach.

1. Investigate if the browser can do this for you or if CSS can solve the specific goals you are working towards.

-   For example, changing visual styling on focus/over should be done with CSS, autofocus on elements can be done with HTML attributes
-   Using buttons with `type='button'` instead of a link or to avoid needing to use `event.preventDefault`
-   Use links to take the user to a new page instead of a button with a click to change the page

2. Investigate if there is an existing JavaScript approach in the code, we do not need to build multiple versions of similar things.
3. Write the HTML first and then assess what parts need to change based on user interactions, if state is minimal then Stimulus may be suitable.
4. Finally, if needed React may be suitable in small cases, but remember that if we want anything to be driven by content in Django templates React may not be suitable.

### How to build a controller

1. Start with the HTML, build as much of the component or UI element as you can in HTML alone, even if that means a few variants if there is state to consider. Ensure it is accessible and follows the CSS guidelines.
2. Once you have the HTML working, add a new `HeaderSearchController.ts` file, a test file and a stories file. Try to decide on a simple name (one word if possible) and name your controller.
3. Avoid using `constructor` on Controller classes, if you need to call something before connection to the DOM you can use [`initialize`](https://stimulus.hotwired.dev/reference/lifecycle-callbacks#methods), this includes binding methods.
4. Add a `connect` method if needed which called once the DOM is ready and the JS is instantiated against your DOM element.
5. You can access the base element with `this.element`, review the Stimulus documentation for full details.
6. Remember to consider scenarios where the element may be disconnected (removed/moved in the DOM), use the `disconnect` method to do any clean up. If you use the `data-action` attributes you do not need to clean up these event listeners, Stimulus will do this for you.

### Best practices

-   Smaller but still generic, controllers that do a small amount of 'work' that is collected together, instead of lots of large or specific controllers.
-   Think about the HTML, use Django templates, consider template overrides and blocks to provide a nice way for more custom behaviour to be added later.
-   Use data-attributes where possible, as per the documented approach, to add event listeners and target elements. It is ok to add event listeners in the controller but opt for the `data-action` approach first, the main benefit here is that it is easier to see in the HTML how the behaviour works and provides a more general purpose functionality out of the controller.
-   Use `this.dispatch` when dispatching `CustomEvent`s to the DOM and whenever possible provide a cancellable behaviour. Events are the preferred way to communicate between controllers and as a bonus provide a nice external API, if the behaviour can be continued use a `continue` function provided to the event's detail.
-   Wrap external libraries in controllers (for example, modals, tooltips), so that if the underlying library changes, the HTML data attributes do not need to change. This gives us the freedom to adopt a better/supported library in the future without too much backwards compatibility issues. This goes for events handling also.
-   Lean towards dispatching events for key behaviour in the UI interaction as this provides a great way for custom code to hook into this without an explicit API, but be sure to document these.
-   Controllers are JavaScript classes and will allow for class inheritance to build on top of base behaviour for variations, however, remember that static attributes do not get inherited and in most cases it will be simpler to use composition of controllers on an element instead of class inheritance.
-   Multiple controllers can be attached to one DOM element for composing behaviour, where practical split out behaviour to separate controllers.
-   Avoid mixing jQuery with Stimulus Controllers as jQuery events are not the same as browser DOM events and can cause confusion, either find a non-jQuery solution or just attach the jQuery widget and set up your own non-jQuery event listeners.
-   It is ok to use a jQuery widget and simply use Stimulus to attach the widget to the right DOM element, but it is better to see if there is an underlying JavaScript implementation to use directly or an alternative library if practical.
-   Telepath will still be used as a data pickle/un-pickle convention if required for more complex data setup.
-   Avoid writing too much HTML (more than `textContent` or basic elements without classes) in the Stimulus controller, instead leverage the `template` element to move large amounts of HTML back into the Django templates. This also helps for translations which can be done in Django and co-located with the other HTML.
-   Avoid using the JavaScript translation functions in Stimulus controllers, this is technically doable but will make it harder for usage of this controller to change this without extending the component, prefer instead to provide translated values in the relevant data values or in `template` / hidden elements within the component as targets.
-   Try to provide generic ways to pass attributes to template components, template tags or similar, Django field widget `attrs` being a good reference example. This makes it easier for other code, within Wagtail or outside, to add more data attributes or append to existing ones to customise behaviour.
-   Avoid the Stimulus controller having knowledge of its own identifier, except in JSDOC examples, remember that the identifier is intentionally disconnected from the controller class so that controllers can be re-used, extended and namespaced for different projects. If you do need to reference a controller's own identifier you can access it via `this.identifier`.
-   Use JSDOC to document methods and classes, including the [`@fires`](https://jsdoc.app/tags-fires.html) for events that are dispatched and [`@listens`](https://jsdoc.app/tags-listens.html) for events that are listened to.
