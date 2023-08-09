from urllib.parse import urlparse

from django.db import models
from django.urls import Resolver404
from django.utils.translation import gettext_lazy as _

from wagtail.models import Page


class Redirect(models.Model):
    old_path = models.CharField(
        verbose_name=_("redirect from"), max_length=255, db_index=True
    )
    site = models.ForeignKey(
        "wagtailcore.Site",
        verbose_name=_("site"),
        null=True,
        blank=True,
        related_name="redirects",
        db_index=True,
        on_delete=models.CASCADE,
    )
    is_permanent = models.BooleanField(
        verbose_name=_("permanent"),
        default=True,
        help_text=_(
            "Recommended. Permanent redirects ensure search engines "
            "forget the old page (the 'Redirect from') and index the new page instead."
        ),
    )
    redirect_page = models.ForeignKey(
        "wagtailcore.Page",
        verbose_name=_("redirect to a page"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    redirect_page_route_path = models.CharField(
        verbose_name=_("target page route"),
        help_text=_(
            "Optionally specify a route on the target page to redirect to. "
            "Leave blank to redirect to the default page route."
        ),
        blank=True,
        max_length=255,
    )
    redirect_link = models.URLField(
        verbose_name=_("redirect to any URL"), blank=True, max_length=255
    )
    automatically_created = models.BooleanField(
        verbose_name=_("automatically created"),
        default=False,
        editable=False,
    )
    created_at = models.DateTimeField(
        verbose_name=_("created at"), auto_now_add=True, null=True
    )

    @property
    def title(self):
        return self.old_path

    def __str__(self):
        return self.title

    @property
    def link(self):
        if self.redirect_page:
            page = self.redirect_page.specific
            base_url = page.url
            if not self.redirect_page_route_path:
                return base_url
            try:
                page.resolve_subpage(self.redirect_page_route_path)
            except (AttributeError, Resolver404):
                return base_url
            return base_url.rstrip("/") + self.redirect_page_route_path
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
    def add_redirect(
        old_path,
        redirect_to=None,
        is_permanent=True,
        page_route_path=None,
        site=None,
        automatically_created=False,
    ):
        """
        Create and save a Redirect instance with a single method.

        :param old_path: the path you wish to redirect
        :param site: the Site (instance) the redirect is applicable to (if not all sites)
        :param redirect_to: a Page (instance) or path (string) where the redirect should point
        :param is_permanent: whether the redirect should be indicated as permanent (i.e. 301 redirect)
        :return: Redirect instance
        """
        redirect = Redirect()

        # Set redirect properties from input parameters
        redirect.old_path = Redirect.normalise_path(old_path)
        redirect.site = site

        # Check whether redirect to is string or Page
        if isinstance(redirect_to, Page):
            # Set redirect page
            redirect.redirect_page = redirect_to
            # Set redirect page route
            if isinstance(page_route_path, str):
                redirect.redirect_page_route_path = Redirect.normalise_page_route_path(
                    page_route_path
                )
        elif isinstance(redirect_to, str):
            # Set redirect link string
            redirect.redirect_link = redirect_to

        redirect.is_permanent = is_permanent
        redirect.automatically_created = automatically_created

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
        if not path.startswith("/"):
            path = "/" + path

        if path.endswith("/") and len(path) > 1:
            path = path[:-1]

        # Parameters must be sorted alphabetically
        parameters = url_parsed[3]
        parameters_components = parameters.split(";")
        parameters = ";".join(sorted(parameters_components))

        # Query string components must be sorted alphabetically
        query_string = url_parsed[4]
        query_string_components = query_string.split("&")
        query_string = "&".join(sorted(query_string_components))

        if parameters:
            path = path + ";" + parameters

        # Add query string to path
        if query_string:
            path = path + "?" + query_string

        return path

    @staticmethod
    def normalise_page_route_path(url):
        # Strip whitespace
        url = url.strip()
        if not url:
            return ""

        # Extract the path from the rest of the value
        path = urlparse(url).path

        if path == "/":
            return ""
        elif not path.startswith("/"):
            path = "/" + path

        return path

    def clean(self):
        # Normalise old path
        self.old_path = Redirect.normalise_path(self.old_path)
        # Normalise or clear page route path
        if self.redirect_page:
            self.redirect_page_route_path = Redirect.normalise_page_route_path(
                self.redirect_page_route_path
            )
        else:
            self.redirect_page_route_path = ""

    class Meta:
        verbose_name = _("redirect")
        verbose_name_plural = _("redirects")
        unique_together = [("old_path", "site")]
