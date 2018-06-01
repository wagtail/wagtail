import hashlib
import os.path
from collections import OrderedDict
from contextlib import contextmanager
from io import BytesIO

from django.conf import settings
from django.core import checks
from django.core.files import File
from django.db import models
from django.forms.utils import flatatt
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from taggit.managers import TaggableManager
from unidecode import unidecode
from willow.image import Image as WillowImage

from wagtail.admin.utils import get_object_usage
from wagtail.core import hooks
from wagtail.core.models import CollectionMember
from wagtail.images.exceptions import InvalidFilterSpecError
from wagtail.images.rect import Rect
from wagtail.search import index
from wagtail.search.queryset import SearchableQuerySetMixin


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
    # A SHA-1 hash of the file contents
    file_hash = models.CharField(max_length=40, blank=True, editable=False)

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
            except Exception as e:
                # File not found
                #
                # Have to catch everything, because the exception
                # depends on the file subclass, and therefore the
                # storage being used.
                raise SourceImageIOError(str(e))

            self.save(update_fields=['file_size'])

        return self.file_size

    def _set_file_hash(self, file_contents):
        self.file_hash = hashlib.sha1(file_contents).hexdigest()

    def get_file_hash(self):
        if self.file_hash == '':
            with self.open_file() as f:
                self._set_file_hash(f.read())

            self.save(update_fields=['file_hash'])

        return self.file_hash

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
        index.AutocompleteField('title'),
        index.FilterField('title'),
        index.RelatedFields('tags', [
            index.SearchField('name', partial_match=True, boost=10),
            index.AutocompleteField('name'),
        ]),
        index.FilterField('uploaded_by_user'),
    ]

    def __str__(self):
        return self.title

    @contextmanager
    def open_file(self):
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
            raise SourceImageIOError(str(e))

        # Seek to beginning
        image_file.seek(0)

        try:
            yield image_file
        finally:
            if close_file:
                image_file.close()

    @contextmanager
    def get_willow_image(self):
        with self.open_file() as image_file:
            yield WillowImage.open(image_file)

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
        return cls.renditions.rel.related_model

    def get_rendition(self, filter):
        if isinstance(filter, str):
            filter = Filter(spec=filter)

        cache_key = filter.get_cache_key(self)
        Rendition = self.get_rendition_model()

        try:
            rendition = self.renditions.get(
                filter_spec=filter.spec,
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
                filter_spec=filter.spec,
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
        from wagtail.images.permissions import permission_policy
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

    class Meta:
        verbose_name = _('image')
        verbose_name_plural = _('images')


class Filter:
    """
    Represents one or more operations that can be applied to an Image to produce a rendition
    appropriate for final display on the website. Usually this would be a resize operation,
    but could potentially involve colour processing, etc.
    """

    def __init__(self, spec=None):
        # The spec pattern is operation1-var1-var2|operation2-var1
        self.spec = spec

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
                willow = operation.run(willow, image, env) or willow

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

                # If the image has an alpha channel, give it a white background
                if willow.has_alpha():
                    willow = willow.set_background_color_rgb((255, 255, 255))

                return willow.save_as_jpeg(output, quality=quality, progressive=True, optimize=True)
            elif output_format == 'png':
                return willow.save_as_png(output, optimize=True)
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
    filter_spec = models.CharField(max_length=255, db_index=True)
    file = models.ImageField(upload_to=get_rendition_upload_to, width_field='width', height_field='height')
    width = models.IntegerField(editable=False)
    height = models.IntegerField(editable=False)
    focal_point_key = models.CharField(max_length=16, blank=True, default='', editable=False)

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

    @classmethod
    def check(cls, **kwargs):
        errors = super(AbstractRendition, cls).check(**kwargs)
        if not cls._meta.abstract:
            if not any(
                set(constraint) == set(['image', 'filter_spec', 'focal_point_key'])
                for constraint in cls._meta.unique_together
            ):
                errors.append(
                    checks.Error(
                        "Custom rendition model %r has an invalid unique_together setting" % cls,
                        hint="Custom rendition models must include the constraint "
                        "('image', 'filter_spec', 'focal_point_key') in their unique_together definition.",
                        obj=cls,
                        id='wagtailimages.E001',
                    )
                )

        return errors

    class Meta:
        abstract = True


class Rendition(AbstractRendition):
    image = models.ForeignKey(Image, related_name='renditions', on_delete=models.CASCADE)

    class Meta:
        unique_together = (
            ('image', 'filter_spec', 'focal_point_key'),
        )
