from collections import namedtuple

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.http.request import split_domain_port
from django.utils.translation import gettext_lazy as _

from wagtail.core.sites import get_site_for_hostname


class SiteManager(models.Manager):
    def get_queryset(self):
        return super(SiteManager, self).get_queryset().order_by(Lower("hostname"))

    def get_by_natural_key(self, hostname, port):
        return self.get(hostname=hostname, port=port)


SiteRootPath = namedtuple('SiteRootPath', 'site_id root_path root_url language_code')


class Site(models.Model):
    hostname = models.CharField(verbose_name=_('hostname'), max_length=255, db_index=True)
    port = models.IntegerField(
        verbose_name=_('port'),
        default=80,
        help_text=_(
            "Set this to something other than 80 if you need a specific port number to appear in URLs"
            " (e.g. development on port 8000). Does not affect request handling (so port forwarding still works)."
        )
    )
    site_name = models.CharField(
        verbose_name=_('site name'),
        max_length=255,
        blank=True,
        help_text=_("Human-readable name for the site.")
    )
    root_page = models.ForeignKey('Page', verbose_name=_('root page'), related_name='sites_rooted_here',
                                  on_delete=models.CASCADE)
    is_default_site = models.BooleanField(
        verbose_name=_('is default site'),
        default=False,
        help_text=_(
            "If true, this site will handle requests for all other hostnames that do not have a site entry of their own"
        )
    )

    objects = SiteManager()

    class Meta:
        unique_together = ('hostname', 'port')
        verbose_name = _('site')
        verbose_name_plural = _('sites')

    def natural_key(self):
        return (self.hostname, self.port)

    def __str__(self):
        default_suffix = " [{}]".format(_("default"))
        if self.site_name:
            return (
                self.site_name
                + (default_suffix if self.is_default_site else "")
            )
        else:
            return (
                self.hostname
                + ("" if self.port == 80 else (":%d" % self.port))
                + (default_suffix if self.is_default_site else "")
            )

    @staticmethod
    def find_for_request(request):
        """
        Find the site object responsible for responding to this HTTP
        request object. Try:

        * unique hostname first
        * then hostname and port
        * if there is no matching hostname at all, or no matching
          hostname:port combination, fall back to the unique default site,
          or raise an exception

        NB this means that high-numbered ports on an extant hostname may
        still be routed to a different hostname which is set as the default

        The site will be cached via request._wagtail_site
        """

        if request is None:
            return None

        if not hasattr(request, '_wagtail_site'):
            site = Site._find_for_request(request)
            setattr(request, '_wagtail_site', site)
        return request._wagtail_site

    @staticmethod
    def _find_for_request(request):
        hostname = split_domain_port(request.get_host())[0]
        port = request.get_port()
        site = None
        try:
            site = get_site_for_hostname(hostname, port)
        except Site.DoesNotExist:
            pass
            # copy old SiteMiddleware behavior
        return site

    @property
    def root_url(self):
        if self.port == 80:
            return 'http://%s' % self.hostname
        elif self.port == 443:
            return 'https://%s' % self.hostname
        else:
            return 'http://%s:%d' % (self.hostname, self.port)

    def clean_fields(self, exclude=None):
        super().clean_fields(exclude)
        # Only one site can have the is_default_site flag set
        try:
            default = Site.objects.get(is_default_site=True)
        except Site.DoesNotExist:
            pass
        except Site.MultipleObjectsReturned:
            raise
        else:
            if self.is_default_site and self.pk != default.pk:
                raise ValidationError(
                    {'is_default_site': [
                        _(
                            "%(hostname)s is already configured as the default site."
                            " You must unset that before you can save this site as default."
                        )
                        % {'hostname': default.hostname}
                    ]}
                )

    @staticmethod
    def get_site_root_paths():
        """
        Return a list of `SiteRootPath` instances, most specific path
        first - used to translate url_paths into actual URLs with hostnames

        Each root path is an instance of the `SiteRootPath` named tuple,
        and have the following attributes:

        - `site_id` - The ID of the Site record
        - `root_path` - The internal URL path of the site's home page (for example '/home/')
        - `root_url` - The scheme/domain name of the site (for example 'https://www.example.com/')
        - `language_code` - The language code of the site (for example 'en')
        """
        result = cache.get('wagtail_site_root_paths')

        # Wagtail 2.11 changed the way site root paths were stored. This can cause an upgraded 2.11
        # site to break when loading cached site root paths that were cached with 2.10.2 or older
        # versions of Wagtail. The line below checks if the any of the cached site urls is consistent
        # with an older version of Wagtail and invalidates the cache.
        if result is None or any(len(site_record) == 3 for site_record in result):
            result = []

            for site in Site.objects.select_related('root_page', 'root_page__locale').order_by('-root_page__url_path', '-is_default_site', 'hostname'):
                if getattr(settings, 'WAGTAIL_I18N_ENABLED', False):
                    result.extend([
                        SiteRootPath(site.id, root_page.url_path, site.root_url, root_page.locale.language_code)
                        for root_page in site.root_page.get_translations(inclusive=True).select_related('locale')
                    ])
                else:
                    result.append(SiteRootPath(site.id, site.root_page.url_path, site.root_url, site.root_page.locale.language_code))

            cache.set('wagtail_site_root_paths', result, 3600)

        return result
