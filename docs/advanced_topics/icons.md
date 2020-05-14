(icons)=

# Icons

Wagtail comes with an icon set. The icons are used throughout the admin interface.

Elements that use icons are:

- [Register Admin Menu Item](register_admin_menu_item)
- [Clientside components](extending_clientside_components)
- [Rich text editor toolbar buttons](extending_the_draftail_editor)
- [ModelAdmin menu](modeladmin_menu_icon)
- [Streamfield blocks](custom_streamfield_blocks)

This document describes how to choose and add icons.

## Available icons and their names

Icons are registered in `wagtail/admin/wagtail_hooks.py`. 
The _filename_ without the extension is the icon name.

Enable the [styleguide](styleguide) to view icons and their names.

[//]: # (The code is included to present an up-to-date icon name list)

```{eval-rst}
.. literalinclude:: ../../wagtail/admin/wagtail_hooks.py
   :language: python
   :pyobject: register_icons
```

## Add a custom icon

Draw or download an icon.

The `svg` tag should:

- Set `id="icon-<name>"` attribute, icons are referenced by this name 
- Set `xmlns="http://www.w3.org/2000/svg"` attribute
- Set `viewBox="..."` attribute
- Include license information if applicable

Set `<path fill="currentColor"` to give the icon the current color.

Example:

```{eval-rst}
.. literalinclude:: ../../wagtail/admin/templates/wagtailadmin/icons/angle-double-left.svg
   :language: xml
```

Add the icon to the icon set with the `register_icons` hook.

```python
@hooks.register("register_icons")
def register_icons(icons):
    return icons + ['path/to/rocket.svg']
```

## Changing icons via template override

When several applications provide different versions of the same template, the application listed first in `INSTALLED_APPS` has precedence.

Place your app before any Wagtail apps in `INSTALLED_APPS`.

Wagtail icons live in `wagtail/admin/templates/wagtailadmin/icons/`.
Place your own SVG files in `<your_app>/templates/wagtailadmin/icons/`.

## Changing icons via hooks

```python
@hooks.register("register_icons")
def register_icons(icons):
    icons.remove("wagtailadmin/icons/time.svg")  # Remove the original icon
    icons.append("path/to/time.svg")  # Add the new icon
    return icons
```

## Icon template tag

Use an icon in a custom template:

```html+django
{% load wagtailadmin_tags %}
{% icon name="rocket" classname="..." title="Launch" %}
```

## Icon font support

Use the `insert_global_admin_css` and reference your icons via `class_names`.
