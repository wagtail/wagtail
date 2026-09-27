from collections import namedtuple
from contextlib import contextmanager

import swapper
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Case, IntegerField, Q, When
from django.db.models.functions import Lower
from django.http.request import split_domain_port
from django.utils.translation import gettext_lazy as _

from wagtail.utils.stash import clear as stash_clear
from wagtail.utils.stash import enabled, get_or_set, stash_scope
from wagtail.utils.stash import get as stash_get
from wagtail.utils.stash import set as stash_set

swapper.set_app_prefix("wagtailcore", "wagtail")

MATCH_HOSTNAME_PORT = 0
MATCH_HOSTNAME_DEFAULT = 1
MATCH_DEFAULT = 2
MATCH_HOSTNAME = 3


def get_site_for_hostname(hostname, port):
    """Return the wagtailcore.Site object for the given hostname and port."""
    Site = apps.get_model("wagtailcore.Site")

    sites = list(
        Site.objects.annotate(
            match=Case(
                # annotate the results by best choice descending
                # put exact hostname+port match first
                When(hostname=hostname, port=port, then=MATCH_HOSTNAME_PORT),
                # then put hostname+default (better than just hostname or just default)
                When(
                    hostname=hostname, is_default_site=True, then=MATCH_HOSTNAME_DEFAULT
                ),
                # then match default with different hostname. there is only ever
                # one default, so order it above (possibly multiple) hostname
                # matches so we can use sites[0] below to access it
                When(is_default_site=True, then=MATCH_DEFAULT),
                # because of the filter below, if it's not default then its a hostname match
                default=MATCH_HOSTNAME,
                output_field=IntegerField(),
            )
        )
        .filter(Q(hostname=hostname) | Q(is_default_site=True))
        .order_by("match")
        .select_related("root_page")
    )

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
        return (
            super()
            .get_queryset()
            .order_by(
                Case(
                    When(site_name="", then=Lower("hostname")),
                    default=Lower("site_name"),
                ),
                Lower("hostname"),
            )
        )

    def get_by_natural_key(self, hostname, port):
        return self.get(hostname=hostname, port=port)


SiteRootPath = namedtuple("SiteRootPath", "site_id root_path root_url language_code")

SITE_ROOT_PATHS_CACHE_KEY = "wagtail_site_root_paths"
# Increase the cache version whenever the structure SiteRootPath tuple changes
SITE_ROOT_PATHS_CACHE_VERSION = 2

WAGTAIL_STASH_SCOPE = "wagtail"
STASH_CURRENT_SITE = "current_site"
STASH_SITE_LOADER = "_site_loader"
STASH_SITE_ROOT_PATHS = "site_root_paths"


def bind_site_loader(loader):
    """Register a lazy site identifier for the current request stash scope."""
    stash_set(STASH_SITE_LOADER, loader, scope=WAGTAIL_STASH_SCOPE)


def load_site_root_paths():
    """Load site root paths from the process cache or database."""
    result = cache.get(SITE_ROOT_PATHS_CACHE_KEY, version=SITE_ROOT_PATHS_CACHE_VERSION)

    if result is None:
        result = []

        for site in Site.objects.select_related(
            "root_page", "root_page__locale"
        ).order_by("-root_page__url_path", "-is_default_site", "hostname"):
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

        cache.set(
            SITE_ROOT_PATHS_CACHE_KEY,
            result,
            3600,
            version=SITE_ROOT_PATHS_CACHE_VERSION,
        )
    else:
        # Convert the cache result to a list of SiteRootPath tuples, as some
        # cache backends (e.g. Redis) don't support named tuples.
        result = [SiteRootPath(*srp) for srp in result]

    return result


def find_site_scope_for_page(page):
    """
    Return the site and site root paths to use for a page, for example when previewing.

    Prefer the site whose root page matches the page's locale and tree position.
    Site root paths are loaded eagerly so they can be injected into a stash scope
    for reuse during rendering.
    """
    site_root_paths = load_site_root_paths()
    if getattr(settings, "WAGTAIL_I18N_ENABLED", False):
        for site in Site.objects.select_related("root_page", "root_page__locale"):
            if site.root_page.locale_id == page.locale_id and page.url_path.startswith(
                site.root_page.url_path
            ):
                return site, site_root_paths
    relevant_paths = tuple(
        srp for srp in site_root_paths if page.url_path.startswith(srp.root_path)
    )
    if not relevant_paths:
        return None, site_root_paths
    if len(relevant_paths) == 1:
        return Site.objects.get(pk=relevant_paths[0].site_id), site_root_paths
    return Site.objects.get(pk=relevant_paths[0].site_id), site_root_paths


def find_site_for_page(page):
    """Return the most appropriate Site for a page."""
    site, _site_root_paths = find_site_scope_for_page(page)
    return site


def _seed_site_stash(site=None, site_root_paths=None):
    if site is not None:
        bind_site_loader(lambda: site)
        stash_set(STASH_CURRENT_SITE, site, scope=WAGTAIL_STASH_SCOPE)
    if site_root_paths is not None:
        stash_set(STASH_SITE_ROOT_PATHS, site_root_paths, scope=WAGTAIL_STASH_SCOPE)


@contextmanager
def wagtail_site_stash_scope(request=None, site=None, site_root_paths=None):
    """
    Open a Wagtail site stash for a block of work when one is not already active.

    Used by :func:`~wagtail.models.sites.bind_site_scope_on_render` and available for custom views that
    render templates without passing ``request`` into every URL helper.

    Pass an explicit ``site`` when the site should not be derived from the
    request hostname (for example, page previews should use the site the page
    belongs to). Otherwise ``site`` is identified from ``request``.

    When ``site`` is provided, ``site_root_paths`` are also injected into the
    stash (loaded eagerly if not passed) so later URL generation reuses them.
    """
    if enabled(scope=WAGTAIL_STASH_SCOPE):
        yield
        return

    if site is None and request is None:
        yield
        return

    with stash_scope(WAGTAIL_STASH_SCOPE):
        if site is not None:
            if site_root_paths is None:
                site_root_paths = load_site_root_paths()
            _seed_site_stash(site=site, site_root_paths=site_root_paths)
        else:
            bind_site_loader(lambda: Site.find_for_request(request))
        yield


def bind_site_scope_on_render(response, site=None, site_root_paths=None):
    """
    Ensure deferred ``TemplateResponse`` rendering runs inside a Wagtail site scope.

    Django renders template responses after the view returns. Wagtail uses this at
    page serve and preview boundaries so page URLs (including those expanded by
    the ``|richtext`` filter) resolve against the current site.
    """
    if getattr(response, "_wagtail_site_scope_bound", False):
        return response

    render = getattr(response, "render", None)
    if not callable(render):
        return response

    request = getattr(response, "_request", None)

    def render_with_site_scope(*args, **kwargs):
        with wagtail_site_stash_scope(
            request, site=site, site_root_paths=site_root_paths
        ):
            return render(*args, **kwargs)

    response.render = render_with_site_scope
    response._wagtail_site_scope_bound = True
    return response


def get_current_site():
    """
    Return the Site for the current stash scope if
    :func:`~wagtail.models.sites.bind_site_scope_on_render` or
    :func:`~wagtail.models.sites.wagtail_site_stash_scope` has bound one,
    otherwise ``None``.
    """

    def load():
        loader = stash_get(STASH_SITE_LOADER, scope=WAGTAIL_STASH_SCOPE)
        if not callable(loader):
            return None
        return loader()

    return get_or_set(STASH_CURRENT_SITE, load, scope=WAGTAIL_STASH_SCOPE)


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
        swapper.get_model_name("wagtailcore", "Page"),
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
            request._wagtail_site = site
        return request._wagtail_site

    @staticmethod
    def _find_for_request(request):
        # Use `_get_raw_host` to avoid ALLOWED_HOSTS checks
        hostname = split_domain_port(request._get_raw_host())[0]
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

    @staticmethod
    def get_site_root_paths():
        """
        Return a list of `SiteRootPath` instances, most specific path
        first - used to translate url_paths into actual URLs with hostnames.

        Each root path is an instance of the `SiteRootPath` named tuple,
        and have the following attributes:

        - ``site_id`` - The ID of the Site record
        - ``root_path`` - The internal URL path of the site's home page (for example '/home/')
        - ``root_url`` - The scheme/domain name of the site (for example 'https://www.example.com/')
        - ``language_code`` - The language code of the site (for example 'en')

        When a request stash scope is active, the result is reused for the
        rest of that scope.
        """

        return get_or_set(
            STASH_SITE_ROOT_PATHS, load_site_root_paths, scope=WAGTAIL_STASH_SCOPE
        )

    @staticmethod
    def clear_site_root_paths_cache():
        cache.delete(SITE_ROOT_PATHS_CACHE_KEY, version=SITE_ROOT_PATHS_CACHE_VERSION)
        stash_clear(STASH_SITE_ROOT_PATHS, scope=WAGTAIL_STASH_SCOPE)


class GroupSitePermissionManager(models.Manager):
    def get_by_natural_key(self, group, site, permission):
        return self.get(group=group, site=site, permission=permission)


class GroupSitePermission(models.Model):
    """
    A rule indicating that a group has permission for some action (e.g. "edit social media settings")
    within a specified site.
    """

    group = models.ForeignKey(
        Group,
        verbose_name=_("group"),
        related_name="site_permissions",
        on_delete=models.CASCADE,
    )
    site = models.ForeignKey(
        Site,
        verbose_name=_("site"),
        related_name="group_permissions",
        on_delete=models.CASCADE,
    )
    permission = models.ForeignKey(
        Permission, verbose_name=_("permission"), on_delete=models.CASCADE
    )

    def __str__(self):
        return "Group %d ('%s') has permission '%s' on site %d ('%s')" % (
            self.group.id,
            self.group,
            self.permission,
            self.site.id,
            self.site,
        )

    def natural_key(self):
        return (self.group, self.site, self.permission)

    objects = GroupSitePermissionManager()

    class Meta:
        unique_together = ("group", "site", "permission")
        verbose_name = _("group site permission")
        verbose_name_plural = _("group site permissions")
