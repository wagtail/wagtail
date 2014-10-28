import os.path
import re

from six import BytesIO

from taggit.managers import TaggableManager

from django.core.files import File
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.db import models
from django.db.models.signals import pre_delete, pre_save
from django.dispatch.dispatcher import receiver
from django.utils.safestring import mark_safe
from django.utils.html import escape, format_html_join
from django.conf import settings
from django.utils.translation import ugettext_lazy  as _
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.core.urlresolvers import reverse

from unidecode import unidecode

from wagtail.wagtailadmin.taggable import TagSearchable
from wagtail.wagtailsearch import index
from wagtail.wagtailimages.rect import Rect
from wagtail.wagtailimages.babel import ImageBabel
from wagtail.wagtailimages import image_operations
from wagtail.wagtailadmin.utils import get_object_usage


def get_upload_to(instance, filename):
    folder_name = 'original_images'
    filename = instance.file.field.storage.get_valid_name(filename)

    # do a unidecode in the filename and then
    # replace non-ascii characters in filename with _ , to sidestep issues with filesystem encoding
    filename = "".join((i if ord(i) < 128 else '_') for i in unidecode(filename))

    while len(os.path.join(folder_name, filename)) >= 95:
        prefix, dot, extension = filename.rpartition('.')
        filename = prefix[:-1] + dot + extension
    return os.path.join(folder_name, filename)


@python_2_unicode_compatible
class AbstractImage(models.Model, TagSearchable):
    title = models.CharField(max_length=255, verbose_name=_('Title') )
    file = models.ImageField(verbose_name=_('File'), upload_to=get_upload_to, width_field='width', height_field='height')
    width = models.IntegerField(editable=False)
    height = models.IntegerField(editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, editable=False)

    tags = TaggableManager(help_text=None, blank=True, verbose_name=_('Tags'))

    focal_point_x = models.PositiveIntegerField(null=True, blank=True)
    focal_point_y = models.PositiveIntegerField(null=True, blank=True)
    focal_point_width = models.PositiveIntegerField(null=True, blank=True)
    focal_point_height = models.PositiveIntegerField(null=True, blank=True)

    def get_usage(self):
        return get_object_usage(self)

    @property
    def usage_url(self):
        return reverse('wagtailimages_image_usage',
                       args=(self.id,))

    search_fields = TagSearchable.search_fields + (
        index.FilterField('uploaded_by_user'),
    )

    def __str__(self):
        return self.title

    def get_rect(self):
        return Rect(0, 0, self.width, self.height)

    def get_babel(self):
        image_file = self.file.file
        image_file.open('rb')
        image_file.seek(0)

        return ImageBabel.from_file(image_file)

    def get_focal_point(self):
        if self.focal_point_x is not None and \
           self.focal_point_y is not None and \
           self.focal_point_width is not None and \
           self.focal_point_height is not None:
            return Rect.from_point(
                self.focal_point_x,
                self.focal_point_y,
                self.focal_point_width,
                self.focal_point_height,
            )

    def has_focal_point(self):
        return self.get_focal_point() is not None

    def set_focal_point(self, rect):
        if rect is not None:
            self.focal_point_x = rect.centroid_x
            self.focal_point_y = rect.centroid_y
            self.focal_point_width = rect.width
            self.focal_point_height = rect.height
        else:
            self.focal_point_x = None
            self.focal_point_y = None
            self.focal_point_width = None
            self.focal_point_height = None

    def get_suggested_focal_point(self):
        babel = self.get_babel()

        faces = babel.detect_faces()
        if faces:
            # Create a bounding box around all faces
            left = min(face.left for face in faces)
            top = min(face.top for face in faces)
            right = max(face.right for face in faces)
            bottom = max(face.bottom for face in faces)
            focal_point = Rect(left, top, right, bottom)
        else:
            features = babel.detect_features()
            if features:
                # Create a bounding box around all features
                left = min(feature.x for feature in features)
                top = min(feature.y for feature in features)
                right = max(feature.x for feature in features)
                bottom = max(feature.y for feature in features)
                focal_point = Rect(left, top, right, bottom)

        # Add 20% to width and height and give it a minimum size
        x, y = focal_point.centroid
        width, height = focal_point.size

        width *= 1.20
        height *= 1.20

        width = max(width, 100)
        height = max(height, 100)

        return Rect.from_point(x, y, width, height)

    def get_rendition(self, filter):
        if not hasattr(filter, 'run'):
            # assume we've been passed a filter spec string, rather than a Filter object
            # TODO: keep an in-memory cache of filters, to avoid a db lookup
            filter, created = Filter.objects.get_or_create(spec=filter)

        try:
            if self.has_focal_point():
                rendition = self.renditions.get(
                    filter=filter,
                    focal_point_key=self.get_focal_point().get_key(),
                )
            else:
                rendition = self.renditions.get(
                    filter=filter,
                    focal_point_key='',
                )
        except ObjectDoesNotExist:
            # Run the filter
            generated_image = filter.run(self, BytesIO())

            # generate new filename derived from old one, inserting the filter spec and focal point key before the extension
            if self.has_focal_point():
                focal_point_key = "focus-" + self.get_focal_point().get_key()
            else:
                focal_point_key = "focus-none"

            input_filename_parts = os.path.basename(self.file.file.name).split('.')
            filename_without_extension = '.'.join(input_filename_parts[:-1])
            extension = '.'.join([focal_point_key, filter.spec] + input_filename_parts[-1:])
            filename_without_extension = filename_without_extension[:(59-len(extension))] # Truncate filename to prevent it going over 60 chars
            output_filename = filename_without_extension + '.' + extension
            generated_image_file = File(generated_image, name=output_filename)

            if self.has_focal_point():
                rendition, created = self.renditions.get_or_create(
                    filter=filter,
                    focal_point_key=self.get_focal_point().get_key(),
                    defaults={'file': generated_image_file}
                )
            else:
                rendition, created = self.renditions.get_or_create(
                    filter=filter,
                    defaults={'file': generated_image_file}
                )

        return rendition

    def is_portrait(self):
        return (self.width < self.height)

    def is_landscape(self):
        return (self.height < self.width)

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    @property
    def default_alt_text(self):
        # by default the alt text field (used in rich text insertion) is populated
        # from the title. Subclasses might provide a separate alt field, and
        # override this
        return self.title

    def is_editable_by_user(self, user):
        if user.has_perm('wagtailimages.change_image'):
            # user has global permission to change images
            return True
        elif user.has_perm('wagtailimages.add_image') and self.uploaded_by_user == user:
            # user has image add permission, which also implicitly provides permission to edit their own images
            return True
        else:
            return False

    class Meta:
        abstract = True


class Image(AbstractImage):
    pass


# Do smartcropping calculations when user saves an image without a focal point
@receiver(pre_save, sender=Image)
def image_feature_detection(sender, instance, **kwargs):
    if getattr(settings, 'WAGTAILIMAGES_FEATURE_DETECTION_ENABLED', False):
        # Make sure the image doesn't already have a focal point
        if not instance.has_focal_point():
            # Set the focal point
            instance.set_focal_point(instance.get_suggested_focal_point())


# Receive the pre_delete signal and delete the file associated with the model instance.
@receiver(pre_delete, sender=Image)
def image_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.file.delete(False)


def get_image_model():
    from django.conf import settings
    from django.db.models import get_model

    try:
        app_label, model_name = settings.WAGTAILIMAGES_IMAGE_MODEL.split('.')
    except AttributeError:
        return Image
    except ValueError:
        raise ImproperlyConfigured("WAGTAILIMAGES_IMAGE_MODEL must be of the form 'app_label.model_name'")

    image_model = get_model(app_label, model_name)
    if image_model is None:
        raise ImproperlyConfigured("WAGTAILIMAGES_IMAGE_MODEL refers to model '%s' that has not been installed" % settings.WAGTAILIMAGES_IMAGE_MODEL)
    return image_model


class Filter(models.Model):
    """
    Represents an operation that can be applied to an Image to produce a rendition
    appropriate for final display on the website. Usually this would be a resize operation,
    but could potentially involve colour processing, etc.
    """
    spec = models.CharField(max_length=255, db_index=True)

    @cached_property
    def operations(self):
        operations = []

        for op_spec in self.spec.split():
            op_spec_parts = op_spec.split('-')
            op_class = self._registered_operations[op_spec_parts[0]]
            operations.append(op_class(*op_spec_parts))

        return operations

    def run(self, image, output_file):
        babel = image.get_babel()

        for operation in self.operations:
            operation.run(babel, image)

        babel.save_as_jpeg(output_file)

        return output_file


    _registered_operations = {}

    @classmethod
    def register_operation(cls, operation_name, operation_class):
        cls._registered_operations[operation_name] = operation_class


# TODO: Make this work with hooks
Filter.register_operation('original', image_operations.DoNothingOperation)
Filter.register_operation('fill', image_operations.FillOperation)
Filter.register_operation('min', image_operations.MinMaxOperation)
Filter.register_operation('max', image_operations.MinMaxOperation)
Filter.register_operation('width', image_operations.WidthHeightOperation)
Filter.register_operation('height', image_operations.WidthHeightOperation)


class AbstractRendition(models.Model):
    filter = models.ForeignKey('Filter', related_name='+')
    file = models.ImageField(upload_to='images', width_field='width', height_field='height')
    width = models.IntegerField(editable=False)
    height = models.IntegerField(editable=False)
    focal_point_key = models.CharField(max_length=255, blank=True, default='', editable=False)

    @property
    def url(self):
        return self.file.url

    @property
    def attrs(self):
        return mark_safe(
            'src="%s" width="%d" height="%d" alt="%s"' % (escape(self.url), self.width, self.height, escape(self.image.title))
        )

    def img_tag(self, extra_attributes=None):
        if extra_attributes:
            extra_attributes_string = format_html_join(' ', '{0}="{1}"', extra_attributes.items())
            return mark_safe('<img %s %s>' % (self.attrs, extra_attributes_string))
        else:
            return mark_safe('<img %s>' % self.attrs)

    class Meta:
        abstract = True


class Rendition(AbstractRendition):
    image = models.ForeignKey('Image', related_name='renditions')

    class Meta:
        unique_together = (
            ('image', 'filter', 'focal_point_key'),
        )


# Receive the pre_delete signal and delete the file associated with the model instance.
@receiver(pre_delete, sender=Rendition)
def rendition_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.file.delete(False)

