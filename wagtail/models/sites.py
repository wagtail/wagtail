from collections import namedtuple
from copy import deepcopy
from typing import List, Tuple, Union

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.http.request import split_domain_port
from django.utils.translation import gettext_lazy as _

from asgiref.local import Local

MATCH_HOSTNAME_PORT = 0
MATCH_HOSTNAME_DEFAULT = 1
MATCH_DEFAULT = 2
MATCH_HOSTNAME = 3


_sites_cache = Local()
_site_root_paths_cache = Local()


SiteRootPath = namedtuple("SiteRootPath", "site_id root_path root_url language_code")


def get_site_for_hostname(hostname, port):
    """Return the wagtailcore.Site object for the given hostname and port."""
    Site = apps.get_model("wagtailcore.Site")

    if isinstance(port, str):
        port = int(port)

    sites = []
    for site in Site.objects.get_all():
        match_rank = None
        if site.hostname == hostname and site.port == port:
            # put exact hostname+port match first
            match_rank = MATCH_HOSTNAME_PORT
        elif site.hostname == hostname and site.is_default_site:
            # then put hostname+default (better than just hostname or just default)
            match_rank = MATCH_HOSTNAME_DEFAULT
        elif site.is_default_site:
            # then match default with different hostname. there is only ever
            # one default, so order it above (possibly multiple) hostname
            # matches so we can use sites[0] below to access it
            match_rank = MATCH_DEFAULT
        elif site.hostname == hostname:
            match_rank = MATCH_HOSTNAME

        if match_rank is not None:
            site.match = match_rank
            sites.append(site)

    sites.sort(key=lambda x: (x.match, x.hostname.lower()))

    if sites:
        # if there's a unique match or hostname (with port or default) match
        if len(sites) == 1 or sites[0].match in (
            MATCH_HOSTNAME_PORT,
            MATCH_HOSTNAME_DEFAULT,
        ):
            return sites[0]

        # if there is a default match with a different hostname, see if
        # there are many hostname matches. if only 1 then use that instead
        # otherwise we use the default
        if sites[0].match == MATCH_DEFAULT:
            return sites[len(sites) == 2]

    raise Site.DoesNotExist()


class SiteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().order_by(Lower("hostname"))

    def get_by_natural_key(self, hostname, port):
        return self.get(hostname=hostname, port=port)

    def get_all(self) -> Tuple["Site"]:
        """
        Returns a tuple of all `Site` objects, ordered for the generation of `SiteRootPath` lists.

        Unless the `WAGTAIL_PER_THREAD_SITE_CACHING` setting has been set to `False`, the return
        value will be cached for the current thread.

        TODO: Consider what can be done to prevent long-running background processes
        (e.g. Celery workers) from hanging onto cached values.
        """
        caching_enabled = getattr(settings, "WAGTAIL_PER_THREAD_SITE_CACHING", True)
        if caching_enabled:
            cached = self._get_cached_list()
            if cached is not None:
                # Return a copy to prevent pollution of cached values and/or
                # garbage collection issues due to stray references
                return deepcopy(cached)

        sites = tuple(
            self.get_queryset()
            .select_related("root_page", "root_page__locale")
            .order_by("-root_page__url_path", "-is_default_site", "hostname")
        )

        # Reuse this value next time
        if caching_enabled:
            _sites_cache.value = deepcopy(sites)

        return sites

    def _get_cached_list(self):
        return getattr(_sites_cache, "value", None)


class Site(models.Model):
    hostname = models.CharField(
        verbose_name=_("hostname"), max_length=255, db_index=True
    )
    port = models.IntegerField(
        verbose_name=_("port"),
        default=80,
        help_text=_(
            "Set this to something other than 80 if you need a specific port number to appear in URLs"
            " (e.g. development on port 8000). Does not affect request handling (so port forwarding still works)."
        ),
    )
    site_name = models.CharField(
        verbose_name=_("site name"),
        max_length=255,
        blank=True,
        help_text=_("Human-readable name for the site."),
    )
    root_page = models.ForeignKey(
        "Page",
        verbose_name=_("root page"),
        related_name="sites_rooted_here",
        on_delete=models.CASCADE,
    )
    is_default_site = models.BooleanField(
        verbose_name=_("is default site"),
        default=False,
        help_text=_(
            "If true, this site will handle requests for all other hostnames that do not have a site entry of their own"
        ),
    )

    objects = SiteManager()

    class Meta:
        unique_together = ("hostname", "port")
        verbose_name = _("site")
        verbose_name_plural = _("sites")

    def natural_key(self):
        return (self.hostname, self.port)

    def __str__(self):
        default_suffix = " [{}]".format(_("default"))
        if self.site_name:
            return self.site_name + (default_suffix if self.is_default_site else "")
        else:
            return (
                self.hostname
                + ("" if self.port == 80 else (":%d" % self.port))
                + (default_suffix if self.is_default_site else "")
            )

    def clean(self):
        self.hostname = self.hostname.lower()

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

        if not hasattr(request, "_wagtail_site"):
            site = Site._find_for_request(request)
            setattr(request, "_wagtail_site", site)
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
            # copy old SiteMiddleware behaviour
        return site

    @property
    def root_url(self):
        if self.port == 80:
            return "http://%s" % self.hostname
        elif self.port == 443:
            return "https://%s" % self.hostname
        else:
            return "http://%s:%d" % (self.hostname, self.port)

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
                    {
                        "is_default_site": [
                            _(
                                "%(hostname)s is already configured as the default site."
                                " You must unset that before you can save this site as default."
                            )
                            % {"hostname": default.hostname}
                        ]
                    }
                )

    @classmethod
    def get_site_root_paths(cls) -> List[SiteRootPath]:
        """
        Return a list of `SiteRootPath` instances, most specific path
        first - used to translate url_paths into actual URLs with hostnames

        Each root path is an instance of the `SiteRootPath` named tuple,
        and have the following attributes:

        - `site_id` - The ID of the Site record
        - `root_path` - The internal URL path of the site's home page (for example '/home/')
        - `root_url` - The scheme/domain name of the site (for example 'https://www.example.com/')
        - `language_code` - The language code of the site (for example 'en')

        NOTE: Unless the `WAGTAIL_PER_THREAD_SITE_CACHING` setting has been set to `False`, the
        return value will be cached for the current thread.
        """
        caching_enabled = getattr(settings, "WAGTAIL_PER_THREAD_SITE_CACHING", True)
        if caching_enabled:
            cached_result = cls._get_cached_site_root_paths()
            if cached_result is not None:
                return deepcopy(cached_result)

        result = []
        for site in Site.objects.get_all():
            if getattr(settings, "WAGTAIL_I18N_ENABLED", False):
                result.extend(
                    [
                        SiteRootPath(
                            site.id,
                            root_page.url_path,
                            site.root_url,
                            root_page.locale.language_code,
                        )
                        for root_page in site.root_page.get_translations(
                            inclusive=True
                        ).select_related("locale")
                    ]
                )
            else:
                result.append(
                    SiteRootPath(
                        site.id,
                        site.root_page.url_path,
                        site.root_url,
                        site.root_page.locale.language_code,
                    )
                )

        # cache result for the next request
        if caching_enabled:
            _site_root_paths_cache.value = result

        return result

    @staticmethod
    def _get_cached_site_root_paths() -> Union[List[SiteRootPath], None]:
        return getattr(_site_root_paths_cache, "value", None)

    @staticmethod
    def clear_caches():
        """
        Convenience method for clearing both the `Site` and `SiteRootPath`
        threadlocal caches for the current thread.

        NOTE: We do not attempt to clear data for other threads or processes
        because, if they are already using a copy of the data, it could do more
        harm than good to change that data mid-request.
        """
        _sites_cache.value = None
        _site_root_paths_cache.value = None

    @staticmethod
    def refresh_caches():
        """
        Convenience method for clearing and repopulating the `Site` and
        `SiteRootPath` threadlocal caches. Mostly used in tests.
        """
        Site.clear_caches()
        Site.get_site_root_paths()
