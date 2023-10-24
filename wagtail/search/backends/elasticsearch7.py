from copy import deepcopy
from urllib.parse import urlparse

from django.utils.crypto import get_random_string
from elasticsearch import VERSION as ELASTICSEARCH_VERSION
from elasticsearch import Elasticsearch, NotFoundError
from elasticsearch.helpers import bulk

from wagtail.search.backends.base import BaseSearchBackend, get_model_root
from wagtail.search.backends.elasticsearch6 import (
    Elasticsearch6Index,
    Elasticsearch6Mapping,
    Elasticsearch6SearchQueryCompiler,
    Elasticsearch6SearchResults,
    Field,
)
from wagtail.search.index import class_is_indexed
from wagtail.utils.utils import deep_update

use_new_elasticsearch_api = ELASTICSEARCH_VERSION >= (7, 15)


class Elasticsearch7Mapping(Elasticsearch6Mapping):
    def get_mapping(self):
        mapping = super().get_mapping()
        return mapping[self.get_document_type()]


class Elasticsearch7Index(Elasticsearch6Index):
    if use_new_elasticsearch_api:

        def put(self):
            self.es.indices.create(index=self.name, **self.backend.settings)

        def delete(self):
            try:
                self.es.indices.delete(index=self.name)
            except NotFoundError:
                pass

        def refresh(self):
            self.es.indices.refresh(index=self.name)

    def add_model(self, model):
        # Get mapping
        mapping = self.mapping_class(model)

        # Put mapping
        self.es.indices.put_mapping(index=self.name, body=mapping.get_mapping())

    if use_new_elasticsearch_api:

        def add_item(self, item):
            # Make sure the object can be indexed
            if not class_is_indexed(item.__class__):
                return

            # Get mapping
            mapping = self.mapping_class(item.__class__)

            # Add document to index
            self.es.index(
                index=self.name,
                document=mapping.get_document(item),
                id=mapping.get_document_id(item),
            )

    else:

        def add_item(self, item):
            # Make sure the object can be indexed
            if not class_is_indexed(item.__class__):
                return
            # Get mapping
            mapping = self.mapping_class(item.__class__)

            # Add document to index
            self.es.index(
                self.name, mapping.get_document(item), id=mapping.get_document_id(item)
            )

    def add_items(self, model, items):
        if not class_is_indexed(model):
            return

        # Get mapping
        mapping = self.mapping_class(model)

        # Create list of actions
        actions = []
        for item in items:
            # Create the action
            action = {"_id": mapping.get_document_id(item)}
            action.update(mapping.get_document(item))
            actions.append(action)

        # Run the actions
        bulk(self.es, actions, index=self.name)

    def delete_item(self, item):
        # Make sure the object can be indexed
        if not class_is_indexed(item.__class__):
            return

        # Get mapping
        mapping = self.mapping_class(item.__class__)

        # Delete document
        try:
            self.es.delete(index=self.name, id=mapping.get_document_id(item))
        except NotFoundError:
            pass  # Document doesn't exist, ignore this exception


class Elasticsearch7SearchQueryCompiler(Elasticsearch6SearchQueryCompiler):
    mapping_class = Elasticsearch7Mapping


class Elasticsearch7SearchResults(Elasticsearch6SearchResults):
    if use_new_elasticsearch_api:

        def _backend_do_search(self, body, **kwargs):
            # As of Elasticsearch 7.15, the 'body' parameter is deprecated; instead, the top-level
            # keys of the body dict are now kwargs in their own right
            return self.backend.es.search(**body, **kwargs)


class ElasticsearchAutocompleteQueryCompilerImpl:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Convert field names into index column names
        # Note: this overrides Elasticsearch7SearchQueryCompiler by using autocomplete fields instead of searchable fields
        if self.fields:
            fields = []
            autocomplete_fields = {
                f.field_name: f
                for f in self.queryset.model.get_autocomplete_search_fields()
            }
            for field_name in self.fields:
                if field_name in autocomplete_fields:
                    field_name = self.mapping.get_field_column_name(
                        autocomplete_fields[field_name]
                    )

                fields.append(field_name)

            self.remapped_fields = fields
        else:
            self.remapped_fields = None

    def get_inner_query(self):
        fields = self.remapped_fields or [self.mapping.edgengrams_field_name]
        fields = [Field(field) for field in fields]
        if len(fields) == 0:
            # No fields. Return a query that'll match nothing
            return {"bool": {"mustNot": {"match_all": {}}}}

        return self._compile_plaintext_query(self.query, fields)


class Elasticsearch7AutocompleteQueryCompiler(
    ElasticsearchAutocompleteQueryCompilerImpl, Elasticsearch7SearchQueryCompiler
):
    pass


class ElasticsearchIndexRebuilder:
    def __init__(self, index):
        self.index = index

    def reset_index(self):
        self.index.reset()

    def start(self):
        # Reset the index
        self.reset_index()

        return self.index

    def finish(self):
        self.index.refresh()


class ElasticsearchAtomicIndexRebuilder(ElasticsearchIndexRebuilder):
    def __init__(self, index):
        self.alias = index
        self.index = index.backend.index_class(
            index.backend, self.alias.name + "_" + get_random_string(7).lower()
        )

    def reset_index(self):
        # Delete old index using the alias
        # This should delete both the alias and the index
        self.alias.delete()

        # Create new index
        self.index.put()

        # Create a new alias
        self.index.put_alias(self.alias.name)

    def start(self):
        # Create the new index
        self.index.put()

        return self.index

    def finish(self):
        self.index.refresh()

        if self.alias.is_alias():
            # Update existing alias, then delete the old index

            # Find index that alias currently points to, we'll delete it after
            # updating the alias
            old_index = self.alias.aliased_indices()

            # Update alias to point to new index
            self.index.put_alias(self.alias.name)

            # Delete old index
            # aliased_indices() can return multiple indices. Delete them all
            for index in old_index:
                if index.name != self.index.name:
                    index.delete()

        else:
            # self.alias doesn't currently refer to an alias in Elasticsearch.
            # This means that either nothing exists in ES with that name or
            # there is currently an index with the that name

            # Run delete on the alias, just in case it is currently an index.
            # This happens on the first rebuild after switching ATOMIC_REBUILD on
            self.alias.delete()

            # Create the alias
            self.index.put_alias(self.alias.name)


class Elasticsearch7SearchBackend(BaseSearchBackend):
    mapping_class = Elasticsearch7Mapping
    index_class = Elasticsearch7Index
    query_compiler_class = Elasticsearch7SearchQueryCompiler
    autocomplete_query_compiler_class = Elasticsearch7AutocompleteQueryCompiler
    results_class = Elasticsearch7SearchResults
    basic_rebuilder_class = ElasticsearchIndexRebuilder
    atomic_rebuilder_class = ElasticsearchAtomicIndexRebuilder
    catch_indexing_errors = True
    timeout_kwarg_name = "timeout"

    settings = {
        "settings": {
            "analysis": {
                "analyzer": {
                    "ngram_analyzer": {
                        "type": "custom",
                        "tokenizer": "lowercase",
                        "filter": ["asciifolding", "ngram"],
                    },
                    "edgengram_analyzer": {
                        "type": "custom",
                        "tokenizer": "lowercase",
                        "filter": ["asciifolding", "edgengram"],
                    },
                },
                "tokenizer": {
                    "ngram_tokenizer": {
                        "type": "ngram",
                        "min_gram": 3,
                        "max_gram": 15,
                    },
                    "edgengram_tokenizer": {
                        "type": "edge_ngram",
                        "min_gram": 2,
                        "max_gram": 15,
                        "side": "front",
                    },
                },
                "filter": {
                    "ngram": {"type": "ngram", "min_gram": 3, "max_gram": 15},
                    "edgengram": {"type": "edge_ngram", "min_gram": 1, "max_gram": 15},
                },
            },
            "index": {
                "max_ngram_diff": 12,
            },
        }
    }

    def _get_host_config_from_url(self, url):
        """Given a parsed URL, return the host configuration to be added to self.hosts"""
        use_ssl = url.scheme == "https"
        port = url.port or (443 if use_ssl else 80)

        http_auth = None
        if url.username is not None and url.password is not None:
            http_auth = (url.username, url.password)

        return {
            "host": url.hostname,
            "port": port,
            "url_prefix": url.path,
            "use_ssl": use_ssl,
            "verify_certs": use_ssl,
            "http_auth": http_auth,
        }

    def _get_options_from_host_urls(self, urls):
        """Given a list of parsed URLs, return a dict of additional options to be passed into the
        Elasticsearch constructor; necessary for options that aren't valid as part of the 'hosts' config"""
        return {}

    def __init__(self, params):
        super().__init__(params)

        # Get settings
        self.hosts = params.pop("HOSTS", None)
        self.index_name = params.pop("INDEX", "wagtail")
        self.timeout = params.pop("TIMEOUT", 10)

        if params.pop("ATOMIC_REBUILD", False):
            self.rebuilder_class = self.atomic_rebuilder_class
        else:
            self.rebuilder_class = self.basic_rebuilder_class

        self.settings = deepcopy(
            self.settings
        )  # Make the class settings attribute as instance settings attribute
        self.settings = deep_update(self.settings, params.pop("INDEX_SETTINGS", {}))

        # Get Elasticsearch interface
        # Any remaining params are passed into the Elasticsearch constructor
        options = params.pop("OPTIONS", {})

        # If HOSTS is not set, convert URLS setting to HOSTS
        if self.hosts is None:
            es_urls = params.pop("URLS", ["http://localhost:9200"])
            # if es_urls is not a list, convert it to a list
            if isinstance(es_urls, str):
                es_urls = [es_urls]

            parsed_urls = [urlparse(url) for url in es_urls]

            self.hosts = [self._get_host_config_from_url(url) for url in parsed_urls]
            options.update(self._get_options_from_host_urls(parsed_urls))

        options[self.timeout_kwarg_name] = self.timeout

        self.es = Elasticsearch(hosts=self.hosts, **options)

    def get_index_for_model(self, model):
        # Split models up into separate indices based on their root model.
        # For example, all page-derived models get put together in one index,
        # while images and documents each have their own index.
        root_model = get_model_root(model)
        index_suffix = (
            "__"
            + root_model._meta.app_label.lower()
            + "_"
            + root_model.__name__.lower()
        )

        return self.index_class(self, self.index_name + index_suffix)

    def get_index(self):
        return self.index_class(self, self.index_name)

    def get_rebuilder(self):
        return self.rebuilder_class(self.get_index())

    def reset_index(self):
        # Use the rebuilder to reset the index
        self.get_rebuilder().reset_index()


SearchBackend = Elasticsearch7SearchBackend
