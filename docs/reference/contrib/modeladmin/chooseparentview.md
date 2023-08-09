# Customising `ChooseParentView`

When adding a new page via Wagtail's explorer view, you essentially choose where you want to add a new page by navigating the relevant part of the page tree and choosing to 'add a child page' to your chosen parent page. Wagtail then asks you to select what type of page you'd like to add.

When adding a page from a `ModelAdmin` list page, we know what type of page needs to be added, but we might not automatically know where in the page tree it should be added. If there's only one possible choice of parent for a new page (as defined by setting `parent_page_types` and `subpage_types` attributes on your models), then we skip a step and use that as the parent. Otherwise, the user must specify a parent page using modeladmin's `ChooseParentView`.

It should be very rare that you need to customise this view, but in case you do, modeladmin offers the following attributes that you can override:

```{contents}
---
local:
depth: 1
---
```

(modeladmin_choose_parent_template_name)=

## `ModelAdmin.choose_parent_template_name`

**Expected value**: The path to a custom template to use for `ChooseParentView`

See the following part of the docs to find out more: [](modeladmin_overriding_templates)

(modeladmin_choose_parent_view_class)=

## `ModelAdmin.choose_parent_view_class`

**Expected value**: A custom `view` class to replace `modeladmin.views.ChooseParentView`

See the following part of the docs to find out more: [](modeladmin_overriding_views)
