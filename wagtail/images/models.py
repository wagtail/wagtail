import hashlib
import logging
import os.path
import time
from collections import OrderedDict
from contextlib import contextmanager
from io import BytesIO
from typing import Union

import willow
from django.apps import apps
from django.conf import settings
from django.core import checks
from django.core.cache import InvalidCacheBackendError, caches
from django.core.files import File
from django.core.files.storage import default_storage
from django.db import models
from django.forms.utils import flatatt
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager

from wagtail import hooks
from wagtail.coreutils import string_to_ascii
from wagtail.images.exceptions import (
    InvalidFilterSpecError,
    UnknownOutputImageFormatError,
)
from wagtail.images.image_operations import (
    FilterOperation,
    ImageTransform,
    TransformOperation,
)
from wagtail.images.rect import Rect
from wagtail.models import CollectionMember, ReferenceIndex
from wagtail.search import index
from wagtail.search.queryset import SearchableQuerySetMixin

logger = logging.getLogger("wagtail.images")


IMAGE_FORMAT_EXTENSIONS = {
    "jpeg": ".jpg",
    "png": ".png",
    "gif": ".gif",
    "webp": ".webp",
}


class SourceImageIOError(IOError):
    """
    Custom exception to distinguish IOErrors that were thrown while opening the source image
    """

    pass


class ImageQuerySet(SearchableQuerySetMixin, models.QuerySet):
    def prefetch_renditions(self, *filters):
        """
        Prefetches generated renditions for the given filters.
        Returns all renditions when no filters are provided.
        """
        rendition_model = self.model.get_rendition_model()
        queryset = rendition_model.objects.all()

        if filters:
            # Get a list of filter spec strings. The given value could contain Filter objects
            filter_specs = [
                filter.spec if isinstance(filter, Filter) else filter
                for filter in filters
            ]
            queryset = queryset.filter(filter_spec__in=filter_specs)

        return self.prefetch_related(
            models.Prefetch(
                "renditions",
                queryset=queryset,
                to_attr="prefetched_renditions",
            )
        )


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


def get_rendition_storage():
    """
    Obtain the storage object for an image rendition file.
    Returns custom storage (if defined), or the default storage.

    This needs to be a module-level function, because we do not yet
    have an instance when Django loads the models.
    """
    storage = getattr(settings, "WAGTAILIMAGES_RENDITION_STORAGE", default_storage)
    if isinstance(storage, str):
        module = import_string(storage)
        storage = module()
    return storage


class ImageFileMixin:
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

            self.save(update_fields=["file_size"])

        return self.file_size

    @contextmanager
    def open_file(self):
        # Open file if it is closed
        close_file = False
        try:
            image_file = self.file

            if self.file.closed:
                # Reopen the file
                if self.is_stored_locally():
                    self.file.open("rb")
                else:
                    # Some external storage backends don't allow reopening
                    # the file. Get a fresh file instance. #1397
                    storage = self._meta.get_field("file").storage
                    image_file = storage.open(self.file.name, "rb")

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
            yield willow.Image.open(image_file)


class WagtailImageFieldFile(models.fields.files.ImageFieldFile):
    """
    Override the ImageFieldFile in order to use Willow instead
    of Pillow.
    """

    def _get_image_dimensions(self):
        """
        override _get_image_dimensions to call our own get_image_dimensions.
        """
        if not hasattr(self, "_dimensions_cache"):
            self._dimensions_cache = self.get_image_dimensions()
        return self._dimensions_cache

    def get_image_dimensions(self):
        """
        The upstream ImageFieldFile calls a local function get_image_dimensions. In this implementation we've made get_image_dimensions
        a method to make it easier to override for Wagtail developers in the future.
        """
        close = self.closed
        try:
            self.open()
            image = willow.Image.open(self)
            return image.get_size()
        finally:
            if close:
                self.close()


class WagtailImageField(models.ImageField):
    """
    Override the attr_class on the Django ImageField Model to inject our ImageFieldFile
    with Willow support.
    """

    attr_class = WagtailImageFieldFile


class AbstractImage(ImageFileMixin, CollectionMember, index.Indexed, models.Model):
    title = models.CharField(max_length=255, verbose_name=_("title"))
    """ Use local ImageField with Willow support.  """
    file = WagtailImageField(
        verbose_name=_("file"),
        upload_to=get_upload_to,
        width_field="width",
        height_field="height",
    )
    width = models.IntegerField(verbose_name=_("width"), editable=False)
    height = models.IntegerField(verbose_name=_("height"), editable=False)
    created_at = models.DateTimeField(
        verbose_name=_("created at"), auto_now_add=True, db_index=True
    )
    uploaded_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("uploaded by user"),
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL,
    )
    uploaded_by_user.wagtail_reference_index_ignore = True

    tags = TaggableManager(help_text=None, blank=True, verbose_name=_("tags"))

    focal_point_x = models.PositiveIntegerField(null=True, blank=True)
    focal_point_y = models.PositiveIntegerField(null=True, blank=True)
    focal_point_width = models.PositiveIntegerField(null=True, blank=True)
    focal_point_height = models.PositiveIntegerField(null=True, blank=True)

    file_size = models.PositiveIntegerField(null=True, editable=False)
    # A SHA-1 hash of the file contents
    file_hash = models.CharField(
        max_length=40, blank=True, editable=False, db_index=True
    )

    objects = ImageQuerySet.as_manager()

    def _set_file_hash(self, file_contents):
        self.file_hash = hashlib.sha1(file_contents).hexdigest()

    def get_file_hash(self):
        if self.file_hash == "":
            with self.open_file() as f:
                self._set_file_hash(f.read())

            self.save(update_fields=["file_hash"])

        return self.file_hash

    def _set_image_file_metadata(self):
        self.file.open()

        # Set new image file size
        self.file_size = self.file.size

        # Set new image file hash
        self._set_file_hash(self.file.read())
        self.file.seek(0)

    def get_upload_to(self, filename):
        folder_name = "original_images"
        filename = self.file.field.storage.get_valid_name(filename)

        # convert the filename to simple ascii characters and then
        # replace non-ascii characters in filename with _ , to sidestep issues with filesystem encoding
        filename = "".join(
            (i if ord(i) < 128 else "_") for i in string_to_ascii(filename)
        )

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
        return ReferenceIndex.get_references_to(self).group_by_source_object()

    @property
    def usage_url(self):
        return reverse("wagtailimages:image_usage", args=(self.id,))

    search_fields = CollectionMember.search_fields + [
        index.SearchField("title", partial_match=True, boost=10),
        index.AutocompleteField("title"),
        index.FilterField("title"),
        index.RelatedFields(
            "tags",
            [
                index.SearchField("name", partial_match=True, boost=10),
                index.AutocompleteField("name"),
            ],
        ),
        index.FilterField("uploaded_by_user"),
    ]

    def __str__(self):
        return self.title

    def get_rect(self):
        return Rect(0, 0, self.width, self.height)

    def get_focal_point(self):
        if (
            self.focal_point_x is not None
            and self.focal_point_y is not None
            and self.focal_point_width is not None
            and self.focal_point_height is not None
        ):
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
        """Get the Rendition model for this Image model"""
        return cls.renditions.rel.related_model

    def get_rendition(self, filter: Union["Filter", str]) -> "AbstractRendition":
        """
        Returns a ``Rendition`` instance with a ``file`` field value (an
        image) reflecting the supplied ``filter`` value and focal point values
        from this object.

        Note: If using custom image models, an instance of the custom rendition
        model will be returned.
        """
        if isinstance(filter, str):
            filter = Filter(spec=filter)

        Rendition = self.get_rendition_model()

        try:
            rendition = self.find_existing_rendition(filter)
        except Rendition.DoesNotExist:
            rendition = self.create_rendition(filter)
            # Reuse this rendition if requested again from this object
            if "renditions" in getattr(self, "_prefetched_objects_cache", {}):
                self._prefetched_objects_cache["renditions"]._result_cache.append(
                    rendition
                )
            elif hasattr(self, "prefetched_renditions"):
                self.prefetched_renditions.append(rendition)

        try:
            cache = caches["renditions"]
            key = Rendition.construct_cache_key(
                self.id, filter.get_cache_key(self), filter.spec
            )
            cache.set(key, rendition)
        except InvalidCacheBackendError:
            pass

        return rendition

    def find_existing_rendition(self, filter: "Filter") -> "AbstractRendition":
        """
        Returns an existing ``Rendition`` instance with a ``file`` field value
        (an image) reflecting the supplied ``filter`` value and focal point
        values from this object.

        If no such rendition exists, a ``DoesNotExist`` error is raised for the
        relevant model.

        Note: If using custom image models, an instance of the custom rendition
        model will be returned.
        """

        Rendition = self.get_rendition_model()
        cache_key = filter.get_cache_key(self)

        # Interrogate prefetched values first (if available)
        if "renditions" in getattr(self, "_prefetched_objects_cache", {}):
            prefetched_renditions = self.renditions.all()
        else:
            prefetched_renditions = getattr(self, "prefetched_renditions", None)

        if prefetched_renditions is not None:
            for rendition in prefetched_renditions:
                if (
                    rendition.filter_spec == filter.spec
                    and rendition.focal_point_key == cache_key
                ):
                    return rendition

            # If renditions were prefetched, assume that if a suitable match
            # existed, it would have been present and already returned above
            # (avoiding further cache/db lookups)
            raise Rendition.DoesNotExist

        # Next, query the cache (if configured)
        try:
            cache = caches["renditions"]
            key = Rendition.construct_cache_key(self.id, cache_key, filter.spec)
            cached_rendition = cache.get(key)
            if cached_rendition:
                return cached_rendition
        except InvalidCacheBackendError:
            pass

        # Resort to a get() lookup
        return self.renditions.get(filter_spec=filter.spec, focal_point_key=cache_key)

    def create_rendition(self, filter: "Filter") -> "AbstractRendition":
        """
        Creates and returns a ``Rendition`` instance with a ``file`` field
        value (an image) reflecting the supplied ``filter`` value and focal
        point values from this object.

        This method is usually called by ``Image.get_rendition()``, after first
        checking that a suitable rendition does not already exist.

        Note: If using custom image models, an instance of the custom rendition
        model will be returned.
        """
        # Because of unique constraints applied to the model, we use
        # get_or_create() to guard against race conditions
        rendition, created = self.renditions.get_or_create(
            filter_spec=filter.spec,
            focal_point_key=filter.get_cache_key(self),
            defaults={"file": self.generate_rendition_file(filter)},
        )
        return rendition

    def generate_rendition_file(self, filter: "Filter") -> File:
        """
        Generates an in-memory image matching the supplied ``filter`` value
        and focal point value from this object, wraps it in a ``File`` object
        with a suitable filename, and returns it. The return value is used
        as the ``file`` field value for rendition objects saved by
        ``AbstractImage.create_rendition()``.

        NOTE: The responsibility of generating the new image from the original
        falls to the supplied ``filter`` object. If you want to do anything
        custom with rendition images (for example, to preserve metadata from
        the original image), you might want to consider swapping out ``filter``
        for an instance of a custom ``Filter`` subclass of your design.
        """

        cache_key = filter.get_cache_key(self)

        logger.debug(
            "Generating '%s' rendition for image %d",
            filter.spec,
            self.pk,
        )

        start_time = time.time()

        try:
            generated_image = filter.run(self, BytesIO())

            logger.debug(
                "Generated '%s' rendition for image %d in %.1fms",
                filter.spec,
                self.pk,
                (time.time() - start_time) * 1000,
            )
        except:  # noqa:B901,E722
            logger.debug(
                "Failed to generate '%s' rendition for image %d",
                filter.spec,
                self.pk,
            )
            raise

        # Generate filename
        input_filename = os.path.basename(self.file.name)
        input_filename_without_extension, input_extension = os.path.splitext(
            input_filename
        )
        output_extension = (
            filter.spec.replace("|", ".")
            + IMAGE_FORMAT_EXTENSIONS[generated_image.format_name]
        )
        if cache_key:
            output_extension = cache_key + "." + output_extension

        # Truncate filename to prevent it going over 60 chars
        output_filename_without_extension = input_filename_without_extension[
            : (59 - len(output_extension))
        ]
        output_filename = output_filename_without_extension + "." + output_extension

        return File(generated_image.f, name=output_filename)

    def is_portrait(self):
        return self.width < self.height

    def is_landscape(self):
        return self.height < self.width

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

        return permission_policy.user_has_permission_for_instance(user, "change", self)

    class Meta:
        abstract = True


class Image(AbstractImage):
    admin_form_fields = (
        "title",
        "file",
        "collection",
        "tags",
        "focal_point_x",
        "focal_point_y",
        "focal_point_width",
        "focal_point_height",
    )

    class Meta(AbstractImage.Meta):
        verbose_name = _("image")
        verbose_name_plural = _("images")
        permissions = [
            ("choose_image", "Can choose image"),
        ]


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
        registered_operations = {}
        for fn in hooks.get_hooks("register_image_operations"):
            registered_operations.update(dict(fn()))

        # Build list of operation objects
        operations = []
        for op_spec in self.spec.split("|"):
            op_spec_parts = op_spec.split("-")

            if op_spec_parts[0] not in registered_operations:
                raise InvalidFilterSpecError(
                    "Unrecognised operation: %s" % op_spec_parts[0]
                )

            op_class = registered_operations[op_spec_parts[0]]
            operations.append(op_class(*op_spec_parts))
        return operations

    @property
    def transform_operations(self):
        return [
            operation
            for operation in self.operations
            if isinstance(operation, TransformOperation)
        ]

    @property
    def filter_operations(self):
        return [
            operation
            for operation in self.operations
            if isinstance(operation, FilterOperation)
        ]

    def get_transform(self, image, size=None):
        """
        Returns an ImageTransform with all the transforms in this filter applied.

        The ImageTransform is an object with two attributes:
         - .size - The size of the final image
         - .matrix - An affine transformation matrix that combines any
           transform/scale/rotation operations that need to be applied to the image
        """

        if not size:
            size = (image.width, image.height)

        transform = ImageTransform(size)
        for operation in self.transform_operations:
            transform = operation.run(transform, image)
        return transform

    def run(self, image, output):
        with image.get_willow_image() as willow:
            original_format = willow.format_name

            # Fix orientation of image
            willow = willow.auto_orient()

            # Transform the image
            transform = self.get_transform(
                image, (willow.image.width, willow.image.height)
            )
            willow = willow.crop(transform.get_rect().round())
            willow = willow.resize(transform.size)

            # Apply filters
            env = {
                "original-format": original_format,
            }
            for operation in self.filter_operations:
                willow = operation.run(willow, image, env) or willow

            # Find the output format to use
            if "output-format" in env:
                # Developer specified an output format
                output_format = env["output-format"]
            else:
                # Convert bmp and webp to png by default
                default_conversions = {
                    "bmp": "png",
                    "webp": "png",
                }

                # Convert unanimated GIFs to PNG as well
                if not willow.has_animation():
                    default_conversions["gif"] = "png"

                # Allow the user to override the conversions
                conversion = getattr(settings, "WAGTAILIMAGES_FORMAT_CONVERSIONS", {})
                default_conversions.update(conversion)

                # Get the converted output format falling back to the original
                output_format = default_conversions.get(
                    original_format, original_format
                )

            if output_format == "jpeg":
                # Allow changing of JPEG compression quality
                if "jpeg-quality" in env:
                    quality = env["jpeg-quality"]
                else:
                    quality = getattr(settings, "WAGTAILIMAGES_JPEG_QUALITY", 85)

                # If the image has an alpha channel, give it a white background
                if willow.has_alpha():
                    willow = willow.set_background_color_rgb((255, 255, 255))

                return willow.save_as_jpeg(
                    output, quality=quality, progressive=True, optimize=True
                )
            elif output_format == "png":
                return willow.save_as_png(output, optimize=True)
            elif output_format == "gif":
                return willow.save_as_gif(output)
            elif output_format == "webp":
                # Allow changing of WebP compression quality
                if (
                    "output-format-options" in env
                    and "lossless" in env["output-format-options"]
                ):
                    return willow.save_as_webp(output, lossless=True)
                elif "webp-quality" in env:
                    quality = env["webp-quality"]
                else:
                    quality = getattr(settings, "WAGTAILIMAGES_WEBP_QUALITY", 85)

                return willow.save_as_webp(output, quality=quality)
            raise UnknownOutputImageFormatError(
                f"Unknown output image format '{output_format}'"
            )

    def get_cache_key(self, image):
        vary_parts = []

        for operation in self.operations:
            for field in getattr(operation, "vary_fields", []):
                value = getattr(image, field, "")
                vary_parts.append(str(value))

        vary_string = "-".join(vary_parts)

        # Return blank string if there are no vary fields
        if not vary_string:
            return ""

        return hashlib.sha1(vary_string.encode("utf-8")).hexdigest()[:8]


class AbstractRendition(ImageFileMixin, models.Model):
    filter_spec = models.CharField(max_length=255, db_index=True)
    """ Use local ImageField with Willow support.  """
    file = WagtailImageField(
        upload_to=get_rendition_upload_to,
        storage=get_rendition_storage,
        width_field="width",
        height_field="height",
    )
    width = models.IntegerField(editable=False)
    height = models.IntegerField(editable=False)
    focal_point_key = models.CharField(
        max_length=16, blank=True, default="", editable=False
    )

    wagtail_reference_index_ignore = True

    @property
    def url(self):
        return self.file.url

    @property
    def alt(self):
        return self.image.default_alt_text

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
        return OrderedDict(
            [
                ("src", self.url),
                ("width", self.width),
                ("height", self.height),
                ("alt", self.alt),
            ]
        )

    @property
    def full_url(self):
        url = self.url
        if hasattr(settings, "WAGTAILADMIN_BASE_URL") and url.startswith("/"):
            url = settings.WAGTAILADMIN_BASE_URL + url
        return url

    @property
    def filter(self):
        return Filter(self.filter_spec)

    @cached_property
    def focal_point(self):
        image_focal_point = self.image.get_focal_point()
        if image_focal_point:
            transform = self.filter.get_transform(self.image)
            return image_focal_point.transform(transform)

    @property
    def background_position_style(self):
        """
        Returns a `background-position` rule to be put in the inline style of an element which uses the rendition for its background.

        This positions the rendition according to the value of the focal point. This is helpful for when the element does not have
        the same aspect ratio as the rendition.

        For example:

            {% image page.image fill-1920x600 as image %}
            <div style="background-image: url('{{ image.url }}'); {{ image.background_position_style }}">
            </div>
        """
        focal_point = self.focal_point
        if focal_point:
            horz = int((focal_point.x * 100) // self.width)
            vert = int((focal_point.y * 100) // self.height)
            return "background-position: {}% {}%;".format(horz, vert)
        else:
            return "background-position: 50% 50%;"

    def img_tag(self, extra_attributes={}):
        attrs = self.attrs_dict.copy()

        attrs.update(apps.get_app_config("wagtailimages").default_attrs)

        attrs.update(extra_attributes)

        return mark_safe("<img{}>".format(flatatt(attrs)))

    def __html__(self):
        return self.img_tag()

    def get_upload_to(self, filename):
        folder_name = "images"
        filename = self.file.field.storage.get_valid_name(filename)
        return os.path.join(folder_name, filename)

    @classmethod
    def check(cls, **kwargs):
        errors = super(AbstractRendition, cls).check(**kwargs)
        if not cls._meta.abstract:
            if not any(
                set(constraint) == {"image", "filter_spec", "focal_point_key"}
                for constraint in cls._meta.unique_together
            ):
                errors.append(
                    checks.Error(
                        "Custom rendition model %r has an invalid unique_together setting"
                        % cls,
                        hint="Custom rendition models must include the constraint "
                        "('image', 'filter_spec', 'focal_point_key') in their unique_together definition.",
                        obj=cls,
                        id="wagtailimages.E001",
                    )
                )

        return errors

    @staticmethod
    def construct_cache_key(image_id, filter_cache_key, filter_spec):
        return "image-{}-{}-{}".format(image_id, filter_cache_key, filter_spec)

    def purge_from_cache(self):
        try:
            cache = caches["renditions"]
            cache.delete(
                self.construct_cache_key(
                    self.image_id, self.focal_point_key, self.filter_spec
                )
            )
        except InvalidCacheBackendError:
            pass

    class Meta:
        abstract = True


class Rendition(AbstractRendition):
    image = models.ForeignKey(
        Image, related_name="renditions", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = (("image", "filter_spec", "focal_point_key"),)


class UploadedImage(models.Model):
    """
    Temporary storage for images uploaded through the multiple image uploader, when validation rules (e.g.
    required metadata fields) prevent creating an Image object from the image file alone. In this case,
    the image file is stored against this model, to be turned into an Image object once the full form
    has been filled in.
    """

    file = models.ImageField(upload_to="uploaded_images", max_length=200)
    uploaded_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("uploaded by user"),
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL,
    )
    uploaded_by_user.wagtail_reference_index_ignore = True
