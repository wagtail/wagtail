from copy import deepcopy

from elasticsearch import VERSION as ELASTICSEARCH_VERSION
from elasticsearch import NotFoundError
from elasticsearch.helpers import bulk

from wagtail.search.backends.elasticsearch6 import (
    Elasticsearch6AutocompleteQueryCompiler,
    Elasticsearch6Index,
    Elasticsearch6Mapping,
    Elasticsearch6SearchBackend,
    Elasticsearch6SearchQueryCompiler,
    Elasticsearch6SearchResults,
)
from wagtail.search.index import class_is_indexed

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


class Elasticsearch7AutocompleteQueryCompiler(
    Elasticsearch6AutocompleteQueryCompiler, Elasticsearch6SearchQueryCompiler
):
    pass


class Elasticsearch7SearchBackend(Elasticsearch6SearchBackend):
    mapping_class = Elasticsearch7Mapping
    index_class = Elasticsearch7Index
    query_compiler_class = Elasticsearch7SearchQueryCompiler
    autocomplete_query_compiler_class = Elasticsearch7AutocompleteQueryCompiler
    results_class = Elasticsearch7SearchResults
    is_deprecated = False

    settings = deepcopy(Elasticsearch6SearchBackend.settings)
    settings["settings"]["index"] = {"max_ngram_diff": 12}

    # Fix ElasticsearchDeprecationWarnings for tokenizer names and token filter names:
    # - [edgeNGram] -> [edge_ngram]
    # - [nGram] -> [ngram]
    settings["settings"]["analysis"]["filter"]["edgengram"]["type"] = "edge_ngram"
    settings["settings"]["analysis"]["filter"]["ngram"]["type"] = "ngram"
    settings["settings"]["analysis"]["tokenizer"]["edgengram_tokenizer"][
        "type"
    ] = "edge_ngram"
    settings["settings"]["analysis"]["tokenizer"]["ngram_tokenizer"]["type"] = "ngram"


SearchBackend = Elasticsearch7SearchBackend
