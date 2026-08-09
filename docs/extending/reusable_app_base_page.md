(reusable_app_base_page)=
# Adapting reusable apps to support custom base page models

Wagtail 8.0 introduces support for [custom base page models](custom_page_models), allowing site implementers to define their own project-specific page class to be used in place of the standard {class}`~wagtail.models.Page` model. This presents additional challenges for the developers of reusable packages, as the package can no longer rely on a known static import path for the page model.

The swappable page model is managed by the [`swapper`](https://github.com/openwisp/django-swappable-models) library. This should be added as a dependency of your package.

The active base page model can be obtained with `swapper.load_model("wagtailcore", "Page")`, and in most cases code can be adapted by replacing the import line

```python
from wagtail.models import Page
```

with:

```python
import swapper

Page = swapper.load_model("wagtailcore", "Page")
```

and leaving all subsequent references to `Page` unchanged. However, calling `swapper.load_model` is only valid after all models have been loaded, and doing this within a module that is imported during model loading will fail with the exception `django.core.exceptions.AppRegistryNotReady: Models aren't loaded yet.`. If the `Page` class is only used within a function or method body, this can be avoided by placing the `Page = swapper.load_model("wagtailcore", "Page")` line at the top of that function or method. For code intended to run on application startup, it may be appropriate to move this to the [`AppConfig.ready`](django.apps.AppConfig.ready) method. If the `Page` class is being used solely in an `isinstance` or `issubclass` test (for example, to provide alternative code paths for page and snippet objects), `AbstractPage` can be used instead as this is a common ancestor of all page models.

The page model's fully-qualified name (such as `"wagtailcore.Page"` or `"myapp.BasePage"`) can be obtained with `swapper.get_model_name("wagtailcore", "Page")`. Unlike `swapper.load_model`, this is valid within model definitions. For example, a foreign key to the page model can be written as:

```python
    page = models.ForeignKey(
        swapper.get_model_name("wagtailcore", "Page"), on_delete=models.CASCADE
    )
```

Note that the same change will also need to be made within migration files.

When using `swapper.get_model_name` in model code in this way, it is recommended to add this line to the top of the file (after the import lines):

```python
swapper.set_app_prefix("wagtailcore", "wagtail")
```

This configures the `swapper` library to look for the `WAGTAIL_PAGE_MODEL` setting when retrieving the model path. This configuration step is performed within the core `wagtail` app, but doing this within your own app too ensures that it properly takes effect in the case that your app is registered in `INSTALLED_APPS` above `wagtail`.

It is not possible to define `Page` subclasses within your reusable app in such a way that they will inherit from a custom page model when one is active. In this situation, the recommended approach is to implement the model's functionality in a mixin class (inheriting from [`models.Model`](django.db.models.Model) and defined as `abstract = True` in the `Meta` class) and define a `Page` subclass inheriting that mixin. Site implementers using the default `Page` model can then use your `Page` subclass as usual, while implementers using a custom page model can import the mixin and define a subclass of their own page model. See the [](form_builder) app for an example of this pattern.

Beyond direct references to the `Page` class, there are various places where the name of the page model emerges as an identifier within Wagtail code. As a result, there may be less obvious instances of the name `page` being hard-coded within your code, which can no longer be relied upon. In particular:

* The permission codenames that govern access to the page tree are derived from the class name - for example, if the base page model is `BasePage` then the permissions will be named `"add_basepage"`, `"change_basepage"`, `"publish_basepage"` and so on, rather than `"add_page"`, `"change_page"`, `"publish_page"`. The `django.contrib.auth.get_permission_codename` function can be used to obtain the correct codename; for example, if `Page` refers to the active page model (via the use of `swapper.load_model` as above), then `get_permission_codename("add", Page)` will return the appropriate codename.
* The `ContentType` record for pages (as used by permissions, the audit log and the reference index) corresponds to the active base page model, not necessarily `wagtailcore.Page`. Code such as `ContentType.objects.get(app_label="wagtailcore", model="page")` should now become `ContentType.objects.get(app_label=Page._meta.app_label, model=Page._meta.model_name)` (where `Page` has been obtained through `swapper.load_model` as before).
* The foreign key relation conventionally named `page_ptr`, created internally by Django to link from a specific page instance to its base page model counterpart, matches the name of the base class - for example, it will be `basepage_ptr` for a base page model named `BasePage`. This can be obtained using the following code:

```python
page_model_name = swapper.split(swapper.get_model_name("wagtailcore", "Page"))[1]
parent_rel_name = f"{page_model_name.lower()}_ptr"
base_page = getattr(specific_page, parent_rel_name)
```

Or if the base page model has been retrieved as `Page` via `swapper.load_model`:

```python
parent_rel_name = f"{Page._meta.object_name.lower()}_ptr"
base_page = getattr(specific_page, parent_rel_name)
```
