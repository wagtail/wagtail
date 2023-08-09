# Customising the base URL path

You can use the following attributes and methods on the `ModelAdmin` class to alter the base URL path used to represent your model in Wagtail's admin area.

```{contents}
---
local:
depth: 1
---
```

(modeladmin_base_url_path)=

## `ModelAdmin.base_url_path`

**Expected value**: A string.

Set this attribute to a string value to override the default base URL path used for the model to `admin/{base_url_path}`.
If not set, the base URL path will be `admin/{app_label}/{model_name}`.
