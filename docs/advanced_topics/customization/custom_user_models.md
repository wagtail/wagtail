# Custom user models

This page shows how to configure Wagtail to accommodate a custom user model.

## Creating a custom user model

This example uses a custom user model that adds a text field and foreign key field.

The custom user model must at minimum inherit from {class}`~django.contrib.auth.models.AbstractBaseUser` and {class}`~django.contrib.auth.models.PermissionsMixin`. In this case, we extend the {class}`~django.contrib.auth.models.AbstractUser` class and add two fields. The foreign key references another model (not shown).

```python
# myapp/models.py
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    country = models.CharField(verbose_name='country', max_length=255)
    status = models.ForeignKey(MembershipStatus, on_delete=models.SET_NULL, null=True, default=1)
```

Add the app containing your user model to `INSTALLED_APPS` - it must be above the `'wagtail.users'` line,
in order to override Wagtail's built-in templates - and set [`AUTH_USER_MODEL`](inv:django#auth-custom-user) to reference
your model. In this example the app is called `myapp` and the model is `User`.

```python
AUTH_USER_MODEL = 'myapp.User'
```

## Creating custom user forms

Now we need to configure Wagtail's user forms to allow the custom fields' values to be updated.
Create your custom user 'create' and 'edit' forms in your app:

```python
# myapp/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _

from wagtail.users.forms import UserEditForm, UserCreationForm

from myapp.models import MembershipStatus


class CustomUserEditForm(UserEditForm):
    status = forms.ModelChoiceField(queryset=MembershipStatus.objects, required=True, label=_("Status"))

    # Use ModelForm's automatic form fields generation for the model's `country` field,
    # but use an explicit custom form field for `status`.
    class Meta(UserEditForm.Meta):
        fields = UserEditForm.Meta.fields | {"country", "status"}


class CustomUserCreationForm(UserCreationForm):
    status = forms.ModelChoiceField(queryset=MembershipStatus.objects, required=True, label=_("Status"))

    # Use ModelForm's automatic form fields generation for the model's `country` field,
    # but use an explicit custom form field for `status`.
    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields | {"country", "status"}
```

## Extending the create and edit templates

Extend the Wagtail user 'create' and 'edit' templates. These extended templates should be placed in a
template directory `wagtailusers/users`.
Using a custom template directory is possible and will be explained later.

Template create.html:

```html+django
{% extends "wagtailusers/users/create.html" %}

{% block extra_fields %}
    <li>{% include "wagtailadmin/shared/field.html" with field=form.country %}</li>
    <li>{% include "wagtailadmin/shared/field.html" with field=form.status %}</li>
{% endblock extra_fields %}
```

Template edit.html:

```html+django
{% extends "wagtailusers/users/edit.html" %}

{% block extra_fields %}
    <li>{% include "wagtailadmin/shared/field.html" with field=form.country %}</li>
    <li>{% include "wagtailadmin/shared/field.html" with field=form.status %}</li>
{% endblock extra_fields %}
```

The `extra_fields` block allows fields to be inserted below the `last_name` field
in the default templates. There is a `fields` block that allows appending
fields to the end or beginning of the existing fields or to allow all the fields to
be redefined.

(custom_userviewset)=

## Creating a custom `UserViewSet`

To make use of the custom forms, create a `UserViewSet` subclass.

```python
# myapp/viewsets.py
from wagtail.users.views.users import UserViewSet as WagtailUserViewSet

from .forms import CustomUserCreationForm, CustomUserEditForm


class UserViewSet(WagtailUserViewSet):
    def get_form_class(self, for_update=False):
        if for_update:
            return CustomUserEditForm
        return CustomUserCreationForm
```

Then, configure the `wagtail.users` application to use the custom viewset, by setting up a custom `AppConfig` class. Within your project folder (which will be the package containing the top-level settings and urls modules), create `apps.py` (if it does not exist already) and add:

```python
# myproject/apps.py
from wagtail.users.apps import WagtailUsersAppConfig


class CustomUsersAppConfig(WagtailUsersAppConfig):
    user_viewset = "myapp.viewsets.UserViewSet"
```

Replace `wagtail.users` in `settings.INSTALLED_APPS` with the path to `CustomUsersAppConfig`.

```python
INSTALLED_APPS = [
    ...,
    # Make sure you have two separate entries for the following:
    "myapp",  # an app that contains the custom user model
    "myproject.apps.CustomUsersAppConfig",  # a custom app config for the wagtail.users app
    # "wagtail.users",  # this should be removed in favour of the custom app config
    ...,
]
```

```{warning}
You can also place the `WagtailUsersAppConfig` subclass inside the same `apps.py` file of your custom user model's app (instead of in a `myproject/apps.py` file), but you need to be careful. Make sure to use two separate config classes instead of turning your existing `AppConfig` subclass into a `WagtailUsersAppConfig` subclass, as that would cause Django to pick up your custom user model as being part of `wagtail.users`. You may also need to set {attr}`~django.apps.AppConfig.default` to `True` in your own app's `AppConfig`, unless you already use a dotted path to the app's `AppConfig` subclass in `INSTALLED_APPS`.
```

The `UserViewSet` class is a subclass of {class}`~wagtail.admin.viewsets.model.ModelViewSet` and thus it supports most of [the customizations available for `ModelViewSet`](generic_views). For example, you can use a custom directory for the templates by setting {attr}`~wagtail.admin.viewsets.model.ModelViewSet.template_prefix`:

```py
class UserViewSet(WagtailUserViewSet):
    template_prefix = "myapp/users/"
```

or customize the create and edit templates specifically:

```py
class UserViewSet(WagtailUserViewSet):
    create_template_name = "myapp/users/create.html"
    edit_template_name = "myapp/users/edit.html"
```

The group forms and views can be customized in a similar way – see [](customizing_group_views).
