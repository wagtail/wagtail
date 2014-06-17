from django.template.loader import render_to_string


class Sitemap(object):
    template = 'wagtailsitemaps/sitemap.xml'

    def __init__(self, site):
        self.site = site

    def get_pages(self):
        return self.site.root_page.get_descendants(inclusive=True).live().order_by('path')

    def get_urls(self):
        for page in self.get_pages():
            latest_revision = page.get_latest_revision()

            yield {
                'location': page.url,
                'lastmod': latest_revision.created_at if latest_revision else None
            }

    def render(self):
        return render_to_string(self.template, {
            'urlset': self.get_urls()
        })
