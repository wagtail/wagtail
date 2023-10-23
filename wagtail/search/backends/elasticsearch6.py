import copy
import warnings
from urllib.parse import urlparse

from elasticsearch import Elasticsearch

from wagtail.search.backends.base import BaseSearchBackend, get_model_root
from wagtail.search.index import get_indexed_models
from wagtail.search.query import Fuzzy, MatchAll, Not, Phrase, PlainText
from wagtail.utils.deprecation import RemovedInWagtail60Warning
from wagtail.utils.utils import deep_update

from .elasticsearch5 import (
    Elasticsearch5Index,
    Elasticsearch5Mapping,
    Elasticsearch5SearchQueryCompiler,
    Elasticsearch5SearchResults,
    ElasticsearchAtomicIndexRebuilder,
    ElasticsearchAutocompleteQueryCompilerImpl,
    ElasticsearchIndexRebuilder,
)


class Field:
    def __init__(self, field_name, boost=1):
        self.field_name = field_name
        self.boost = boost


class Elasticsearch6Mapping(Elasticsearch5Mapping):
    all_field_name = "_all_text"
    edgengrams_field_name = "_edgengrams"

    def get_boost_field_name(self, boost):
        # replace . with _ to avoid issues with . in field names
        boost = str(float(boost)).replace(".", "_")
        return f"{self.all_field_name}_boost_{boost}"

    def get_document_id(self, obj):
        return str(obj.pk)

    def get_document_type(self):
        return "doc"

    def get_mapping(self):
        mapping = super().get_mapping()

        # Add _all_text field
        mapping[self.get_document_type()]["properties"][self.all_field_name] = {
            "type": "text"
        }

        unique_boosts = set()

        # Replace {"include_in_all": true} with {"copy_to": ["_all_text", "_all_text_boost_2"]}
        def replace_include_in_all(mapping):
            for field_mapping in mapping["properties"].values():
                if "include_in_all" in field_mapping:
                    if field_mapping["include_in_all"]:
                        field_mapping["copy_to"] = self.all_field_name

                        if "boost" in field_mapping:
                            # added to unique_boosts to avoid duplicate fields, or cases like 2.0 and 2
                            unique_boosts.add(field_mapping["boost"])
                            field_mapping["copy_to"] = [
                                field_mapping["copy_to"],
                                self.get_boost_field_name(field_mapping["boost"]),
                            ]
                            del field_mapping["boost"]

                    del field_mapping["include_in_all"]

                if field_mapping["type"] == "nested":
                    replace_include_in_all(field_mapping)

        replace_include_in_all(mapping[self.get_document_type()])
        for boost in unique_boosts:
            mapping[self.get_document_type()]["properties"][
                self.get_boost_field_name(boost)
            ] = {"type": "text"}

        return mapping


class Elasticsearch6Index(Elasticsearch5Index):
    pass


class Elasticsearch6SearchQueryCompiler(Elasticsearch5SearchQueryCompiler):
    mapping_class = Elasticsearch6Mapping

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        remapped_fields = self.remapped_fields or [self.mapping.all_field_name]
        remapped_fields = [Field(field) for field in remapped_fields]

        models = get_indexed_models()
        unique_boosts = set()
        for model in models:
            for field in model.get_searchable_search_fields():
                if field.boost:
                    unique_boosts.add(float(field.boost))

        self.remapped_fields = remapped_fields + [
            Field(self.mapping.get_boost_field_name(boost), boost)
            for boost in unique_boosts
        ]

    def get_boosted_fields(self, fields):
        boosted_fields = []
        if not isinstance(fields, list):
            fields = [fields]
        for field in fields:
            if field.boost != 1:
                boosted_fields.append(f"{field.field_name}^{field.boost}")
            else:
                boosted_fields.append(field.field_name)
        return boosted_fields

    def _compile_fuzzy_query(self, query, fields):
        if len(fields) == 1:
            return {
                "match": {
                    fields[0]: {
                        "query": query.query_string,
                        "fuzziness": "AUTO",
                    }
                }
            }
        return {
            "multi_match": {
                "query": query.query_string,
                "fields": self.get_boosted_fields(fields),
                "fuzziness": "AUTO",
            }
        }

    def _compile_plaintext_query(self, query, fields, boost=1.0):
        return super()._compile_plaintext_query(
            query, self.get_boosted_fields(fields), boost
        )

    def _compile_phrase_query(self, query, fields):
        return super()._compile_phrase_query(query, self.get_boosted_fields(fields))

    def get_inner_query(self):
        if self.remapped_fields:
            fields = self.remapped_fields
        else:
            fields = [self.mapping.all_field_name]

        if len(fields) == 0:
            # No fields. Return a query that'll match nothing
            return {"bool": {"mustNot": {"match_all": {}}}}

        # Handle MatchAll and PlainText separately as they were supported
        # before "search query classes" was implemented and we'd like to
        # keep the query the same as before
        if isinstance(self.query, MatchAll):
            return {"match_all": {}}

        elif isinstance(self.query, PlainText):
            return self._compile_plaintext_query(self.query, fields)

        elif isinstance(self.query, Phrase):
            return self._compile_phrase_query(self.query, fields)

        elif isinstance(self.query, Fuzzy):
            return self._compile_fuzzy_query(self.query, fields)

        elif isinstance(self.query, Not):
            return {
                "bool": {
                    "mustNot": [
                        self._compile_query(self.query.subquery, field)
                        for field in fields
                    ]
                }
            }

        else:
            if len(fields) == 1:
                return self._compile_query(self.query, fields[0])
            else:
                # Compile a query for each field then combine with disjunction
                # max (or operator which takes the max score out of each of the
                # field queries)
                field_queries = []
                for field in fields:
                    field_queries.append(self._compile_query(self.query, field))

                return {"dis_max": {"queries": field_queries}}


class Elasticsearch6SearchResults(Elasticsearch5SearchResults):
    pass


class Elasticsearch6AutocompleteQueryCompiler(
    ElasticsearchAutocompleteQueryCompilerImpl, Elasticsearch6SearchQueryCompiler
):
    def get_inner_query(self):
        fields = self.remapped_fields or [self.mapping.edgengrams_field_name]
        fields = [Field(field) for field in fields]
        if len(fields) == 0:
            # No fields. Return a query that'll match nothing
            return {"bool": {"mustNot": {"match_all": {}}}}

        return self._compile_plaintext_query(self.query, fields)


class Elasticsearch6SearchBackend(BaseSearchBackend):
    mapping_class = Elasticsearch6Mapping
    index_class = Elasticsearch6Index
    query_compiler_class = Elasticsearch6SearchQueryCompiler
    autocomplete_query_compiler_class = Elasticsearch6AutocompleteQueryCompiler
    results_class = Elasticsearch6SearchResults
    basic_rebuilder_class = ElasticsearchIndexRebuilder
    atomic_rebuilder_class = ElasticsearchAtomicIndexRebuilder
    catch_indexing_errors = True
    timeout_kwarg_name = "timeout"
    is_deprecated = True  # overriden on subclasses which are not deprecated

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
                        "type": "nGram",
                        "min_gram": 3,
                        "max_gram": 15,
                    },
                    "edgengram_tokenizer": {
                        "type": "edgeNGram",
                        "min_gram": 2,
                        "max_gram": 15,
                        "side": "front",
                    },
                },
                "filter": {
                    "ngram": {"type": "nGram", "min_gram": 3, "max_gram": 15},
                    "edgengram": {"type": "edgeNGram", "min_gram": 1, "max_gram": 15},
                },
            }
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

        if self.is_deprecated:
            warnings.warn(
                f"The {self.__module__} search backend is deprecated and will be removed in a future release. "
                "Please upgrade to Elasticsearch 7 or above.",
                RemovedInWagtail60Warning,
            )

        # Get settings
        self.hosts = params.pop("HOSTS", None)
        self.index_name = params.pop("INDEX", "wagtail")
        self.timeout = params.pop("TIMEOUT", 10)

        if params.pop("ATOMIC_REBUILD", False):
            self.rebuilder_class = self.atomic_rebuilder_class
        else:
            self.rebuilder_class = self.basic_rebuilder_class

        self.settings = copy.deepcopy(
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


SearchBackend = Elasticsearch6SearchBackend
