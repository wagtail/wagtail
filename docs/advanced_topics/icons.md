(icons)=

# Icons

Wagtail comes with an SVG icon set. The icons are used throughout the admin interface.

Elements that use icons are:

-   [Register Admin Menu Item](register_admin_menu_item)
-   [Client-side React components](extending_client_side_react)
-   [Rich text editor toolbar buttons](extending_the_draftail_editor)
-   [Snippets](wagtailsnippets_icon)
-   [StreamField blocks](custom_streamfield_blocks)

This document describes how to choose, add and customize icons.

## Add a custom icon

Draw or download an icon and save it in a template folder:

```xml
# app/templates/app_name/toucan.svg

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" id="icon-toucan">
  <!--! CC0 license. https://creativecommons.org/publicdomain/zero/1.0/ -->
  <path d="M321 662v1a41 41 0 1 1-83-2V470c0-129 71-221 222-221 122 0 153-42 153-93 0-34-18-60-53-72v-4c147 23 203 146 203 257 0 107-80 247-277 247v79a41 41 0 1 1-82-1v46a41 41 0 0 1-83 0v-46Z"/>
  <path d="M555 136a23 23 0 1 0-46 0 23 23 0 0 0 46 0Zm-69-57H175c-60 0-137 36-137 145l9-8 367 6 72 18V79Z"/>
</svg>
```

The `svg` tag should:

-   Set the `id="icon-<name>"` attribute, icons are referenced by this `name`. The `name` should only contain lowercase letters, numbers, and hyphens.
-   Set the `xmlns="http://www.w3.org/2000/svg"` attribute.
-   Set the `viewBox="..."` attribute, and no `width` and `height` attributes.
-   If the icon should be mirrored in right-to-left (RTL) languages, set the `class="icon--directional"` attribute.
-   Include license / source information in a `<!--! -->` HTML comment, if applicable.

Set `fill="currentColor"` or remove `fill` attributes so the icon color changes according to usage.

Add the icon with the `register_icons` hook.

```python
@hooks.register("register_icons")
def register_icons(icons):
    return icons + ['app_name/toucan.svg']
```

The majority of Wagtail’s default icons are drawn on a 16x16 viewBox, sourced from the [FontAwesome v6 free icons set](https://fontawesome.com/v6/search?m=free).

## Icon template tag

Use an icon in a custom template:

```html+django
{% load wagtailadmin_tags %}
{% icon name="toucan" classname="..." title="..." %}
```

## Changing icons via hooks

```python
@hooks.register("register_icons")
def register_icons(icons):
    icons.remove("wagtailadmin/icons/time.svg")  # Remove the original icon
    icons.append("path/to/time.svg")  # Add the new icon
    return icons
```

## Changing icons via template override

When several applications provide different versions of the same template, the application listed first in `INSTALLED_APPS` has precedence.

Place your app before any Wagtail apps in `INSTALLED_APPS`.

Wagtail icons live in `wagtail/admin/templates/wagtailadmin/icons/`.
Place your own SVG files in `<your_app>/templates/wagtailadmin/icons/`.

(custom_icons_userbar)=

### Using custom icons in the userbar

The userbar provides quick actions within page views when logged in. To customize the items shown in the user bar, you can use the [`construct_wagtail_userbar`](construct_wagtail_userbar) hook. If you want to use custom icons within these menu items they must be made available in the correct template.

```html+django
{# <yourapp>/templates/wagtailadmin/userbar/base.html #}
{% extends "wagtailadmin/userbar/base.html" %}

{% block icons %}
    {{ block.super }}
    {% include "wagtailadmin/icons/toucan.svg" %}
{% endblock %}
```

(available_icons)=

## Available icons

Enable the [styleguide](styleguide) to view the available icons and their names for any given project.

Here are all available icons out of the box:

<details open="">

<summary>Toggle icons table</summary>

```{include} ../_static/wagtail_icons_table.txt

```

</details>
