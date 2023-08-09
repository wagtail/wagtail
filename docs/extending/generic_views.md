# Generic views

Wagtail provides several generic views for handling common tasks such as creating / editing model instances and chooser modals. Since these often involve several related views with shared properties (such as the model that we're working with, and its associated icon) Wagtail also implements the concept of a _viewset_, which allows a bundle of views to be defined collectively, and their URLs to be registered with the admin app as a single operation through the `register_admin_viewset` hook.

## ModelViewSet

The `wagtail.admin.viewsets.model.ModelViewSet` class provides the views for listing, creating, editing, and deleting model instances. For example, if we have the following model:

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


person_viewset = PersonViewSet("person")  # defines /admin/person/ as the base URL
```

This viewset can then be registered with the Wagtail admin to make it available under the URL `/admin/person/`, by adding the following to `wagtail_hooks.py`:

```python
from wagtail import hooks

from .views import person_viewset


@hooks.register("register_admin_viewset")
def register_viewset():
    return person_viewset
```

Various additional attributes are available to customise the viewset - see [](../reference/viewsets).

## ChooserViewSet

The `wagtail.admin.viewsets.chooser.ChooserViewSet` class provides the views that make up a modal chooser interface, allowing users to select from a list of model instances to populate a ForeignKey field. Using the same `Person` model, the following definition (to be placed in `views.py`) will generate the views for a person chooser modal:

```python
from wagtail.admin.viewsets.chooser import ChooserViewSet


class PersonChooserViewSet(ChooserViewSet):
    # The model can be specified as either the model class or an "app_label.model_name" string;
    # using a string avoids circular imports when accessing the StreamField block class (see below)
    model = "myapp.Person"

    icon = "user"
    choose_one_text = "Choose a person"
    choose_another_text = "Choose another person"
    edit_item_text = "Edit this person"
    form_fields = ["first_name", "last_name"]  # fields to show in the "Create" tab


person_chooser_viewset = PersonChooserViewSet("person_chooser")
```

Again this can be registered with the `register_admin_viewset` hook:

```python
from wagtail import hooks

from .views import person_chooser_viewset


@hooks.register("register_admin_viewset")
def register_viewset():
    return person_chooser_viewset
```

Registering a chooser viewset will also set up a chooser widget to be used whenever a ForeignKey field to that model appears in a `WagtailAdminModelForm` - see [](./forms). In particular, this means that a panel definition such as `FieldPanel("author")`, where `author` is a foreign key to the `Person` model, will automatically use this chooser interface. The chooser widget class can also be retrieved directly (for use in ordinary Django forms, for example) as the `widget_class` property on the viewset. For example, placing the following code in `widgets.py` will make the chooser widget available to be imported with `from myapp.widgets import PersonChooserWidget`:

```python
from .views import person_chooser_viewset

PersonChooserWidget = person_chooser_viewset.widget_class
```

The viewset also makes a StreamField chooser block class available, through the method `get_block_class`. Placing the following code in `blocks.py` will make a chooser block available for use in StreamField definitions by importing `from myapp.blocks import PersonChooserBlock`:

```python
from .views import person_chooser_viewset

PersonChooserBlock = person_chooser_viewset.get_block_class(
    name="PersonChooserBlock", module_path="myapp.blocks"
)
```

## Chooser viewsets for non-model datasources

While the generic chooser views are primarily designed to use Django models as the data source, choosers based on other sources such as REST API endpoints can be implemented by overriding the individual methods that deal with data retrieval.

Within `wagtail.admin.views.generic.chooser`:

-   `BaseChooseView.get_object_list()` - returns a list of records to be displayed in the chooser. (In the default implementation, this is a Django QuerySet, and the records are model instances.)
-   `BaseChooseView.columns` - a list of `wagtail.admin.ui.tables.Column` objects specifying the fields of the record to display in the final table
-   `BaseChooseView.apply_object_list_ordering(objects)` - given a list of records as returned from `get_object_list`, returns the list with the desired ordering applied
-   `ChosenViewMixin.get_object(pk)` - returns the record identified by the given primary key
-   `ChosenResponseMixin.get_chosen_response_data(item)` - given a record, returns the dictionary of data that will be passed back to the chooser widget to populate it (consisting of items `id` and `title`, unless the chooser widget's JavaScript has been customised)

Within `wagtail.admin.widgets`:

-   `BaseChooser.get_instance(value)` - given a value that may be a record, a primary key, or None, returns the corresponding record or None
-   `BaseChooser.get_value_data_from_instance(item)` - given a record, returns the dictionary of data that will populate the chooser widget (consisting of items `id` and `title`, unless the widget's JavaScript has been customised)

For example, the following code will implement a chooser that runs against a JSON endpoint for the User model at `http://localhost:8000/api/users/`, set up with Django REST Framework using the default configuration and no pagination:

```python
from django.views.generic.base import View
import requests

from wagtail.admin.ui.tables import Column, TitleColumn
from wagtail.admin.views.generic.chooser import (
    BaseChooseView, ChooseViewMixin, ChooseResultsViewMixin, ChosenResponseMixin, ChosenViewMixin, CreationFormMixin
)
from wagtail.admin.viewsets.chooser import ChooserViewSet
from wagtail.admin.widgets import BaseChooser


class BaseUserChooseView(BaseChooseView):
    @property
    def columns(self):
        return [
            TitleColumn(
                "title",
                label="Title",
                accessor='username',
                id_accessor='id',
                url_name=self.chosen_url_name,
                link_attrs={"data-chooser-modal-choice": True},
            ),
            Column(
                "email", label="Email", accessor="email"
            )
        ]

    def get_object_list(self):
        r = requests.get("http://localhost:8000/api/users/")
        r.raise_for_status()
        results = r.json()
        return results

    def apply_object_list_ordering(self, objects):
        return objects


class UserChooseView(ChooseViewMixin, CreationFormMixin, BaseUserChooseView):
    pass


class UserChooseResultsView(ChooseResultsViewMixin, CreationFormMixin, BaseUserChooseView):
    pass


class UserChosenViewMixin(ChosenViewMixin):
    def get_object(self, pk):
        r = requests.get("http://localhost:8000/api/users/%d/" % int(pk))
        r.raise_for_status()
        return r.json()


class UserChosenResponseMixin(ChosenResponseMixin):
    def get_chosen_response_data(self, item):
        return {
            "id": item["id"],
            "title": item["username"],
        }


class UserChosenView(UserChosenViewMixin, UserChosenResponseMixin, View):
    pass


class BaseUserChooserWidget(BaseChooser):
    def get_instance(self, value):
        if value is None:
            return None
        elif isinstance(value, dict):
            return value
        else:
            r = requests.get("http://localhost:8000/api/users/%d/" % int(value))
            r.raise_for_status()
            return r.json()

    def get_value_data_from_instance(self, instance):
        return {
            "id": instance["id"],
            "title": instance["username"],
        }


class UserChooserViewSet(ChooserViewSet):
    icon = "user"
    choose_one_text = "Choose a user"
    choose_another_text = "Choose another user"
    edit_item_text = "Edit this user"

    choose_view_class = UserChooseView
    choose_results_view_class = UserChooseResultsView
    chosen_view_class = UserChosenView
    base_widget_class = BaseUserChooserWidget


user_chooser_viewset = UserChooserViewSet("user_chooser", url_prefix="user-chooser")
```

If the data source implements its own pagination - meaning that the pagination mechanism built into the chooser should be bypassed - the `BaseChooseView.get_results_page(request)` method can be overridden instead of `get_object_list`. This should return an instance of `django.core.paginator.Page`. For example, if the API in the above example followed the conventions of the Wagtail API, implementing pagination with `offset` and `limit` URL parameters and returning a dict consisting of `meta` and `results`, the `BaseUserChooseView` implementation could be modified as follows:

```python
from django.core.paginator import Page, Paginator

class APIPaginator(Paginator):
    """
    Customisation of Django's Paginator class for use when we don't want it to handle
    slicing on the result set, but still want it to generate the page numbering based
    on a known result count.
    """
    def __init__(self, count, per_page, **kwargs):
        self._count = int(count)
        super().__init__([], per_page, **kwargs)

    @property
    def count(self):
        return self._count

class BaseUserChooseView(BaseChooseView):
    @property
    def columns(self):
        return [
            TitleColumn(
                "title",
                label="Title",
                accessor='username',
                id_accessor='id',
                url_name=self.chosen_url_name,
                link_attrs={"data-chooser-modal-choice": True},
            ),
            Column(
                "email", label="Email", accessor="email"
            )
        ]

    def get_results_page(self, request):
        try:
            page_number = int(request.GET.get('p', 1))
        except ValueError:
            page_number = 1

        r = requests.get("http://localhost:8000/api/users/", params={
            'offset': (page_number - 1) * self.per_page,
            'limit': self.per_page,
        })
        r.raise_for_status()
        result = r.json()
        paginator = APIPaginator(result['meta']['total_count'], self.per_page)
        page = Page(result['items'], page_number, paginator)
        return page
```
