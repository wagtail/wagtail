from django.db import models
from django.utils.translation import ugettext_lazy as _
from taggit.managers import TaggableManager
from wagtail.documents.models import AbstractDocument
from wagtail.images.models import AbstractImage, AbstractRendition


class Image(AbstractImage):
    admin_form_fields = (
        'title',
        'file',
        'collection',
        'tags',
        'focal_point_x',
        'focal_point_y',
        'focal_point_width',
        'focal_point_height',
    )

    tags = TaggableManager(help_text=None, blank=True, verbose_name=_('tags'), related_name='images')

    class Meta:
        verbose_name = _('image')
        verbose_name_plural = _('images')


class Rendition(AbstractRendition):
    image = models.ForeignKey(Image, related_name='renditions', on_delete=models.CASCADE)

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
