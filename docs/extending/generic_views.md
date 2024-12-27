```{currentmodule} wagtail.admin.viewsets.model

```

(generic_views)=

# Generic views

Wagtail provides several generic views for handling common tasks such as creating / editing model instances and chooser modals. For convenience, these views are bundled in [viewsets](viewsets_reference).

(modelviewset)=

## ModelViewSet

The {class}`~wagtail.admin.viewsets.model.ModelViewSet` class provides the views for listing, creating, editing, and deleting model instances. For example, if we have the following model:

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
    add_to_admin_menu = True
    copy_view_enabled = False
    inspect_view_enabled = True


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

The viewset can be further customized by overriding other attributes and methods.

### Icon

You can define an {attr}`~.ViewSet.icon` attribute on the `ModelViewSet` to specify the icon that is used across the views in the viewset. The `icon` needs to be [registered in the Wagtail icon library](../../advanced_topics/icons).

### URL prefix and namespace

The {attr}`~.ViewSet.url_prefix` and {attr}`~.ViewSet.url_namespace` properties can be overridden to use a custom URL prefix and namespace for the views. If unset, they default to the model's `model_name`.

(modelviewset_menu)=

### Menu item

By default, registering a `ModelViewSet` will not register a main menu item. To add a menu item, set {attr}`~.ViewSet.add_to_admin_menu` to `True`. Alternatively, if you want to add the menu item inside the "Settings" menu, you can set {attr}`~.ViewSet.add_to_settings_menu` to `True`. Unless {attr}`~.ViewSet.menu_icon` is specified, the menu will use the same {attr}`~.ViewSet.icon` used for the views. The {attr}`~.ViewSet.menu_url` property can be overridden to customize the menu item's link, which defaults to the listing view for the model.

Unless specified, the menu item will be labeled after the model's verbose name. You can customize the menu item's label, name, and order by setting the {attr}`~.ViewSet.menu_label`, {attr}`~.ViewSet.menu_name`, and {attr}`~.ViewSet.menu_order` attributes respectively. If you would like to customize the `MenuItem` instance completely, you could override the {meth}`~.ViewSet.get_menu_item` method.

You can group multiple `ModelViewSet`s' menu items inside a single top-level menu item using the {class}`~wagtail.admin.viewsets.model.ModelViewSetGroup` class. It is similar to `ViewSetGroup`, except it takes the {attr}`~django.db.models.Options.app_label` of the first viewset's model as the default {attr}`~.ViewSetGroup.menu_label`. Refer to [the examples for `ViewSetGroup`](using_base_viewsetgroup) for more details.

(modelviewset_listing)=

### Listing view

The {attr}`~ModelViewSet.list_display` attribute can be set to specify the columns shown on the listing view. To customize the number of items to be displayed per page, you can set the {attr}`~ModelViewSet.list_per_page` attribute. Additionally, the {attr}`~ModelViewSet.ordering` attribute can be used to override the `default_ordering` configured in the listing view.

You can add the ability to filter the listing view by defining a {attr}`~ModelViewSet.list_filter` attribute and specifying the list of fields to filter. Wagtail uses the django-filter package under the hood, and this attribute will be passed as django-filter's `FilterSet.Meta.fields` attribute. This means you can also pass a dictionary that maps the field name to a list of lookups.

If you would like to make further customizations to the filtering mechanism, you can also use a custom `wagtail.admin.filters.WagtailFilterSet` subclass by overriding the {attr}`~ModelViewSet.filterset_class` attribute. The `list_filter` attribute is ignored if `filterset_class` is set. For more details, refer to [django-filter's documentation](https://django-filter.readthedocs.io/en/stable/guide/usage.html#the-filter).

You can add the ability to export the listing view to a spreadsheet by setting the {attr}`~ModelViewSet.list_export` attribute to specify the columns to be exported. The {attr}`~ModelViewSet.export_filename` attribute can be used to customize the file name of the exported spreadsheet.

(modelviewset_create_edit)=

### Create and edit views

You can define a `panels` or `edit_handler` attribute on the `ModelViewSet` or your Django model to use Wagtail's panels mechanism. For more details, see [](forms_panels_overview).

If neither `panels` nor `edit_handler` is defined and the {meth}`~ModelViewSet.get_edit_handler` method is not overridden, the form will be rendered as a plain Django form. You can customize the form by setting the {attr}`~ModelViewSet.form_fields` attribute to specify the fields to be shown on the form. Alternatively, you can set the {attr}`~ModelViewSet.exclude_form_fields` attribute to specify the fields to be excluded from the form. If panels are not used, you must define `form_fields` or `exclude_form_fields`, unless {meth}`~ModelViewSet.get_form_class` is overridden.

(modelviewset_copy)=

### Copy view

The copy view is enabled by default and will be accessible by users with the 'add' permission on the model. To disable it, set {attr}`~.ModelViewSet.copy_view_enabled` to `False`.

The view's form will be generated in the same way as create or edit forms. To use a custom form, override the `copy_view_class` and modify the `form_class` property on that class.

(modelviewset_inspect)=

### Inspect view

The inspect view is disabled by default, as it's not often useful for most models. However, if you need a view that enables users to view more detailed information about an instance without the option to edit it, you can enable the inspect view by setting {attr}`~ModelViewSet.inspect_view_enabled` on your `ModelViewSet` class.

When inspect view is enabled, an 'Inspect' button will automatically appear for each row on the listing view, which takes you to a view that shows a list of field values for that particular instance.

By default, all 'concrete' fields (where the field value is stored as a column in the database table for your model) will be shown. You can customize what values are displayed by specifying the {attr}`~ModelViewSet.inspect_view_fields` or the {attr}`~ModelViewSet.inspect_view_fields_exclude` attributes on your `ModelViewSet` class.

(modelviewset_templates)=

### Templates

If {attr}`~ModelViewSet.template_prefix` is set, Wagtail will look for the views' templates in the following directories within your project or app, before resorting to the defaults:

1. `templates/{template_prefix}/{app_label}/{model_name}/`
2. `templates/{template_prefix}/{app_label}/`
3. `templates/{template_prefix}/`

To override the template used by the `IndexView` for example, you could create a new `index.html` template and put it in one of those locations. For example, given `custom/campaign` as the `template_prefix` and a `Shirt` model in a `merch` app, you could add your custom template as `templates/custom/campaign/merch/shirt/index.html`.

For some common views, Wagtail also allows you to override the template used by overriding the `{view_name}_template_name` property on the viewset. The following is a list of customization points for the views:

-   `IndexView`: `index.html` or {attr}`~ModelViewSet.index_template_name`
    -   For the results fragment used in AJAX responses (e.g. when searching), customize `index_results.html` or {attr}`~ModelViewSet.index_results_template_name`
-   `CreateView`: `create.html` or {attr}`~ModelViewSet.create_template_name`
-   `EditView`: `edit.html` or {attr}`~ModelViewSet.edit_template_name`
-   `DeleteView`: `delete.html` or {attr}`~ModelViewSet.delete_template_name`
-   `HistoryView`: `history.html` or {attr}`~ModelViewSet.history_template_name`
-   `InspectView`: `inspect.html` or {attr}`~ModelViewSet.inspect_template_name`

### Other customizations

By default, the model registered with a `ModelViewSet` will also be registered to the [reference index](managing_the_reference_index). You can turn off this behavior by setting {attr}`~ModelViewSet.add_to_reference_index` to `False`.

Various additional attributes are available to customize the viewset - see the {class}`ModelViewSet` documentation.

(chooserviewset)=

## ChooserViewSet

The {class}`~wagtail.admin.viewsets.chooser.ChooserViewSet` class provides the views that make up a modal chooser interface, allowing users to select from a list of model instances to populate a ForeignKey field. Using the same `Person` model, the following definition (to be placed in `views.py`) will generate the views for a person chooser modal:

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

To set this up, define a `url_filter_parameters` attribute on the ChooserViewSet. This specifies a list of URL parameters that will be recognized for filtering the results - whenever these are passed in the URL, a `filter` clause on the correspondingly-named field will be applied to the queryset. These parameters should also be listed in the `preserve_url_parameters` attribute, so that they are preserved in the URL when navigating through the chooser (such as when following pagination links). The following definition will allow the person chooser to be filtered by country:

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
        FieldPanel('author', widget=PersonChooserWidget(linked_fields={
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
