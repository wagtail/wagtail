from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.template.loader import render_to_string


class BaseItem(object):
    template = 'wagtailadmin/edit_bird/base_item.html'

    @property
    def can_render(self):
        return True

    def render(self, request):
        if self.can_render:
            return render_to_string(self.template, dict(self=self, request=request), context_instance=RequestContext(request))


class EditPageItem(BaseItem):
    template = 'wagtailadmin/edit_bird/edit_page_item.html'

    def __init__(self, page):
        self.page = page

    @property
    def can_render(self):
        # Don't render if the page doesn't have an id
        return self.page.id


def render_edit_bird(request, items):
    # Render the items
    rendered_items = [item.render(request) for item in items]

    # Remove any unrendered items
    rendered_items = [item for item in rendered_items if item]

    # Quit if no items rendered
    if not rendered_items:
        return

    # Render the edit bird
    return render_to_string('wagtailadmin/edit_bird/edit_bird.html', {
        'items': [item.render(request) for item in items],
    })
