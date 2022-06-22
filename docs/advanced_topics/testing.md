(reference)=

# Testing your Wagtail site

Wagtail comes with some utilities that simplify writing tests for your site.

## WagtailPageTests

**_class_ wagtail.test.utils.WagtailPageTests**
`WagtailPageTests` extends `django.test.TestCase`, adding a few new `assert` methods. You should extend this class to make use of its methods:

```python
from wagtail.test.utils import WagtailPageTests
from myapp.models import MyPage

class MyPageTests(WagtailPageTests):
    def test_can_create_a_page(self):
        ...
```

**assertCanCreateAt(_parent_model, child_model, msg=None_)**
Assert a particular child Page type can be created under a parent Page type. `parent_model` and `child_model` should be the Page classes being tested.

```python
def test_can_create_under_home_page(self):
    # You can create a ContentPage under a HomePage
    self.assertCanCreateAt(HomePage, ContentPage)
```

**assertCanNotCreateAt(_parent_model, child_model, msg=None_)**
Assert a particular child Page type can not be created under a parent Page type. `parent_model` and `child_model` should be the Page classes being tested.

```python
def test_cant_create_under_event_page(self):
    # You can not create a ContentPage under an EventPage
    self.assertCanNotCreateAt(EventPage, ContentPage)
```

**assertCanCreate(_parent, child_model, data, msg=None_)**
Assert that a child of the given Page type can be created under the parent, using the supplied POST data.

`parent` should be a Page instance, and `child_model` should be a Page subclass. `data` should be a dict that will be POSTed at the Wagtail admin Page creation method.

```python
from wagtail.test.utils.form_data import nested_form_data, streamfield

def test_can_create_content_page(self):
    # Get the HomePage
    root_page = HomePage.objects.get(pk=2)

    # Assert that a ContentPage can be made here, with this POST data
    self.assertCanCreate(root_page, ContentPage, nested_form_data({
        'title': 'About us',
        'body': streamfield([
            ('text', 'Lorem ipsum dolor sit amet'),
        ])
    }))
```

See [](form_data_test_helpers) for a set of functions useful for constructing POST data.

**assertAllowedParentPageTypes(_child_model, parent_models, msg=None_)**
Test that the only page types that `child_model` can be created under are `parent_models`.

The list of allowed parent models may differ from those set in `Page.parent_page_types`, if the parent models have set `Page.subpage_types`.

```python
def test_content_page_parent_pages(self):
    # A ContentPage can only be created under a HomePage
    # or another ContentPage
    self.assertAllowedParentPageTypes(
        ContentPage, {HomePage, ContentPage})

    # An EventPage can only be created under an EventIndex
    self.assertAllowedParentPageTypes(
        EventPage, {EventIndex})
```

**assertAllowedSubpageTypes(_parent_model, child_models, msg=None_)**
Test that the only page types that can be created under `parent_model` are `child_models`.

The list of allowed child models may differ from those set in `Page.subpage_types`, if the child models have set `Page.parent_page_types`.

```python
def test_content_page_subpages(self):
    # A ContentPage can only have other ContentPage children
    self.assertAllowedSubpageTypes(
        ContentPage, {ContentPage})

    # A HomePage can have ContentPage and EventIndex children
    self.assertAllowedSubpageTypes(
        HomePage, {ContentPage, EventIndex})
```

(form_data_test_helpers)=

## Form data helpers

```{eval-rst}
.. automodule:: wagtail.test.utils.form_data

   .. autofunction:: nested_form_data

   .. autofunction:: rich_text

   .. autofunction:: streamfield

   .. autofunction:: inline_formset
```

## Fixtures

### Using `dumpdata`

Creating [fixtures](django:howto/initial-data) for tests is best done by creating content in a development
environment, and using Django's [dumpdata](https://docs.djangoproject.com/en/stable/ref/django-admin/#django-admin-dumpdata) command.

Note that by default `dumpdata` will represent `content_type` by the primary key; this may cause consistency issues when adding / removing models, as content types are populated separately from fixtures. To prevent this, use the `--natural-foreign` switch, which represents content types by `["app", "model"]` instead.

### Manual modification

You could modify the dumped fixtures manually, or even write them all by hand.
Here are a few things to be wary of.

#### Custom Page models

When creating customised Page models in fixtures, you will need to add both a
`wagtailcore.page` entry, and one for your custom Page model.

Let's say you have a `website` module which defines a `Homepage(Page)` class.
You could create such a homepage in a fixture with:

```json
[
    {
        "model": "wagtailcore.page",
        "pk": 3,
        "fields": {
            "title": "My Customer's Homepage",
            "content_type": ["website", "homepage"],
            "depth": 2
        }
    },
    {
        "model": "website.homepage",
        "pk": 3,
        "fields": {}
    }
]
```

#### Treebeard fields

Filling in the `path` / `numchild` / `depth` fields is necessary in order for tree operations like `get_parent()` to work correctly.
`url_path` is another field that can cause errors in some uncommon cases if it isn't filled in.

The [Treebeard docs](https://django-treebeard.readthedocs.io/en/latest/mp_tree.html) might help in understanding how this works.
