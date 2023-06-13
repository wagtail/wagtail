import copy
from urllib.parse import urlparse
from warnings import warn

from elasticsearch import NotFoundError
from wagtail.search.backends.elasticsearch7 import (
    Elasticsearch7Index,
    Elasticsearch7Mapping,
    Elasticsearch7SearchBackend,
    Elasticsearch7SearchQueryCompiler,
    Elasticsearch7SearchResults,
    ElasticsearchAutocompleteQueryCompilerImpl,
)
from wagtail.search.index import class_is_indexed
from wagtail.utils.utils import deep_update


class Elasticsearch8Mapping(Elasticsearch7Mapping):
    def get_field_mapping(self, field):
        # Boost is no longer supported during index, rather use it while querying.
        if hasattr(field, "boost"):
            warn("Elasticsearch8 backend does not support boost on index.")
            field.boost = None

        return super().get_field_mapping(field)


class Elasticsearch8Index(Elasticsearch7Index):
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
        
    def put(self):
        self.es.indices.create(index=self.name, settings=self.backend.settings)

    def delete(self):
        try:
            self.es.indices.delete(index=self.name)
        except NotFoundError:
            pass

    def exists(self):
        return self.es.indices.exists(index=self.name)

    def refresh(self):
        self.es.indices.refresh(index=self.name)
        


class Elasticsearch8SearchQueryCompiler(Elasticsearch7SearchQueryCompiler):
    mapping_class = Elasticsearch8Mapping


class Elasticsearch8SearchResults(Elasticsearch7SearchResults):
    pass


class Elasticsearch8AutocompleteQueryCompiler(
    Elasticsearch7SearchQueryCompiler, ElasticsearchAutocompleteQueryCompilerImpl
):
    pass


class Elasticsearch8SearchBackend(Elasticsearch7SearchBackend):
    mapping_class = Elasticsearch8Mapping
    index_class = Elasticsearch8Index
    query_compiler_class = Elasticsearch8SearchQueryCompiler
    autocomplete_query_compiler_class = Elasticsearch8AutocompleteQueryCompiler
    results_class = Elasticsearch8SearchResults

    settings = copy.deepcopy(Elasticsearch7SearchBackend.settings)
    settings = settings["settings"]

    def _get_settings(self, index_settings):

        # Make the class settings attribute as instance settings attribute
        settings = copy.deepcopy(self.settings)

        # To also support the old notation of settings, we include this line
        index_settings = index_settings.get("settings", index_settings)

        return deep_update(settings, index_settings)

    def _convert_urls_to_hosts(self, es_urls):
        hosts = []

        # if es_urls is not a list, convert it to a list
        if isinstance(es_urls, str):
            es_urls = [es_urls]

        for url in es_urls:
            parsed_url = urlparse(url)

            use_ssl = parsed_url.scheme == "https"
            port = parsed_url.port or (443 if use_ssl else 80)

            hosts.append(
                {
                    "host": parsed_url.hostname,
                    "port": port,
                    "url_prefix": parsed_url.path,
                    "use_ssl": use_ssl,
                }
            )

        return hosts


SearchBackend = Elasticsearch8SearchBackend
