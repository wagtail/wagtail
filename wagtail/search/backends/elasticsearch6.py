import copy
import warnings
from collections import OrderedDict
from urllib.parse import urlparse

from django.utils.crypto import get_random_string
from elasticsearch import Elasticsearch, NotFoundError
from elasticsearch.helpers import bulk

from wagtail.search.backends.base import (
    BaseSearchBackend,
    BaseSearchResults,
    FilterFieldError,
    get_model_root,
)
from wagtail.search.index import class_is_indexed, get_indexed_models
from wagtail.search.query import Fuzzy, MatchAll, Not, Phrase, PlainText
from wagtail.utils.deprecation import RemovedInWagtail60Warning
from wagtail.utils.utils import deep_update

from .elasticsearch5 import (
    Elasticsearch5Mapping,
    Elasticsearch5SearchQueryCompiler,
    ElasticsearchAutocompleteQueryCompilerImpl,
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


class Elasticsearch6Index:
    def __init__(self, backend, name):
        self.backend = backend
        self.es = backend.es
        self.mapping_class = backend.mapping_class
        self.name = name

    def put(self):
        self.es.indices.create(self.name, self.backend.settings)

    def delete(self):
        try:
            self.es.indices.delete(self.name)
        except NotFoundError:
            pass

    def exists(self):
        return self.es.indices.exists(self.name)

    def is_alias(self):
        return self.es.indices.exists_alias(name=self.name)

    def aliased_indices(self):
        """
        If this index object represents an alias (which appear the same in the
        Elasticsearch API), this method can be used to fetch the list of indices
        the alias points to.

        Use the is_alias method if you need to find out if this an alias. This
        returns an empty list if called on an index.
        """
        return [
            self.backend.index_class(self.backend, index_name)
            for index_name in self.es.indices.get_alias(name=self.name).keys()
        ]

    def put_alias(self, name):
        """
        Creates a new alias to this index. If the alias already exists it will
        be repointed to this index.
        """
        self.es.indices.put_alias(name=name, index=self.name)

    def add_model(self, model):
        # Get mapping
        mapping = self.mapping_class(model)

        # Put mapping
        self.es.indices.put_mapping(
            # pass update_all_types=True as a workaround to avoid "Can't redefine search field" errors -
            # see https://github.com/wagtail/wagtail/issues/2968
            index=self.name,
            doc_type=mapping.get_document_type(),
            body=mapping.get_mapping(),
            update_all_types=True,
        )

    def add_item(self, item):
        # Make sure the object can be indexed
        if not class_is_indexed(item.__class__):
            return

        # Get mapping
        mapping = self.mapping_class(item.__class__)

        # Add document to index
        self.es.index(
            self.name,
            mapping.get_document_type(),
            mapping.get_document(item),
            id=mapping.get_document_id(item),
        )

    def add_items(self, model, items):
        if not class_is_indexed(model):
            return

        # Get mapping
        mapping = self.mapping_class(model)
        doc_type = mapping.get_document_type()

        # Create list of actions
        actions = []
        for item in items:
            # Create the action
            action = {
                "_type": doc_type,
                "_id": mapping.get_document_id(item),
            }
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
            self.es.delete(
                self.name,
                mapping.get_document_type(),
                mapping.get_document_id(item),
            )
        except NotFoundError:
            pass  # Document doesn't exist, ignore this exception

    def refresh(self):
        self.es.indices.refresh(self.name)

    def reset(self):
        # Delete old index
        self.delete()

        # Create new index
        self.put()


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


class Elasticsearch6SearchResults(BaseSearchResults):
    fields_param_name = "stored_fields"
    supports_facet = True

    def facet(self, field_name):
        # Get field
        field = self.query_compiler._get_filterable_field(field_name)
        if field is None:
            raise FilterFieldError(
                'Cannot facet search results with field "'
                + field_name
                + "\". Please add index.FilterField('"
                + field_name
                + "') to "
                + self.query_compiler.queryset.model.__name__
                + ".search_fields.",
                field_name=field_name,
            )

        # Build body
        body = self._get_es_body()
        column_name = self.query_compiler.mapping.get_field_column_name(field)

        body["aggregations"] = {
            field_name: {
                "terms": {
                    "field": column_name,
                    "missing": 0,
                }
            }
        }

        # Send to Elasticsearch
        response = self._backend_do_search(
            body,
            index=self.backend.get_index_for_model(
                self.query_compiler.queryset.model
            ).name,
            size=0,
        )

        return OrderedDict(
            [
                (bucket["key"] if bucket["key"] != 0 else None, bucket["doc_count"])
                for bucket in response["aggregations"][field_name]["buckets"]
            ]
        )

    def _get_es_body(self, for_count=False):
        body = {"query": self.query_compiler.get_query()}

        if not for_count:
            sort = self.query_compiler.get_sort()

            if sort is not None:
                body["sort"] = sort

        return body

    def _get_results_from_hits(self, hits):
        """
        Yields Django model instances from a page of hits returned by Elasticsearch
        """
        # Get pks from results
        pks = [hit["fields"]["pk"][0] for hit in hits]
        scores = {str(hit["fields"]["pk"][0]): hit["_score"] for hit in hits}

        # Initialise results dictionary
        results = {str(pk): None for pk in pks}

        # Find objects in database and add them to dict
        for obj in self.query_compiler.queryset.filter(pk__in=pks):
            results[str(obj.pk)] = obj

            if self._score_field:
                setattr(obj, self._score_field, scores.get(str(obj.pk)))

        # Yield results in order given by Elasticsearch
        for pk in pks:
            result = results[str(pk)]
            if result:
                yield result

    def _backend_do_search(self, body, **kwargs):
        # Send the search query to the backend. Wrapped here so that it can be overridden
        # to handle different calling conventions for the 'body' parameter
        return self.backend.es.search(body=body, **kwargs)

    def _do_search(self):
        PAGE_SIZE = 100

        if self.stop is not None:
            limit = self.stop - self.start
        else:
            limit = None

        use_scroll = limit is None or limit > PAGE_SIZE

        body = self._get_es_body()
        params = {
            "index": self.backend.get_index_for_model(
                self.query_compiler.queryset.model
            ).name,
            "_source": False,
            self.fields_param_name: "pk",
        }

        if use_scroll:
            params.update(
                {
                    "scroll": "2m",
                    "size": PAGE_SIZE,
                }
            )

            # The scroll API doesn't support offset, manually skip the first results
            skip = self.start

            # Send to Elasticsearch
            page = self._backend_do_search(body, **params)

            while True:
                hits = page["hits"]["hits"]

                if len(hits) == 0:
                    break

                # Get results
                if skip < len(hits):
                    for result in self._get_results_from_hits(hits):
                        if limit is not None and limit == 0:
                            break

                        if skip == 0:
                            yield result

                            if limit is not None:
                                limit -= 1
                        else:
                            skip -= 1

                    if limit is not None and limit == 0:
                        break
                else:
                    # Skip whole page
                    skip -= len(hits)

                # Fetch next page of results
                if "_scroll_id" not in page:
                    break

                page = self.backend.es.scroll(scroll_id=page["_scroll_id"], scroll="2m")

            # Clear the scroll
            if "_scroll_id" in page:
                self.backend.es.clear_scroll(scroll_id=page["_scroll_id"])
        else:
            params.update(
                {
                    "from_": self.start,
                    "size": limit or PAGE_SIZE,
                }
            )

            # Send to Elasticsearch
            hits = self._backend_do_search(body, **params)["hits"]["hits"]

            # Get results
            for result in self._get_results_from_hits(hits):
                yield result

    def _do_count(self):
        # Get count
        hit_count = self.backend.es.count(
            index=self.backend.get_index_for_model(
                self.query_compiler.queryset.model
            ).name,
            body=self._get_es_body(for_count=True),
        )["count"]

        # Add limits
        hit_count -= self.start
        if self.stop is not None:
            hit_count = min(hit_count, self.stop - self.start)

        return max(hit_count, 0)


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
