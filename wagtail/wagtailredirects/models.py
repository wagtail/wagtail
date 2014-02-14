from django.db import models

from wagtail.wagtailadmin.edit_handlers import FieldPanel, MultiFieldPanel, PageChooserPanel

from urlparse import urlparse


class Redirect(models.Model):
    old_path = models.CharField("Redirect from", max_length=255, unique=True, db_index=True)
    site = models.ForeignKey('wagtailcore.Site', null=True, blank=True, related_name='redirects', db_index=True, editable=False)
    is_permanent = models.BooleanField("Permanent", default=True, help_text="Recommended. Permanent redirects ensure search engines forget the old page (the 'Redirect from') and index the new page instead.")
    redirect_page = models.ForeignKey('wagtailcore.Page', verbose_name="Redirect to a page", null=True, blank=True)
    redirect_link = models.URLField("Redirect to any URL", blank=True)

    @property
    def title(self):
        return self.old_path

    @property
    def link(self):
        if self.redirect_page:
            return self.redirect_page.url
        else:
            return self.redirect_link

    def get_is_permanent_display(self):
        if self.is_permanent:
            return "permanent"
        else:
            return "temporary"

    @classmethod
    def get_for_site(cls, site=None):
        if site:
            return cls.objects.filter(models.Q(site=site) | models.Q(site=None))
        else:
            return cls.objects.all()

    @staticmethod
    def normalise_path(url):
        # Parse url
        url_parsed = urlparse(url)

        # Path must start with / but not end with /
        path = url_parsed[2]
        if not path.startswith('/'):
            path = '/' + path

        if path.endswith('/'):
            path = path[:-1]

        # Query string components must be sorted alphabetically
        query_string = url_parsed[4]
        query_string_components = query_string.split('&')
        query_string = '&'.join(sorted(query_string_components))

        # Add query string to path
        if query_string:
            path = path + '?' + query_string

        return path

    def clean(self):
        # Normalise old path
        self.old_path = Redirect.normalise_path(self.old_path)

Redirect.content_panels = [
    MultiFieldPanel([
        FieldPanel('old_path'),
        FieldPanel('is_permanent'),
        PageChooserPanel('redirect_page'),
        FieldPanel('redirect_link'),
    ])
]
