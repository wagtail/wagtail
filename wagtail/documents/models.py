import os.path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.dispatch import Signal
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from taggit.managers import TaggableManager

from wagtail.admin.utils import get_object_usage
from wagtail.core.models import CollectionMember
from wagtail.search import index
from wagtail.search.queryset import SearchableQuerySetMixin


class DocumentQuerySet(SearchableQuerySetMixin, models.QuerySet):
    pass


class AbstractDocument(CollectionMember, index.Indexed, models.Model):
    title = models.CharField(max_length=255, verbose_name=_('title'))
    file = models.FileField(upload_to='documents', verbose_name=_('file'))
    created_at = models.DateTimeField(verbose_name=_('created at'), auto_now_add=True)
    uploaded_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('uploaded by user'),
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL
    )

    tags = TaggableManager(help_text=None, blank=True, verbose_name=_('tags'))

    file_size = models.PositiveIntegerField(null=True, editable=False)

    objects = DocumentQuerySet.as_manager()

    search_fields = CollectionMember.search_fields + [
        index.SearchField('title', partial_match=True, boost=10),
        index.AutocompleteField('title'),
        index.FilterField('title'),
        index.RelatedFields('tags', [
            index.SearchField('name', partial_match=True, boost=10),
            index.AutocompleteField('name'),
        ]),
        index.FilterField('uploaded_by_user'),
    ]

    def get_file_size(self):
        if self.file_size is None:
            try:
                self.file_size = self.file.size
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception:
                # File doesn't exist
                return

            self.save(update_fields=['file_size'])

        return self.file_size

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
        from wagtail.documents.permissions import permission_policy
        return permission_policy.user_has_permission_for_instance(user, 'change', self)

    class Meta:
        abstract = True
        verbose_name = _('document')


class Document(AbstractDocument):
    admin_form_fields = (
        'title',
        'file',
        'collection',
        'tags'
    )


def get_document_model():
    """
    Get the document model from the ``WAGTAILDOCS_DOCUMENT_MODEL`` setting.
    Defauts to the standard :class:`~wagtail.documents.models.Document` model
    if no custom model is defined.
    """
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


document_served = Signal(providing_args=['request'])
