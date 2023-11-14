import hashlib
import itertools
import logging
import os.path
import re
import time
from collections import OrderedDict, defaultdict
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from io import BytesIO
from tempfile import SpooledTemporaryFile
from typing import Any, Dict, Iterable, List, Optional, Union

import willow
from django.apps import apps
from django.conf import settings
from django.core import checks
from django.core.cache import DEFAULT_CACHE_ALIAS, InvalidCacheBackendError, caches
from django.core.cache.backends.base import BaseCache
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import models
from django.db.models import Q
from django.forms.utils import flatatt
from django.urls import reverse
from django.utils.functional import cached_property, classproperty
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
from wagtail.images.fields import image_format_name_to_content_type
from wagtail.images.image_operations import (
    FilterOperation,
    FormatOperation,
    ImageTransform,
    TransformOperation,
)
from wagtail.images.rect import Rect
from wagtail.models import CollectionMember, ReferenceIndex
from wagtail.search import index
from wagtail.search.queryset import SearchableQuerySetMixin
from wagtail.utils.file import hash_filelike

logger = logging.getLogger("wagtail.images")


IMAGE_FORMAT_EXTENSIONS = {
    "avif": ".avif",
    "jpeg": ".jpg",
    "png": ".png",
    "gif": ".gif",
    "webp": ".webp",
    "svg": ".svg",
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
        if self.is_svg():
            # We can't run feature detection on SVGs, and don't provide a
            # pathway from SVG -> raster formats, so don't try it.
            return None

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

    def _get_prefetched_renditions(self) -> Union[Iterable["AbstractRendition"], None]:
        if "renditions" in getattr(self, "_prefetched_objects_cache", {}):
            return self.renditions.all()
        return getattr(self, "prefetched_renditions", None)

    def _add_to_prefetched_renditions(self, rendition: "AbstractRendition") -> None:
        # Reuse this rendition if requested again from this object
        try:
            self._prefetched_objects_cache["renditions"]._result_cache.append(rendition)
        except (AttributeError, KeyError):
            pass
        try:
            self.prefetched_renditions.append(rendition)
        except AttributeError:
            pass

    def get_rendition(self, filter: Union["Filter", str]) -> "AbstractRendition":
        """
        Returns a ``Rendition`` instance with a ``file`` field value (an
        image) reflecting the supplied ``filter`` value and focal point values
        from this object.

        Note: If using custom image models, an instance of the custom rendition
        model will be returned.
        """
        Rendition = self.get_rendition_model()

        if isinstance(filter, str):
            filter = Filter(spec=filter)

        try:
            rendition = self.find_existing_rendition(filter)
        except Rendition.DoesNotExist:
            rendition = self.create_rendition(filter)
            # Reuse this rendition if requested again from this object
            self._add_to_prefetched_renditions(rendition)

        cache_key = Rendition.construct_cache_key(
            self, filter.get_cache_key(self), filter.spec
        )
        Rendition.cache_backend.set(cache_key, rendition)

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

        try:
            return self.find_existing_renditions(filter)[filter]
        except KeyError:
            raise Rendition.DoesNotExist

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

    def get_renditions(
        self, *filters: Union["Filter", str]
    ) -> Dict[str, "AbstractRendition"]:
        """
        Returns a ``dict`` of ``Rendition`` instances with image files reflecting
        the supplied ``filters``, keyed by filter spec patterns.

        Note: If using custom image models, instances of the custom rendition
        model will be returned.
        """
        Rendition = self.get_rendition_model()
        # We don’t support providing mixed Filter and string arguments in the same call.
        if isinstance(filters[0], str):
            filters = [Filter(spec) for spec in dict.fromkeys(filters).keys()]

        # Find existing renditions where possible
        renditions = self.find_existing_renditions(*filters)

        # Create any renditions not found in prefetched values, cache or database
        not_found = [f for f in filters if f not in renditions]
        for filter, rendition in self.create_renditions(*not_found).items():
            self._add_to_prefetched_renditions(rendition)
            renditions[filter] = rendition

        # Update the cache
        cache_additions = {
            Rendition.construct_cache_key(
                self, filter.get_cache_key(self), filter.spec
            ): rendition
            for filter, rendition in renditions.items()
            # prevent writing of cached data back to the cache
            if not getattr(rendition, "_from_cache", False)
        }
        if cache_additions:
            Rendition.cache_backend.set_many(cache_additions)

        # Make sure key insertion order matches the input order.
        return {filter.spec: renditions[filter] for filter in filters}

    def find_existing_renditions(
        self, *filters: "Filter"
    ) -> Dict["Filter", "AbstractRendition"]:
        """
        Returns a dictionary of existing ``Rendition`` instances with ``file``
        values (images) reflecting the supplied ``filters`` and the focal point
        values from this object.

        Filters for which an existing rendition cannot be found are ommitted
        from the return value. If none of the requested renditions have been
        created before, the return value will be an empty dict.
        """
        Rendition = self.get_rendition_model()
        filters_by_spec: Dict[str, Filter] = {f.spec: f for f in filters}
        found: Dict[Filter, AbstractRendition] = {}

        # Interrogate prefetched values first (where available)
        prefetched_renditions = self._get_prefetched_renditions()
        if prefetched_renditions is not None:
            # NOTE: When renditions are prefetched, it's assumed that if the
            # requested renditions exist, they will be present in the
            # prefetched value, and further cache/database lookups are avoided.

            # group renditions by the filters of interest
            potential_matches: Dict[Filter, List[AbstractRendition]] = defaultdict(list)
            for rendition in prefetched_renditions:
                try:
                    filter = filters_by_spec[rendition.filter_spec]
                except KeyError:
                    continue  # this rendition can be ignored
                else:
                    potential_matches[filter].append(rendition)

            # For each filter we have renditions for, look for one with a
            # 'focal_point_key' value matching filter.get_cache_key()
            for filter, renditions in potential_matches.items():
                focal_point_key = filter.get_cache_key(self)
                for rendition in renditions:
                    if rendition.focal_point_key == focal_point_key:
                        # to prevent writing of cached data back to the cache
                        rendition._from_cache = True
                        # use this rendition
                        found[filter] = rendition
                        # skip to the next filter
                        break
        else:
            # Renditions are not prefetched, so attempt to find suitable
            # items in the cache or database

            # Query the cache first
            cache_keys = [
                Rendition.construct_cache_key(self, filter.get_cache_key(self), spec)
                for spec, filter in filters_by_spec.items()
            ]
            for rendition in Rendition.cache_backend.get_many(cache_keys).values():
                filter = filters_by_spec[rendition.filter_spec]
                found[filter] = rendition

            # For items not found in the cache, look in the database
            not_found = [f for f in filters if f not in found]
            if not_found:
                lookup_q = Q()
                for filter in not_found:
                    lookup_q |= Q(
                        filter_spec=filter.spec,
                        focal_point_key=filter.get_cache_key(self),
                    )
                for rendition in self.renditions.filter(lookup_q):
                    filter = filters_by_spec[rendition.filter_spec]
                    found[filter] = rendition
        return found

    def create_renditions(
        self, *filters: "Filter"
    ) -> Dict["Filter", "AbstractRendition"]:
        """
        Creates multiple ``Rendition`` instances with image files reflecting the supplied
        ``filters``, and returns them as a ``dict`` keyed by the relevant ``Filter`` instance.
        Where suitable renditions already exist in the database, they will be returned instead,
        so as not to create duplicates.

        This method is usually called by ``Image.get_renditions()``, after first
        checking that a suitable rendition does not already exist.

        Note: If using custom image models, an instance of the custom rendition
        model will be returned.
        """
        Rendition = self.get_rendition_model()

        if not filters:
            return {}

        if len(filters) == 1:
            # create_rendition() is better for single renditions, as it can
            # utilize QuerySet.get_or_create(), which has better handling of
            # race conditions
            filter = filters[0]
            return {filter: self.create_rendition(filter)}

        return_value: Dict[Filter, AbstractRendition] = {}
        filter_map: Dict[str, Filter] = {f.spec: f for f in filters}

        with self.open_file() as file:
            original_image_bytes = file.read()

        to_create = []

        def _generate_single_rendition(filter):
            # Using ContentFile here ensures we generate all renditions. Simply
            # passing self.file required several page reloads to generate all
            image_file = self.generate_rendition_file(
                filter, source=ContentFile(original_image_bytes, name=self.file.name)
            )
            to_create.append(
                Rendition(
                    image=self,
                    filter_spec=filter.spec,
                    focal_point_key=filter.get_cache_key(self),
                    file=image_file,
                )
            )

        with ThreadPoolExecutor() as executor:
            executor.map(_generate_single_rendition, filters)

        # Rendition generation can take a while. So, if other processes have created
        # identical renditions in the meantime, we should find them to avoid clashes.
        # NB: Clashes can still occur, because there is no get_or_create() equivalent
        # for multiple objects. However, this will reduce that risk considerably.
        files_for_deletion: List[File] = []

        # Assemble Q() to identify potential clashes
        lookup_q = Q()
        for rendition in to_create:
            lookup_q |= Q(
                filter_spec=rendition.filter_spec,
                focal_point_key=rendition.focal_point_key,
            )

        for existing in self.renditions.filter(lookup_q):
            # Include the existing rendition in the return value
            filter = filter_map[existing.filter_spec]
            return_value[filter] = existing

            for new in to_create:
                if (
                    new.filter_spec == existing.filter_spec
                    and new.focal_point_key == existing.focal_point_key
                ):
                    # Avoid creating the new version
                    to_create.remove(new)
                    # Mark for deletion later, so as not to hold up creation
                    files_for_deletion.append(new.file)

        for new in Rendition.objects.bulk_create(to_create, ignore_conflicts=True):
            filter = filter_map[new.filter_spec]
            return_value[filter] = new

        # Delete redundant rendition image files
        for file in files_for_deletion:
            file.delete(save=False)

        return return_value

    def generate_rendition_file(self, filter: "Filter", *, source: File = None) -> File:
        """
        Generates an in-memory image matching the supplied ``filter`` value
        and focal point value from this object, wraps it in a ``File`` object
        with a suitable filename, and returns it. The return value is used
        as the ``file`` field value for rendition objects saved by
        ``AbstractImage.create_rendition()``.

        If the contents of ``self.file`` has already been read into memory, the
        ``source`` keyword can be used to provide a reference to the in-memory
        ``File``, bypassing the need to reload the image contents from storage.

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
            generated_image = filter.run(
                self,
                SpooledTemporaryFile(max_size=settings.FILE_UPLOAD_MAX_MEMORY_SIZE),
                source=source,
            )

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


class Filter:
    """
    Represents one or more operations that can be applied to an Image to produce a rendition
    appropriate for final display on the website. Usually this would be a resize operation,
    but could potentially involve colour processing, etc.
    """

    spec_pattern = re.compile(r"^[A-Za-z0-9_\-\.]+$")
    pipe_spec_pattern = re.compile(r"^[A-Za-z0-9_\-\.\|]+$")
    expanding_spec_pattern = re.compile(r"^[A-Za-z0-9_\-\.{},]+$")
    pipe_expanding_spec_pattern = re.compile(r"^[A-Za-z0-9_\-\.{},\|]+$")

    def __init__(self, spec=None):
        # The spec pattern is operation1-var1-var2|operation2-var1
        self.spec = spec

    @classmethod
    def expand_spec(self, spec: Union["str", Iterable["str"]]) -> List["str"]:
        """
        Converts a spec pattern with brace-expansions, into a list of spec patterns.
        For example, "width-{100,200}" becomes ["width-100", "width-200"].

        Supports providing filter specs already split, or pipe or space-separated.
        """
        if isinstance(spec, str):
            separator = "|" if "|" in spec else " "
            spec = spec.split(separator)

        expanded_segments = []
        for segment in spec:
            # Check if segment has braces to expand
            if "{" in segment and "}" in segment:
                prefix, options_suffixed = segment.split("{")
                options_pattern, suffix = options_suffixed.split("}")
                options = options_pattern.split(",")
                expanded_segments.append(
                    [prefix + option + suffix for option in options]
                )
            else:
                expanded_segments.append([segment])

        # Cartesian product of all expanded segments (equivalent to nested for loops).
        combinations = itertools.product(*expanded_segments)

        return ["|".join(combination) for combination in combinations]

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

        transform = ImageTransform(size, image_is_svg=image.is_svg())
        for operation in self.transform_operations:
            transform = operation.run(transform, image)
        return transform

    @contextmanager
    def get_willow_image(self, image: AbstractImage, source: File = None):
        if source is not None:
            yield willow.Image.open(source)
        else:
            with image.get_willow_image() as willow_image:
                yield willow_image

    def run(self, image: AbstractImage, output: BytesIO, source: File = None):
        with self.get_willow_image(image, source) as willow:

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
                    "avif": "png",
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
                    quality = getattr(settings, "WAGTAILIMAGES_WEBP_QUALITY", 80)

                return willow.save_as_webp(output, quality=quality)
            elif output_format == "avif":
                # Allow changing of AVIF compression quality
                if (
                    "output-format-options" in env
                    and "lossless" in env["output-format-options"]
                ):
                    return willow.save_as_avif(output, lossless=True)
                elif "avif-quality" in env:
                    quality = env["avif-quality"]
                else:
                    quality = getattr(settings, "WAGTAILIMAGES_AVIF_QUALITY", 80)
                return willow.save_as_avif(output, quality=quality)
            elif output_format == "svg":
                return willow.save_as_svg(output)
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


class ResponsiveImage:
    """
    A custom object used to represent a collection of renditions.
    Provides a 'renditions' property to access the renditions,
    and renders to the front-end HTML.
    """

    def __init__(
        self,
        renditions: Dict[str, "AbstractRendition"],
        attrs: Optional[Dict[str, Any]] = None,
    ):
        self.renditions = list(renditions.values())
        self.attrs = attrs

    @classmethod
    def get_width_srcset(cls, renditions_list: List["AbstractRendition"]):
        if len(renditions_list) == 1:
            # No point in using width descriptors if there is a single image.
            return renditions_list[0].url

        return ", ".join([f"{r.url} {r.width}w" for r in renditions_list])

    def __html__(self):
        attrs = self.attrs or {}

        # No point in adding a srcset if there is a single image.
        if len(self.renditions) > 1:
            attrs["srcset"] = self.get_width_srcset(self.renditions)

        # The first rendition is the "base" / "fallback" image.
        return self.renditions[0].img_tag(attrs)

    def __str__(self):
        return mark_safe(self.__html__())

    def __bool__(self):
        return bool(self.renditions)

    def __eq__(self, other: "ResponsiveImage"):
        if isinstance(other, ResponsiveImage):
            return self.renditions == other.renditions and self.attrs == other.attrs
        return False


class Picture(ResponsiveImage):
    # Keep this separate from FormatOperation.supported_formats,
    # as the order our formats are defined in is essential for the picture tag.
    # Defines the order of <source> elements in the tag when format operations
    # are in use, and the priority order to identify the "fallback" format.
    # The browser will pick the first supported format in this list.
    source_format_order = ["avif", "webp", "jpeg", "png", "gif"]

    def __init__(
        self,
        renditions: Dict[str, "AbstractRendition"],
        attrs: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(renditions, attrs)
        # Store renditions grouped by format separately for access from templates.
        self.formats = self.get_formats(renditions)

    def get_formats(
        self, renditions: Dict[str, "AbstractRendition"]
    ) -> Dict[str, List["AbstractRendition"]]:
        """
        Group renditions by the format they are for, if any.
        If there is only one format, no grouping is required.
        """
        formats = defaultdict(list)
        for spec, rendition in renditions.items():
            for fmt in FormatOperation.supported_formats:
                # Identify the spec’s format (if any).
                if f"format-{fmt}" in spec:
                    formats[fmt].append(rendition)
                    break
        # Avoid the split by format if there is only one.
        if len(formats.keys()) < 2:
            return {}

        return formats

    def get_fallback_format(self):
        for fmt in reversed(self.source_format_order):
            if fmt in self.formats:
                return fmt

    def __html__(self):
        # If there aren’t multiple formats, render a vanilla img tag with srcset.
        if not self.formats:
            return mark_safe(f"<picture>{super().__html__()}</picture>")

        attrs = self.attrs or {}

        sizes = f'sizes="{attrs["sizes"]}" ' if "sizes" in attrs else ""
        fallback_format = self.get_fallback_format()
        fallback_renditions = self.formats[fallback_format]

        sources = []

        for fmt in self.source_format_order:
            if fmt != fallback_format and fmt in self.formats:
                srcset = self.get_width_srcset(self.formats[fmt])
                mime = image_format_name_to_content_type(fmt)
                sources.append(f'<source srcset="{srcset}" {sizes}type="{mime}">')

        if len(fallback_renditions) > 1:
            attrs["srcset"] = self.get_width_srcset(fallback_renditions)

        # The first rendition is the "base" / "fallback" image.
        fallback = fallback_renditions[0].img_tag(attrs)

        return mark_safe(f"<picture>{''.join(sources)}{fallback}</picture>")


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
            return f"background-position: {horz}% {vert}%;"
        else:
            return "background-position: 50% 50%;"

    def img_tag(self, extra_attributes={}):
        attrs = self.attrs_dict.copy()

        attrs.update(apps.get_app_config("wagtailimages").default_attrs)

        attrs.update(extra_attributes)

        return mark_safe(f"<img{flatatt(attrs)}>")

    def __html__(self):
        return self.img_tag()

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
