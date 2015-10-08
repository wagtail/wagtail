from __future__ import unicode_literals

from taggit.managers import TaggableManager

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailsearch import index
from wagtail.wagtailadmin.taggable import TagSearchable


EMBED_TYPES = (
    ('video', 'Video'),
    ('photo', 'Photo'),
    ('link', 'Link'),
    ('rich', 'Rich'),
)


@python_2_unicode_compatible
class Embed(models.Model, TagSearchable):
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
    tags = TaggableManager(help_text=None, blank=True, verbose_name=_('Tags'))

    search_fields = TagSearchable.search_fields + (
        index.SearchField('author_name', partial_match=True, boost=10),
        index.SearchField('provider_name', partial_match=False, boost=10),
        index.FilterField('last_updated'),
        index.FilterField('type'),
    )

    class Meta:
        unique_together = ('url', 'max_width')
        verbose_name = _('Embed')
        ordering = ['-last_updated', ]

    def __str__(self):
        return self.url
