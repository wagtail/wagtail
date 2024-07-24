import os
import re
from io import BytesIO
from tempfile import NamedTemporaryFile, SpooledTemporaryFile
from typing import Optional

import filetype
from defusedxml import ElementTree
from filetype.types import image as image_types

from .registry import registry


class UnrecognisedImageFormatError(IOError):
    pass


class BadImageOperationError(ValueError):
    """
    Raised when the arguments to an image operation are invalid,
    e.g. a crop where the left coordinate is greater than the right coordinate
    """

    pass


class Image:
    @classmethod
    def check(cls):
        pass

    @staticmethod
    def operation(func):
        func._willow_operation = True
        return func

    @staticmethod
    def converter_to(to_class, cost=None):
        def wrapper(func):
            func._willow_converter_to = (to_class, cost)
            return func

        return wrapper

    @staticmethod
    def converter_from(from_class, cost=None):
        def wrapper(func):
            if not hasattr(func, "_willow_converter_from"):
                func._willow_converter_from = []

            if isinstance(from_class, list):
                func._willow_converter_from.extend([(sc, cost) for sc in from_class])
            else:
                func._willow_converter_from.append((from_class, cost))

            return func

        return wrapper

    def __getattr__(self, attr):
        try:
            operation, _, conversion_path, _ = registry.find_operation(type(self), attr)
        except LookupError:
            # Operation doesn't exist
            raise AttributeError(
                f"{self.__class__.__name__!r} object has no attribute {attr!r}"
            )

        def wrapper(*args, **kwargs):
            image = self

            for converter, _ in conversion_path:
                image = converter(image)

            return operation(image, *args, **kwargs)

        return wrapper

    # A couple of helpful methods

    @classmethod
    def open(cls, f):
        # Detect image format
        image_format = filetype.guess_extension(f)

        if image_format is None and cls.maybe_xml(f):
            image_format = "svg"

        # Find initial class
        initial_class = INITIAL_IMAGE_CLASSES.get(image_format)
        if not initial_class:
            if image_format:
                raise UnrecognisedImageFormatError(
                    f"Cannot load {image_format} images ({INITIAL_IMAGE_CLASSES!r})"
                )
            else:
                raise UnrecognisedImageFormatError("Unknown image format")

        return initial_class(f)

    @classmethod
    def maybe_xml(cls, f):
        # Check if it looks like an XML doc, it will be validated
        # properly when we parse it in SvgImageFile
        f.seek(0)
        pattern = re.compile(rb"^\s*<")
        for line in f:
            if pattern.match(line):
                f.seek(0)
                return True
        f.seek(0)
        return False

    def save(
        self, image_format, output, apply_optimizers=True
    ) -> Optional["ImageFile"]:
        # Get operation name
        if image_format not in [
            "jpeg",
            "png",
            "gif",
            "bmp",
            "tiff",
            "webp",
            "svg",
            "heic",
            "avif",
            "ico",
        ]:
            raise ValueError("Unknown image format: %s" % image_format)

        operation_name = "save_as_" + image_format
        return getattr(self, operation_name)(output, apply_optimizers=apply_optimizers)

    def optimize(self, image_file, image_format: str):
        """
        Runs all available optimizers for the given image format on the given image file.

        If the passed image file is a SpooledTemporaryFile or just bytes, we are converting it to a
        NamedTemporaryFile to guarantee we can access the file so the optimizers to work on it.
        If we get a string, we assume it's a path to a file, and will attempt to load it from
        the file system.
        """
        optimizers = registry.get_optimizers_for_format(image_format)
        if not optimizers:
            return

        named_file_created = False
        try:
            if isinstance(image_file, SpooledTemporaryFile):
                file = image_file._file
                with NamedTemporaryFile(delete=False) as named_file:
                    if hasattr(file, "getvalue"):  # e.g. BytesIO
                        named_file.write(file.getvalue())
                    else:  # e.g. BufferedRandom
                        file.seek(0)
                        named_file.write(file.read())
                    file_path = named_file.name
                named_file_created = True
            elif isinstance(image_file, BytesIO):
                with NamedTemporaryFile(delete=False) as named_file:
                    named_file.write(image_file.getvalue())
                    file_path = named_file.name
                named_file_created = True
            elif hasattr(image_file, "name"):
                file_path = image_file.name
            elif isinstance(image_file, str):
                file_path = image_file
            elif isinstance(image_file, bytes):
                with NamedTemporaryFile(delete=False) as named_file:
                    named_file.write(image_file)
                    file_path = named_file.name
                    named_file_created = True

            for optimizer in optimizers:
                optimizer.process(file_path)

            if hasattr(image_file, "seek"):
                # rewind and replace the image file with the optimized version
                image_file.seek(0)
                with open(file_path, "rb") as f:
                    image_file.write(f.read())

                if hasattr(image_file, "truncate"):
                    image_file.truncate()  # bring the file size down to the actual image size
        finally:
            if named_file_created:
                os.unlink(file_path)


class ImageBuffer(Image):
    def __init__(self, size, data):
        self.size = size
        self.data = data

    @Image.operation
    def get_size(self):
        return self.size


class RGBImageBuffer(ImageBuffer):
    mode = "RGB"

    @Image.operation
    def has_alpha(self):
        return False

    @Image.operation
    def has_animation(self):
        return False


class RGBAImageBuffer(ImageBuffer):
    mode = "RGBA"

    @Image.operation
    def has_alpha(self):
        return True

    @Image.operation
    def has_animation(self):
        return False


class ImageFile(Image):
    @property
    def format_name(self):
        """
        Willow internal name for the image format
        ImageFile implementations MUST override this.
        """
        raise NotImplementedError

    @property
    def mime_type(self):
        """
        Returns the MIME type of the image file
        ImageFile implementations MUST override this.
        """
        raise NotImplementedError

    def __init__(self, f):
        self.f = f


class JPEGImageFile(ImageFile):
    @property
    def format_name(self):
        return "jpeg"

    @property
    def mime_type(self):
        return "image/jpeg"


class PNGImageFile(ImageFile):
    @property
    def format_name(self):
        return "png"

    @property
    def mime_type(self):
        return "image/png"


class GIFImageFile(ImageFile):
    @property
    def format_name(self):
        return "gif"

    @property
    def mime_type(self):
        return "image/gif"


class BMPImageFile(ImageFile):
    @property
    def format_name(self):
        return "bmp"

    @property
    def mime_type(self):
        return "image/bmp"


class TIFFImageFile(ImageFile):
    @property
    def format_name(self):
        return "tiff"

    @property
    def mime_type(self):
        return "image/tiff"


class WebPImageFile(ImageFile):
    @property
    def format_name(self):
        return "webp"

    @property
    def mime_type(self):
        return "image/webp"


class SvgImageFile(ImageFile):
    format_name = "svg"
    mime_type = "image/svg+xml"

    def __init__(self, f, dom=None):
        if dom is None:
            f.seek(0)
            # Will raise xml.etree.ElementTree.ParseError if invalid
            self.dom = ElementTree.parse(f)
            f.seek(0)
        else:
            self.dom = dom
        super().__init__(f)


class HeicImageFile(ImageFile):
    @property
    def format_name(self):
        return "heic"

    @property
    def mime_type(self):
        return "image/heic"


class AvifImageFile(ImageFile):
    @property
    def format_name(self):
        return "avif"

    @property
    def mime_type(self):
        return "image/avif"


class IcoImageFile(ImageFile):
    format_name = "ico"
    mime_type = "image/x-icon"


INITIAL_IMAGE_CLASSES = {
    # A mapping of image formats to their initial class
    image_types.Jpeg().extension: JPEGImageFile,
    image_types.Png().extension: PNGImageFile,
    image_types.Gif().extension: GIFImageFile,
    image_types.Bmp().extension: BMPImageFile,
    image_types.Tiff().extension: TIFFImageFile,
    image_types.Webp().extension: WebPImageFile,
    "svg": SvgImageFile,
    image_types.Heic().extension: HeicImageFile,
    image_types.Avif().extension: AvifImageFile,
    image_types.Ico().extension: IcoImageFile,
}
