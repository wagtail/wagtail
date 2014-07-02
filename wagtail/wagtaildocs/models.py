import os.path

from taggit.managers import TaggableManager

from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.dispatch import Signal
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils.translation import ugettext_lazy  as _
from django.utils.encoding import python_2_unicode_compatible

from wagtail.wagtailadmin.taggable import TagSearchable


@python_2_unicode_compatible
class Document(models.Model, TagSearchable):
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    file = models.FileField(upload_to='documents' , verbose_name=_('File'))
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, editable=False)

    tags = TaggableManager(help_text=None, blank=True, verbose_name=_('Tags'))

    indexed_fields = {
        'uploaded_by_user_id': {
            'type': 'integer',
            'store': 'yes',
            'indexed': 'no',
            'boost': 0,
        },
    }

    def __str__(self):
        return self.title

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    @property
    def file_extension(self):
        parts = self.filename.split('.')
        if len(parts) > 1:
            return parts[-1]
        else:
            return ''

    @property
    def url(self):
        return reverse('wagtaildocs_serve', args=[self.id, self.filename])

    def is_editable_by_user(self, user):
        if user.has_perm('wagtaildocs.change_document'):
            # user has global permission to change documents
            return True
        elif user.has_perm('wagtaildocs.add_document') and self.uploaded_by_user == user:
            # user has document add permission, which also implicitly provides permission to edit their own documents
            return True
        else:
            return False


# Receive the pre_delete signal and delete the file associated with the model instance.
@receiver(pre_delete, sender=Document)
def image_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.file.delete(False)


document_served = Signal(providing_args=['request'])
