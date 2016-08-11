from __future__ import absolute_import, unicode_literals

from django.db import models
from django.utils.six.moves.urllib.parse import urlparse
from django.utils.translation import ugettext_lazy as _


class Redirect(models.Model):
    old_path = models.CharField(verbose_name=_("redirect from"), max_length=255, db_index=True)
    site = models.ForeignKey(
        'wagtailcore.Site',
        verbose_name=_('site'),
        null=True, blank=True,
        related_name='redirects',
        db_index=True,
        on_delete=models.CASCADE
    )
    is_permanent = models.BooleanField(verbose_name=_("permanent"), default=True, help_text=_(
        "Recommended. Permanent redirects ensure search engines "
        "forget the old page (the 'Redirect from') and index the new page instead."
    ))
    redirect_page = models.ForeignKey(
        'wagtailcore.Page',
        verbose_name=_("redirect to a page"),
        null=True, blank=True,
        on_delete=models.CASCADE
    )
    redirect_link = models.URLField(verbose_name=_("redirect to any URL"), blank=True)

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
            return _("permanent")
        else:
            return _("temporary")

    @classmethod
    def get_for_site(cls, site=None):
        if site:
            return cls.objects.filter(models.Q(site=site) | models.Q(site=None))
        else:
            return cls.objects.all()

    @staticmethod
    def normalise_path(url):
        # Strip whitespace
        url = url.strip()

        # Parse url
        url_parsed = urlparse(url)

        # Path must start with / but not end with /
        path = url_parsed[2]
        if not path.startswith('/'):
            path = '/' + path

        if path.endswith('/') and len(path) > 1:
            path = path[:-1]

        # Parameters must be sorted alphabetically
        parameters = url_parsed[3]
        parameters_components = parameters.split(';')
        parameters = ';'.join(sorted(parameters_components))

        # Query string components must be sorted alphabetically
        query_string = url_parsed[4]
        query_string_components = query_string.split('&')
        query_string = '&'.join(sorted(query_string_components))

        if parameters:
            path = path + ';' + parameters

        # Add query string to path
        if query_string:
            path = path + '?' + query_string

        return path

    def clean(self):
        # Normalise old path
        self.old_path = Redirect.normalise_path(self.old_path)

    class Meta:
        verbose_name = _('redirect')
        unique_together = [('old_path', 'site')]
