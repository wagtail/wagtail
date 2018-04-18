from django.db import models
from django.urls import reverse

from .registry import register_setting

__all__ = ['BaseSetting', 'register_setting']


class BaseSetting(models.Model):
    """
    The abstract base model for settings. Subclasses must be registered using
    :func:`~wagtail.contrib.settings.registry.register_setting`
    """

    site = models.OneToOneField(
        'wagtailcore.Site', unique=True, db_index=True, editable=False, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    @classmethod
    def for_site(cls, site):
        """
        Get an instance of this setting for the site.
        """
        instance, created = cls.objects.get_or_create(site=site)
        return instance

    def get_edit_url(self):
        return reverse(
            'wagtailsettings:edit',
            args=(self._meta.app_label, self._meta.model_name, self.site_id,))
