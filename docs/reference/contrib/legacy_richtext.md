# Legacy richtext

```{module} wagtail.contrib.legacy.richtext

```

Provides the legacy richtext wrapper.

Place `wagtail.contrib.legacy.richtext` before `wagtail` in `INSTALLED_APPS`.

```python
INSTALLED_APPS = [
    ...
    "wagtail.contrib.legacy.richtext",
    "wagtail",
    ...
]
```

The `{{ page.body|richtext }}` template filter will now render:

```html+django
<div class="rich-text">...</div>
```
