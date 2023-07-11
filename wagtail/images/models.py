import logging
import os.path
from contextlib import contextmanager

import willow
from django.conf import settings
from django.core import checks
from django.core.cache import DEFAULT_CACHE_ALIAS, InvalidCacheBackendError, caches
from django.core.cache.backends.base import BaseCache
from django.core.files.storage import default_storage
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property, classproperty
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager

from wagtail.coreutils import string_to_ascii
from wagtail.images.filter import Filter
from wagtail.images.rect import Rect
from wagtail.images.rendition_backends import (
    BaseRendition,
    get_rendition_backends_for_image,
)
from wagtail.models import CollectionMember, ReferenceIndex
from wagtail.search import index
from wagtail.search.queryset import SearchableQuerySetMixin
from wagtail.utils.file import hash_filelike

logger = logging.getLogger("wagtail.images")


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
    but simply delegates to the `get_upload_to` method of the instance, so that BaseRendition
    subclasses can override it.
    """
    return instance.get_upload_to(filename)


def get_rendition_upload_to(instance, filename):
    """
    Obtain a valid upload path for an image rendition file.

    This needs to be a module-level function so that it can be referenced within migrations,
    but simply delegates to the `get_upload_to` method of the instance, so that BaseRendition
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
            except Exception as e:  # noqa: BLE001
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
        except OSError as e:
            # re-throw this as a SourceImageIOError so that calling code can distinguish
            # these from errors elsewhere in the process
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
            else:
                self.seek(0)


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

    def _set_file_hash(self):
        with self.open_file() as f:
            self.file_hash = hash_filelike(f)

    def get_file_hash(self):
        if self.file_hash == "":
            self._set_file_hash()
            self.save(update_fields=["file_hash"])

        return self.file_hash

    def _set_image_file_metadata(self):
        self.file.open()

        # Set new image file size
        self.file_size = self.file.size

        # Set new image file hash
        self._set_file_hash()
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
        return ReferenceIndex.get_grouped_references_to(self)

    @property
    def usage_url(self):
        return reverse("wagtailimages:image_usage", args=(self.id,))

    search_fields = CollectionMember.search_fields + [
        index.SearchField("title", boost=10),
        index.AutocompleteField("title"),
        index.FilterField("title"),
        index.RelatedFields(
            "tags",
            [
                index.SearchField("name", boost=10),
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

    def get_rendition(self, filter: Filter | str) -> BaseRendition | None:
        """
        Returns a ``Rendition`` instance with a ``file`` field value (an
        image) reflecting the supplied ``filter`` value and focal point values
        from the provided image.

        Note: If using custom image models, an instance of the custom rendition
        model will be returned.
        """
        for backend in get_rendition_backends_for_image(self):
            rendition = backend.get_rendition(self, filter)
            if rendition is not None:
                return rendition

        return None

    def get_renditions(self, *filter_specs: str) -> dict[str, BaseRendition] | None:
        """
        Returns a ``dict`` of ``Rendition`` instances with image files reflecting
        the supplied ``filter_specs``, keyed by the relevant ``filter_spec`` string.

        Note: If using custom image models, instances of the custom rendition
        model will be returned.
        """
        for backend in get_rendition_backends_for_image(self):
            renditions = backend.get_renditions(self, *filter_specs)
            if renditions is not None:
                return renditions

        return None

    def is_portrait(self):
        return self.width < self.height

    def is_landscape(self):
        return self.height < self.width

    def is_svg(self):
        _, ext = os.path.splitext(self.file.name)
        return ext.lower() == ".svg"

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


class AbstractRendition(BaseRendition, ImageFileMixin, models.Model):
    filter_spec = models.CharField(max_length=255, db_index=True)
    # Use local ImageField with Willow support
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
            return f"background-position: {horz}% {vert}%;"
        else:
            return "background-position: 50% 50%;"

    def get_upload_to(self, filename):
        folder_name = "images"
        filename = self.file.field.storage.get_valid_name(filename)
        return os.path.join(folder_name, filename)

    @classmethod
    def check(cls, **kwargs):
        errors = super().check(**kwargs)
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

    @classproperty
    def cache_backend(cls) -> BaseCache:
        try:
            return caches["renditions"]
        except InvalidCacheBackendError:
            return caches[DEFAULT_CACHE_ALIAS]

    @staticmethod
    def construct_cache_key(image, filter_cache_key, filter_spec):
        return "wagtail-rendition-" + "-".join(
            [str(image.id), image.file_hash, filter_cache_key, filter_spec]
        )

    @classproperty
    def cache_backend(cls) -> BaseCache:
        try:
            return caches["renditions"]
        except InvalidCacheBackendError:
            return caches[DEFAULT_CACHE_ALIAS]

    def get_cache_key(self):
        return self.construct_cache_key(
            self.image, self.focal_point_key, self.filter_spec
        )

    def purge_from_cache(self):
        self.cache_backend.delete(self.get_cache_key())

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
