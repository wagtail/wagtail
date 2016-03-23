from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


EMBED_TYPES = (
    ('video', 'Video'),
    ('photo', 'Photo'),
    ('link', 'Link'),
    ('rich', 'Rich'),
)


@python_2_unicode_compatible
class Embed(models.Model):
    """
    When embed code is fetched from a provider (eg, youtube) we cache that code
    in the database so we don't need to ask for it again.

    This model is used for caching the embed html code. It also stores some
    metadata which gets displayed in the editor.

    If an instance of this model is deleted, it will be automatically refetched
    next time the embed code is needed.
    """
    url = models.URLField()
    max_width = models.SmallIntegerField(null=True, blank=True)
    type = models.CharField(max_length=10, choices=EMBED_TYPES)
    html = models.TextField(blank=True)
    title = models.TextField(blank=True)
    author_name = models.TextField(blank=True)
    provider_name = models.TextField(blank=True)
    thumbnail_url = models.URLField(null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('url', 'max_width')
        verbose_name = _('embed')

    def __str__(self):
        return self.url
