import uuid
import warnings

from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext as _

from wagtail.coreutils import InvokeViaAttributeShortcut
from wagtail.models import Locale, Site, TranslatableMixin
from wagtail.utils.deprecation import RemovedInWagtail50Warning

from .registry import register_setting
from .utils import get_locale_for

__all__ = [
    "AbstractSiteSetting",
    "AbstractGenericSetting",
    "BaseSetting",  # RemovedInWagtail50Warning
    "BaseGenericSetting",
    "BaseTranslatableGenericSetting",
    "BaseSiteSetting",
    "BaseTranslatableSiteSetting",
    "register_setting",
]


class AbstractSetting(models.Model):
    """
    The abstract base model for settings. Subclasses must be registered using
    :func:`~wagtail.contrib.settings.registry.register_setting`
    """

    class Meta:
        abstract = True

    # Override to fetch ForeignKey values in the same query when
    # retrieving settings (e.g. via `for_request()`)
    select_related = None

    @classmethod
    def base_queryset(cls):
        """
        Returns a queryset of objects of this type to use as a base.

        You can use the `select_related` attribute on your class to
        specify a list of foreign key field names, which the method
        will attempt to select additional related-object data for
        when the query is executed.

        If your needs are more complex than this, you can override
        this method on your custom class.
        """
        queryset = cls.objects.all()
        if cls.select_related is not None:
            queryset = queryset.select_related(*cls.select_related)
        return queryset

    @classmethod
    def get_cache_attr_name(cls):
        """
        Returns the name of the attribute that should be used to store
        a reference to the fetched/created object on a request.
        """
        return "_{}.{}".format(cls._meta.app_label, cls._meta.model_name).lower()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Per-instance page URL cache
        self._page_url_cache = {}

    @cached_property
    def page_url(self):
        # Allows get_page_url() to be invoked using
        # `obj.page_url.foreign_key_name` syntax
        return InvokeViaAttributeShortcut(self, "get_page_url")

    def get_page_url(self, attribute_name, request=None):
        """
        Returns the URL of a page referenced by a foreign key
        (or other attribute) matching the name ``attribute_name``.
        If the field value is null, or links to something other
        than a ``Page`` object, an empty string is returned.
        The result is also cached per-object to facilitate
        fast repeat access.

        Raises an ``AttributeError`` if the object has no such
        field or attribute.
        """
        if attribute_name in self._page_url_cache:
            return self._page_url_cache[attribute_name]

        if not hasattr(self, attribute_name):
            raise AttributeError(
                "'{}' object has no attribute '{}'".format(
                    self.__class__.__name__, attribute_name
                )
            )

        page = getattr(self, attribute_name)

        if hasattr(page, "specific"):
            url = page.specific.get_url(getattr(self, "_request", None))
        else:
            url = ""

        self._page_url_cache[attribute_name] = url
        return url

    @classmethod
    def _get_locale(cls, *args, **kwargs):
        return None

    def __getstate__(self):
        # Ignore 'page_url' when pickling
        state = super().__getstate__()
        state.pop("page_url", None)
        return state


class AbstractSiteSetting(AbstractSetting):
    class Meta:
        abstract = True

    @staticmethod
    def get_instance(queryset, site, **kwargs):
        raise NotImplementedError

    @classmethod
    def for_site(cls, site, **kwargs):
        """
        Get or create an instance of this setting for the site.
        """
        return cls.get_instance(cls.base_queryset(), site, **kwargs)

    @classmethod
    def for_request(cls, request):
        """
        Get or create an instance of this model for the request,
        and cache the result on the request for faster repeat access.
        """
        attr_name = cls.get_cache_attr_name()
        if hasattr(request, attr_name):
            return getattr(request, attr_name)

        site = Site.find_for_request(request)
        site_settings = cls.for_site(site, locale=cls._get_locale(request=request))

        # For more efficient page url generation
        site_settings._request = request
        setattr(request, attr_name, site_settings)
        return site_settings

    def __str__(self):
        return _("%(site_setting)s for %(site)s") % {
            "site_setting": self._meta.verbose_name,
            "site": self.site,
        }


class BaseSiteSetting(AbstractSiteSetting):
    site = models.OneToOneField(
        Site,
        unique=True,
        db_index=True,
        editable=False,
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True

    @staticmethod
    def get_instance(queryset, site, **kwargs):
        return queryset.get_or_create(site=site)[0]


class BaseTranslatableSiteSetting(TranslatableMixin, AbstractSiteSetting):
    site = models.ForeignKey(
        Site, db_index=True, editable=False, on_delete=models.CASCADE
    )

    class Meta:
        abstract = True
        unique_together = [("site", "locale"), ("translation_key", "locale")]

    @staticmethod
    def _get_translation_key(site_id):
        # The translation key should be derived from the site ID
        # because we want only one instance per site/locale,
        # so the site ID is basically the translation key.
        return uuid.uuid5(
            uuid.UUID("4e47faf7-d91f-411f-8a8f-51a05d75f992"), str(site_id)
        )

    @classmethod
    def _get_locale(cls, request):
        return get_locale_for(request=request, model=cls)

    @staticmethod
    def get_instance(queryset, site, locale=None):
        return queryset.get_or_create(
            site=site,
            locale=locale or Locale.get_active(),
            translation_key=BaseTranslatableSiteSetting._get_translation_key(site.id),
        )[0]


class AbstractGenericSetting(AbstractSetting):
    """
    Generic settings are singleton models - only one instance of each model
    can be created.
    """

    class Meta:
        abstract = True

    @classmethod
    def _get_or_create(cls, **kwargs):
        raise NotImplementedError

    @classmethod
    def load(cls, request_or_site=None, locale=None):
        """
        Get or create an instance of this model.
        If `request_or_site` is present and is a request object, then we cache
        the result on the request for faster repeat access.
        """
        # We can only cache on the request, so if there is no request then
        # we know there's nothing in the cache.
        if request_or_site is None or isinstance(request_or_site, Site):
            return cls._get_or_create(locale=locale)

        # Check if we already have this in the cache and return it if so.
        attr_name = cls.get_cache_attr_name()
        if hasattr(request_or_site, attr_name):
            return getattr(request_or_site, attr_name)

        locale = cls._get_locale(locale=locale, request=request_or_site)
        obj = cls._get_or_create(locale=locale)

        # Cache for next time.
        setattr(request_or_site, attr_name, obj)
        return obj

    def __str__(self):
        return self._meta.verbose_name


class BaseGenericSetting(AbstractGenericSetting):
    class Meta:
        abstract = True

    @classmethod
    def _get_or_create(cls, **kwargs):
        """
        Internal convenience method to get or create the first instance.

        We cannot hardcode `pk=1`, for example, as not all database backends
        use sequential IDs (e.g. Postgres).
        """

        first_obj = cls.base_queryset().first()
        if first_obj is None:
            return cls.objects.create()
        return first_obj


class BaseTranslatableGenericSetting(TranslatableMixin, AbstractGenericSetting):
    # The translation key should be derived from a constant
    # because we want only one instance per locale,
    # so the first instance's ID (=1) is basically the translation key.
    _translation_key = uuid.uuid5(
        uuid.UUID("4e47faf7-d91f-411f-8a8f-51a05d75f992"), "1"
    )

    class Meta:
        abstract = True
        unique_together = [("translation_key", "locale")]

    @classmethod
    def _get_locale(cls, locale, request):
        return locale or get_locale_for(request=request, model=cls)

    @classmethod
    def _get_or_create(cls, locale=None):
        """
        Internal convenience method to get or create the instance associated
        to the locale requested.
        """
        return cls.base_queryset().get_or_create(
            locale=locale or Locale.get_active(),
            translation_key=cls._translation_key,
        )[0]


class BaseSetting(BaseSiteSetting):
    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        warnings.warn(
            (
                "`wagtail.contrib.settings.models.BaseSetting` "
                "is obsolete and should be replaced by "
                "`wagtail.contrib.settings.models.BaseSiteSetting` or "
                "`wagtail.contrib.settings.models.BaseGenericSetting`"
            ),
            category=RemovedInWagtail50Warning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
