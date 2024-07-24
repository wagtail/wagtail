from django.core.exceptions import ImproperlyConfigured
from elasticsearch import NotFoundError

from wagtail.search.backends.elasticsearch7 import (
    Elasticsearch7AutocompleteQueryCompiler,
    Elasticsearch7Index,
    Elasticsearch7Mapping,
    Elasticsearch7SearchBackend,
    Elasticsearch7SearchQueryCompiler,
    Elasticsearch7SearchResults,
)
from wagtail.search.index import class_is_indexed


class Elasticsearch8Mapping(Elasticsearch7Mapping):
    pass


class Elasticsearch8Index(Elasticsearch7Index):
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
        self.es.indices.put_mapping(index=self.name, **mapping.get_mapping())

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


class Elasticsearch8SearchQueryCompiler(Elasticsearch7SearchQueryCompiler):
    mapping_class = Elasticsearch8Mapping


class Elasticsearch8SearchResults(Elasticsearch7SearchResults):
    def _backend_do_search(self, body, **kwargs):
        # As of Elasticsearch 7.15, the 'body' parameter is deprecated; instead, the top-level
        # keys of the body dict are now kwargs in their own right
        return self.backend.es.search(**body, **kwargs)


class Elasticsearch8AutocompleteQueryCompiler(Elasticsearch7AutocompleteQueryCompiler):
    mapping_class = Elasticsearch8Mapping


class Elasticsearch8SearchBackend(Elasticsearch7SearchBackend):
    mapping_class = Elasticsearch8Mapping
    index_class = Elasticsearch8Index
    query_compiler_class = Elasticsearch8SearchQueryCompiler
    autocomplete_query_compiler_class = Elasticsearch8AutocompleteQueryCompiler
    results_class = Elasticsearch8SearchResults
    timeout_kwarg_name = "request_timeout"

    def _get_host_config_from_url(self, url):
        """Given a parsed URL, return the host configuration to be added to self.hosts"""
        use_ssl = url.scheme == "https"
        port = url.port or (443 if use_ssl else 80)

        # the verify_certs and http_auth options are no longer valid in Elasticsearch 8
        return {
            "host": url.hostname,
            "port": port,
            "path_prefix": url.path,
            "scheme": url.scheme,
        }

    def _get_options_from_host_urls(self, urls):
        """Given a list of parsed URLs, return a dict of additional options to be passed into the
        Elasticsearch constructor; necessary for options that aren't valid as part of the 'hosts' config"""
        opts = super()._get_options_from_host_urls(urls)

        basic_auth = (urls[0].username, urls[0].password)
        # Ensure that all urls have the same credentials
        if any((url.username, url.password) != basic_auth for url in urls):
            raise ImproperlyConfigured(
                "Elasticsearch host configuration is invalid. "
                "Elasticsearch 8 does not support multiple hosts with differing authentication credentials."
            )

        if basic_auth != (None, None):
            opts["basic_auth"] = basic_auth

        return opts


SearchBackend = Elasticsearch8SearchBackend
