(performance_overview)=

# Performance

Wagtail is designed for speed, both in the editor interface and on the front-end, but if you want even better performance or you need to handle very high volumes of traffic, here are some tips on eking out the most from your installation.

We have tried to minimize external dependencies for a working installation of Wagtail, in order to make it as simple as possible to get going. However, a number of default settings can be configured for better performance:

## Cache

We recommend [Redis](https://redis.io/) as a fast, persistent cache. Install Redis through your package manager (on Debian or Ubuntu: `sudo apt-get install redis-server`), add `django-redis` to your `requirements.txt`, and enable it as a cache backend:

```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/dbname',
        # for django-redis < 3.8.0, use:
        # 'LOCATION': '127.0.0.1:6379',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

(custom_image_renditions_cache)=

To use a different cache backend for [caching image renditions](caching_image_renditions), configure the "renditions" backend:

```python
CACHES = {
    'default': {...},
    'renditions': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'TIMEOUT': 600,
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}
```

## Image URLs

If all you need is the URL to an image (such as for use in meta tags or other tag attributes), it is likely more efficient to use the [image serve view](using_images_outside_wagtail) and `{% image_url %}` tag:

```html+django
<meta property="og:image" content="{% image_url page.hero_image width-600 %}" />
```

Rather than finding or creating the rendition in the page request, the image serve view offloads this to a separate view, which only creates the rendition when the user requests the image (or returning an existing rendition if it already exists). This can drastically speed up page loads with many images. This may increase the number of requests handled by Wagtail if you're using an external storage backend (for example Amazon S3).

Another side benefit is it prevents errors during conversation from causing page errors. If an image is too large for Willow to handle (the size of an image can be constrained with [`WAGTAILIMAGES_MAX_IMAGE_PIXELS`](wagtailimages_max_image_pixels)), Willow may crash. As the resize is done outside the page load, the image will be missing, but the rest of the page content will remain.

The same can be achieved in Python using [`generate_image_url`](dynamic_image_urls).

## Prefetch image rendition

When using a queryset to render a list of images or objects with images, you can [prefetch the renditions](prefetching_image_renditions) needed with a single additional query. For long lists of items, or where multiple renditions are used for each item, this can provide a significant boost to performance.

(performance_frontend_caching)=

## Frontend caching proxy

Many websites use a frontend cache such as [Varnish](https://varnish-cache.org/), [Squid](http://www.squid-cache.org/), [Cloudflare](https://www.cloudflare.com/) or [CloudFront](https://aws.amazon.com/cloudfront/) to support high volumes of traffic with excellent response times. The downside of using a frontend cache though is that they don't respond well to updating content and will often keep an old version of a page cached after it has been updated.

Wagtail supports being [integrated](frontend_cache_purging) with many CDNs, so it can inform them when a page changes, so the cache can be cleared immediately and users see the changes sooner.

If you have multiple frontends configured (eg Cloudflare for one site, CloudFront for another), it's recommended to set the [`HOSTNAMES`](frontendcache_multiple_backends) key to the list of hostnames the backend can purge, to prevent unnecessary extra purge requests.

(performance_page_urls)=

## Page URLs

To fully resolve the URL of a page, Wagtail requires information from a few different sources.

The methods used to get the URL of a `Page` such as `Page.get_url` and `Page.get_full_url` optionally accept extra arguments for `request` and `current_site`. Passing these arguments enable much of underlying site-level URL information to be reused for the current request. In situations such as navigation menu generation, plus any links that appear in page content, providing `request` or `current_site` can result in a drastic reduction in the number of cache or database queries your site will generate for a given page load.

When using the [`{% pageurl %}`](pageurl_tag) or [`{% fullpageurl %}`](fullpageurl_tag) template tags, the request is automatically passed in, so no further optimization is needed.

## Search

Wagtail has strong support for [Elasticsearch](https://www.elastic.co) - both in the editor interface and for users of your site - but can fall back to a database search if Elasticsearch isn't present. Elasticsearch is faster and more powerful than the Django ORM for text search, so we recommend installing it or using a hosted service like [Searchly](http://www.searchly.com/).

For details on configuring Wagtail for Elasticsearch, see [](wagtailsearch_backends_elasticsearch).

## Database

Wagtail is tested on PostgreSQL, SQLite, MySQL and MariaDB. It may work on some third-party database backends as well, but this is not guaranteed.

We recommend PostgreSQL for production use, however, the choice of database ultimately depends on a combination of factors, including personal preference, team expertise, and specific project requirements. The most important aspect is to ensure that your selected database can meet the performance and scalability requirements of your project.

### Image attributes

For some images, it may be beneficial to lazy load images, so the rest of the page can continue to load. It can be configured site-wide [](adding_default_attributes_to_images) or per-image [](image_tag_alt). For more details you can read about the [`loading='lazy'` attribute](https://developer.mozilla.org/en-US/docs/Web/Performance/Lazy_loading#images_and_iframes) and the [`'decoding='async'` attribute](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/img#attr-decoding) or this [web.dev article on lazy loading images](https://web.dev/lazy-loading-images/).

This optimization is already handled for you for images in the admin site.

## Template fragment caching

Django supports [template fragment caching](<inv:django:std:label#topics/cache:template fragment caching>), which allows caching portions of a template. Using Django's `{% cache %}` tag natively with Wagtail can be [dangerous](https://github.com/wagtail/wagtail/issues/5074) as it can result in preview content being shown to end users. Instead, Wagtail provides 2 extra template tags: [`{% wagtailcache %}`](wagtailcache) and [`{% wagtailpagecache %}`](wagtailpagecache) which both avoid these issues.

(page_cache_key)=

## Page cache key

It's often necessary to cache a value based on an entire page, rather than a specific value. For this, {attr}`~wagtail.models.Page.cache_key` can be used to get a unique value for the state of a page. Should something about the page change, so will its cache key. You can also use the value to create longer, more specific cache keys when using Django's caching framework directly. For example:

```python
from django.core.cache import cache

result = page.expensive_operation()
cache.set("expensive_result_" + page.cache_key, result, 3600)

# Later...
cache.get("expensive_result_" + page.cache_key)
```

To modify the cache key, such as including a custom model field value, you can override {attr}`~wagtail.models.Page.get_cache_key_components`:

```python
def get_cache_key_components(self):
    components = super().get_cache_key_components()
    components.append(self.external_slug)
    return components
```

Manually updating a page might not result in a change to its cache key, unless the default component field values are modified directly. To be sure of a change in the cache key value, try saving the changes to a `Revision` instead, and then publishing it.

## Django

Wagtail is built on Django. Many of the [performance tips](inv:django#topics/performance) set out by Django are also applicable to Wagtail.
