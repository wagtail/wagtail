# Customizing admin templates

In your projects with Wagtail, you may wish to replace elements such as the Wagtail logo within the admin interface with your own branding. This can be done through Django's template inheritance mechanism.

You need to create a `templates/wagtailadmin/` folder within one of your apps - this may be an existing one or a new one created for this purpose, for example, `dashboard`. This app must be registered in `INSTALLED_APPS` before `wagtail.admin`:

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

The template blocks that are available to customize the branding in the admin interface are as follows:

### `branding_logo`

To replace the default logo, create a template file `dashboard/templates/wagtailadmin/base.html` that overrides the block `branding_logo`:

```html+django
{% extends "wagtailadmin/base.html" %}
{% load static %}

{% block branding_logo %}
    <img src="{% static 'images/custom-logo.svg' %}" alt="Custom Project" width="80" />
{% endblock %}
```

The logo also appears on the following pages and can be replaced with its template file:

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

(custom_user_profile_avatar)=

## Custom user profile avatar

To render a user avatar other than the one sourced from the `UserProfile` model or from [gravatar](https://gravatar.com/), you can use the [`get_avatar_url`](#get_avatar_url) hook and resolve the avatar's image url as you see fit.

For example, you might have an avatar on a `Profile` model in your own application that is keyed to the `auth.User` model in the familiar pattern. In that case, you could register your hook as the in following example, and the Wagtail admin avatar will be replaced with your own `Profile` avatar accordingly.

```python
@hooks.register('get_avatar_url')
def get_profile_avatar(user, size):
    return user.profile.avatar
```

Additionally, you can use the default `size` parameter that is passed in to the hook if you need to attach it to a request or do any further processing on your image.

(custom_user_interface_fonts)=

## Custom user interface fonts

To customize the font families used in the admin user interface, inject a CSS file using the hook [](insert_global_admin_css) and override the variables within the `:root` selector:

```css
:root {
    --w-font-sans: Papyrus;
    --w-font-mono: Courier;
}
```

(custom_user_interface_colors)=

## Custom user interface colors

```{warning}
The default Wagtail colors conform to the WCAG2.1 AA level color contrast requirements. When customizing the admin colors you should test the contrast using tools like [Axe](https://www.deque.com/axe/browser-extensions/).
```

To customize the colors used in the admin user interface, inject a CSS file using the hook [](insert_global_admin_css) and set the desired variables within the `:root` selector. Color variables are reused across both the light and dark themes of the admin interface. To change the colors of a specific theme, use:

-   `:root, .w-theme-light` for the light theme.
-   `.w-theme-dark` for the dark theme.
-   `@media (prefers-color-scheme: light) { .w-theme-system { […] }}` for the light theme via system settings.
-   `@media (prefers-color-scheme: dark) { .w-theme-system { […] }}` for the dark theme via system settings.

There are two ways to customize Wagtail’s color scheme:

-   Set static color variables, which are then reused in both light and dark themes across a wide number of UI components.
-   Set semantic colors, which are more numerous but allow customizing specific UI components.

For static colors, either set each color separately (for example `--w-color-primary: #2E1F5E;`); or separately set [HSL](https://en.wikipedia.org/wiki/HSL_and_HSV) (`--w-color-primary-hue`, `--w-color-primary-saturation`, `--w-color-primary-lightness`) variables so all shades are customized at once. For example, setting `--w-color-secondary-hue: 180;` will customize all of the secondary shades at once.

```{include} ../../_static/wagtail_colors_tables.txt

```

(custom_ui_information_density)=

## Custom UI information density

To customize information density of the admin user interface, inject a CSS file using the hook [](insert_global_admin_css). Set the `--w-density-factor` CSS variable to increase or reduce the UI density. The default value is `1`, the "snug" UI theming uses `0.5`. Here are example overrides:

```css
:root,
:host {
    /* Reduce the UI density by 20% for users of the default theme. */
    --w-density-factor: 0.8;
}

:root,
:host {
    /* Increase the UI density by 20% for users of the default theme. */
    --w-density-factor: 1.2;
}

.w-density-snug {
    /* For snug theme users, set a UI density even lower than vanilla Wagtail. */
    --w-density-factor: 0.25;
}
```

UI components which have been designed to use the `--w-density-factor` will increase in size or spacing accordingly.

## Specifying a site or page in the branding

The admin interface has a number of variables available to the renderer context that can be used to customize the branding in the admin page. These can be useful for customizing the dashboard on a multi-tenanted Wagtail installation:

### `root_page`

Returns the highest explorable page object for the currently logged-in user. If the user has no explore rights, this will default to `None`.

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

To add extra buttons to the login form, override the `submit_buttons` block. You will need to add `{{ block.super }}` somewhere in your block to include the sign-in button:

```html+django
{% extends "wagtailadmin/login.html" %}

{% block submit_buttons %}
    {{ block.super }}
    <a href="{% url 'signup' %}"><button type="button" class="button">{% trans 'Sign up' %}</button></a>
{% endblock %}
```

### `login_form`

To completely customize the login form, override the `login_form` block. This block wraps the whole contents of the `<form>` element:

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

## Extending client-side JavaScript

Wagtail provides multiple ways to [extend client-side JavaScript](extending_client_side).
