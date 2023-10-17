import hashlib

from typing import TYPE_CHECKING

from django.utils.functional import cached_property

from wagtail import hooks
from wagtail.images.exceptions import InvalidFilterSpecError
from wagtail.images.image_operations import (
    Operation,
    FilterOperation,
    ImageTransform,
    TransformOperation,
)

if TYPE_CHECKING:
    from wagtail.images.models import AbstractImage


class Filter:
    """
    Represents one or more operations that can be applied to an Image to
    produce a rendition appropriate for final display on the website. Usually
    this would be a resize operation, but could potentially involve colour
    processing, etc.
    """

    def __init__(self, spec: str = None):
        # The spec pattern is operation1-var1-var2|operation2-var1
        self.spec = spec

    @cached_property
    def operations(self) -> list[Operation]:
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
    def transform_operations(self) -> list[TransformOperation]:
        return [
            operation
            for operation in self.operations
            if isinstance(operation, TransformOperation)
        ]

    @property
    def filter_operations(self) -> list[FilterOperation]:
        return [
            operation
            for operation in self.operations
            if isinstance(operation, FilterOperation)
        ]

    def get_transform(
        self, image: "AbstractImage", size: tuple[int, int] = None
    ) -> ImageTransform:
        """
        Returns an ImageTransform with all the transforms in this filter
        applied.
        """
        if not size:
            size = (image.width, image.height)

        transform = ImageTransform(size, image_is_svg=image.is_svg())
        for operation in self.transform_operations:
            transform = operation.run(transform, image)
        return transform

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
