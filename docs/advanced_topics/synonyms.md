# How to… use synonyms with Elasticsearch to improve search results

Users might not always use the same terms as you to refer to something. An example might be 'waste', 'refuse', 'garbage', 'trash' and 'rubbish'. If you configure these as synonyms via the search engine, then you will not need to tag pages with every possible synonym, and a search query `Page.objects.search("gift")` could always return results including a page called "Donate to our Charity".

```eval_rst note:: Stemming, and language-specific configuration

Synonym searching is not necessary for the search engine to match a query "cherries" to a page _Cherry flavour ice cream_. The Postgres or Elasticsearch search backends should do that automatically, so long as you have the correct language configured. See 

- :doc:`/reference/contrib/postgres_search#language-postgresql-search-configuration`
- `Elasticsearch documentation <https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-lang-analyzer.html>`_
```

This how-to guide will show you how to configure Elasticsearch to use synonym matching, first for a hardcoded source of synonyms, and then for 

Note: We will assume that your synonyms content is dynamic, and therefore you want to read it in from the database, and we will manage the synonyms in the admin.

Note: We will assume the following code goes in a Django app called `customsearch` in the root of your project.

## 1. Fetch synonyms terms when a search is performed

Elasticsearch will accept synonyms as a list of strings in the format: 

```python
[
    "foo, fish, jam",
    "bar, tobogganing, showers, toasters"
]
```

If these are set, then a search for "foo", "fish", or "jam" will return identical results, and will include pages indexed for any of those words.

If you already have an approach to generating synonyms, and they do not change, this is the only step needed to make Elasticsearch aware of them. In your site settings:

```python
WAGTAILSEARCH_BACKENDS = {
    "default": {
        "BACKEND": "wagtail.search.backends.elasticsearch7",
        "INDEX": "wagtail",
        "OPTIONS": {},
        "INDEX_SETTINGS": {
            "settings": {
                "analysis": {
                    "analyzer": {
                        "default": {"tokenizer": "whitespace", "filter": ["synonym"]},
                    },
                    "filter": {
                        "synonym": {
                            "type": "synonym",
                            "synonyms": [
                                "foo, fish, jam",
                                "bar, tobogganing, showers, toasters",
                            ],
                        },
                    },
                },
            },
        },
    },
}
```

## 2. Permit dynamic synonyms

We'll make the backend compatible with dynamic synonyms first. An approach to creating these synonyms is in a later step.

The backend's settings `Elasticsearch7SearchBackend.settings` are read from your project's settings every time the backend is instantiated. Let's create a placeholder function to generate our synonym list. Edit `customsearch/utils.py`:

```python
def get_synonyms():
    """This is still a static list"""
    return [
        "foo, fish, jam",
        "bar, tobogganing, showers, toasters",
    ]
```

We now create a new custom search backend that reads this every time it is instantiated. This backend is instantiated for every search query using the `queryset.search()` syntax, so we can be assured it will call the function every time. Edit `customsearch/elasticsearch7.py`:

```python
import copy

from wagtail.search.backends.elasticsearch7 import Elasticsearch7SearchBackend

from customsearch.utils import get_synonyms


class SearchBackend(Elasticsearch7SearchBackend):
    settings = copy.deepcopy(Elasticsearch7SearchBackend.settings)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.settings["settings"]["analysis"]["filter"]["synonym"] = {
            "type": "synonym",
            "synonyms": get_synonyms(),
        }
```

Now we must update our site settings to use this. Wagtail expects the path to a search backend module, which must contain a `SearchBackend` class:

```python
WAGTAILSEARCH_BACKENDS = {
    "default": {
        "BACKEND": "customsearch.elasticsearch7",
        ...
```

## 3. Make synonyms editable

We will add an admin menu item to edit the synonyms.

### Add a Term model

```python
from django.contrib.postgres.fields import ArrayField
from django.db import models

from wagtail.admin.edit_handlers import FieldPanel


class Term(models.Model):
    canonical_term = models.CharField(
        max_length=50,
        unique=True,
        help_text="A word or phrase that returns intended search results",
    )
    synonyms = ArrayField(
        models.CharField(max_length=50, blank=False),
        help_text=(
            "A list of other terms which should match pages containing the canonical "
            "term. Separate with commas, multiple word phrases are supported."
        ),
    )

    panels = [
        FieldPanel("canonical_term"),
        FieldPanel("synonyms"),
    ]

    class Meta:
        verbose_name = "Search synonym"

    def __str__(self):
        synonyms = ", ".join(self.synonyms[:5])
        return f"{self.canonical_term}: {synonyms}"
```

Register the above as an admin menu item. Edit `customsearch/wagtail_hooks.py`:

```python
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register

from customsearch.models import Term


class TermModelAdmin(ModelAdmin):
    model = Term
    menu_icon = "search"
    list_display = ("canonical_term", "synonyms")


modeladmin_register(TaxonomiesModelAdminGroup)
```

### Make our synonyms dynamic

Now update the `get_synonyms` function to return dynamic content. Edit `customsearch/utils.py`:

```python
from bc.search.models import Term


def get_synonyms(force_update=False):
    return [
        ", ".join(
            [term.canonical_term] + [synonym.lower() for synonym in term.synonyms]
            )
        for term in Term.objects.all()
    ] or [""]  # This `or` clause is necessary for Elasticsearch 5 only.
```

Note: Elasticsearch 5 will return an error response "synonym requires either `synonyms` or `synonyms_path` to be configured" if you send an empty list. If you are not using that backend, the `or [""]` part can be omitted.

## 4. Cache the results, to improve performance

It is likely that searches happen more often than updates to the synonyms. If your site has caching enabled, then we can improve our synonyms function.

### Update the cache when synonyms are edited

Edit `customsearch/signal_handlers.py`:

```python
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from customsearch.models import Term
from customsearch.utils import get_synonyms


@receiver([post_save, post_delete], sender=Term)
def cache_synonyms_receiver(**kwargs):
    get_synonyms(force_update=True)
```

Load the signal handlers in your app's config. Edit `customsearch/apps.py`:

```python
from django.apps import AppConfig


class CustomSearchConfig(AppConfig):
    name = "customsearch"

    def ready(self):
        import customsearch.signal_handlers
```

In `settings.INSTALLED_APPS`, use `customsearch.apps.CustomSearchConfig`, rather than `customsearch`.

### Use the cached value

Edit `customsearch/utils.py`:

```
from django.core.cache import caches

from customsearch.models import Term

cache = caches["default"]

SYNONYMS_CACHE_KEY = "searchbackend_synonyms"


def get_synonyms(force_update=False):
    synonyms = None if force_update else cache.get(SYNONYMS_CACHE_KEY)

    if not synonyms:
        synonyms = [
            ", ".join(
                [term.canonical_term] + [synonym.lower() for synonym in term.synonyms]
            )
            for term in Term.objects.all()
        ]
        cache.set(SYNONYMS_CACHE_KEY, synonyms)

    return synonyms or [""]  # This `or` clause is necessary for Elasticsearch 5 only.
```

## 5. Add unit tests

This is not the core part of the how-to guide, but code should be tested. Add a test file in a location that your test runner will find it.

```python
from unittest.mock import patch

import factory

from django.test import TestCase

from customsearch.utils import SYNONYMS_CACHE_KEY, cache, get_synonyms


class TermFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "search.Term"


class SynonymTest(TestCase):
    def test_basic(self):
        TermFactory(canonical_term="foo", synonyms=["soup", "potatoes"])
        self.assertListEqual(get_synonyms(), ["foo, soup, potatoes"])

    def test_multi_word_phrase_synonym(self):
        TermFactory(
            canonical_term="foo",
            synonyms=["haircuts arguments", "small things", "rabbits"],
        )
        self.assertListEqual(
            get_synonyms(), ["foo, haircuts arguments, small things, rabbits"],
        )

    def test_multi_word_canonical_term(self):
        TermFactory(
            canonical_term="people with noses", synonyms=["more jam", "soot", "flies"]
        )
        self.assertListEqual(
            get_synonyms(), ["people with noses, more jam, soot, flies"],
        )

    def test_multiple_synonyms(self):
        TermFactory(canonical_term="foo", synonyms=["fish", "jam"])
        TermFactory(
            canonical_term="bar", synonyms=["tobogganing", "showers", "toasters"]
        )
        self.assertListEqual(
            get_synonyms(), ["foo, fish, jam", "bar, tobogganing, showers, toasters"],
        )

    def test_synonyms_are_lower_cased(self):
        TermFactory(canonical_term="foo", synonyms=["Belgium", "fire", "water"])
        self.assertListEqual(get_synonyms(), ["foo, belgium, fire, water"])

    @patch("bc.search.signal_handlers.get_synonyms")
    def test_signal_is_triggered(self, mock_get_synonyms):
        TermFactory(canonical_term="foo", synonyms=["lights", "Burma"])
        mock_get_synonyms.assert_called_once_with(force_update=True)

    def test_synonyms_are_cached(self):
        cache.delete(SYNONYMS_CACHE_KEY)
        self.assertEqual(cache.get(SYNONYMS_CACHE_KEY), None)

        TermFactory(canonical_term="foo", synonyms=["light", "air"])
        self.assertListEqual(cache.get(SYNONYMS_CACHE_KEY), ["foo, light, air"])

    def test_synonym_cache_can_be_updated(self):
        TermFactory(
            canonical_term="foo", synonyms=["things that go 'uhh'", "Arthur Negus"]
        )
        cache.set(SYNONYMS_CACHE_KEY, ["foo, colonel gaddafi"])
        self.assertListEqual(cache.get(SYNONYMS_CACHE_KEY), ["foo, colonel gaddafi"])
        self.assertListEqual(
            get_synonyms(force_update=True), ["foo, things that go 'uhh', arthur negus"]
        )
        self.assertListEqual(
            cache.get(SYNONYMS_CACHE_KEY), ["foo, things that go 'uhh', arthur negus"]
        )

    def test_cache_is_used(self):
        cache.set(SYNONYMS_CACHE_KEY, ["foo, eggnog, radiators"])
        self.assertListEqual(get_synonyms(), ["foo, eggnog, radiators"])

        TermFactory(canonical_term="bar", synonyms=["grandmothers"])
        self.assertListEqual(get_synonyms(), ["bar, grandmothers"])
```

## Suggestions for improvement

- Generate the synonyms a different way, that suits you.
- Write the synonyms out to a file, if you have a lot of content, because reading them inline in the filter increases cluster size unnecessarily [Elasticsearch synonyms documentation][es_docs].

## References

- [Elasticsearch synonyms documentation][es_docs], including more information about the Solr style syntax and file-based synonyms.
- [Search backends explanation](reference/search_backends.md)


- [es_docs](https://www.elastic.co/guide/en/elasticsearch/reference/7.10/analysis-synonym-tokenfilter.html)

