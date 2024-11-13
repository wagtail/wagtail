# UI guidelines

Wagtail’s user interface is built with:

-   **HTML** using [Django templates](inv:django#ref/templates/language)
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
-   Use IDs for semantics only, classes for styling, `data-` attributes for JavaScript behavior.
-   Order attributes with `id` first, then `class`, then any `data-` or other attributes with Stimulus `data-controller` first.
-   For comments, use [Django template syntax](inv:django#template-comments) instead of HTML.

## CSS guidelines

We use [Prettier](https://prettier.io/) for formatting and [Stylelint](https://stylelint.io/) for linting.

-   We follow [BEM](https://getbem.com/) and [ITCSS](https://www.xfive.co/blog/itcss-scalable-maintainable-css-architecture/), with a large amount of utilities created with [Tailwind](https://tailwindcss.com/).
-   Familiarise yourself with our [stylelint-config-wagtail](https://github.com/wagtail/stylelint-config-wagtail) configuration, which details our preferred code style.
-   Use `rems` for `font-size`, because they offer absolute control over text. Additionally, unit-less `line-height` is preferred because it does not inherit a percentage value of its parent element, but instead is based on a multiplier of the `font-size`.
-   Always use variables for design tokens such as colors or font sizes, rather than hard-coding specific values.
-   We use the `w-` prefix for all styles intended to be reusable by Wagtail site implementers.

### Stylesheets

Most of our styles are combined into a single main stylesheet, `core.css`. This is the recommended approach for all new styles, to reduce potential style clashes, and encourage reuse of utilities and component styles between views. Imports within `core.scss` are structured according to ITCSS. There are two major exceptions to the ITCSS structure:

-   Legacy vendor CSS in `vendor/` is imported in the order it was loaded in before adding in the main stylesheet, to avoid compatibility issues. If possible, those styles should be converted to components and loaded further down the cascade.
-   Legacy layout-specific styles in `layouts/` are imported at the very end of the file, matching how styles were previously loaded across multiple stylesheets. If possible, those styles should be converted to components or utilities and loaded further up the cascade.

When creating new styles, always prefer components, adding a new stylesheet in the `components` folder and importing it in `core.scss`.

### Global styles

For all of our styles, we use:

-   A very old version of `normalize.css` as a CSS reset.
-   `box-sizing: border-box`, with elements always inheriting the `box-sizing` of their parent.
-   Global CSS variables for colors, so they can be changed by site implementers.
-   Global CSS variables for font family, so they can be changed by site implementers.
-   A `--w-direction-factor` CSS variable, set to `1` by default and `-1` for RTL languages, to allow reversing of calculations of physical values (transforms, background positions) and mirroring of icons and visuals with directional elements like arrows.
-   The `--w-density-factor` CSS variable, to let users control the information density of the UI. Set to `1` by default, and lower or higher values to reduce or increase the spacing and size of UI elements.

### Tailwind usage

We use [Tailwind](https://tailwindcss.com/) to manage our design tokens via its theme, and generate CSS utilities. It is configured in `tailwind.config.js`, with a base configuration intended to be reusable in other projects.

Wagtail uses most of Tailwind’s core plugins, with an override for them to create [Logical properties and values](https://rtlstyling.com/posts/rtl-styling#css-logical-properties) styles while still using Tailwind’s default utility and design token names.

With utility classes, we recommend to:

-   Keep their number to a reasonable maximum, creating component styles instead if the utilities are inter-dependent, or if they are frequently reused together.
-   Avoid utilities relating to font size, weight, or other typographic considerations. Instead, use the higher-level type scale as defined in `typography.js`.

### Sass usage

We keep our Sass usage to a minimum, preferring verbose vanilla CSS over advanced Sass syntax. Here are specific Sass features to completely avoid:

-   Placeholders / `@extend`. Leads to unexpected cascading of styles.
-   Color manipulation. All of our colors are defined in JavaScript via Tailwind, to generate CSS variable definitions and documentation consistently.

And Sass features to use with caution:

-   Sass nesting. Avoid relying on Sass nesting specifically, and overly specific selectors. Most styles can be written with either one or two levels of nesting, 3 for specific UI states, and 4 in the most complex scenarios only.
-   Parent selector (`&`) interpolation. Only use interpolation in class names sparingly, so we can more easily search for styles across the project.
-   Sass variables. Prefer Tailwind theme variables to reuse our design tokens, or CSS variables when a specific property changes based on state. Sass variables should only be used as shorter aliases for those scenarios, or as local component variables.
-   Mixins. Only create new mixins if the styles can’t be written as reusable component or utility styles.
-   Sass math. With most of our design tokens defined in Tailwind, loaded via PostCSS, we use `calc` functions for math operations rather than Sass.

### Forced colors mode

Also known as Windows High Contrast mode, or Contrast Themes. This is a feature of Windows for users to override websites’ styles with their own, so text is more readable. We intend to fully support it in all of our styles. Here are recommended practices:

-   Add additional borders where the background color would otherwise convey the position of specific elements, particularly for page regions and components layered above the page.
-   Overrides with `@media (forced-colors: active)` should only be used when there is no simpler alternative. Write CSS for WHCM support from the get-go rather than with sweeping overrides.
-   Never use `forced-color-adjust: none`. It compromises compatibility with a wide range of custom themes, and should only be needed if a component relies on a specific color hue to work (which is an anti-pattern).

## JavaScript guidelines

We use [Prettier](https://prettier.io/) for formatting and [ESLint](https://eslint.org/) for linting.

-   We follow a somewhat relaxed version of the [Airbnb styleguide](https://github.com/airbnb/javascript).
-   Familiarise yourself with our [eslint-config-wagtail](https://github.com/wagtail/eslint-config-wagtail) configuration, which details our preferred code style.

(ui_guidelines_stimulus)=

## Stimulus

Wagtail uses [Stimulus](https://stimulus.hotwired.dev/) as a lightweight framework to attach interactive behavior to DOM elements via `data-` attributes.

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
3. For initialization, consider which [controller lifecycle methods](https://stimulus.hotwired.dev/reference/lifecycle-callbacks#methods) to use, if any (`connect`, `initialize`).
4. If relevant, also consider how to handle the controlled element being removed from the DOM [`disconnect` lifecycle method](https://stimulus.hotwired.dev/reference/lifecycle-callbacks#disconnection).
5. Document controller classes and methods with [JSDoc annotations](https://jsdoc.app/index.html).
6. Use [values](https://stimulus.hotwired.dev/reference/values) to provide options and also reactive state, avoiding instance properties if possible. Prefer falsey or empty defaults and avoid too much usage of the Object type when using values.
7. Build the behavior around small, discrete, methods and use [Stimulus actions](https://stimulus.hotwired.dev/reference/actions) declared in HTML to drive when they are called.

### Helpful tips

-   Prefer controllers that do a small amount of 'work' that is collected together, instead of lots of large or specific controllers.
-   Lean towards dispatching events for key behavior in the UI interaction as this provides a great way for custom code to hook into this without an explicit API, but be sure to document these.
-   Multiple controllers can be attached to one DOM element for composing behavior, where practical split out behavior to separate controllers.
-   Consider when to document controller usage for non-contributors.
-   When writing unit tests, note that DOM updates triggered by data attribute changes are completed async (next `microtick`) so will require a await Promise or similar to check for the changes in JSDom.
-   Avoid hard-coding a controller's identifier, instead reference it with `this.identifier` if adjusting attributes. This way the controller can be used easily with a changed identifier or extended by other classes in the future.

## Multilingual support

This is an area of active improvement for Wagtail, with [ongoing discussions](https://github.com/wagtail/wagtail/discussions/8017).

-   Always use the `trimmed` attribute on `blocktranslate` tags to prevent unnecessary whitespace from being added to the translation strings.

### Right-to-left language support

We support right-to-left languages, and in particular viewing the Wagtail admin interface in a horizontally mirrored layout. Here are guidelines to guarantee support:

-   Write styles with [logical properties and values](https://rtlstyling.com/posts/rtl-styling#css-logical-properties) whenever possible.
-   For styles that can only be written with physical properties (translations, background positions), use the `--w-direction-factor` variable equal to 1 or -1 so the value reverses based on the `dir` attribute of the element or page.
-   As a last resort, use `[dir='rtl']` style if there is no other way to write styles.

Make sure to also reverse the direction of any position calculation in JavaScript, as there is no support of logical values in DOM APIs (x-axis offsets always from the left).

## Icons

We use inline SVG elements for Wagtail’s icons, for performance and so icons can be styled with CSS. View [](icons) for information on how icons are set up for Wagtail users.

### Adding icons

Icons are SVG files in the [Wagtail admin template folder](https://github.com/wagtail/wagtail/tree/main/wagtail/admin/templates/wagtailadmin/icons).

When adding or updating an icon,

1. Run it through [SVGO](https://jakearchibald.github.io/svgomg/) with appropriate compression settings.
2. Manually remove any unnecessary attributes. Set the `viewBox` attribute, and remove `width` and `height` attributes.
3. Manually add its `id` attribute with a prefix of `icon-` and the icon name matching the file name. Keep the icon as named from its source if possible.
4. Add or preserve licensing information as an HTML comment starting with an exclamation mark: `<!--! Icon license -->`. For Font Awesome, we want: `<!--! [icon name] ([icon style]): Font Awesome [version] -->`. For example, `<!--! triangle-exclamation (solid): Font Awesome Pro 6.4.0 -->`.
5. Add the icon to Wagtail’s own implementation of the `register_icons` hook, in alphabetical order.
6. Go to the styleguide and copy the Wagtail icons table according to instructions in the template, pasting the result in `wagtail_icons_table.txt`.
7. If the icon requires [right-to-left mirroring](https://rtlstyling.com/posts/rtl-styling#bidirectional-icons), add the `class="icon--directional"` attribute.
