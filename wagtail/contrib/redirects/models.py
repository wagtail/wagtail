from urllib.parse import urlparse

from django.db import models
from django.utils.translation import gettext_lazy as _

from wagtail.core.models import Page


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
    redirect_link = models.URLField(verbose_name=_("redirect to any URL"), blank=True, max_length=255)

    @property
    def title(self):
        return self.old_path

    def __str__(self):
        return self.title

    @property
    def link(self):
        if self.redirect_page:
            return self.redirect_page.url
        elif self.redirect_link:
            return self.redirect_link

        return None

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
    def add_redirect(old_path, redirect_to=None, is_permanent=True):
        """
        Create and save a Redirect instance with a single method.

        :param old_path: the path you wish to redirect
        :param redirect_to: a Page (instance) or path (string) where the redirect should point
        :param is_permanent: whether the redirect should be indicated as permanent (i.e. 301 redirect)
        :return: Redirect instance
        """
        redirect = Redirect()

        # Set redirect properties from input parameters
        redirect.old_path = Redirect.normalise_path(old_path)

        # Check whether redirect to is string or Page
        if isinstance(redirect_to, Page):
            # Set redirect page
            redirect.redirect_page = redirect_to
        elif isinstance(redirect_to, str):
            # Set redirect link string
            redirect.redirect_link = redirect_to

        redirect.is_permanent = is_permanent

        redirect.save()

        return redirect

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
