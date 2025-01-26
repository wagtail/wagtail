(documents_overview)=

# Documents overview

This page provides an overview of the basics of using the `'wagtail.documents'` app in your Wagtail project.

## Including `'wagtail.documents'` in `INSTALLED_APPS`

To use the `wagtail.documents` app, you need to include it in the `INSTALLED_APPS` list in your Django project's settings. Simply add it to the list like this:

```python
# settings.py

INSTALLED_APPS = [
    # ...
    'wagtail.documents',
    # ...
]
```

## Setting up URLs

Next, you need to set up URLs for the `wagtail.documents` app. You can include these URLs in your project's main urls.py file. To do this, add the following lines:

```python
# urls.py

from wagtail.documents import urls as wagtaildocs_urls

urlpatterns = [
    # ...
    path('documents/', include(wagtaildocs_urls)),
    # ...
]
```

New documents saved are stored in the [reference index](managing_the_reference_index) by default.

## Using documents in a Page

To include a document file in a Wagtail page, you can use `FieldPanel` in your page model.

Here's an example:

```python
# models.py

from wagtail.admin.panels import FieldPanel
from wagtail.documents import get_document_model


class YourPage(Page):
    # ...
    document = models.ForeignKey(
        get_document_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    content_panels = Page.content_panels + [
        # ...
        FieldPanel('document'),
    ]

```

This allows you to select a document file when creating or editing a page, and link to it in your page template.

Here's an example template to access the document field and render it:

```html+django
{% extends "base.html" %}
{% block content %}
    {% if page.document %}
        <h2>Document: {{ page.document.title }}</h2>
        <p>File Type: {{ page.document.file_extension }}</p>
        <a href="{{ page.document.url }}" target="_blank">View Document</a>
    {% else %}
        <p>No document attached to this page.</p>
    {% endif %}
    <div>{{ page.body }}</div>
{% endblock %}
```

## Using documents within `RichTextFields`

Links to documents can be made in pages using the [`RichTextField`](rich_text_field). By default, Wagtail will include the features for adding links to documents see [](rich_text_features).

You can either exclude or include these by passing the `features` to your `RichTextField`. In the example below we create a `RichTextField` with only documents and basic formatting.

```python
# models.py
from wagtail.fields import RichTextField

class BlogPage(Page):
    # ...other fields
    document_footnotes = RichTextField(
        blank=True,
        features=["bold", "italic", "ol", "document-link"]
    )

    panels = [
        # ...other panels
        FieldPanel("document_footnotes"),
    ]
```

## Using documents within `StreamField`

`StreamField` provides a content editing model suitable for pages that do not follow a fixed structure. To add links to documents using `StreamField`, include it in your models and also include the `DocumentChooserBlock`.

Create a `Page` model with a `StreamField` named `doc` and a `DocumentChooserBlock` named `doc_link` inside the field:

```python
# models.py

from wagtail.fields import StreamField
from wagtail.documents.blocks import DocumentChooserBlock


class BlogPage(Page):
    # ... other fields

    documents = StreamField([
            ('document', DocumentChooserBlock())
        ],
        null=True,
        blank=True,
        use_json_field=True,
    )

    panels = [
        # ... other panels
        FieldPanel("documents"),
    ]
```

In `blog_page.html`, add the following block of code to display the document link in the page:

```html+django
{% for block in page.documents %}
    <a href="{{ block.value.url }}">{{ block.value.title }}</a>
{% endfor %}
```

## Working documents and collections

Documents in Wagtail can be organized within [collections](https://guide.wagtail.org/en-latest/how-to-guides/manage-collections/). Collections provide a way to group related documents. You can cross-link documents between collections and make them accessible through different parts of your site.

Here's an example:

```python
from wagtail.documents import get_document_model

class PageWithCollection(Page):
    collection = models.ForeignKey(
        "wagtailcore.Collection",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name='Document Collection',
    )

    content_panels = Page.content_panels + [
        FieldPanel("collection"),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        documents = get_document_model().objects.filter(collection=self.collection)
        context['documents'] = documents
        return context

```

Here’s an example template to access the document collection and render it:

```html+django
{% extends "base.html" %}
{% load wagtailcore_tags %}

{% block content %}
    {% if documents %}
    <h3>Documents:</h3>
    <ul>
        {% for document in documents %}
        <li>
            <a href="{{ document.url }}" target="_blank">{{ document.title }}</a>
        </li>
        {% endfor %}
    </ul>
    {% endif %}
{% endblock %}
```

## Making documents private

If you want to restrict access to certain documents, you can place them in [private collections](https://guide.wagtail.org/en-latest/how-to-guides/manage-collections/#privacy-settings).

Private collections are not publicly accessible, and their contents are only available to users with the appropriate permissions.

## API access

Documents in Wagtail can be accessed through the API via the `wagtail.documents.api.v2.views.DocumentsAPIViewSet`. This allows you to programmatically interact with documents, retrieve their details, and perform various operations.

For more details, you can refer to the [API section](api_v2_configure_endpoints) that provides additional information and usage examples.
