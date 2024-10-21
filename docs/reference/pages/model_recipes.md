(page_model_recipes)=

# Recipes

## Overriding the {meth}`~wagtail.models.Page.serve` Method

Wagtail defaults to serving {class}`~wagtail.models.Page`-derived models by passing a reference to the page object to a Django HTML template matching the model's name, but suppose you wanted to serve something other than HTML? You can override the {meth}`~wagtail.models.Page.serve` method provided by the {class}`~wagtail.models.Page` class and handle the Django request and response more directly.

Consider this example of an `EventPage` object which is served as an iCal file if the `format` variable is set in the request:

```python
class EventPage(Page):
    ...

    def serve(self, request):
        if "format" in request.GET:
            if request.GET['format'] == 'ical':
                # Export to ical format
                response = HttpResponse(
                    export_event(self, 'ical'),
                    content_type='text/calendar',
                )
                response['Content-Disposition'] = 'attachment; filename=' + self.slug + '.ics'
                return response
            else:
                # Unrecognised format error
                message = 'Could not export event\n\nUnrecognised format: ' + request.GET['format']
                return HttpResponse(message, content_type='text/plain')
        else:
            # Display event page as usual
            return super().serve(request)
```

{meth}`~wagtail.models.Page.serve` takes a Django request object and returns a Django response object. Wagtail returns a `TemplateResponse` object with the template and context that it generates, which allows middleware to function as intended, so keep in mind that a simpler response object like a `HttpResponse` will not receive these benefits.

With this strategy, you could use Django or Python utilities to render your model in JSON or XML or any other format you'd like.

(overriding_route_method)=

## Adding Endpoints with Custom {meth}`~wagtail.models.Page.route` Methods

```{note}
A much simpler way of adding more endpoints to pages is provided by the [](routable_page_mixin) mixin.
```

Wagtail routes requests by iterating over the path components (separated with a forward slash `/`), finding matching objects based on their slug, and delegating further routing to that object's model class. The Wagtail source is very instructive in figuring out what's happening. This is the default `route()` method of the `Page` class:

```python
class Page(...):
    ...

    def route(self, request, path_components):
        if path_components:
            # request is for a child of this page
            child_slug = path_components[0]
            remaining_components = path_components[1:]

            # find a matching child or 404
            try:
                subpage = self.get_children().get(slug=child_slug)
            except Page.DoesNotExist:
                raise Http404

            # delegate further routing
            return subpage.specific.route(request, remaining_components)

        else:
            # request is for this very page
            if self.live:
                # Return a RouteResult that will tell Wagtail to call
                # this page's serve() method
                return RouteResult(self)
            else:
                # the page matches the request, but isn't published, so 404
                raise Http404
```

{meth}`~wagtail.models.Page.route` takes the current object (`self`), the `request` object, and a list of the remaining `path_components` from the request URL. It either continues delegating routing by calling {meth}`~wagtail.models.Page.route` again on one of its children in the Wagtail tree or ends the routing process by returning a `RouteResult` object or raising a 404 error.

The `RouteResult` object (defined in wagtail.url_routing) encapsulates all the information Wagtail needs to call a page's {meth}`~wagtail.models.Page.serve` method and return a final response: this information consists of the page object, and any additional `args`/`kwargs` to be passed to {meth}`~wagtail.models.Page.serve`.

By overriding the {meth}`~wagtail.models.Page.route` method, we could create custom endpoints for each object in the Wagtail tree. One use case might be using an alternate template when encountering the `print/` endpoint in the path. Another might be a REST API which interacts with the current object. Just to see what's involved, lets make a simple model which prints out all of its child path components.

First, `models.py`:

```python
from django.shortcuts import render
from wagtail.url_routing import RouteResult
from django.http.response import Http404
from wagtail.models import Page

# ...

class Echoer(Page):

    def route(self, request, path_components):
        if path_components:
            # tell Wagtail to call self.serve() with an additional 'path_components' kwarg
            return RouteResult(self, kwargs={'path_components': path_components})
        else:
            if self.live:
                # tell Wagtail to call self.serve() with no further args
                return RouteResult(self)
            else:
                raise Http404

    def serve(self, path_components=[]):
        return render(request, self.template, {
            'page': self,
            'echo': ' '.join(path_components),
            })
```

This model, `Echoer`, doesn't define any properties, but does subclass `Page` so objects will be able to have a custom title and slug. The template just has to display our `{{ echo }}` property.

Now, once creating a new `Echoer` page in the Wagtail admin titled "Echo Base," requests such as:

```
http://127.0.0.1:8000/echo-base/tauntaun/kennel/bed/and/breakfast/
```

Will return:

```
tauntaun kennel bed and breakfast
```

Be careful if you're introducing new required arguments to the `serve()` method - Wagtail still needs to be able to display a default view of the page for previewing and moderation, and by default will attempt to do this by calling `serve()` with a request object and no further arguments. If your `serve()` method does not accept that as a method signature, you will need to override the page's `serve_preview()` method to call `serve()` with suitable arguments:

```python
def serve_preview(self, request, mode_name):
    return self.serve(request, variant='radiant')
```
