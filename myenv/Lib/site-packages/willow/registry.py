from collections import defaultdict
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .optimizers import OptimizerBase


class UnrecognisedOperationError(LookupError):
    """
    Raised when the operation isn't in any of the known image classes.
    """

    pass


class UnavailableOperationError(LookupError):
    """
    Raised when all the image classes the operation exists in are not available.
    (most likely due to a missing image library.)
    """

    pass


class UnroutableOperationError(LookupError):
    """
    Raised when there is no way to convert the image into an image class that
    supports the operation.
    """

    pass


class WillowRegistry:
    def __init__(self):
        self._registered_image_classes = set()
        self._unavailable_image_classes = {}
        self._registered_operations = defaultdict(dict)
        self._registered_converters = {}
        self._registered_converter_costs = {}
        self._registered_optimizers: List["OptimizerBase"] = []

    def register_operation(self, image_class, operation_name, func):
        self._registered_operations[image_class][operation_name] = func

    def register_converter(self, from_image_class, to_image_class, func, cost=None):
        self._registered_converters[from_image_class, to_image_class] = func

        if cost is not None:
            self._registered_converter_costs[from_image_class, to_image_class] = cost

    def register_image_class(self, image_class):
        self._registered_image_classes.add(image_class)

        # Check the image class
        try:
            image_class.check()
        except Exception as e:  # noqa: BLE001
            self._unavailable_image_classes[image_class] = e

        # Find and register operations/converters
        for attr in dir(image_class):
            val = getattr(image_class, attr)
            if hasattr(val, "_willow_operation"):
                self.register_operation(image_class, val.__name__, val)
            elif hasattr(val, "_willow_converter_to"):
                self.register_converter(
                    image_class,
                    val._willow_converter_to[0],
                    val,
                    cost=val._willow_converter_to[1],
                )
            elif hasattr(val, "_willow_converter_from"):
                for converter_from, cost in val._willow_converter_from:
                    self.register_converter(converter_from, image_class, val, cost=cost)

    def register_plugin(self, plugin):
        image_classes = getattr(plugin, "willow_image_classes", [])
        operations = getattr(plugin, "willow_operations", [])
        converters = getattr(plugin, "willow_converters", [])

        for image_class in image_classes:
            self.register_image_class(image_class)

        for operation in operations:
            self.register_operation(operation[0], operation[1], operation[2])

        for converter in converters:
            self.register_converter(converter[0], converter[1], converter[2])

    def register_optimizer(self, optimizer_class: "OptimizerBase"):
        """Registers an optimizer class."""
        try:
            # try to check Django settings, if used in that context
            from django.conf import settings

            enabled_optimizers = getattr(settings, "WILLOW_OPTIMIZERS", False)
        except ImportError:
            # fall back to env vars.
            import os

            enabled_optimizers = os.environ.get("WILLOW_OPTIMIZERS", False)

        if not enabled_optimizers:
            # WILLOW_OPTIMIZERS is either not set, or is set to a false-y value, so skip registration
            return

        if isinstance(enabled_optimizers, str):
            if enabled_optimizers.lower() == "false":
                return
            elif enabled_optimizers.lower() == "true":
                enabled_optimizers = True
            else:
                enabled_optimizers = enabled_optimizers.split(",")

        if enabled_optimizers is True:
            add_optimizer = True
        else:
            add_optimizer = optimizer_class.library_name in enabled_optimizers

        if (
            add_optimizer
            and optimizer_class.check_library()
            and optimizer_class not in self._registered_optimizers
        ):
            self._registered_optimizers.append(optimizer_class)

    def get_operation(self, image_class, operation_name):
        return self._registered_operations[image_class][operation_name]

    def operation_exists(self, operation_name):
        for image_class_operations in self._registered_operations.values():
            if operation_name in image_class_operations:
                return True

        return False

    def get_converter(self, from_image_class, to_image_class):
        return self._registered_converters[from_image_class, to_image_class]

    def get_converter_cost(self, from_image_class, to_image_class):
        return self._registered_converter_costs.get(
            (from_image_class, to_image_class), 100
        )

    def get_image_classes(self, with_operation=None, available=None):
        image_classes = self._registered_image_classes.copy()

        if with_operation:
            image_classes = set(
                filter(
                    lambda image_class: image_class in self._registered_operations
                    and with_operation in self._registered_operations[image_class],
                    image_classes,
                )
            )

            if not image_classes:
                raise UnrecognisedOperationError(
                    f"Could not find image class with the '{with_operation}' operation"
                )

        if available:
            # Remove unavailable image classes
            available_image_classes = image_classes - set(
                self._unavailable_image_classes.keys()
            )

            # Raise error if all image classes failed the check
            if not available_image_classes:
                raise UnavailableOperationError(
                    "\n".join(
                        [
                            "The operation '{}' is available in the following image classes but they all raised errors:".format(
                                with_operation
                            )
                        ]
                        + [
                            "{image_class_name}: {error_message}".format(
                                image_class_name=image_class.__name__,
                                error_message=str(
                                    self._unavailable_image_classes.get(
                                        image_class, "Unknown error"
                                    )
                                ),
                            )
                            for image_class in image_classes
                        ]
                    )
                )

            return available_image_classes
        else:
            return image_classes

    def get_optimizers_for_format(self, image_format: str) -> List["OptimizerBase"]:
        optimizers = []
        for optimizer in self._registered_optimizers:
            if optimizer.applies_to(image_format):
                optimizers.append(optimizer)

        return optimizers

    # Routing

    # In some cases, it may not be possible to convert directly between two
    # image classes, so we need to use one or more intermediate classes in order
    # to get to where we want to be.

    # For example, the OpenCV plugin doesn't load JPEG images, so the image
    # needs to be loaded into either Pillow or Wand first and converted to
    # OpenCV.

    # Using a routing algorithm, we're able to work out the best path to take.

    def get_converters_from(self, from_image_class):
        """
        Yields a tuple for each image class that can be directly converted
        from the specified image classes. The tuple contains the converter
        function and the image class.

        For example:

        >>> list(registry.get_converters_from(Pillow))
        [
            (convert_pillow_to_wand, Wand),
            (save_as_jpeg, JpegFile)
            ...
        ]
        """
        for (c_from, c_to), converter in self._registered_converters.items():
            if c_from is from_image_class:
                yield converter, c_to

    def find_all_paths(self, start, end, path=[], seen_classes=set()):
        """
        Returns all paths between two image classes.

        Each path is a list of tuples representing the steps to take in order to
        convert to the new class. Each tuple contains two items: The converter
        function to call and the class that step converts to.

        The order of the paths returned is undefined.

        For example:

        >>> registry.find_all_paths(JpegFile, OpenCV)
        [
            [
                (load_jpeg_into_pillow, Pillow),
                (convert_pillow_to_opencv, OpenCV)
            ],
            [
                (load_jpeg_into_wand, Wand),
                (convert_wand_to_opencv, OpenCV)
            ]
        ]
        """
        # Implementation based on https://www.python.org/doc/essays/graphs/
        if start == end:
            return [path]

        if start in seen_classes:
            return []

        if (
            start not in self._registered_image_classes
            or start in self._unavailable_image_classes
        ):
            return []

        paths = []
        for converter, next_class in self.get_converters_from(start):
            if next_class not in path:
                newpaths = self.find_all_paths(
                    next_class,
                    end,
                    path + [(converter, next_class)],
                    seen_classes.union({start}),
                )

                paths.extend(newpaths)

        return paths

    def get_path_cost(self, start, path):
        """
        Costs up a path and returns the cost as an integer.
        """
        last_class = start
        total_cost = 0

        for converter, next_class in path:
            total_cost += self.get_converter_cost(last_class, next_class)
            last_class = next_class

        return total_cost

    def find_shortest_path(self, start, end):
        """
        Finds the shortest path between two image classes.

        This is similar to the find_all_paths function, except it only returns
        the path with the lowest cost.
        """
        current_path = None
        current_cost = None

        for path in self.find_all_paths(start, end):
            cost = self.get_path_cost(start, path)

            if current_cost is None or cost < current_cost:
                current_cost = cost
                current_path = path

        return current_path, current_cost

    def find_closest_image_class(self, start, image_classes):
        """
        Finds which of the specified image classes is the closest, based on the
        sum of the costs for the conversions needed to convert the image into it.
        """
        current_class = None
        current_path = None
        current_cost = None

        for image_class in image_classes:
            path, cost = self.find_shortest_path(start, image_class)

            if cost is None:
                # no path found, e.g. from BMP to SVG
                continue

            if current_cost is None or cost < current_cost:
                current_class = image_class
                current_cost = cost
                current_path = path

        return current_class, current_path, current_cost

    def find_operation(self, from_class, operation_name):
        """
        Finds an operation that can be used by an image in the specified from_class.

        This function returns four values:
         - The operation function
         - The class which the operation is implemented on
         - A path to convert the image into the correct class for the operation
         - The total cost of all the conversions

        The path (third value) is a list of two-element tuple. Each tuple contains
        a function to call and a reference to the class that step converts to. See
        below for an example.

        How it works:

        If the specified operation_name is implemented for from_class, that is returned
        with an empty conversion path.

        If the specified operation_name is implemented on another class (but not from_class)
        that operation is returned with the conversion path to that new class.

        If it's implemented on multiple image classes, the closest one is chosen (based
        on the sum of the costs of each conversion step).

        If the operation_name is not implemented anywhere, there is no route to
        any image class that implements it or all the image classes that implement
        it are unavailable, a LookupError will be raised.

        Basic example:

            >>> func, cls, path, cost = registry.find_operation(JPEGImageFile, 'resize')
            >>> func
            PillowImage.resize
            >>> cls
            PillowImage
            >>> path
            [
                (PillowImage.open, PillowImage)
            ]
            >>> cost
            100

        To run the found operation on an image,  run each conversion function on that
        image then run the operation function:

            >>> image = Image.open(...)
            >>> func, cls, path, cost = registry.find_operation(type(image), operation_name)
            >>> for converter, new_class in path:
            ...    image = converter(image)
            ...
            >>> func(image, *args, **kwargs)
        """
        try:
            # Firstly, we check if the operation is implemented on from_class
            func = self.get_operation(from_class, operation_name)
            cls = from_class
            path = []
            cost = 0
        except LookupError:
            # Not implemented on the current class. Find the closest, available,
            # routable class that has it instead
            image_classes = self.get_image_classes(
                with_operation=operation_name, available=True
            )

            # Choose an image class
            # image_classes will always have a value here as get_image_classes raises
            # LookupError if there are no image classes available.
            cls, path, cost = self.find_closest_image_class(from_class, image_classes)

            if path is None:
                raise UnroutableOperationError(
                    "The operation '{}' is available in the image class '{}'"
                    " but it can't be converted to from '{}'".format(
                        operation_name,
                        ", ".join(
                            image_class.__name__ for image_class in image_classes
                        ),
                        from_class.__name__,
                    )
                )

            # Get the operation function
            func = self.get_operation(cls, operation_name)

        return func, cls, path, cost


registry = WillowRegistry()
