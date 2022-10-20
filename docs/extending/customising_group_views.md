(customising_group_views)=

# Customising group edit/create views

The views for managing groups within the app are collected into a 'viewset' class, which acts as a single point of reference for all shared components of those views, such as forms. By subclassing the viewset, it is possible to override those components and customise the behaviour of the group management interface.

## Custom edit/create forms

This example shows how to customise forms on the 'edit group' and 'create group' views in the Wagtail admin.

Let's say you need to connect Active Directory groups with Django groups.
We create a model for Active Directory groups as follows:

```python
from django.contrib.auth.models import Group
from django.db import models


class ADGroup(models.Model):
    guid = models.CharField(verbose_name="GUID", max_length=64, db_index=True, unique=True)
    name = models.CharField(verbose_name="Group", max_length=255)
    domain = models.CharField(verbose_name="Domain", max_length=255, db_index=True)
    description = models.TextField(verbose_name="Description", blank=True, null=True)
    roles = models.ManyToManyField(Group, verbose_name="Role", related_name="adgroups", blank=True)

class Meta:
    verbose_name = "AD group"
    verbose_name_plural = "AD groups"
```

However, there is no role field on the Wagtail group 'edit' or 'create' view.
To add it, inherit from `wagtail.users.forms.GroupForm` and add a new field:

```python
from django import forms

from wagtail.users.forms import GroupForm as WagtailGroupForm

from .models import ADGroup


class GroupForm(WagtailGroupForm):
    adgroups = forms.ModelMultipleChoiceField(
        label="AD groups",
        required=False,
        queryset=ADGroup.objects.order_by("name"),
    )

    class Meta(WagtailGroupForm.Meta):
        fields = WagtailGroupForm.Meta.fields + ("adgroups",)

    def __init__(self, initial=None, instance=None, **kwargs):
        if instance is not None:
            if initial is None:
                initial = {}
            initial["adgroups"] = instance.adgroups.all()
        super().__init__(initial=initial, instance=instance, **kwargs)

    def save(self, commit=True):
        instance = super().save()
        instance.adgroups.set(self.cleaned_data["adgroups"])
        return instance
```

Now add your custom form into the group viewset by inheriting the default Wagtail `GroupViewSet` class and overriding the `get_form_class` method.

```python
from wagtail.users.views.groups import GroupViewSet as WagtailGroupViewSet

from .forms import GroupForm


class GroupViewSet(WagtailGroupViewSet):
    def get_form_class(self, for_update=False):
        return GroupForm
```

Add the field to the group 'edit'/'create' templates:

```html+django
{% extends "wagtailusers/groups/edit.html" %}
{% load wagtailusers_tags wagtailadmin_tags i18n %}

{% block extra_fields %}
    <li>{% include "wagtailadmin/shared/field.html" with field=form.adgroups %}</li>
{% endblock extra_fields %}
```

Finally, we configure the `wagtail.users` application to use the custom viewset, by setting up a custom `AppConfig` class. Within your project folder (which will be the package containing the top-level settings and urls modules), create `apps.py` (if it does not exist already) and add:

```python
from wagtail.users.apps import WagtailUsersAppConfig


class CustomUsersAppConfig(WagtailUsersAppConfig):
    group_viewset = "myapplication.someapp.viewsets.GroupViewSet"
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
