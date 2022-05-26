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
