# Custom user models

## Custom user forms example

This example shows how to add a text field and foreign key field to a custom user model
and configure Wagtail user forms to allow the fields values to be updated.

Create a custom user model. This must at minimum inherit from `AbstractBaseUser` and `PermissionsMixin`. In this case we extend the `AbstractUser` class and add two fields. The foreign key references another model (not shown).

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
    {% include "wagtailadmin/shared/field_as_li.html" with field=form.country %}
    {% include "wagtailadmin/shared/field_as_li.html" with field=form.status %}
{% endblock extra_fields %}
```

Template edit.html:

```html+django
{% extends "wagtailusers/users/edit.html" %}

{% block extra_fields %}
    {% include "wagtailadmin/shared/field_as_li.html" with field=form.country %}
    {% include "wagtailadmin/shared/field_as_li.html" with field=form.status %}
{% endblock extra_fields %}
```

The `extra_fields` block allows fields to be inserted below the `last_name` field
in the default templates. Other block overriding options exist to allow appending
fields to the end or beginning of the existing fields, or to allow all the fields to
be redefined.

Add the wagtail settings to your project to reference the user form additions:

```python
WAGTAIL_USER_EDIT_FORM = 'users.forms.CustomUserEditForm'
WAGTAIL_USER_CREATION_FORM = 'users.forms.CustomUserCreationForm'
WAGTAIL_USER_CUSTOM_FIELDS = ['country', 'status']
```
