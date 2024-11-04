(testing_reference)=

# Testing your Wagtail site

Wagtail comes with some utilities that simplify writing tests for your site.

## WagtailPageTestCase

**_class_ wagtail.test.utils.WagtailPageTestCase**
`WagtailPageTestCase` extends `django.test.TestCase`, adding a few new `assert` methods. You should extend this class to make use of its methods:

```python
from wagtail.test.utils import WagtailPageTestCase
from myapp.models import MyPage

class MyPageTests(WagtailPageTestCase):
    def test_can_create_a_page(self):
        ...
```

**assertPageIsRoutable(_page, route_path="/", msg=None_)**

Asserts that `page` can be routed to without raising a `Http404` error.

For page types with multiple routes, you can use `route_path` to specify an alternate route to test.

This assertion is great for getting coverage on custom routing logic for page types. Here is an example:

```python
from wagtail.test.utils import WagtailPageTestCase
from myapp.models import EventListPage

class EventListPageRoutabilityTests(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        # create page(s) for testing
        ...

    def test_default_route(self):
        self.assertPageIsRoutable(self.page)

    def test_year_archive_route(self):
        # NOTE: Despite this page type raising a 404 when no events exist for
        # the specified year, routing should still be successful
        self.assertPageIsRoutable(self.page, "archive/year/1984/")

```

**assertPageIsRenderable(_page, route_path="/", query_data=None, post_data=None, user=None, accept_404=False, accept_redirect=False, msg=None_)**

Asserts that `page` can be rendered without raising a fatal error.

For page types with multiple routes, you can use `route_path` to specify a partial path to be added to the page's regular `url`.

When `post_data` is provided, the test makes a `POST` request with `post_data` in the request body. Otherwise, a `GET` request is made.

When supplied, `query_data` is always converted to a querystring and added to the request URL.

When `user` is provided, the test is conducted with them as the active user.

By default, the assertion will fail if the request to the page URL results in a 301, 302 or 404 HTTP response. If you are testing a page/route where a 404 response is expected, you can use `accept_404=True` to indicate this, and the assertion will pass when encountering a 404 response. Likewise, if you are testing a page/route where a redirect response is expected, you can use `accept_redirect=True` to indicate this, and the assertion will pass when encountering 301 or 302 response.

This assertion is great for getting coverage on custom rendering logic for page types. Here is an example:

```python
def test_default_route_rendering(self):
    self.assertPageIsRenderable(self.page)

def test_year_archive_route_with_zero_matches(self):
    # NOTE: Should raise a 404 when no events exist for the specified year
    self.assertPageIsRenderable(self.page, "archive/year/1984/", accept_404=True)

def test_month_archive_route_with_zero_matches(self):
    # NOTE: Should redirect to year-specific view when no events exist for the specified month
    self.assertPageIsRenderable(self.page, "archive/year/1984/07/", accept_redirect=True)
```

**assertPageIsEditable(_page, post_data=None, user=None, msg=None_)**

Asserts that the page edit view works for `page` without raising a fatal error.

When `user` is provided, the test is conducted with them as the active user. Otherwise, a superuser is created and used for the test.

After a successful `GET` request, a `POST` request is made with field data in the request body. If `post_data` is provided, that will be used for this purpose. If not, this data will be extracted from the `GET` response HTML.

This assertion is great for getting coverage on custom fields, panel configuration and custom validation logic. Here is an example:

```python
def test_editability(self):
    self.assertPageIsEditable(self.page)

def test_editability_on_post(self):
    self.assertPageIsEditable(
        self.page,
        post_data={
            "title": "Fabulous events",
            "slug": "events",
            "show_featured": True,
            "show_expired": False,
            "action-publish": "",
        }
    )
```

**assertPageIsPreviewable(_page, mode="", post_data=None, user=None, msg=None_)**

Asserts that the page preview view can be loaded for `page` without raising a fatal error.

For page types that support different preview modes, you can use `mode` to specify the preview mode to be tested.

When `user` is provided, the test is conducted with them as the active user. Otherwise, a superuser is created and used for the test.

To load the preview, the test client needs to make a `POST` request including all required field data in the request body. If `post_data` is provided, that will be used for this purpose. If not, the method will attempt to extract this data from the page edit view.

This assertion is great for getting coverage on custom preview modes, or getting reassurance that custom rendering logic is compatible with Wagtail's preview mode. Here is an example:

```python
def test_general_previewability(self):
    self.assertPageIsPreviewable(self.page)

def test_archive_previewability(self):
    self.assertPageIsPreviewable(self.page, mode="year-archive")
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

**assertCanCreate(_parent, child_model, data, msg=None_, publish=True)**
Assert that a child of the given Page type can be created under the parent, using the supplied POST data.

`parent` should be a Page instance, and `child_model` should be a Page subclass. `data` should be a dict that will be POSTed at the Wagtail admin Page creation method.

`publish` specifies whether the page being created should be published or not - default is `True`.

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

## Creating Page objects within tests

If you want to create page objects within tests, you will need to go through some steps before actually creating the page you want to test.

-   Pages can't be created directly with `MyPage.objects.create()` as you would do with a regular Django model, they need to be added as children to a parent page with `parent.add_child(instance=child)`.
-   To start the page tree, you need a root page that can be created with `Page.get_first_root_node()`.
-   You also need a `Site` set up with the correct `hostname` and a `root_page`.

```python
from wagtail.models import Page, Site
from wagtail.rich_text import RichText
from wagtail.test.utils import WagtailPageTestCase

from home.models import HomePage, MyPage


class MyPageTest(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        root = Page.get_first_root_node()
        Site.objects.create(
            hostname="testserver",
            root_page=root,
            is_default_site=True,
            site_name="testserver",
        )
        home = HomePage(title="Home")
        root.add_child(instance=home)
        cls.page = MyPage(
            title="My Page",
            slug="mypage",
        )
        home.add_child(instance=cls.page)

    def test_get(self):
        response = self.client.get(self.page.url)
        self.assertEqual(response.status_code, 200)
```

### Working with Page content

You will likely want to test the content of your page. If it includes a `StreamField`, you will need to set its content as a list of tuples with the block's name and content. For `RichTextBlock`, the content has to be an instance of `RichText`.

```python
...
from wagtail.rich_text import RichText

class MyPageTest(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        ...
        # Create page instance here
        cls.page.body.extend(
            [
                ("heading", "Just a CharField Heading"),
                ("paragraph", RichText("<p>First paragraph</p>")),
                ("paragraph", RichText("<p>Second paragraph</p>")),
            ]
        )
        cls.page.save()

    def test_page_content(self):
        response = self.client.get(self.page.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Just a CharField Heading")
        self.assertContains(response, "<p>First paragraph</p>")
        self.assertContains(response, "<p>Second paragraph</p>")
```

## Fixtures

### Using `dumpdata`

Creating [fixtures](inv:django#howto/initial-data) for tests is best done by creating content in a development
environment, and using Django's [`dumpdata`](inv:django#dumpdata) command.

Note that by default `dumpdata` will represent `content_type` by the primary key; this may cause consistency issues when adding / removing models, as content types are populated separately from fixtures. To prevent this, use the `--natural-foreign` switch, which represents content types by `["app", "model"]` instead.

### Manual modification

You could modify the dumped fixtures manually, or even write them all by hand.
Here are a few things to be wary of.

#### Custom Page models

When creating customized Page models in fixtures, you will need to add both a
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

Filling in the `path` / `numchild` / `depth` fields is necessary for tree operations like `get_parent()` to work correctly.
`url_path` is another field that can cause errors in some uncommon cases if it isn't filled in.

The [Treebeard docs](inv:treebeard:std:doc#mp_tree) might help in understanding how this works.
