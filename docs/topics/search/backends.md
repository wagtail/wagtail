(wagtailsearch_backends)=

# Backends

Wagtailsearch has support for multiple backends, giving you the choice between using the database for search or an external service such as Elasticsearch.

You can configure which backend to use with the `WAGTAILSEARCH_BACKENDS` setting:

```python
WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'wagtail.search.backends.database',
    }
}
```

(wagtailsearch_backends_auto_update)=

## `AUTO_UPDATE`

By default, Wagtail will automatically keep all indexes up to date. This could impact performance when editing content, especially if your index is hosted on an external service.

The `AUTO_UPDATE` setting allows you to disable this on a per-index basis:

```python
WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': ...,
        'AUTO_UPDATE': False,
    }
}
```

If you have disabled auto-update, you must run the [](update_index) command on a regular basis to keep the index in sync with the database.

(wagtailsearch_backends_atomic_rebuild)=

## `ATOMIC_REBUILD`

By default (when using the Elasticsearch backend), Wagtail creates a new index when the `update_index` is run, reindexes the content into the new index then, using an alias, activates the new index. It then deletes the old index.

If creating new indexes is not an option for you, you can disable this behaviour by setting `ATOMIC_REBUILD` to `False`. This will make Wagtail delete the index then build a new one. Note that this will cause the search engine to not return results until the rebuild is complete.

## `BACKEND`

Here's a list of backends that Wagtail supports out of the box.

(wagtailsearch_backends_database)=

### Database Backend (default)

`wagtail.search.backends.database`

The database search backend searches content in the database using the full-text search features of the database backend in use (such as PostgreSQL FTS, SQLite FTS5).
This backend is intended to be used for development and also should be good enough to use in production on sites that don't require any Elasticsearch specific features.

If you use the PostgreSQL database backend, you must add `django.contrib.postgres` to your [`INSTALLED_APPS`](inv:django:std:setting#INSTALLED_APPS) setting.

(wagtailsearch_backends_elasticsearch)=

### Elasticsearch Backend

Elasticsearch versions 7, 8 and 9 are supported. Use the appropriate backend for your version:

-   `wagtail.search.backends.elasticsearch7` (Elasticsearch 7.x)
-   `wagtail.search.backends.elasticsearch8` (Elasticsearch 8.x)
-   `wagtail.search.backends.elasticsearch9` (Elasticsearch 9.x)

Prerequisites are the [Elasticsearch](https://www.elastic.co/downloads/elasticsearch) service itself and, via pip, the [elasticsearch-py](https://elasticsearch-py.readthedocs.io/) package. The major version of the package must match the installed version of Elasticsearch:

```sh
pip install "elasticsearch>=7.0.0,<8.0.0"  # for Elasticsearch 7.x
```

```sh
pip install "elasticsearch>=8.0.0,<9.0.0"  # for Elasticsearch 8.x
```

```sh
pip install "elasticsearch>=9.0.0,<10.0.0"  # for Elasticsearch 9.x
```

The backend is configured in settings:

```python
WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'wagtail.search.backends.elasticsearch9',
        'URLS': ['https://localhost:9200'],
        'INDEX_PREFIX': '',
        'TIMEOUT': 5,
        'OPTIONS': {},
        'INDEX_SETTINGS': {},
    }
}
```

Other than `BACKEND`, the keys are optional and default to the values shown. Any defined key in `OPTIONS` is passed directly to the Elasticsearch constructor as a case-sensitive keyword argument (for example `'max_retries': 1`).

`INDEX_PREFIX` specifies a string such as `"mysite_"` to be used as a prefix of all index names. This allows multiple Wagtail instances to share the same Elasticsearch server. An index will be created for each model according to the format `{prefix}{app_label}_{model_name}`, for example: `mysite_wagtailcore_page`.

A username and password may be optionally supplied to the `URL` field to provide authentication credentials for the Elasticsearch service:

```python
WAGTAILSEARCH_BACKENDS = {
    'default': {
        ...
        'URLS': ['https://username:password@localhost:9200'],
        ...
    }
}
```

`INDEX_SETTINGS` is a dictionary used to override the default settings to create the index. The default settings are as follows:

```python
{
    "settings": {
        "analysis": {
            "analyzer": {
                "ngram_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["asciifolding", "lowercase", "ngram"],
                },
                "edgengram_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["asciifolding", "lowercase", "edgengram"],
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
```

Any new key defined in `INDEX_SETTINGS` is added to the defaults, and any existing key, if not a dictionary, is replaced with the new value. Here's a sample of how to configure the number of shards and set the Italian LanguageAnalyzer as the default analyzer:

```python
WAGTAILSEARCH_BACKENDS = {
    'default': {
        ...,
        'INDEX_SETTINGS': {
            'settings': {
                'index': {
                    'number_of_shards': 1,
                },
                'analysis': {
                    'analyzer': {
                        'default': {
                            'type': 'italian'
                        }
                    }
                }
            }
        }
    }
```

If you prefer not to run an Elasticsearch server in development or production, there are many hosted services available, including [Bonsai](https://bonsai.io/), which offers a free account suitable for testing and development. To use Bonsai:

-   Sign up for an account at `Bonsai`
-   Use your Bonsai dashboard to create a Cluster.
-   Configure `URLS` in the Elasticsearch entry in `WAGTAILSEARCH_BACKENDS` using the Cluster URL from your Bonsai dashboard
-   Run `./manage.py update_index`

(opensearch)=

### OpenSearch

OpenSearch is a community-driven search engine originally created as a fork of Elasticsearch. OpenSearch versions 2 and 3 are supported. Use the appropriate backend for your version:

-   `wagtail.search.backends.opensearch2` (OpenSearch 2.x)
-   `wagtail.search.backends.opensearch3` (OpenSearch 3.x)

Prerequisites are the [OpenSearch](https://opensearch.org/downloads/) service itself and, via pip, the [opensearch-py](https://opensearch-project.github.io/opensearch-py/) package. The major version of the package must match the installed version of Elasticsearch:

```sh
pip install "opensearch-py>=2,<3"  # for OpenSearch 2.x
```

```sh
pip install "opensearch-py>=3,<4"  # for OpenSearch 3.x
```

The backend is configured in settings:

```python
WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'wagtail.search.backends.opensearch3',
        'URLS': ['https://localhost:9200'],
        'INDEX_PREFIX': 'wagtail_',
        'TIMEOUT': 5,
        'OPTIONS': {},
        'INDEX_SETTINGS': {},
    }
}
```

The default configuration of OpenSearch has SSL enabled and certificate-based authentication. This can be configured as follows:

```python
WAGTAILSEARCH_BACKENDS = {
    "default": {
        "BACKEND": "wagtail.search.backends.opensearch3",
        "INDEX_PREFIX": "wagtail_",
        "URLS": ["https://localhost:9200"],
        "OPTIONS": {
            "verify_certs": True,
            "ca_certs": "/path/to/root-ca.pem",
            "client_cert": "/path/to/user.pem",
            "client_key": "/path/to/user-key.pem",
        },
    },
}
```

If using the [demo configuration](https://docs.opensearch.org/latest/security/configuration/demo-configuration/), the certificates can be found in the Opensearch config directory (typically `/usr/share/opensearch/config/` or `/etc/opensearch/`); the client certificate and key are named `kirk.pem` and `kirk-key.pem` respectively.

### Amazon AWS OpenSearch

The OpenSearch backend is compatible with [Amazon OpenSearch Service](https://aws.amazon.com/opensearch-service/), but requires additional configuration to handle IAM based authentication. This can be done with the [requests-aws4auth](https://pypi.org/project/requests-aws4auth/) package along with the following configuration:

```python
from elasticsearch import RequestsHttpConnection
from requests_aws4auth import AWS4Auth

WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'wagtail.search.backends.opensearch3',
        'INDEX_PREFIX': 'wagtail_',
        'TIMEOUT': 5,
        'HOSTS': [{
            'host': 'YOURCLUSTER.REGION.es.amazonaws.com',
            'port': 443,
            'use_ssl': True,
            'verify_certs': True,
            'http_auth': AWS4Auth('ACCESS_KEY', 'SECRET_KEY', 'REGION', 'es'),
        }],
        'OPTIONS': {
            'connection_class': RequestsHttpConnection,
        },
    }
}
```

## Rolling Your Own

Wagtail's search implementation is provided by the [django-modelsearch](https://github.com/kaedroho/django-modelsearch) package, and backends implement the interface defined in `modelsearch/backends/base.py`. At a minimum, the backend's `search()` method must return a collection of objects or `model.objects.none()`.
