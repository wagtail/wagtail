Generic views
=============

Wagtail provides a number of generic views for handling common tasks such as creating / editing model instances, and chooser modals. Since these often involve several related views with shared properties (such as the model that we're working with, and its associated icon) Wagtail also implements the concept of a _viewset_, which allows a bundle of views to be defined collectively, and their URLs to be registered with the admin app as a single operation through the `register_admin_viewset` hook.

ModelViewSet
------------

The `wagtail.admin.viewsets.model.ModelViewSet` class provides the views for listing, creating, editing and deleting model instances. For example, if we have the following model:

```python
from django.db import models

class Person(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    def __str__(self):
        return "%s %s" % (self.first_name, self.last_name)
```

The following definition (to be placed in the same app's `views.py`) will generate a set of views for managing Person instances:

```python
from wagtail.admin.viewsets.model import ModelViewSet
from .models import Person


class PersonViewSet(ModelViewSet):
    model = Person
    form_fields = ["first_name", "last_name"]
    icon = "user"
```

This viewset can then be registered with the Wagtail admin to make it available under the URL `/admin/person/`, by adding the following to `wagtail_hooks.py`:

```python
from wagtail import hooks

from .views import PersonViewSet


@hooks.register("register_admin_viewset")
def register_viewset():
    return PersonViewSet("person")
```

Various additional attributes are available to customise the viewset - see [](../reference/viewsets).
