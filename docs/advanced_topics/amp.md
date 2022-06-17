# How to build a site with AMP support

This recipe document describes a method for creating an
[AMP](https://amp.dev/) version of a Wagtail site and hosting it separately
to the rest of the site on a URL prefix. It also describes how to make Wagtail
render images with the `<amp-img>` tag when a user is visiting a page on the
AMP version of the site.

## Overview

In the next section, we will add a new URL entry that points at Wagtail's
internal `serve()` view which will have the effect of rendering the whole
site again under the `/amp` prefix.

Then, we will add some utilities that will allow us to track whether the
current request is in the `/amp` prefixed version of the site without needing
a request object.

After that, we will add a template context processor to allow us to check from
within templates which version of the site is being rendered.

Then, finally, we will modify the behaviour of the `{% image %}` tag to make it
render `<amp-img>` tags when rendering the AMP version of the site.

## Creating the second page tree

We can render the whole site at a different prefix by duplicating the Wagtail
URL in the project `urls.py` file and giving it a prefix. This must be before
the default URL from Wagtail, or it will try to find `/amp` as a page:

```python
# <project>/urls.py

urlpatterns += [
    # Add this line just before the default ``include(wagtail_urls)`` line
    path('amp/', include(wagtail_urls)),

    path('', include(wagtail_urls)),
]
```

If you now open `http://localhost:8000/amp/` in your browser, you should see
the homepage.

## Making pages aware of "AMP mode"

All the pages will now render under the `/amp` prefix, but right now there
isn't any difference between the AMP version and the normal version.

To make changes, we need to add a way to detect which URL was used to render
the page. To do this, we will have to wrap Wagtail's `serve()` view and
set a thread-local to indicate to all downstream code that AMP mode is active.

```{note}
Why a thread-local?

(feel free to skip this part if you're not interested)

Modifying the `request` object would be the most common way to do this.
However, the image tag rendering is performed in a part of Wagtail that
does not have access to the request.

Thread-locals are global variables that can have a different value for each
running thread. As each thread only handles one request at a time, we can
use it as a way to pass around data that is specific to that request
without having to pass the request object everywhere.

Django uses thread-locals internally to track the currently active language
for the request.

Python implements thread-local data through the `threading.local` class,
but as of Django 3.x, multiple requests can be handled in a single thread
and so thread-locals will no longer be unique to a single request. Django
therefore provides `asgiref.Local` as a drop-in replacement.
```

Now let's create that thread-local and some utility functions to interact with it,
save this module as `amp_utils.py` in an app in your project:

```python
# <app>/amp_utils.py

from contextlib import contextmanager
from asgiref.local import Local

_amp_mode_active = Local()

@contextmanager
def activate_amp_mode():
    """
    A context manager used to activate AMP mode
    """
    _amp_mode_active.value = True
    try:
        yield
    finally:
        del _amp_mode_active.value

def amp_mode_active():
    """
    Returns True if AMP mode is currently active
    """
    return hasattr(_amp_mode_active, 'value')
```

This module defines two functions:

-   `activate_amp_mode` is a context manager which can be invoked using Python's
    `with` syntax. In the body of the `with` statement, AMP mode would be active.

-   `amp_mode_active` is a function that returns `True` when AMP mode is active.

Next, we need to define a view that wraps Wagtail's builtin `serve` view and
invokes the `activate_amp_mode` context manager:

```python
# <app>/amp_views.py

from django.template.response import SimpleTemplateResponse
from wagtail.views import serve as wagtail_serve

from .amp_utils import activate_amp_mode

def serve(request, path):
    with activate_amp_mode():
        response = wagtail_serve(request, path)

        # Render template responses now while AMP mode is still active
        if isinstance(response, SimpleTemplateResponse):
            response.render()

        return response
```

Then we need to create a `amp_urls.py` file in the same app:

```python
# <app>/amp_urls.py

from django.urls import re_path
from wagtail.urls import serve_pattern

from . import amp_views

urlpatterns = [
    re_path(serve_pattern, amp_views.serve, name='wagtail_amp_serve')
]
```

Finally, we need to update the project's main `urls.py` to use this new URLs
file for the `/amp` prefix:

```python
# <project>/urls.py

from myapp import amp_urls as wagtail_amp_urls

urlpatterns += [
    # Change this line to point at your amp_urls instead of Wagtail's urls
    path('amp/', include(wagtail_amp_urls)),

    re_path(r'', include(wagtail_urls)),
]
```

After this, there shouldn't be any noticeable difference to the AMP version of
the site.

## Write a template context processor so that AMP state can be checked in templates

This is optional, but worth doing so we can confirm that everything is working
so far.

Add a `amp_context_processors.py` file into your app that contains the
following:

```python
# <app>/amp_context_processors.py

from .amp_utils import amp_mode_active

def amp(request):
    return {
        'amp_mode_active': amp_mode_active(),
    }
```

Now add the path to this context processor to the
`['OPTIONS']['context_processors']` key of the `TEMPLATES` setting:

```python
# Either <project>/settings.py or <project>/settings/base.py

TEMPLATES = [
    {
        ...

        'OPTIONS': {
            'context_processors': [
                ...
                # Add this after other context processors
                'myapp.amp_context_processors.amp',
            ],
        },
    },
]
```

You should now be able to use the `amp_mode_active` variable in templates.
For example:

```html+django
{% if amp_mode_active %}
    AMP MODE IS ACTIVE!
{% endif %}
```

## Using a different page template when AMP mode is active

You're probably not going to want to use the same templates on the AMP site as
you do on the normal web site. Let's add some logic in to make Wagtail use a
separate template whenever a page is served with AMP enabled.

We can use a mixin, which allows us to re-use the logic on different page types.
Add the following to the bottom of the amp_utils.py file that you created earlier:

```python
# <app>/amp_utils.py

import os.path

...

class PageAMPTemplateMixin:

    @property
    def amp_template(self):
        # Get the default template name and insert `_amp` before the extension
        name, ext = os.path.splitext(self.template)
        return name + '_amp' + ext

    def get_template(self, request):
        if amp_mode_active():
            return self.amp_template

        return super().get_template(request)
```

Now add this mixin to any page model, for example:

```python
# <app>/models.py

from .amp_utils import PageAMPTemplateMixin

class MyPageModel(PageAMPTemplateMixin, Page):
    ...
```

When AMP mode is active, the template at `app_label/mypagemodel_amp.html`
will be used instead of the default one.

If you have a different naming convention, you can override the
`amp_template` attribute on the model. For example:

```python
# <app>/models.py

from .amp_utils import PageAMPTemplateMixin

class MyPageModel(PageAMPTemplateMixin, Page):
    amp_template = 'my_custom_amp_template.html'
```

## Overriding the `{% image %}` tag to output `<amp-img>` tags

Finally, let's change Wagtail's `{% image %}` tag, so it renders an `<amp-img>`
tags when rendering pages with AMP enabled. We'll make the change on the
`Rendition` model itself so it applies to both images rendered with the
`{% image %}` tag and images rendered in rich text fields as well.

Doing this with a [Custom image model](custom_image_model) is easier, as
you can override the `img_tag` method on your custom `Rendition` model to
return a different tag.

For example:

```python
from django.forms.utils import flatatt
from django.utils.safestring import mark_safe

from wagtail.images.models import AbstractRendition

...

class CustomRendition(AbstractRendition):
    def img_tag(self, extra_attributes):
        attrs = self.attrs_dict.copy()
        attrs.update(extra_attributes)

        if amp_mode_active():
            return mark_safe('<amp-img{}>'.format(flatatt(attrs)))
        else:
            return mark_safe('<img{}>'.format(flatatt(attrs)))

    ...
```

Without a custom image model, you will have to monkey-patch the builtin
`Rendition` model.
Add this anywhere in your project where it would be imported on start:

```python
from django.forms.utils import flatatt
from django.utils.safestring import mark_safe

from wagtail.images.models import Rendition

def img_tag(rendition, extra_attributes={}):
    """
    Replacement implementation for Rendition.img_tag

    When AMP mode is on, this returns an <amp-img> tag instead of an <img> tag
    """
    attrs = rendition.attrs_dict.copy()
    attrs.update(extra_attributes)

    if amp_mode_active():
        return mark_safe('<amp-img{}>'.format(flatatt(attrs)))
    else:
        return mark_safe('<img{}>'.format(flatatt(attrs)))

Rendition.img_tag = img_tag
```
