import inspect

from warnings import warn

from django.forms import Media
from django.template.loader import render_to_string

from wagtail.admin.auth import user_has_any_page_permission
from wagtail.admin.components import Component
from wagtail.admin.navigation import get_site_for_user
from wagtail.core import hooks
from wagtail.core.models import Page, Site
from wagtail.utils.deprecation import RemovedInWagtail217Warning


class SummaryItem(Component):
    order = 100

    def __init__(self, request):
        self.request = request

    # RemovedInWagtail217Warning:
    # For Component.get_context, request and parent_context are required arguments,
    # but we need this wrapper to account for the possibility of a pre-2.15 render() method
    # or an overridden get_context() method calling it without arguments
    def get_context(self, request=None, parent_context=None):
        if request is None and parent_context is None:
            return {}
        else:
            return super().get_context(request, parent_context)

    # RemovedInWagtail217Warning:
    # old render method deprecated in 2.15; provided here in case subclasses call it via super()
    def render(self):
        return render_to_string(self.template, self.get_context(), request=self.request)
    render.is_base_method = True

    def render_html(self, request, parent_context):
        use_old_render_method = False
        if not getattr(self.render, 'is_base_method', False):
            # this SummaryItem subclass has overridden render() - use their implementation in
            # preference to following the Component.render_html path
            message = (
                "Summary item %r should provide render_html(self, request, parent_context) rather than render(self). "
                "See https://docs.wagtail.io/en/stable/releases/2.15.html#admin-homepage-panels-and-summary-items-now-use-components"
                % self
            )
            warn(message, category=RemovedInWagtail217Warning)
            use_old_render_method = True

        if not inspect.signature(self.get_context).parameters:
            # get_context has been overridden with a version that doesn't accept the
            # request / parent_context arguments passed by Component.render_html
            message = (
                "%s.get_context() (on summary item %r) should accept parameters 'request' and 'parent_context'. "
                "See https://docs.wagtail.io/en/stable/releases/2.15.html#admin-homepage-panels-and-summary-items-now-use-components"
                % (type(self).__name__, self)
            )
            warn(message, category=RemovedInWagtail217Warning)
            use_old_render_method = True

        if use_old_render_method:
            return self.render()
        else:
            return super().render_html(request, parent_context)

    def is_shown(self):
        return True


class PagesSummaryItem(SummaryItem):
    order = 100
    template = 'wagtailadmin/home/site_summary_pages.html'

    def get_context(self, request, parent_context):
        site_details = get_site_for_user(request.user)
        root_page = site_details['root_page']
        site_name = site_details['site_name']

        if root_page:
            page_count = Page.objects.descendant_of(root_page, inclusive=True).count()

            if root_page.is_root():
                # If the root page the user has access to is the Wagtail root,
                # subtract one from this count because the root is not a real page.
                page_count -= 1

                # If precisely one site exists, link to its homepage rather than the
                # tree root, to discourage people from trying to create pages as siblings
                # of the homepage (#1883)
                try:
                    root_page = Site.objects.get().root_page
                except (Site.DoesNotExist, Site.MultipleObjectsReturned):
                    pass
        else:
            page_count = 0

        return {
            'root_page': root_page,
            'total_pages': page_count,
            'site_name': site_name,
        }

    def is_shown(self):
        return user_has_any_page_permission(self.request.user)


class SiteSummaryPanel(Component):
    template = 'wagtailadmin/home/site_summary.html'
    name = 'site_summary'
    order = 100

    def __init__(self, request):
        self.request = request
        summary_items = []
        for fn in hooks.get_hooks('construct_homepage_summary_items'):
            fn(request, summary_items)
        self.summary_items = [s for s in summary_items if s.is_shown()]
        self.summary_items.sort(key=lambda p: p.order)

    def get_context(self, request, parent_context):
        context = super().get_context(request, parent_context)
        context['summary_items'] = self.summary_items
        return context

    @property
    def media(self):
        media = Media()
        for item in self.summary_items:
            media += item.media
        return media
