from warnings import warn

from django.forms import Media
from django.template.loader import get_template, render_to_string

from wagtail.admin.auth import user_has_any_page_permission
from wagtail.admin.navigation import get_site_for_user
from wagtail.admin.ui.components import Component
from wagtail.core import hooks
from wagtail.core.models import Page, Site
from wagtail.utils.deprecation import RemovedInWagtail217Warning


class SummaryItem(Component):
    order = 100
    template = None  # RemovedInWagtail217Warning - should set template_name instead

    def __init__(self, request):
        self.request = request

    def get_context(self):
        # RemovedInWagtail217Warning:
        # old get_context method deprecated in 2.15; provided here in case subclasses call it from
        # overridden render() methods or via super()
        return {}
    get_context.is_base_method = True

    def render(self):
        # RemovedInWagtail217Warning:
        # old render method deprecated in 2.15; provided here in case subclasses call it via super()
        return render_to_string(self.template, self.get_context(), request=self.request)
    render.is_base_method = True

    def render_html(self, parent_context=None):
        if not getattr(self.render, 'is_base_method', False):
            # this SummaryItem subclass has overridden render() - use their implementation in
            # preference to following the Component.render_html path
            message = (
                "Summary item %r should provide render_html(self, parent_context) rather than render(self). "
                "See https://docs.wagtail.io/en/stable/releases/2.15.html#template-components-2-15"
                % self
            )
            warn(message, category=RemovedInWagtail217Warning)
            return self.render()
        elif not getattr(self.get_context, 'is_base_method', False):
            # this SummaryItem subclass has overridden get_context() - use their implementation in
            # preference to Component.get_context_data
            message = (
                "Summary item %r should provide get_context_data(self, parent_context) rather than get_context(self). "
                "See https://docs.wagtail.io/en/stable/releases/2.15.html#template-components-2-15"
                % self
            )
            warn(message, category=RemovedInWagtail217Warning)
            context_data = self.get_context()
        else:
            context_data = self.get_context_data(parent_context)

        if self.template is not None:
            warn(
                "%s should define template_name instead of template. "
                "See https://docs.wagtail.io/en/stable/releases/2.15.html#template-components-2-15" % type(self).__name__,
                category=RemovedInWagtail217Warning
            )
            template_name = self.template
        else:
            template_name = self.template_name

        template = get_template(template_name)
        return template.render(context_data)

    def is_shown(self):
        return True


class PagesSummaryItem(SummaryItem):
    order = 100
    template_name = 'wagtailadmin/home/site_summary_pages.html'

    def get_context_data(self, parent_context):
        site_details = get_site_for_user(self.request.user)
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
    name = 'site_summary'
    template_name = 'wagtailadmin/home/site_summary.html'
    order = 100

    def __init__(self, request):
        self.request = request
        summary_items = []
        for fn in hooks.get_hooks('construct_homepage_summary_items'):
            fn(request, summary_items)
        self.summary_items = [s for s in summary_items if s.is_shown()]
        self.summary_items.sort(key=lambda p: p.order)

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        context['summary_items'] = self.summary_items
        return context

    @property
    def media(self):
        media = Media()
        for item in self.summary_items:
            media += item.media
        return media
