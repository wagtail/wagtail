# Legacy richtext

Potato `(っ◕‿◕)っ`

Test eval RST

```eval_rst
.. automodule:: wagtail.contrib.routable_page.models
.. autoclass:: RoutablePageMixin

    .. automethod:: render

    .. automethod:: get_subpage_urls

    .. automethod:: resolve_subpage

        Example:

        .. code-block:: python

            view, args, kwargs = page.resolve_subpage('/past/')
            response = view(request, *args, **kwargs)

    .. automethod:: reverse_subpage

        Example:

        .. code-block:: python

            url = page.url + page.reverse_subpage('events_for_year', kwargs={'year': '2014'})
```

Important 1:

``` important::
    Ensure that none of your field names are the same as your class names. This will cause errors due to the way Django handles relations (`read more <https://github.com/wagtail/wagtail/issues/503>`_). In our examples we have avoided this by appending "Page" to each model name.
```

Important 2:

``` important:: Test 2
```

Provides the legacy richtext wrapper.

Place `wagtail.contrib.legacy.richtext` before `wagtail.core` in  `INSTALLED_APPS`.

```python
INSTALLED_APPS = [
    ...
    "wagtail.contrib.legacy.richtext",
    "wagtail.core",
    ...
]
```

The `{{ page.body|richtext }}` template filter will now render:

```html+django
<div class="rich-text">...</div>
```
