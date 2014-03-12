from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.template.loader import render_to_string


class BaseItem(object):
    template = 'wagtailadmin/edit_bird/base_item.html'

    def render(self, request):
        return render_to_string(self.template, dict(self=self, request=request), context_instance=RequestContext(request))


class EditPageItem(BaseItem):
    template = 'wagtailadmin/edit_bird/edit_page_item.html'

    def __init__(self, page):
        self.page = page

    def render(self, request):
        # Don't render if the page doesn't have an id
        if not self.page.id:
            return

        # Don't render if user doesn't have permission to access the admin area
        if not request.user.has_perm('wagtailadmin.access_admin'):
            return

        # Don't render if the user doesn't have permission to edit this page
        permission_checker = self.page.permissions_for_user(request.user)
        if not permission_checker.can_edit():
            return

        return super(EditPageItem, self).render(request)


def render_edit_bird(request, items):
    # Don't render if the user is not logged in
    if not request.user.is_authenticated():
        return

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
