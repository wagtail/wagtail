from django_medusa.renderers import StaticSiteRenderer
from .models import Site


class PageRenderer(StaticSiteRenderer):
    def get_paths(self):
        # Get site
        # TODO: Find way to get this to work with other sites
        site = Site.objects.filter(is_default_site=True).first()
        if site is None:
            return []

        # Return list of paths
        return site.root_page.get_medusa_paths()


renderers = [PageRenderer]
