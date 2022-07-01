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

If you have disabled auto update, you must run the [](update_index) command on a regular basis to keep the index in sync with the database.

(wagtailsearch_backends_atomic_rebuild)=

## `ATOMIC_REBUILD`

```{warning}
This option may not work on Elasticsearch version 5.4.x, due to [a bug in the handling of aliases](https://github.com/elastic/elasticsearch/issues/24644) - please upgrade to 5.5 or later.
```

By default (when using the Elasticsearch backend), when the `update_index` command is run, Wagtail deletes the index and rebuilds it from scratch. This causes the search engine to not return results until the rebuild is complete and is also risky as you can't rollback if an error occurs.

Setting the `ATOMIC_REBUILD` setting to `True` makes Wagtail rebuild into a separate index while keep the old index active until the new one is fully built. When the rebuild is finished, the indexes are swapped atomically and the old index is deleted.

## `BACKEND`

Here's a list of backends that Wagtail supports out of the box.

(wagtailsearch_backends_database)=

### Database Backend (default)

`wagtail.search.backends.database`

The database search backend searches content in the database using the full text search features of the database backend in use (such as PostgreSQL FTS, SQLite FTS5).
This backend is intended to be used for development and also should be good enough to use in production on sites that don't require any Elasticsearch specific features.

(wagtailsearch_backends_elasticsearch)=

### Elasticsearch Backend

Elasticsearch versions 5, 6 and 7 are supported. Use the appropriate backend for your version:

-   `wagtail.search.backends.elasticsearch5` (Elasticsearch 5.x)
-   `wagtail.search.backends.elasticsearch6` (Elasticsearch 6.x)
-   `wagtail.search.backends.elasticsearch7` (Elasticsearch 7.x)

Prerequisites are the [Elasticsearch](https://www.elastic.co/downloads/elasticsearch) service itself and, via pip, the [elasticsearch-py](https://elasticsearch-py.readthedocs.org) package. The major version of the package must match the installed version of Elasticsearch:

```sh
pip install "elasticsearch>=5.0.0,<6.0.0"  # for Elasticsearch 5.x
```

```sh
pip install "elasticsearch>=6.4.0,<7.0.0"  # for Elasticsearch 6.x
```

```sh
pip install "elasticsearch>=7.0.0,<8.0.0"  # for Elasticsearch 7.x
```

```{warning}
Version 6.3.1 of the Elasticsearch client library is incompatible with Wagtail. Use 6.4.0 or above.
```

The backend is configured in settings:

```python
WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'wagtail.search.backends.elasticsearch5',
        'URLS': ['http://localhost:9200'],
        'INDEX': 'wagtail',
        'TIMEOUT': 5,
        'OPTIONS': {},
        'INDEX_SETTINGS': {},
    }
}
```

Other than `BACKEND`, the keys are optional and default to the values shown. Any defined key in `OPTIONS` is passed directly to the Elasticsearch constructor as case-sensitive keyword argument (e.g. `'max_retries': 1`).

A username and password may be optionally be supplied to the `URL` field to provide authentication credentials for the Elasticsearch service:

```python
WAGTAILSEARCH_BACKENDS = {
    'default': {
        ...
        'URLS': ['http://username:password@localhost:9200'],
        ...
    }
}
```

`INDEX_SETTINGS` is a dictionary used to override the default settings to create the index. The default settings are defined inside the `ElasticsearchSearchBackend` class in the module `wagtail/wagtail/search/backends/elasticsearch7.py`. Any new key is added, any existing key, if not a dictionary, is replaced with the new value. Here's a sample on how to configure the number of shards and setting the Italian LanguageAnalyzer as the default analyzer:

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

If you prefer not to run an Elasticsearch server in development or production, there are many hosted services available, including [Bonsai](https://bonsai.io/), who offer a free account suitable for testing and development. To use Bonsai:

-   Sign up for an account at `Bonsai`
-   Use your Bonsai dashboard to create a Cluster.
-   Configure `URLS` in the Elasticsearch entry in `WAGTAILSEARCH_BACKENDS` using the Cluster URL from your Bonsai dashboard
-   Run `./manage.py update_index`

### Amazon AWS Elasticsearch

The Elasticsearch backend is compatible with [Amazon Elasticsearch Service](https://aws.amazon.com/elasticsearch-service/), but requires additional configuration to handle IAM based authentication. This can be done with the [requests-aws4auth](https://pypi.python.org/pypi/requests-aws4auth) package along with the following configuration:

```python
from elasticsearch import RequestsHttpConnection
from requests_aws4auth import AWS4Auth

WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'wagtail.search.backends.elasticsearch5',
        'INDEX': 'wagtail',
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

Wagtail search backends implement the interface defined in `wagtail/wagtail/wagtailsearch/backends/base.py`. At a minimum, the backend's `search()` method must return a collection of objects or `model.objects.none()`. For a fully-featured search backend, examine the Elasticsearch backend code in `elasticsearch.py`.
