# Customising the menu item

You can use the following attributes and methods on the `ModelAdmin` class to alter the menu item used to represent your model in Wagtail's admin area.

```{contents}
---
local:
depth: 1
---
```

(modeladmin_menu_label)=

## `ModelAdmin.menu_label`

**Expected value**: A string.

Set this attribute to a string value to override the label used for the menu item that appears in Wagtail's sidebar. If not set, the menu item will use `verbose_name_plural` from your model's `Meta` data.

(modeladmin_menu_icon)=

## `ModelAdmin.menu_icon`

**Expected value**: A string matching one of Wagtail's icon class names.

If you want to change the icon used to represent your model, you can set the `menu_icon` attribute on your class to use one of the other icons available in Wagtail's CMS. The same icon will be used for the menu item in Wagtail's sidebar, and will also appear in the header on the list page and other views for your model. If not set, `'doc-full-inverse'` will be used for page-type models, and `'snippet'` for others.

If you're using a `ModelAdminGroup` class to group together several `ModelAdmin` classes in their own sub-menu, and want to change the menu item used to represent the group, you should override the `menu_icon` attribute on your `ModelAdminGroup` class (`'folder-open-inverse'` is the default).

(modeladmin_menu_order)=

## `ModelAdmin.menu_order`

**Expected value**: An integer between `1` and `999`.

If you want to change the position of the menu item for your model (or group of models) in Wagtail's sidebar, you do that by setting `menu_order`. The value should be an integer between `1` and `999`. The lower the value, the higher up the menu item will appear.

Wagtail's 'Explorer' menu item has an order value of `100`, so supply a value greater than that if you wish to keep the explorer menu item at the top.

(modeladmin_add_to_settings_menu)=

## `ModelAdmin.add_to_settings_menu`

**Expected value**: `True` or `False`

If you'd like the menu item for your model to appear in Wagtail's 'Settings' sub-menu instead of at the top level, add `add_to_settings_menu = True` to your `ModelAdmin` class.

This will only work for individual `ModelAdmin` classes registered with their own `modeladmin_register` call. It won't work for members of a `ModelAdminGroup`.

## `ModelAdmin.add_to_admin_menu`

**Expected value**: `True` or `False`

If you'd like this model admin to be excluded from the menu, set to `False`.
