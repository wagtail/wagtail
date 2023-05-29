# UI Guidelines

Wagtail’s user interface is built with:

-   **HTML** using [Django templates](django:ref/templates/language)
-   **CSS** using [Sass](https://sass-lang.com/) and [Tailwind](https://tailwindcss.com/)
-   **JavaScript** with [TypeScript](https://www.typescriptlang.org/)
-   **SVG** for our icons, minified with [SVGO](https://jakearchibald.github.io/svgomg/)

## Linting and formatting

Here are the available commands:

-   `make lint` will run all linting, `make lint-server` lints templates, and `make lint-client` lints JS/CSS.
-   `make format` will run all formatting and fixing of linting issues. There is also `make format-server` and `make format-client`.

Have a look at our `Makefile` tasks and `package.json` scripts if you prefer more granular options.

## HTML guidelines

We use [djhtml](https://github.com/rtts/djhtml) for formatting and [Curlylint](https://www.curlylint.org/) for linting.

-   Write [valid](https://validator.w3.org/nu/), [semantic](https://html5doctor.com/element-index/) HTML.
-   Follow [ARIA authoring practices](https://w3c.github.io/aria-practices/), in particular, [No ARIA is better than Bad ARIA](https://w3c.github.io/aria-practices/#no_aria_better_bad_aria).
-   Use IDs for semantics only, classes for styling, `data-` attributes for JavaScript behaviour.
-   Order attributes with `id` first, then `class`, then any `data-` or other attributes with Stimulus `data-controller` first.
-   For comments, use [Django template syntax](https://docs.djangoproject.com/en/stable/ref/templates/language/#comments) instead of HTML.

## CSS guidelines

We use [Prettier](https://prettier.io/) for formatting and [Stylelint](https://stylelint.io/) for linting.

-   We follow [BEM](https://getbem.com/) and [ITCSS](https://www.xfive.co/blog/itcss-scalable-maintainable-css-architecture/), with a large amount of utilities created with [Tailwind](https://tailwindcss.com/).
-   Familiarise yourself with our [stylelint-config-wagtail](https://github.com/wagtail/stylelint-config-wagtail) configuration, which details our preferred code style.
-   Use `rems` for `font-size`, because they offer absolute control over text. Additionally, unit-less `line-height` is preferred because it does not inherit a percentage value of its parent element, but instead is based on a multiplier of the `font-size`.
-   Always use variables for design tokens such as colours or font sizes, rather than hard-coding specific values.
-   We use the `w-` prefix for all styles intended to be reusable by Wagtail site implementers.

## JavaScript guidelines

We use [Prettier](https://prettier.io/) for formatting and [ESLint](https://eslint.org/) for linting.

-   We follow a somewhat relaxed version of the [Airbnb styleguide](https://github.com/airbnb/javascript).
-   Familiarise yourself with our [eslint-config-wagtail](https://github.com/wagtail/eslint-config-wagtail) configuration, which details our preferred code style.

(ui_guidelines_stimulus)=

## Stimulus

Wagtail uses [Stimulus](https://stimulus.hotwired.dev/) as a lightweight framework to attach interactive behaviour to DOM elements via `data-` attributes.

### Why Stimulus

Stimulus is a lightweight framework that allows developers to create interactive UI elements in a simple way. It makes it easy to do small-scale reactivity via changes to data attributes and does not require developers to 'init' things everywhere, unlike JQuery. It also provides an alternative to using inline script tag usage and window globals which reduces complexity in the codebase.

### When to use Stimulus

Stimulus is our [preferred library](https://github.com/wagtail/rfcs/pull/78) for simple client-side interactivity. It’s a good fit when:

-   The interactivity requires JavaScript. Otherwise, consider using HTML and CSS only.
-   Some of the logic is defined via HTML templates, not just JavaScript.
-   The interactivity is simple, and doesn’t require usage of more heavyweight libraries like React.

Wagtail’s admin interface also leverages jQuery for similar scenarios. This is considered legacy and will eventually be removed. For new features, carefully consider whether existing jQuery code should be reused, or whether a rebuild with Stimulus is more appropriate.

### How to build a Stimulus controller

First think of how to name the controller. Keep it concise, one or two words ideally. Then,

1. Start with the HTML templates, build as much of the UI as you can in HTML alone. Ensure it is accessible and follows the CSS guidelines.
2. Create the controller file in our `client/src/controllers` folder, along with its tests (see [](testing)) and Storybook stories.
3. For initialisation, consider which [controller lifecycle methods](https://stimulus.hotwired.dev/reference/lifecycle-callbacks#methods) to use, if any (`connect`, `initialize`).
4. If relevant, also consider how to handle the controlled element being removed from the DOM [`disconnect` lifecycle method](https://stimulus.hotwired.dev/reference/lifecycle-callbacks#disconnection).
5. Document controller classes and methods with [JSDoc annotations](https://jsdoc.app/index.html).
6. Use [values](https://stimulus.hotwired.dev/reference/values) to provide options and also reactive state, avoiding instance properties if possible. Prefer falsey or empty defaults and avoid too much usage of the Object type when using values.
7. Build the behaviour around small, discrete, methods and use [Stimulus actions](https://stimulus.hotwired.dev/reference/actions) declared in HTML to drive when they are called.

### Helpful tips

-   Prefer controllers that do a small amount of 'work' that is collected together, instead of lots of large or specific controllers.
-   Lean towards dispatching events for key behaviour in the UI interaction as this provides a great way for custom code to hook into this without an explicit API, but be sure to document these.
-   Multiple controllers can be attached to one DOM element for composing behaviour, where practical split out behaviour to separate controllers.
-   Consider when to document controller usage for non-contributors.
-   When writing unit tests, note that DOM updates triggered by data attribute changes are completed async (next `microtick`) so will require a await Promise or similar to check for the changes in JSDom.
-   Avoid hard-coding a controller's identifier, instead reference it with `this.identifier` if adjusting attributes. This way the controller can be used easily with a changed identifier or extended by other classes in the future.

## Multilingual support

This is an area of active improvement for Wagtail, with [ongoing discussions](https://github.com/wagtail/wagtail/discussions/8017).

-   Always use the `trimmed` attribute on `blocktranslate` tags to prevent unnecessary whitespace from being added to the translation strings.

## SVG icons

We use inline SVG elements for Wagtail’s icons, for performance and so icons can be styled with CSS. View [](icons) for information on how icons are set up for Wagtail users.

### Adding icons

Icons are SVG files in the [Wagtail admin template folder](https://github.com/wagtail/wagtail/tree/main/wagtail/admin/templates/wagtailadmin/icons).

When adding or updating an icon,

1. Run it through [SVGO](https://jakearchibald.github.io/svgomg/) with appropriate compression settings.
2. Manually remove any unnecessary attributes.
3. Manually add its `id` attribute with a prefix of `icon-` and the icon name matching the file name. Keep the icon as named from its source if possible.
4. Add or preserve licensing information as a HTML comment starting with an exclamation mark: `<!--! Icon license -->`. For Font Awesome, we want: `<!--! [icon name] ([icon style]): Font Awesome [version] -->`. For example, `<!--! triangle-exclamation (solid): Font Awesome Pro 6.4.0 -->`.
5. Add the icon to Wagtail’s own implementation of the `register_icons` hook, in alphabetical order.
6. Go to the styleguide and copy the Wagtail icons table according to instructions in the template, pasting the result in `wagtail_icons_table.txt`.
