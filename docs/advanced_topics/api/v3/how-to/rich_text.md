(api_v3_rich_text)=

# How to work with rich text via the API

Wagtail stores rich text in an internal database format (`db-html`) that contains
references to pages and images as identifiers rather than URLs. The v3 API lets
you read and write rich text in multiple representations.

## Prerequisites

- Wagtail v3 Write API installed and mounted (see {ref}`api_ninja`).
- [bakerydemo](https://github.com/wagtail/bakerydemo) running locally with demo
  fixtures loaded (`python manage.py loaddata bakerydemo/base/fixtures/bakerydemo.json`).
- The `home` and `breads` apps must be installed (they are in bakerydemo by default).

## Reading rich text (HTML output)

By default, the API serialises rich text as expanded HTML — internal page and
image references are resolved to live URLs. Use `expand_db_html` from
`wagtail.rich_text`:

```python
# api.py
from ninja import Router
from wagtail.rich_text import expand_db_html
from home.models import HomePage

router = Router()


@router.get("/pages/{page_id}/body")
def get_page_body(request, page_id: int):
    """Return the rich-text body of a HomePage as expanded HTML."""
    page = HomePage.objects.get(pk=page_id)
    return {"body": expand_db_html(page.body)}
```

Test against bakerydemo (the home page has pk=3 in the standard demo fixtures):

```sh
curl http://localhost:8000/api/v3/pages/3/body
# {"body": "<p>Welcome to the Wagtail bakery…</p>"}
```

## Reading rich text as Markdown

Install [`markdownify`](https://pypi.org/project/markdownify/) first:

```sh
pip install markdownify
```

Then convert the expanded HTML to Markdown:

```python
from markdownify import markdownify
from wagtail.rich_text import expand_db_html
from home.models import HomePage


@router.get("/pages/{page_id}/body/markdown")
def get_page_body_markdown(request, page_id: int):
    page = HomePage.objects.get(pk=page_id)
    html = expand_db_html(page.body)
    return {"body": markdownify(html)}
```

## Reading raw DB HTML

Clients that need to re-submit unchanged rich text, or that perform their own
link resolution, should request the raw internal format:

```python
@router.get("/pages/{page_id}/body/raw")
def get_page_body_raw(request, page_id: int):
    page = HomePage.objects.get(pk=page_id)
    # str() on a RichTextField value returns the raw db-html string.
    return {"body": str(page.body)}
```

(api_v3_rich_text_write)=

## Writing rich text (round-trip)

When creating or updating a page via the API, pass rich text in the **db-html**
format. This is the string that Wagtail stores directly in the database, where
page links look like `<a id="1" linktype="page">` and image embeds look like
`<embed id="1" embedtype="image" format="fullwidth"/>`.

```python
from ninja import Schema
from wagtail.models import Page
from breads.models import BreadPage


class BreadPageIn(Schema):
    title: str
    slug: str
    introduction: str  # Plain text introduction field
    parent_page_id: int


@router.post("/pages/breads/")
def create_bread_page(request, payload: BreadPageIn):
    """
    Create a new BreadPage as a child of the given parent.

    `introduction` is a plain TextField on BreadPage, not a RichTextField,
    so no db-html conversion is needed.
    """
    parent = Page.objects.get(pk=payload.parent_page_id)
    page = BreadPage(
        title=payload.title,
        slug=payload.slug,
        introduction=payload.introduction,
    )
    # treebeard add_child creates the page and saves it.
    parent.add_child(instance=page)
    return {"id": page.pk, "title": page.title}
```

### Passing rich text to a RichTextField

If your page model has a `RichTextField`, pass the raw db-html string directly.
The API does **not** auto-convert plain HTML — write the db-html format as stored:

```python
# For a RichTextField named `body`:
page = MyPage(
    title="My page",
    body="<p>Simple paragraph with no embeds.</p>",  # valid db-html
)
parent.add_child(instance=page)
```

For rich text that contains page links or image embeds, use the exact internal
format documented in {ref}`rich_text_internals`.

```{note}
There is no public utility to convert arbitrary consumer-facing HTML back to
db-html. If your client receives expanded HTML and needs to re-submit it,
store the raw db-html from the initial `/raw` endpoint and round-trip that
instead.
```

## See also

- {ref}`rich_text_internals` — internals of Wagtail's rich text storage.
- {ref}`api_v3_create_page_streamfield` — creating pages with StreamField content.
