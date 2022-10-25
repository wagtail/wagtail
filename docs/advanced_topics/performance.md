# Performance

Wagtail is designed for speed, both in the editor interface and on the front-end, but if you want even better performance or you need to handle very high volumes of traffic, here are some tips on eking out the most from your installation.

## Editor interface

We have tried to minimise external dependencies for a working installation of Wagtail, in order to make it as simple as possible to get going. However, a number of default settings can be configured for better performance:

### Cache

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

### Caching image renditions

If you define a cache named 'renditions' (typically alongside your 'default' cache),
Wagtail will cache image rendition lookups, which may improve the performance of pages
which include many images.

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

### Image URLs

If all you need is the URL to an image (such as for use in meta tags or other tag attributes), it is likely more efficient to use the [image serve view](using_images_outside_wagtail) and `{% image_url %}` tag:

```html+django
<meta property="og:image" content="{% image_url page.hero_image width-600 %}" />
```

Rather than finding or creating the rendition in the page request, the image serve view offloads this to a separate view, which only creates the rendition when the user requests the image (or returning an existing rendition if it already exists). This can drastically speed up page loads with many images. This may increase the number of requests handled by Wagtail if you're using an external storage backend (for example Amazon S3).

Another side benefit is it prevents errors during conversation from causing page errors. If an image is too large for Willow to handle (the size of an image can be constrained with [`WAGTAILIMAGES_MAX_IMAGE_PIXELS`](wagtailimages_max_image_pixels)), Willow may crash. As the resize is done outside the page load, the image will be missing, but the rest of the page content will remain.

The same can be achieved in Python using [`generate_image_url`](dynamic_image_urls).

### Search

Wagtail has strong support for [Elasticsearch](https://www.elastic.co) - both in the editor interface and for users of your site - but can fall back to a database search if Elasticsearch isn't present. Elasticsearch is faster and more powerful than the Django ORM for text search, so we recommend installing it or using a hosted service like [Searchly](http://www.searchly.com/).

For details on configuring Wagtail for Elasticsearch, see [](wagtailsearch_backends_elasticsearch).

### Database

Wagtail is tested on PostgreSQL, SQLite and MySQL. It may work on some third-party database backends as well, but this is not guaranteed. We recommend PostgreSQL for production use.

### Templates

The overhead from reading and compiling templates adds up. Django wraps its default loaders with [cached template loader](django.template.loaders.cached.Loader) which stores the compiled `Template` in memory and returns it for subsequent requests. The cached loader is automatically enabled when `DEBUG` is `False`. If you are using custom loaders, update your settings to use it:

```python
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [os.path.join(BASE_DIR, 'templates')],
    'OPTIONS': {
        'loaders': [
            ('django.template.loaders.cached.Loader', [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
                'path.to.custom.Loader',
            ]),
        ],
    },
}]
```

## Public users

(caching_proxy)=

### Caching proxy

To support high volumes of traffic with excellent response times, we recommend a caching proxy. Both [Varnish](https://varnish-cache.org/) and [Squid](http://www.squid-cache.org/) have been tested in production. Hosted proxies like [Cloudflare](https://www.cloudflare.com/) should also work well.

Wagtail supports automatic cache invalidation for Varnish/Squid. See [](frontend_cache_purging) for more information.

### Image attributes

For some images, it may be beneficial to lazy load images, so the rest of the page can continue to load. It can be configured site-wide [](adding_default_attributes_to_images) or per-image [](image_tag_alt). For more details you can read about the [`loading='lazy'` attribute](https://developer.mozilla.org/en-US/docs/Web/Performance/Lazy_loading#images_and_iframes) and the [`'decoding='async'` attribute](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/img#attr-decoding) or this [web.dev article on lazy loading images](https://web.dev/lazy-loading-images/).

This optimisation is already handled for you for images in the admin site.
