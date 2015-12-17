from __future__ import unicode_literals

import os.path

from taggit.managers import TaggableManager

from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.dispatch import Signal
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible

from wagtail.wagtailadmin.taggable import TagSearchable
from wagtail.wagtailadmin.utils import get_object_usage
from wagtail.wagtailsearch import index
from wagtail.wagtailsearch.queryset import SearchableQuerySetMixin


class DocumentQuerySet(SearchableQuerySetMixin, models.QuerySet):
    pass


@python_2_unicode_compatible
class AbstractDocument(models.Model, TagSearchable):
    title = models.CharField(max_length=255, verbose_name=_('title'))
    file = models.FileField(upload_to='documents', verbose_name=_('file'))
    created_at = models.DateTimeField(verbose_name=_('created at'), auto_now_add=True)
    uploaded_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('uploaded by user'),
        null=True,
        blank=True,
        editable=False
    )

    tags = TaggableManager(help_text=None, blank=True, verbose_name=_('tags'))

    objects = DocumentQuerySet.as_manager()

    search_fields = TagSearchable.search_fields + (
        index.FilterField('uploaded_by_user'),
    )

    def __str__(self):
        return self.title

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    @property
    def file_extension(self):
        return os.path.splitext(self.filename)[1][1:]

    @property
    def url(self):
        return reverse('wagtaildocs_serve', args=[self.id, self.filename])

    def get_usage(self):
        return get_object_usage(self)

    @property
    def usage_url(self):
        return reverse('wagtaildocs:document_usage',
                       args=(self.id,))

    def is_editable_by_user(self, user):
        if user.has_perm('wagtaildocs.change_document'):
            # user has global permission to change documents
            return True
        elif user.has_perm('wagtaildocs.add_document') and self.uploaded_by_user == user:
            # user has document add permission, which also implicitly provides permission to edit their own documents
            return True
        else:
            return False

    class Meta:
        abstract = True
        verbose_name = _('document')


class Document(AbstractDocument):
    admin_form_fields = (
        'title',
        'file',
        'tags'
    )


def get_document_model():
    from django.conf import settings
    from django.apps import apps

    try:
        app_label, model_name = settings.WAGTAILDOCS_DOCUMENT_MODEL.split('.')
    except AttributeError:
        return Document
    except ValueError:
        raise ImproperlyConfigured("WAGTAILDOCS_DOCUMENT_MODEL must be of the form 'app_label.model_name'")

    document_model = apps.get_model(app_label, model_name)
    if document_model is None:
        raise ImproperlyConfigured(
            "WAGTAILDOCS_DOCUMENT_MODEL refers to model '%s' that has not been installed" %
            settings.WAGTAILDOCS_DOCUMENT_MODEL
        )
    return document_model


# Receive the pre_delete signal and delete the file associated with the model instance.
@receiver(pre_delete, sender=Document)
def document_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.file.delete(False)


document_served = Signal(providing_args=['request'])
