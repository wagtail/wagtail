# Custom user models

## Custom user forms example

This example shows how to add a text field and foreign key field to a custom user model
and configure Wagtail user forms to allow the fields values to be updated.

Create a custom user model. This must at minimum inherit from `AbstractBaseUser` and `PermissionsMixin`. In this case, we extend the `AbstractUser` class and add two fields. The foreign key references another model (not shown).

```python
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    country = models.CharField(verbose_name='country', max_length=255)
    status = models.ForeignKey(MembershipStatus, on_delete=models.SET_NULL, null=True, default=1)
```

Add the app containing your user model to `INSTALLED_APPS` - it must be above the `'wagtail.users'` line,
in order to override Wagtail's built-in templates - and set [AUTH_USER_MODEL](https://docs.djangoproject.com/en/stable/topics/auth/customizing/#substituting-a-custom-user-model) to reference
your model. In this example the app is called `users` and the model is `User`

```python
AUTH_USER_MODEL = 'users.User'
```

Create your custom user 'create' and 'edit' forms in your app:

```python
from django import forms
from django.utils.translation import gettext_lazy as _

from wagtail.users.forms import UserEditForm, UserCreationForm

from users.models import MembershipStatus


class CustomUserEditForm(UserEditForm):
    country = forms.CharField(required=True, label=_("Country"))
    status = forms.ModelChoiceField(queryset=MembershipStatus.objects, required=True, label=_("Status"))


class CustomUserCreationForm(UserCreationForm):
    country = forms.CharField(required=True, label=_("Country"))
    status = forms.ModelChoiceField(queryset=MembershipStatus.objects, required=True, label=_("Status"))
```

Extend the Wagtail user 'create' and 'edit' templates. These extended templates should be placed in a
template directory `wagtailusers/users`.

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
in the default templates. Other block-overriding options exist to allow appending
fields to the end or beginning of the existing fields or to allow all the fields to
be redefined.

Add the Wagtail settings to your project to reference the user form additions:

```python
WAGTAIL_USER_EDIT_FORM = 'users.forms.CustomUserEditForm'
WAGTAIL_USER_CREATION_FORM = 'users.forms.CustomUserCreationForm'
WAGTAIL_USER_CUSTOM_FIELDS = ['country', 'status']
```

```{versionadded} 6.2
The ability to customize the `UserViewSet` was added. Instead of customizing the forms via the `WAGTAIL_USER_EDIT_FORM`, `WAGTAIL_USER_CREATION_FORM`, and `WAGTAIL_USER_CUSTOM_FIELDS` settings, we recommend customizing them via the viewset instead, as explained below. The aforementioned settings might be deprecated in a future release.
```

(custom_userviewset)=

## Custom `UserViewSet`

Alternatively, you can also customize the forms and the views by creating a `UserViewSet` subclass. For example, with the above custom form classes, you can create the following `UserViewSet` subclass:

```python
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
from wagtail.users.apps import WagtailUsersAppConfig


class CustomUsersAppConfig(WagtailUsersAppConfig):
    user_viewset = "myapplication.someapp.viewsets.UserViewSet"
```

Replace `wagtail.users` in `settings.INSTALLED_APPS` with the path to `CustomUsersAppConfig`.

```python
INSTALLED_APPS = [
    ...,
    "myapplication.apps.CustomUsersAppConfig",
    # "wagtail.users",
    ...,
]
```

If you want to customize the group forms and views, see [](customizing_group_views).
