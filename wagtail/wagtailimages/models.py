from __future__ import absolute_import, unicode_literals

import hashlib
import inspect
import os.path
import warnings
from collections import OrderedDict
from contextlib import contextmanager

import django
from django.conf import settings
from django.core import checks
from django.core.exceptions import ImproperlyConfigured
from django.core.files import File
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_delete, pre_save
from django.db.utils import DatabaseError
from django.dispatch.dispatcher import receiver
from django.forms.widgets import flatatt
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.six import BytesIO, string_types, text_type
from django.utils.translation import ugettext_lazy as _
from taggit.managers import TaggableManager
from unidecode import unidecode
from willow.image import Image as WillowImage

from wagtail.utils.deprecation import RemovedInWagtail19Warning
from wagtail.wagtailadmin.utils import get_object_usage
from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.models import CollectionMember
from wagtail.wagtailimages.exceptions import InvalidFilterSpecError
from wagtail.wagtailimages.rect import Rect
from wagtail.wagtailsearch import index
from wagtail.wagtailsearch.queryset import SearchableQuerySetMixin


class SourceImageIOError(IOError):
    """
    Custom exception to distinguish IOErrors that were thrown while opening the source image
    """
    pass


class ImageQuerySet(SearchableQuerySetMixin, models.QuerySet):
    pass


def get_upload_to(instance, filename):
    """
    Obtain a valid upload path for an image file.

    This needs to be a module-level function so that it can be referenced within migrations,
    but simply delegates to the `get_upload_to` method of the instance, so that AbstractImage
    subclasses can override it.
    """
    return instance.get_upload_to(filename)


def get_rendition_upload_to(instance, filename):
    """
    Obtain a valid upload path for an image rendition file.

    This needs to be a module-level function so that it can be referenced within migrations,
    but simply delegates to the `get_upload_to` method of the instance, so that AbstractRendition
    subclasses can override it.
    """
    return instance.get_upload_to(filename)


@python_2_unicode_compatible
class AbstractImage(CollectionMember, index.Indexed, models.Model):
    title = models.CharField(max_length=255, verbose_name=_('title'))
    file = models.ImageField(
        verbose_name=_('file'), upload_to=get_upload_to, width_field='width', height_field='height'
    )
    width = models.IntegerField(verbose_name=_('width'), editable=False)
    height = models.IntegerField(verbose_name=_('height'), editable=False)
    created_at = models.DateTimeField(verbose_name=_('created at'), auto_now_add=True, db_index=True)
    uploaded_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('uploaded by user'),
        null=True, blank=True, editable=False, on_delete=models.SET_NULL
    )

    tags = TaggableManager(help_text=None, blank=True, verbose_name=_('tags'))

    focal_point_x = models.PositiveIntegerField(null=True, blank=True)
    focal_point_y = models.PositiveIntegerField(null=True, blank=True)
    focal_point_width = models.PositiveIntegerField(null=True, blank=True)
    focal_point_height = models.PositiveIntegerField(null=True, blank=True)

    file_size = models.PositiveIntegerField(null=True, editable=False)

    objects = ImageQuerySet.as_manager()

    def is_stored_locally(self):
        """
        Returns True if the image is hosted on the local filesystem
        """
        try:
            self.file.path

            return True
        except NotImplementedError:
            return False

    def get_file_size(self):
        if self.file_size is None:
            try:
                self.file_size = self.file.size
            except OSError:
                # File doesn't exist
                return

            self.save(update_fields=['file_size'])

        return self.file_size

    def get_upload_to(self, filename):
        folder_name = 'original_images'
        filename = self.file.field.storage.get_valid_name(filename)

        # do a unidecode in the filename and then
        # replace non-ascii characters in filename with _ , to sidestep issues with filesystem encoding
        filename = "".join((i if ord(i) < 128 else '_') for i in unidecode(filename))

        # Truncate filename so it fits in the 100 character limit
        # https://code.djangoproject.com/ticket/9893
        full_path = os.path.join(folder_name, filename)
        if len(full_path) >= 95:
            chars_to_trim = len(full_path) - 94
            prefix, extension = os.path.splitext(filename)
            filename = prefix[:-chars_to_trim] + extension
            full_path = os.path.join(folder_name, filename)

        return full_path

    def get_usage(self):
        return get_object_usage(self)

    @property
    def usage_url(self):
        return reverse('wagtailimages:image_usage',
                       args=(self.id,))

    search_fields = CollectionMember.search_fields + [
        index.SearchField('title', partial_match=True, boost=10),
        index.RelatedFields('tags', [
            index.SearchField('name', partial_match=True, boost=10),
        ]),
        index.FilterField('uploaded_by_user'),
    ]

    def __str__(self):
        return self.title

    @contextmanager
    def get_willow_image(self):
        # Open file if it is closed
        close_file = False
        try:
            image_file = self.file

            if self.file.closed:
                # Reopen the file
                if self.is_stored_locally():
                    self.file.open('rb')
                else:
                    # Some external storage backends don't allow reopening
                    # the file. Get a fresh file instance. #1397
                    storage = self._meta.get_field('file').storage
                    image_file = storage.open(self.file.name, 'rb')

                close_file = True
        except IOError as e:
            # re-throw this as a SourceImageIOError so that calling code can distinguish
            # these from IOErrors elsewhere in the process
            raise SourceImageIOError(text_type(e))

        # Seek to beginning
        image_file.seek(0)

        try:
            yield WillowImage.open(image_file)
        finally:
            if close_file:
                image_file.close()

    def get_rect(self):
        return Rect(0, 0, self.width, self.height)

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
        with self.get_willow_image() as willow:
            faces = willow.detect_faces()

            if faces:
                # Create a bounding box around all faces
                left = min(face[0] for face in faces)
                top = min(face[1] for face in faces)
                right = max(face[2] for face in faces)
                bottom = max(face[3] for face in faces)
                focal_point = Rect(left, top, right, bottom)
            else:
                features = willow.detect_features()
                if features:
                    # Create a bounding box around all features
                    left = min(feature[0] for feature in features)
                    top = min(feature[1] for feature in features)
                    right = max(feature[0] for feature in features)
                    bottom = max(feature[1] for feature in features)
                    focal_point = Rect(left, top, right, bottom)
                else:
                    return None

        # Add 20% to width and height and give it a minimum size
        x, y = focal_point.centroid
        width, height = focal_point.size

        width *= 1.20
        height *= 1.20

        width = max(width, 100)
        height = max(height, 100)

        return Rect.from_point(x, y, width, height)

    @classmethod
    def get_rendition_model(cls):
        """ Get the Rendition model for this Image model """
        if django.VERSION >= (1, 9):
            return cls.renditions.rel.related_model
        else:
            return cls.renditions.related.related_model

    def get_rendition(self, filter):
        if isinstance(filter, string_types):
            filter, created = Filter.objects.get_or_create(spec=filter)

        cache_key = filter.get_cache_key(self)
        Rendition = self.get_rendition_model()

        try:
            rendition = self.renditions.get(
                filter=filter,
                focal_point_key=cache_key,
            )
        except Rendition.DoesNotExist:
            # Generate the rendition image
            generated_image = filter.run(self, BytesIO())

            # Generate filename
            input_filename = os.path.basename(self.file.name)
            input_filename_without_extension, input_extension = os.path.splitext(input_filename)

            # A mapping of image formats to extensions
            FORMAT_EXTENSIONS = {
                'jpeg': '.jpg',
                'png': '.png',
                'gif': '.gif',
            }

            output_extension = filter.spec.replace('|', '.') + FORMAT_EXTENSIONS[generated_image.format_name]
            if cache_key:
                output_extension = cache_key + '.' + output_extension

            # Truncate filename to prevent it going over 60 chars
            output_filename_without_extension = input_filename_without_extension[:(59 - len(output_extension))]
            output_filename = output_filename_without_extension + '.' + output_extension

            rendition, created = self.renditions.get_or_create(
                filter=filter,
                focal_point_key=cache_key,
                defaults={'file': File(generated_image.f, name=output_filename)}
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
        from wagtail.wagtailimages.permissions import permission_policy
        return permission_policy.user_has_permission_for_instance(user, 'change', self)

    class Meta:
        abstract = True


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


# Do smartcropping calculations when user saves an image without a focal point
@receiver(pre_save, sender=Image)
def image_feature_detection(sender, instance, **kwargs):
    if getattr(settings, 'WAGTAILIMAGES_FEATURE_DETECTION_ENABLED', False):
        # Make sure the image doesn't already have a focal point
        if not instance.has_focal_point():
            # Set the focal point
            instance.set_focal_point(instance.get_suggested_focal_point())


# Receive the post_delete signal and delete the file associated with the model instance.
@receiver(post_delete, sender=Image)
def image_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.file.delete(False)


def get_image_model():
    from django.conf import settings
    from django.apps import apps

    try:
        app_label, model_name = settings.WAGTAILIMAGES_IMAGE_MODEL.split('.')
    except AttributeError:
        return Image
    except ValueError:
        raise ImproperlyConfigured("WAGTAILIMAGES_IMAGE_MODEL must be of the form 'app_label.model_name'")

    image_model = apps.get_model(app_label, model_name)
    if image_model is None:
        raise ImproperlyConfigured(
            "WAGTAILIMAGES_IMAGE_MODEL refers to model '%s' that has not been installed" %
            settings.WAGTAILIMAGES_IMAGE_MODEL
        )
    return image_model


class Filter(models.Model):
    """
    Represents one or more operations that can be applied to an Image to produce a rendition
    appropriate for final display on the website. Usually this would be a resize operation,
    but could potentially involve colour processing, etc.
    """

    # The spec pattern is operation1-var1-var2|operation2-var1
    spec = models.CharField(max_length=255, unique=True)

    @cached_property
    def operations(self):
        # Search for operations
        self._search_for_operations()

        # Build list of operation objects
        operations = []
        for op_spec in self.spec.split('|'):
            op_spec_parts = op_spec.split('-')

            if op_spec_parts[0] not in self._registered_operations:
                raise InvalidFilterSpecError("Unrecognised operation: %s" % op_spec_parts[0])

            op_class = self._registered_operations[op_spec_parts[0]]
            operations.append(op_class(*op_spec_parts))
        return operations

    def run(self, image, output):
        with image.get_willow_image() as willow:
            original_format = willow.format_name

            # Fix orientation of image
            willow = willow.auto_orient()

            env = {
                'original-format': original_format,
            }
            for operation in self.operations:
                # Check that the operation can take the "env" argument
                try:
                    inspect.getcallargs(operation.run, willow, image, env)
                    accepts_env = True
                except TypeError:
                    # Check that the paramters fit the old style, so we don't
                    # raise a warning if there is a coding error
                    inspect.getcallargs(operation.run, willow, image)
                    accepts_env = False
                    warnings.warn("ImageOperation run methods should take 4 "
                                  "arguments. %d.run only takes 3.",
                                  RemovedInWagtail19Warning)

                # Call operation
                if accepts_env:
                    willow = operation.run(willow, image, env) or willow
                else:
                    willow = operation.run(willow, image) or willow

            # Find the output format to use
            if 'output-format' in env:
                # Developer specified an output format
                output_format = env['output-format']
            else:
                # Default to outputting in original format
                output_format = original_format

                # Convert BMP files to PNG
                if original_format == 'bmp':
                    output_format = 'png'

                # Convert unanimated GIFs to PNG as well
                if original_format == 'gif' and not willow.has_animation():
                    output_format = 'png'

            if output_format == 'jpeg':
                # Allow changing of JPEG compression quality
                if 'jpeg-quality' in env:
                    quality = env['jpeg-quality']
                elif hasattr(settings, 'WAGTAILIMAGES_JPEG_QUALITY'):
                    quality = settings.WAGTAILIMAGES_JPEG_QUALITY
                else:
                    quality = 85

                return willow.save_as_jpeg(output, quality=quality, progressive=True, optimize=True)
            elif output_format == 'png':
                return willow.save_as_png(output)
            elif output_format == 'gif':
                return willow.save_as_gif(output)

    def get_cache_key(self, image):
        vary_parts = []

        for operation in self.operations:
            for field in getattr(operation, 'vary_fields', []):
                value = getattr(image, field, '')
                vary_parts.append(str(value))

        vary_string = '-'.join(vary_parts)

        # Return blank string if there are no vary fields
        if not vary_string:
            return ''

        return hashlib.sha1(vary_string.encode('utf-8')).hexdigest()[:8]

    _registered_operations = None

    @classmethod
    def _search_for_operations(cls):
        if cls._registered_operations is not None:
            return

        operations = []
        for fn in hooks.get_hooks('register_image_operations'):
            operations.extend(fn())

        cls._registered_operations = dict(operations)


class AbstractRendition(models.Model):
    filter = models.ForeignKey(Filter, related_name='+', null=True, blank=True)
    filter_spec = models.CharField(max_length=255, db_index=True, blank=True, default='')
    file = models.ImageField(upload_to=get_rendition_upload_to, width_field='width', height_field='height')
    width = models.IntegerField(editable=False)
    height = models.IntegerField(editable=False)
    focal_point_key = models.CharField(max_length=255, blank=True, default='', editable=False)

    @property
    def url(self):
        return self.file.url

    @property
    def alt(self):
        return self.image.title

    @property
    def attrs(self):
        """
        The src, width, height, and alt attributes for an <img> tag, as a HTML
        string
        """
        return flatatt(self.attrs_dict)

    @property
    def attrs_dict(self):
        """
        A dict of the src, width, height, and alt attributes for an <img> tag.
        """
        return OrderedDict([
            ('src', self.url),
            ('width', self.width),
            ('height', self.height),
            ('alt', self.alt),
        ])

    def img_tag(self, extra_attributes={}):
        attrs = self.attrs_dict.copy()
        attrs.update(extra_attributes)
        return mark_safe('<img{}>'.format(flatatt(attrs)))

    def __html__(self):
        return self.img_tag()

    def get_upload_to(self, filename):
        folder_name = 'images'
        filename = self.file.field.storage.get_valid_name(filename)
        return os.path.join(folder_name, filename)

    def save(self, *args, **kwargs):
        # populate the `filter_spec` field with the spec string of the filter. In Wagtail 1.8
        # Filter will be dropped as a model, and lookups will be done based on this string instead
        self.filter_spec = self.filter.spec
        return super(AbstractRendition, self).save(*args, **kwargs)

    @classmethod
    def check(cls, **kwargs):
        errors = super(AbstractRendition, cls).check(**kwargs)

        # If a filter_spec column exists on this model, and contains null entries, warn that
        # a data migration needs to be performed to populate it

        try:
            null_filter_spec_exists = cls.objects.filter(filter_spec='').exists()
        except DatabaseError:
            # The database is not in a state where the above lookup makes sense;
            # this is entirely expected, because system checks are performed before running
            # migrations. We're only interested in the specific case where the column exists
            # in the db and contains nulls.
            null_filter_spec_exists = False

        if null_filter_spec_exists:
            errors.append(
                checks.Warning(
                    "Custom image model %r needs a data migration to populate filter_src" % cls,
                    hint="The database representation of image filters has been changed, and a data "
                    "migration needs to be put in place before upgrading to Wagtail 1.8, in order to "
                    "avoid data loss. See http://docs.wagtail.io/en/latest/releases/1.7.html#filter-spec-migration",
                    obj=cls,
                    id='wagtailimages.W001',
                )
            )

        return errors

    class Meta:
        abstract = True


class Rendition(AbstractRendition):
    image = models.ForeignKey(Image, related_name='renditions', on_delete=models.CASCADE)

    class Meta:
        unique_together = (
            ('image', 'filter', 'focal_point_key'),
        )


# Receive the post_delete signal and delete the file associated with the model instance.
@receiver(post_delete, sender=Rendition)
def rendition_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.file.delete(False)
