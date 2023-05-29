# Customising admin templates

In your projects with Wagtail, you may wish to replace elements such as the Wagtail logo within the admin interface with your own branding. This can be done through Django's template inheritance mechanism.

You need to create a `templates/wagtailadmin/` folder within one of your apps - this may be an existing one, or a new one created for this purpose, for example, `dashboard`. This app must be registered in `INSTALLED_APPS` before `wagtail.admin`:

```python
INSTALLED_APPS = (
    # ...

    'dashboard',

    'wagtail',
    'wagtail.admin',

    # ...
)
```

(custom_branding)=

## Custom branding

The template blocks that are available to customise the branding in the admin interface are as follows:

### `branding_logo`

To replace the default logo, create a template file `dashboard/templates/wagtailadmin/base.html` that overrides the block `branding_logo`:

```html+django
{% extends "wagtailadmin/base.html" %}
{% load static %}

{% block branding_logo %}
    <img src="{% static 'images/custom-logo.svg' %}" alt="Custom Project" width="80" />
{% endblock %}
```

The logo also appears in the following pages and can be replaced with its template file:

-   **login page** - create a template file `dashboard/templates/wagtailadmin/login.html` that overwrites the `branding_logo` block.
-   **404 error page** - create a template file `dashboard/templates/wagtailadmin/404.html` that overrides the `branding_logo` block.
-   **wagtail userbar** - create a template file `dashboard/templates/wagtailadmin/userbar/base.html` that overwrites the `branding_logo` block.

### `branding_favicon`

To replace the favicon displayed when viewing admin pages, create a template file `dashboard/templates/wagtailadmin/admin_base.html` that overrides the block `branding_favicon`:

```html+django
{% extends "wagtailadmin/admin_base.html" %}
{% load static %}

{% block branding_favicon %}
    <link rel="shortcut icon" href="{% static 'images/favicon.ico' %}" />
{% endblock %}
```

### `branding_title`

To replace the title prefix (which is 'Wagtail' by default), create a template file `dashboard/templates/wagtailadmin/admin_base.html` that overrides the block `branding_title`:

```html+django
{% extends "wagtailadmin/admin_base.html" %}

{% block branding_title %}Frank's CMS{% endblock %}
```

### `branding_login`

To replace the login message, create a template file `dashboard/templates/wagtailadmin/login.html` that overrides the block `branding_login`:

```html+django
{% extends "wagtailadmin/login.html" %}

{% block branding_login %}Sign in to Frank's Site{% endblock %}
```

### `branding_welcome`

To replace the welcome message on the dashboard, create a template file `dashboard/templates/wagtailadmin/home.html` that overrides the block `branding_welcome`:

```html+django
{% extends "wagtailadmin/home.html" %}

{% block branding_welcome %}Welcome to Frank's Site{% endblock %}
```

(custom_user_interface_fonts)=

## Custom user interface fonts

To customise the font families used in the admin user interface, inject a CSS file using the hook [](insert_global_admin_css) and override the variables within the `:root` selector:

```css
:root {
    --w-font-sans: Papyrus;
    --w-font-mono: Courier;
}
```

(custom_user_interface_colours)=

## Custom user interface colours

```{warning}
The default Wagtail colours conform to the WCAG2.1 AA level colour contrast requirements. When customising the admin colours you should test the contrast using tools like [Axe](https://www.deque.com/axe/browser-extensions/).
```

To customise the colours used in the admin user interface, inject a CSS file using the hook [](insert_global_admin_css) and set the desired variables within the `:root` selector. There are two ways to customisation options: either set each colour separately (for example `--w-color-primary: #2E1F5E;`); or separately set [HSL](https://en.wikipedia.org/wiki/HSL_and_HSV) (`--w-color-primary-hue`, `--w-color-primary-saturation`, `--w-color-primary-lightness`) variables so all shades are customised at once. For example, setting `--w-color-secondary-hue: 180;` will customise all of the secondary shades at once.

<section><div><!-- Auto-generated with Storybook. See https://github.com/wagtail/wagtail/blob/main/client/src/tokens/colors.stories.tsx. Copy this comment’s parent section to update the `custom_user_interface_colours` documentation. --></div><p>Make sure to test any customisations against our <a href="https://contrast-grid.eightshapes.com/?version=1.1.0&amp;es-color-form__tile-size=compact&amp;es-color-form__show-contrast=aaa&amp;es-color-form__show-contrast=aa&amp;es-color-form__show-contrast=aa18&amp;background-colors=%23000000%2C%20black%0D%0A%23F6F6F8%2C%20grey-50%0D%0A%23E0E0E0%2C%20grey-100%0D%0A%23C8C8C8%2C%20grey-150%0D%0A%23929292%2C%20grey-200%0D%0A%235C5C5C%2C%20grey-400%0D%0A%23333333%2C%20grey-500%0D%0A%23262626%2C%20grey-600%0D%0A%23FFFFFF%2C%20white%0D%0A%23261A4E%2C%20primary-200%0D%0A%232E1F5E%2C%20primary%0D%0A%23F2FCFC%2C%20secondary-50%0D%0A%2380D7D8%2C%20secondary-75%0D%0A%2300B0B1%2C%20secondary-100%0D%0A%23005B5E%2C%20secondary-400%0D%0A%23004345%2C%20secondary-600%0D%0A%23007D7E%2C%20secondary%0D%0A%23E2F5FC%2C%20info-50%0D%0A%231F7E9A%2C%20info-100%0D%0A%23E0FBF4%2C%20positive-50%0D%0A%231B8666%2C%20positive-100%0D%0A%23FFF5D8%2C%20warning-50%0D%0A%23FAA500%2C%20warning-100%0D%0A%23FDE9E9%2C%20critical-50%0D%0A%23FD5765%2C%20critical-100%0D%0A%23CD4444%2C%20critical-200&amp;foreground-colors=%23000000%2C%20black%0D%0A%23F6F6F8%2C%20grey-50%0D%0A%23E0E0E0%2C%20grey-100%0D%0A%23C8C8C8%2C%20grey-150%0D%0A%23929292%2C%20grey-200%0D%0A%235C5C5C%2C%20grey-400%0D%0A%23333333%2C%20grey-500%0D%0A%23262626%2C%20grey-600%0D%0A%23FFFFFF%2C%20white%0D%0A%23261A4E%2C%20primary-200%0D%0A%232E1F5E%2C%20primary%0D%0A%23F2FCFC%2C%20secondary-50%0D%0A%2380D7D8%2C%20secondary-75%0D%0A%2300B0B1%2C%20secondary-100%0D%0A%23005B5E%2C%20secondary-400%0D%0A%23004345%2C%20secondary-600%0D%0A%23007D7E%2C%20secondary%0D%0A%231F7E9A%2C%20info-100%0D%0A%231B8666%2C%20positive-100%0D%0A%23FAA500%2C%20warning-100%0D%0A%23FD5765%2C%20critical-100%0D%0A%23CD4444%2C%20critical-200">Contrast Grid</a>. Try out your own customisations with this interactive style editor:</p><style> :root {--w-color-black-hue: 0;--w-color-black-saturation: 0%;--w-color-black-lightness: 0%;--w-color-black: hsl(var(--w-color-black-hue) var(--w-color-black-saturation) var(--w-color-black-lightness));--w-color-grey-50-hue: calc(var(--w-color-grey-600-hue) + 240);--w-color-grey-50-saturation: calc(var(--w-color-grey-600-saturation) + 12.5%);--w-color-grey-50-lightness: calc(var(--w-color-grey-600-lightness) + 82%);--w-color-grey-50: hsl(var(--w-color-grey-50-hue) var(--w-color-grey-50-saturation) var(--w-color-grey-50-lightness));--w-color-grey-100-hue: var(--w-color-grey-600-hue);--w-color-grey-100-saturation: var(--w-color-grey-600-saturation);--w-color-grey-100-lightness: calc(var(--w-color-grey-600-lightness) + 72.9%);--w-color-grey-100: hsl(var(--w-color-grey-100-hue) var(--w-color-grey-100-saturation) var(--w-color-grey-100-lightness));--w-color-grey-150-hue: var(--w-color-grey-600-hue);--w-color-grey-150-saturation: var(--w-color-grey-600-saturation);--w-color-grey-150-lightness: calc(var(--w-color-grey-600-lightness) + 63.5%);--w-color-grey-150: hsl(var(--w-color-grey-150-hue) var(--w-color-grey-150-saturation) var(--w-color-grey-150-lightness));--w-color-grey-200-hue: var(--w-color-grey-600-hue);--w-color-grey-200-saturation: var(--w-color-grey-600-saturation);--w-color-grey-200-lightness: calc(var(--w-color-grey-600-lightness) + 42.4%);--w-color-grey-200: hsl(var(--w-color-grey-200-hue) var(--w-color-grey-200-saturation) var(--w-color-grey-200-lightness));--w-color-grey-400-hue: var(--w-color-grey-600-hue);--w-color-grey-400-saturation: var(--w-color-grey-600-saturation);--w-color-grey-400-lightness: calc(var(--w-color-grey-600-lightness) + 21.2%);--w-color-grey-400: hsl(var(--w-color-grey-400-hue) var(--w-color-grey-400-saturation) var(--w-color-grey-400-lightness));--w-color-grey-500-hue: var(--w-color-grey-600-hue);--w-color-grey-500-saturation: var(--w-color-grey-600-saturation);--w-color-grey-500-lightness: calc(var(--w-color-grey-600-lightness) + 5.1%);--w-color-grey-500: hsl(var(--w-color-grey-500-hue) var(--w-color-grey-500-saturation) var(--w-color-grey-500-lightness));--w-color-grey-600-hue: 0;--w-color-grey-600-saturation: 0%;--w-color-grey-600-lightness: 14.9%;--w-color-grey-600: hsl(var(--w-color-grey-600-hue) var(--w-color-grey-600-saturation) var(--w-color-grey-600-lightness));--w-color-white-hue: 0;--w-color-white-saturation: 0%;--w-color-white-lightness: 100%;--w-color-white: hsl(var(--w-color-white-hue) var(--w-color-white-saturation) var(--w-color-white-lightness));--w-color-primary-200-hue: calc(var(--w-color-primary-hue) - 0.5);--w-color-primary-200-saturation: calc(var(--w-color-primary-saturation) - 0.4%);--w-color-primary-200-lightness: calc(var(--w-color-primary-lightness) - 4.1%);--w-color-primary-200: hsl(var(--w-color-primary-200-hue) var(--w-color-primary-200-saturation) var(--w-color-primary-200-lightness));--w-color-primary-hue: 254.3;--w-color-primary-saturation: 50.4%;--w-color-primary-lightness: 24.5%;--w-color-primary: hsl(var(--w-color-primary-hue) var(--w-color-primary-saturation) var(--w-color-primary-lightness));--w-color-secondary-50-hue: calc(var(--w-color-secondary-hue) - 0.5);--w-color-secondary-50-saturation: calc(var(--w-color-secondary-saturation) - 37.5%);--w-color-secondary-50-lightness: calc(var(--w-color-secondary-lightness) + 72.2%);--w-color-secondary-50: hsl(var(--w-color-secondary-50-hue) var(--w-color-secondary-50-saturation) var(--w-color-secondary-50-lightness));--w-color-secondary-75-hue: calc(var(--w-color-secondary-hue) + 0.2);--w-color-secondary-75-saturation: calc(var(--w-color-secondary-saturation) - 47%);--w-color-secondary-75-lightness: calc(var(--w-color-secondary-lightness) + 42.8%);--w-color-secondary-75: hsl(var(--w-color-secondary-75-hue) var(--w-color-secondary-75-saturation) var(--w-color-secondary-75-lightness));--w-color-secondary-100-hue: calc(var(--w-color-secondary-hue) - 0.2);--w-color-secondary-100-saturation: var(--w-color-secondary-saturation);--w-color-secondary-100-lightness: calc(var(--w-color-secondary-lightness) + 10%);--w-color-secondary-100: hsl(var(--w-color-secondary-100-hue) var(--w-color-secondary-100-saturation) var(--w-color-secondary-100-lightness));--w-color-secondary-400-hue: calc(var(--w-color-secondary-hue) + 1.4);--w-color-secondary-400-saturation: var(--w-color-secondary-saturation);--w-color-secondary-400-lightness: calc(var(--w-color-secondary-lightness) - 6.3%);--w-color-secondary-400: hsl(var(--w-color-secondary-400-hue) var(--w-color-secondary-400-saturation) var(--w-color-secondary-400-lightness));--w-color-secondary-600-hue: calc(var(--w-color-secondary-hue) + 1.2);--w-color-secondary-600-saturation: var(--w-color-secondary-saturation);--w-color-secondary-600-lightness: calc(var(--w-color-secondary-lightness) - 11.2%);--w-color-secondary-600: hsl(var(--w-color-secondary-600-hue) var(--w-color-secondary-600-saturation) var(--w-color-secondary-600-lightness));--w-color-secondary-hue: 180.5;--w-color-secondary-saturation: 100%;--w-color-secondary-lightness: 24.7%;--w-color-secondary: hsl(var(--w-color-secondary-hue) var(--w-color-secondary-saturation) var(--w-color-secondary-lightness));--w-color-info-50-hue: calc(var(--w-color-info-100-hue) + 2.5);--w-color-info-50-saturation: calc(var(--w-color-info-100-saturation) + 14.8%);--w-color-info-50-lightness: calc(var(--w-color-info-100-lightness) + 57.4%);--w-color-info-50: hsl(var(--w-color-info-50-hue) var(--w-color-info-50-saturation) var(--w-color-info-50-lightness));--w-color-info-100-hue: 193.7;--w-color-info-100-saturation: 66.5%;--w-color-info-100-lightness: 36.3%;--w-color-info-100: hsl(var(--w-color-info-100-hue) var(--w-color-info-100-saturation) var(--w-color-info-100-lightness));--w-color-positive-50-hue: calc(var(--w-color-positive-100-hue) + 2.3);--w-color-positive-50-saturation: calc(var(--w-color-positive-100-saturation) + 10.6%);--w-color-positive-50-lightness: calc(var(--w-color-positive-100-lightness) + 61.5%);--w-color-positive-50: hsl(var(--w-color-positive-50-hue) var(--w-color-positive-50-saturation) var(--w-color-positive-50-lightness));--w-color-positive-100-hue: 162.1;--w-color-positive-100-saturation: 66.5%;--w-color-positive-100-lightness: 31.6%;--w-color-positive-100: hsl(var(--w-color-positive-100-hue) var(--w-color-positive-100-saturation) var(--w-color-positive-100-lightness));--w-color-warning-50-hue: calc(var(--w-color-warning-100-hue) - 2.3);--w-color-warning-50-saturation: calc(var(--w-color-warning-100-saturation) - 21.3%);--w-color-warning-50-lightness: calc(var(--w-color-warning-100-lightness) + 41.8%);--w-color-warning-50: hsl(var(--w-color-warning-50-hue) var(--w-color-warning-50-saturation) var(--w-color-warning-50-lightness));--w-color-warning-100-hue: 39.6;--w-color-warning-100-saturation: 100%;--w-color-warning-100-lightness: 49%;--w-color-warning-100: hsl(var(--w-color-warning-100-hue) var(--w-color-warning-100-saturation) var(--w-color-warning-100-lightness));--w-color-critical-50-hue: var(--w-color-critical-200-hue);--w-color-critical-50-saturation: calc(var(--w-color-critical-200-saturation) + 25.5%);--w-color-critical-50-lightness: calc(var(--w-color-critical-200-lightness) + 41.8%);--w-color-critical-50: hsl(var(--w-color-critical-50-hue) var(--w-color-critical-50-saturation) var(--w-color-critical-50-lightness));--w-color-critical-100-hue: calc(var(--w-color-critical-200-hue) + 354.9);--w-color-critical-100-saturation: calc(var(--w-color-critical-200-saturation) + 39.8%);--w-color-critical-100-lightness: calc(var(--w-color-critical-200-lightness) + 13.2%);--w-color-critical-100: hsl(var(--w-color-critical-100-hue) var(--w-color-critical-100-saturation) var(--w-color-critical-100-lightness));--w-color-critical-200-hue: 0;--w-color-critical-200-saturation: 57.8%;--w-color-critical-200-lightness: 53.5%;--w-color-critical-200: hsl(var(--w-color-critical-200-hue) var(--w-color-critical-200-saturation) var(--w-color-critical-200-lightness));} .wagtail-color-swatch { border-collapse: separate; border-spacing: 4px; } .wagtail-color-swatch td:first-child { height: 1.5rem; width: 1.5rem; border: 1px solid #333; forced-color-adjust: none; } </style><pre><style contenteditable="true" style="display: block;">:root {
  --w-color-primary: #2E1F5E;
  /* Any valid CSS format is supported. */
  --w-color-primary-200: hsl(253.8 50% 20.4%);
  /* Set each HSL component separately to change all hues at once. */
  --w-color-secondary-hue: 180.5;
  --w-color-secondary-saturation: 100%;
  --w-color-secondary-lightness: 24.7%;
}</style></pre><table class="wagtail-color-swatch"><thead><tr><th aria-label="Swatch"></th><th>Variable</th><th>Usage</th></tr></thead><tbody><tr><td style="background-color: var(--w-color-black);"></td><td><code>--w-color-black</code></td><td>Shadows only</td></tr><tr><td style="background-color: var(--w-color-grey-600);"></td><td><code>--w-color-grey-600</code></td><td>Body copy, user content</td></tr><tr><td style="background-color: var(--w-color-grey-500);"></td><td><code>--w-color-grey-500</code></td><td>Panels, dividers in dark mode</td></tr><tr><td style="background-color: var(--w-color-grey-400);"></td><td><code>--w-color-grey-400</code></td><td>Help text, placeholders, meta text, neutral state indicators</td></tr><tr><td style="background-color: var(--w-color-grey-200);"></td><td><code>--w-color-grey-200</code></td><td>Dividers, button borders</td></tr><tr><td style="background-color: var(--w-color-grey-150);"></td><td><code>--w-color-grey-150</code></td><td>Field borders</td></tr><tr><td style="background-color: var(--w-color-grey-100);"></td><td><code>--w-color-grey-100</code></td><td>Dividers, panel borders</td></tr><tr><td style="background-color: var(--w-color-grey-50);"></td><td><code>--w-color-grey-50</code></td><td>Background for panels, row highlights</td></tr><tr><td style="background-color: var(--w-color-white);"></td><td><code>--w-color-white</code></td><td>Page backgrounds, Panels, Button text</td></tr><tr><td style="background-color: var(--w-color-primary);"></td><td><code>--w-color-primary</code></td><td>Wagtail branding, Panels, Headings, Buttons, Labels</td></tr><tr><td style="background-color: var(--w-color-primary-200);"></td><td><code>--w-color-primary-200</code></td><td>Accent for elements used in conjunction with primary colour in sidebar</td></tr><tr><td style="background-color: var(--w-color-secondary);"></td><td><code>--w-color-secondary</code></td><td>Primary buttons, action links</td></tr><tr><td style="background-color: var(--w-color-secondary-600);"></td><td><code>--w-color-secondary-600</code></td><td>Hover states for two-tone buttons</td></tr><tr><td style="background-color: var(--w-color-secondary-400);"></td><td><code>--w-color-secondary-400</code></td><td>Two-tone buttons, hover states</td></tr><tr><td style="background-color: var(--w-color-secondary-100);"></td><td><code>--w-color-secondary-100</code></td><td>UI element highlights over dark backgrounds</td></tr><tr><td style="background-color: var(--w-color-secondary-75);"></td><td><code>--w-color-secondary-75</code></td><td>UI element highlights over dark text</td></tr><tr><td style="background-color: var(--w-color-secondary-50);"></td><td><code>--w-color-secondary-50</code></td><td>Button backgrounds, highlighted fields background</td></tr><tr><td style="background-color: var(--w-color-info-100);"></td><td><code>--w-color-info-100</code></td><td>Background and icons for information messages</td></tr><tr><td style="background-color: var(--w-color-info-50);"></td><td><code>--w-color-info-50</code></td><td>Background only, for information messages</td></tr><tr><td style="background-color: var(--w-color-positive-100);"></td><td><code>--w-color-positive-100</code></td><td>Positive states</td></tr><tr><td style="background-color: var(--w-color-positive-50);"></td><td><code>--w-color-positive-50</code></td><td>Background only, for positive states</td></tr><tr><td style="background-color: var(--w-color-warning-100);"></td><td><code>--w-color-warning-100</code></td><td>Background and icons for potentially dangerous states</td></tr><tr><td style="background-color: var(--w-color-warning-50);"></td><td><code>--w-color-warning-50</code></td><td>Background only, for potentially dangerous states</td></tr><tr><td style="background-color: var(--w-color-critical-200);"></td><td><code>--w-color-critical-200</code></td><td>Dangerous actions or states (over light background), errors</td></tr><tr><td style="background-color: var(--w-color-critical-100);"></td><td><code>--w-color-critical-100</code></td><td>Dangerous actions or states (over dark background)</td></tr><tr><td style="background-color: var(--w-color-critical-50);"></td><td><code>--w-color-critical-50</code></td><td>Background only, for dangerous states</td></tr></tbody></table></section>

Colour variables are reused across both the light and dark themes of the admin interface. To change the colours of a specific theme, use:

-   `.w-theme-light` for the light theme.
-   `.w-theme-dark` for the dark theme.
-   `@media (prefers-color-scheme: light) { .w-theme-system { […] }}` for the light theme via system settings.
-   `@media (prefers-color-scheme: dark) { .w-theme-system { […] }}` for the dark theme via system settings.

## Specifying a site or page in the branding

The admin interface has a number of variables available to the renderer context that can be used to customise the branding in the admin page. These can be useful for customising the dashboard on a multitenanted Wagtail installation:

### `root_page`

Returns the highest explorable page object for the currently logged in user. If the user has no explore rights, this will default to `None`.

### `root_site`

Returns the name on the site record for the above root page.

### `site_name`

Returns the value of `root_site`, unless it evaluates to `None`. In that case, it will return the value of `settings.WAGTAIL_SITE_NAME`.

To use these variables, create a template file `dashboard/templates/wagtailadmin/home.html`, just as if you were overriding one of the template blocks in the dashboard, and use them as you would any other Django template variable:

```html+django
{% extends "wagtailadmin/home.html" %}

{% block branding_welcome %}Welcome to the Admin Homepage for {{ root_site }}{% endblock %}
```

## Extending the login form

To add extra controls to the login form, create a template file `dashboard/templates/wagtailadmin/login.html`.

### `above_login` and `below_login`

To add content above or below the login form, override these blocks:

```html+django
{% extends "wagtailadmin/login.html" %}

{% block above_login %} If you are not Frank you should not be here! {% endblock %}
```

### `fields`

To add extra fields to the login form, override the `fields` block. You will need to add `{{ block.super }}` somewhere in your block to include the username and password fields:

```html+django
{% extends "wagtailadmin/login.html" %}

{% block fields %}
    {{ block.super }}
    <li>
        <div>
            <label for="id_two-factor-auth">Two factor auth token</label>
            <input type="text" name="two-factor-auth" id="id_two-factor-auth">
        </div>
    </li>
{% endblock %}
```

### `submit_buttons`

To add extra buttons to the login form, override the `submit_buttons` block. You will need to add `{{ block.super }}` somewhere in your block to include the sign in button:

```html+django
{% extends "wagtailadmin/login.html" %}

{% block submit_buttons %}
    {{ block.super }}
    <a href="{% url 'signup' %}"><button type="button" class="button">{% trans 'Sign up' %}</button></a>
{% endblock %}
```

### `login_form`

To completely customise the login form, override the `login_form` block. This block wraps the whole contents of the `<form>` element:

```html+django
{% extends "wagtailadmin/login.html" %}

{% block login_form %}
    <p>Some extra form content</p>
    {{ block.super }}
{% endblock %}
```

## Extending the password reset request form

To add extra controls to the password reset form, create a template file `dashboard/templates/wagtailadmin/account/password_reset/form.html`.

### `above_form` and `below_form`

To add content above or below the password reset form, override these blocks:

```html+django
{% extends "wagtailadmin/account/password_reset/form.html" %}

{% block above_login %} If you have not received your email within 7 days, call us. {% endblock %}
```

### `submit_buttons`

To add extra buttons to the password reset form, override the `submit_buttons` block. You will need to add `{{ block.super }}` somewhere in your block if you want to include the original submit button:

```html+django
{% extends "wagtailadmin/account/password_reset/form.html" %}

{% block submit_buttons %}
    <a href="{% url 'helpdesk' %}">Contact the helpdesk</a>
{% endblock %}
```

(extending_clientside_components)=

## Extending client-side components

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
