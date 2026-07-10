(permissions_reference)=

# Permissions

```{note}
This document covers the internals of Wagtail's permissions system. You should read about [how Wagtail makes use of Django's permissions system](permissions_overview) first.

Please note that aside from the {func}`~wagtail.permissions.register_permission_policy` function, the APIs described in this document are considered internal and thus are not subject to our [](deprecation_policy).
```

At the basic level, Wagtail's permission system is implemented using a set of classes called "permission policies" that define the permission rules for a given Django model. Whenever a permission test is performed, a global registry is consulted to determine the permission policy instance to use for a given Django model. As such, any model managed within Wagtail should register a corresponding permission policy instance to the global registry.

Other supporting code (not documented here) is used by pages and snippets to cater for more specific permission checks needed by features such as publishing, locking, and workflows. As a result, the following should not be considered a comprehensive documentation of how Wagtail does permission checks.

## Permission policies

```{eval-rst}
.. autoclass:: wagtail.permission_policies.BasePermissionPolicy

   .. automethod:: get_all_permissions_for_user
   .. automethod:: get_cached_permissions_for_user
   .. automethod:: user_has_permission
   .. automethod:: user_has_any_permission
   .. automethod:: users_with_any_permission
   .. automethod:: users_with_permission
   .. automethod:: user_has_permission_for_instance
   .. automethod:: user_has_any_permission_for_instance
   .. automethod:: instances_user_has_any_permission_for
   .. automethod:: instances_user_has_permission_for
   .. automethod:: users_with_any_permission_for_instance
   .. automethod:: users_with_permission_for_instance

.. autoclass:: wagtail.permission_policies.BaseDjangoAuthPermissionPolicy

.. autoclass:: wagtail.permission_policies.ModelPermissionPolicy

.. autoclass:: wagtail.permission_policies.OwnershipPermissionPolicy

.. autoclass:: wagtail.permission_policies.collections.CollectionPermissionPolicy

.. autoclass:: wagtail.permission_policies.collections.CollectionOwnershipPermissionPolicy

.. autoclass:: wagtail.permission_policies.collections.CollectionManagementPermissionPolicy

.. autoclass:: wagtail.permission_policies.pages.PagePermissionPolicy

.. autoclass:: wagtail.permission_policies.sites.SitePermissionPolicy
```

## Permission policy registry

```{eval-rst}
.. autoclass:: wagtail.permissions.PolicyRegistry

   .. automethod:: get_by_type
   .. automethod:: get

.. autodata:: wagtail.permissions.policies_registry
```

Retrieving a permission policy for a given Django model class or instance can be done as below.

```py
from wagtail.permissions import policies_registry
from .models import MyModel

# With the model class
policies_registry.get_by_type(MyModel)
# With a model instance
policies_registry.get(MyModel.objects.first())
```

```{eval-rst}
.. autofunction:: wagtail.permissions.register_permission_policy
```

To register a permission policy for a model, call this function at the top of
the model app's `wagtail_hooks.py`.

```py
# wagtail_hooks.py
from wagtail.permissions import register_permission_policy
from .models import MyModel


register_permission_policy(MyModel)
...  # More customizations
```

Alternatively, you can also call the function from the
[`AppConfig.ready()`](django.apps.AppConfig.ready) method.

```py
# apps.py
class MyAppConfig(AppConfig):
    ...

    def ready(self):
        from wagtail.permissions import register_permission_policy
        from .models import MyModel

        register_permission_policy(MyModel)
```

```{note}
Currently, `register_permission_policy(MyModel)` is the only officially supported use case of this function.

While it is possible to register a custom permission policy instance for any model (including Wagtail's built-in models), we cannot guarantee that a custom permissions implementation would always be respected by Wagtail. We intend to support this in the future. Refer to our issue tracker for [supporting custom permission behavior](https://github.com/wagtail/wagtail/issues/2907) for more details.
```
