from __future__ import unicode_literals

from django.forms import MediaDefiningClass, Media
from django.forms.utils import flatatt
from django.utils.text import slugify
from django.utils.safestring import mark_safe
from django.utils.six import text_type

from django.utils.six import with_metaclass

from wagtail.utils.compat import render_to_string
from wagtail.wagtailcore import hooks
from wagtail.wagtailadmin.forms import SearchForm


class SearchArea(with_metaclass(MediaDefiningClass)):
    template = 'wagtailadmin/shared/search_area.html'

    def __init__(self, label, url, name=None, classnames='', attrs=None, order=1000):
        self.label = label
        self.url = url
        self.classnames = classnames
        self.name = (name or slugify(text_type(label)))
        self.order = order

        if attrs:
            self.attr_string = flatatt(attrs)
        else:
            self.attr_string = ""

    def is_shown(self, request):
        """
        Whether this search area should be shown for the given request; permission
        checks etc should go here. By default, search areas are shown all the time
        """
        return True

    def is_active(self, request):
        return request.path.startswith(self.url)

    def render_html(self, request, query):
        return render_to_string(self.template, {
            'name': self.name,
            'url': self.url,
            'classnames': self.classnames,
            'attr_string': self.attr_string,
            'label': self.label,
            'active': self.is_active(request),
            'query_string': query
        }, request=request)


class Search(object):
    def __init__(self, register_hook_name, construct_hook_name=None):
        self.register_hook_name = register_hook_name
        self.construct_hook_name = construct_hook_name
        # _registered_search_areas will be populated on first access to the
        # registered_search_areas property. We can't populate it in __init__ because
        # we can't rely on all hooks modules to have been imported at the point that
        # we create the admin_search and settings_search instances
        self._registered_search_areas = None

    @property
    def registered_search_areas(self):
        if self._registered_search_areas is None:
            self._registered_search_areas = [fn() for fn in hooks.get_hooks(self.register_hook_name)]
        return self._registered_search_areas

    def search_items_for_request(self, request):
        return [item for item in self.registered_search_areas if item.is_shown(request)]

    def active_search(self, request):
        return [item for item in self.search_items_for_request(request) if item.is_active(request)]

    @property
    def media(self):
        media = Media()
        for item in self.registered_search_areas:
            media += item.media
        return media

    def render_html(self, request):
        search_areas = self.search_items_for_request(request)

        # Get query parameter
        form = SearchForm(request.GET)
        query = ''
        if form.is_valid():
            query = form.cleaned_data['q']

        # provide a hook for modifying the search area, if construct_hook_name has been set
        if self.construct_hook_name:
            for fn in hooks.get_hooks(self.construct_hook_name):
                fn(request, search_areas)

        rendered_search_areas = []
        for item in sorted(search_areas, key=lambda i: i.order):
            rendered_search_areas.append(item.render_html(request, query))

        return mark_safe(''.join(rendered_search_areas))


admin_search_areas = Search(register_hook_name='register_admin_search_area', construct_hook_name='construct_search')
