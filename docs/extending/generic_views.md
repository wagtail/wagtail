(generic_views)=

# Generic views

Wagtail provides several generic views for handling common tasks such as creating / editing model instances and chooser modals. Since these often involve several related views with shared properties (such as the model that we're working with, and its associated icon) Wagtail also implements the concept of a _viewset_, which allows a bundle of views to be defined collectively, and their URLs to be registered with the admin app as a single operation through the [`register_admin_viewset`](register_admin_viewset) hook.

## ModelViewSet

The {class}`wagtail.admin.viewsets.model.ModelViewSet` class provides the views for listing, creating, editing, and deleting model instances. For example, if we have the following model:

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

(chooser_viewsets_limiting_choices)=

### Limiting choices via linked fields

Chooser viewsets provide a mechanism for limiting the options displayed in the chooser according to another input field on the calling page. For example, suppose the person model has a country field - we can then set up a page model with a country dropdown and a person chooser, where an editor first selects a country from the dropdown and then opens the person chooser to be presented with a list of people from that country.

To set this up, define a `url_filter_parameters` attribute on the ChooserViewSet. This specifies a list of URL parameters that will be recognised for filtering the results - whenever these are passed in the URL, a `filter` clause on the correspondingly-named field will be applied to the queryset. These parameters should also be listed in the `preserve_url_parameters` attribute, so that they are preserved in the URL when navigating through the chooser (such as when following pagination links). The following definition will allow the person chooser to be filtered by country:

```python
class PersonChooserViewSet(ChooserViewSet):
    model = "myapp.Person"
    url_filter_parameters = ["country"]
    preserve_url_parameters = ["multiple", "country"]
```

The chooser widget now needs to be configured to pass these URL parameters when opening the modal. This is done by passing a `linked_fields` dictionary to the widget's constructor, where the keys are the names of the URL parameters to be passed, and the values are CSS selectors for the corresponding input fields on the calling page. For example, suppose we have a page model with a country dropdown and a person chooser:

```python
class BlogPage(Page):
    country = models.ForeignKey(Country, null=True, blank=True, on_delete=models.SET_NULL)
    author = models.ForeignKey(Person, null=True, blank=True, on_delete=models.SET_NULL)

    content_panels = Page.content_panels + [
        FieldPanel('country'),
        FieldPanel('person', widget=PersonChooserWidget(linked_fields={
            # pass the country selected in the id_country input to the person chooser
            # as a URL parameter `country`
            'country': '#id_country',
        })),
    ]
```

A number of other lookup mechanisms are available:

```python
PersonChooserWidget(linked_fields={
    'country': {'selector': '#id_country'}  # equivalent to 'country': '#id_country'
})

# Look up by ID
PersonChooserWidget(linked_fields={
    'country': {'id': 'id_country'}
})

# Regexp match, for use in StreamFields and InlinePanels where IDs are dynamic:
# 1) Match the ID of the current widget's form element (the PersonChooserWidget)
#      against the regexp '^id_blog_person_relationship-\d+-'
# 2) Append 'country' to the matched substring
# 3) Retrieve the input field with that ID
PersonChooserWidget(linked_fields={
    'country': {'match': r'^id_blog_person_relationship-\d+-', 'append': 'country'},
})
```

(chooser_viewsets_non_model_data)=

### Chooser viewsets for non-model datasources

While the generic chooser views are primarily designed to use Django models as the data source, choosers based on other sources such as REST API endpoints can be implemented through the use of the [queryish](https://pypi.org/project/queryish/) library, which allows any data source to be wrapped in a Django QuerySet-like interface. This can then be passed to ChooserViewSet like a normal model. For example, the Pokemon example from the _queryish_ documentation could be made into a chooser as follows:

```python
# views.py

import re
from queryish.rest import APIModel
from wagtail.admin.viewsets.chooser import ChooserViewSet


class Pokemon(APIModel):
    class Meta:
        base_url = "https://pokeapi.co/api/v2/pokemon/"
        detail_url = "https://pokeapi.co/api/v2/pokemon/%s/"
        fields = ["id", "name"]
        pagination_style = "offset-limit"
        verbose_name_plural = "pokemon"

    @classmethod
    def from_query_data(cls, data):
        return cls(
            id=int(re.match(r'https://pokeapi.co/api/v2/pokemon/(\d+)/', data['url']).group(1)),
            name=data['name'],
        )

    @classmethod
    def from_individual_data(cls, data):
        return cls(
            id=data['id'],
            name=data['name'],
        )

    def __str__(self):
        return self.name


class PokemonChooserViewSet(ChooserViewSet):
    model = Pokemon

    choose_one_text = "Choose a pokemon"
    choose_another_text = "Choose another pokemon"


pokemon_chooser_viewset = PokemonChooserViewSet("pokemon_chooser")


# wagtail_hooks.py

from wagtail import hooks

from .views import pokemon_chooser_viewset


@hooks.register("register_admin_viewset")
def register_pokemon_chooser_viewset():
    return pokemon_chooser_viewset
```
