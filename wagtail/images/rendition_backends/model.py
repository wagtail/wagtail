import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Iterable, TYPE_CHECKING

from django.core.files import File
from django.core.files.base import ContentFile
from django.db.models import Q

from wagtail.images.filters import Filter


if TYPE_CHECKING:
    from wagtail.images.models import AbstractImage, AbstractRendition


logger = logging.getLogger("wagtail.images")


class RenditionModelBackendMixin:
    """
    A mixin for rendition backends that use a Django model to store and
    recall rendtions for images.
    """

    def get_rendition(
        self, image: "AbstractImage", filter: Filter | str
    ) -> "AbstractRendition":
        """
        Returns a ``Rendition`` instance with a ``file`` field value (an
        image) reflecting the supplied ``filter`` value and focal point values
        from the provided image.

        Note: If using custom image models, an instance of the custom rendition
        model will be returned.
        """
        Rendition = image.get_rendition_model()

        if isinstance(filter, str):
            filter = Filter(spec=filter)

        try:
            rendition = self._find_existing_rendition(image, filter)
        except Rendition.DoesNotExist:
            rendition = self.create_rendition(image, filter)
            # Reuse this rendition if requested again from the provided image
            self._add_to_prefetched_renditions(image, rendition)

        cache_key = Rendition.construct_cache_key(
            image, filter.get_cache_key(image), filter.spec
        )
        Rendition.cache_backend.set(cache_key, rendition)

        return rendition

    def get_renditions(
        self, image: "AbstractImage", *filter_specs: str
    ) -> dict[str, "AbstractRendition"]:
        """
        Returns a ``dict`` of ``Rendition`` instances with image files
        reflecting the supplied ``filter_specs``, keyed by the relevant
        ``filter_spec`` string.

        Note: If using custom image models, instances of the custom rendition
        model will be returned.
        """
        Rendition = image.get_rendition_model()
        filters = [Filter(spec) for spec in dict.fromkeys(filter_specs).keys()]

        # Find existing renditions where possible
        renditions = self._find_existing_renditions(image, *filters)

        # Create any renditions not found in prefetched values, cache or
        # database
        not_found = [f for f in filters if f not in renditions]
        for filter, rendition in self.create_renditions(image, *not_found).items():
            self._add_to_prefetched_renditions(image, rendition)
            renditions[filter] = rendition

        # Update the cache
        cache_additions = {
            Rendition.construct_cache_key(
                image, filter.get_cache_key(image), filter.spec
            ): rendition
            for filter, rendition in renditions.items()
            # prevent writing of cached data back to the cache
            if not getattr(rendition, "_from_cache", False)
        }
        if cache_additions:
            Rendition.cache_backend.set_many(cache_additions)

        # Return a dict in the expected format
        return {filter.spec: rendition for filter, rendition in renditions.items()}

    @staticmethod
    def _get_prefetched_renditions(
        image: "AbstractImage",
    ) -> Iterable["AbstractRendition"] | None:
        if "renditions" in getattr(image, "_prefetched_objects_cache", {}):
            return image.renditions.all()
        return getattr(image, "prefetched_renditions", None)

    @staticmethod
    def _add_to_prefetched_renditions(
        image: "AbstractImage", rendition: "AbstractRendition"
    ) -> None:
        # Reuse this rendition if requested again from the provided image
        try:
            image._prefetched_objects_cache["renditions"]._result_cache.append(
                rendition
            )
        except (AttributeError, KeyError):
            pass
        try:
            image.prefetched_renditions.append(rendition)
        except AttributeError:
            pass

    def _find_existing_rendition(
        self, image: "AbstractImage", filter: Filter
    ) -> "AbstractRendition":
        """
        Returns an existing ``Rendition`` instance with a ``file`` field value
        (an image) reflecting the supplied ``filter`` value and focal point
        values from the provided image.

        If no such rendition exists, a ``DoesNotExist`` error is raised for the
        relevant model.

        Note: If using custom image models, an instance of the custom rendition
        model will be returned.
        """
        Rendition = image.get_rendition_model()

        try:
            return self._find_existing_renditions(image, filter)[filter]
        except KeyError:
            raise Rendition.DoesNotExist

    def create_rendition(
        self, image: "AbstractImage", filter: Filter
    ) -> "AbstractRendition":
        """
        Creates and returns a ``Rendition`` instance with a ``file`` field
        value (an image) reflecting the supplied ``filter`` value and focal
        point values from the provided image.

        This method is usually called by ``Image.get_rendition()``, after first
        checking that a suitable rendition does not already exist.

        Note: If using custom image models, an instance of the custom rendition
        model will be returned.
        """
        # Because of unique constraints applied to the model, we use
        # get_or_create() to guard against race conditions
        rendition, created = image.renditions.get_or_create(
            filter_spec=filter.spec,
            focal_point_key=filter.get_cache_key(image),
            defaults={"file": self.generate_rendition_file(image, filter)},
        )
        return rendition

    def _find_existing_renditions(
        self, image: "AbstractImage", *filters: Filter
    ) -> dict[Filter, "AbstractRendition"]:
        """
        Returns a dictionary of existing ``Rendition`` instances with ``file``
        values (images) reflecting the supplied ``filters`` and the focal point
        values from the provided image.

        Filters for which an existing rendition cannot be found are ommitted
        from the return value. If none of the requested renditions have been
        created before, the return value will be an empty dict.
        """
        Rendition = image.get_rendition_model()
        filters_by_spec: dict[str, Filter] = {f.spec: f for f in filters}
        found: dict[Filter, "AbstractRendition"] = {}

        # Interrogate prefetched values first (where available)
        prefetched_renditions = self._get_prefetched_renditions(image)
        if prefetched_renditions is not None:
            # NOTE: When renditions are prefetched, it's assumed that if the
            # requested renditions exist, they will be present in the
            # prefetched value, and further cache/database lookups are avoided.

            # group renditions by the filters of interest
            potential_matches = defaultdict(list)
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
                focal_point_key = filter.get_cache_key(image)
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
                Rendition.construct_cache_key(image, filter.get_cache_key(image), spec)
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
                        focal_point_key=filter.get_cache_key(image),
                    )
                for rendition in image.renditions.filter(lookup_q):
                    filter = filters_by_spec[rendition.filter_spec]
                    found[filter] = rendition
        return found

    def create_renditions(
        self, image: "AbstractImage", *filters: Filter
    ) -> dict[Filter, "AbstractRendition"]:
        """
        Creates multiple ``Rendition`` instances with image files reflecting
        the supplied ``filters``, and returns them as a ``dict`` keyed by the
        relevant ``Filter`` instance. Where suitable renditions already exist
        in the database, they will be returned instead, so as not to create
        duplicates.

        This method is usually called by ``Image.get_renditions()``, after
        first checking that a suitable rendition does not already exist.

        Note: If using custom image models, an instance of the custom rendition
        model will be returned.
        """
        Rendition = image.get_rendition_model()

        if not filters:
            return {}

        if len(filters) == 1:
            # create_rendition() is better for single renditions, as it can
            # utilize QuerySet.get_or_create(), which has better handling of
            # race conditions
            filter = filters[0]
            return {filter: self.create_rendition(image, filter)}

        return_value: dict[Filter, "AbstractRendition"] = {}
        filter_map: dict[str, Filter] = {f.spec: f for f in filters}

        with image.open_file() as file:
            original_image_bytes = file.read()

        to_create = []

        def _generate_single_rendition(filter):
            # Using ContentFile here ensures we generate all renditions. Simply
            # passing self.file required several page reloads to generate all
            f = ContentFile(original_image_bytes, name=image.file.name)
            image_file = self.generate_rendition_file(image, filter, source=f)
            to_create.append(
                Rendition(
                    image=image,
                    filter_spec=filter.spec,
                    focal_point_key=filter.get_cache_key(image),
                    file=image_file,
                )
            )

        with ThreadPoolExecutor() as executor:
            executor.map(_generate_single_rendition, filters)

        # Rendition generation can take a while. So, if other processes have
        # created identical renditions in the meantime, we should find them to
        # avoid clashes.
        # NB: Clashes can still occur, because there is no get_or_create()
        # equivalent for multiple objects. However, this will reduce that risk
        # considerably.
        files_for_deletion: list[File] = []

        # Assemble Q() to identify potential clashes
        lookup_q = Q()
        for rendition in to_create:
            lookup_q |= Q(
                filter_spec=rendition.filter_spec,
                focal_point_key=rendition.focal_point_key,
            )

        for existing in image.renditions.filter(lookup_q):
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

    def generate_rendition_file(
        self, image: "AbstractImage", filter: Filter, *, source: File = None
    ) -> File:
        """
        Generates an in-memory image matching the supplied ``filter`` value
        and focal point value from the provided image, wraps it in a ``File``
        object with a suitable filename, and returns it. The return value is
        used as the ``file`` field value for rendition objects saved by
        ``create_rendition()`` and ``create_renditions()``.
        """
        raise NotImplementedError
