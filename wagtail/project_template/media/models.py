from django.db import models
from django.utils.translation import ugettext_lazy as _
from wagtail.documents.models import AbstractDocument
from wagtail.images.models import AbstractImage, AbstractRendition

from taggit.managers import TaggableManager


class Image(AbstractImage):
    admin_form_fields = (
        'title',
        'file',
        'collection',
        'tags',
        'default_alt_text'
        'focal_point_x',
        'focal_point_y',
        'focal_point_width',
        'focal_point_height',
    )

    tags = TaggableManager(help_text=None, blank=True, verbose_name=_('tags'), related_name='images')
    generic_alt_text = models.CharField(max_length=600, verbose_name=_('default alt text'), blank=True)

    @property
    def default_alt_text(self):
        if self.generic_alt_text:
            return self.generic_alt_text
        else:
            return super().default_alt_text

    class Meta:
        verbose_name = _('image')
        verbose_name_plural = _('images')


class Rendition(AbstractRendition):
    image = models.ForeignKey(Image, related_name='renditions', on_delete=models.CASCADE)

    @property
    def alt(self):
        return self.image.default_alt_text

    class Meta:
        unique_together = (
            ('image', 'filter_spec', 'focal_point_key'),
        )


class Document(AbstractDocument):
    admin_form_fields = (
        'title',
        'file',
        'collection',
        'tags'
    )

    tags = TaggableManager(help_text=None, blank=True, verbose_name=_('tags'), related_name='documents')
