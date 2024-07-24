import functools
from ctypes import c_char_p, c_void_p

from willow.image import (
    AvifImageFile,
    BadImageOperationError,
    BMPImageFile,
    GIFImageFile,
    HeicImageFile,
    IcoImageFile,
    Image,
    JPEGImageFile,
    PNGImageFile,
    RGBAImageBuffer,
    RGBImageBuffer,
    TIFFImageFile,
    WebPImageFile,
)


class UnsupportedRotation(Exception):
    pass


def _wand_image():
    import wand.image

    return wand.image


def _wand_color():
    import wand.color

    return wand.color


def _wand_api():
    import wand.api

    return wand.api


def _wand_version():
    import wand.version

    return wand.version


class WandImage(Image):
    def __init__(self, image):
        self.image = image

    @classmethod
    def check(cls):
        _wand_image()
        _wand_color()
        _wand_api()
        _wand_version()

    def _clone(self):
        return WandImage(self.image.clone())

    @classmethod
    def is_format_supported(cls, image_format):
        return bool(_wand_version().formats(image_format))

    @Image.operation
    def get_size(self):
        return self.image.size

    @Image.operation
    def get_frame_count(self):
        return len(self.image.sequence)

    @Image.operation
    def has_alpha(self):
        return self.image.alpha_channel

    @Image.operation
    def has_animation(self):
        return self.image.animation

    @Image.operation
    def resize(self, size):
        clone = self._clone()
        clone.image.resize(size[0], size[1])
        return clone

    @Image.operation
    def crop(self, rect):
        left, top, right, bottom = rect
        width, height = self.image.size
        if (
            left >= right
            or left >= width
            or right <= 0
            or top >= bottom
            or top >= height
            or bottom <= 0
        ):
            raise BadImageOperationError(f"Invalid crop dimensions: {rect!r}")

        clone = self._clone()
        clone.image.crop(
            # clamp to image boundaries
            left=max(0, left),
            top=max(0, top),
            right=min(right, width),
            bottom=min(bottom, height),
        )
        return clone

    @Image.operation
    def rotate(self, angle):
        not_a_multiple_of_90 = angle % 90

        if not_a_multiple_of_90:
            raise UnsupportedRotation(
                "Sorry - we only support right angle rotations - i.e. multiples of 90 degrees"
            )

        clone = self.image.clone()
        clone.rotate(angle)
        return WandImage(clone)

    @Image.operation
    def set_background_color_rgb(self, color):
        if not self.has_alpha():
            # Don't change image that doesn't have an alpha channel
            return self

        # Check type of color
        if not isinstance(color, (tuple, list)) or not len(color) == 3:
            raise TypeError("the 'color' argument must be a 3-element tuple or list")

        clone = self._clone()

        # Wand will perform the compositing at the point of setting alpha_channel to 'remove'
        clone.image.background_color = _wand_color().Color(
            "rgb({}, {}, {})".format(*color)
        )
        clone.image.alpha_channel = "remove"

        if clone.image.alpha_channel:
            # ImageMagick <=6 fails to set alpha_channel to False, so do it manually
            clone.image.alpha_channel = False

        return clone

    def get_icc_profile(self):
        return self.image.profiles.get("icc")

    def get_exif_data(self):
        return self.image.profiles.get("exif")

    @Image.operation
    def save_as_jpeg(
        self,
        f,
        quality: int = 85,
        progressive: bool = False,
        apply_optimizers: bool = True,
        **kwargs,
    ):
        """
        Save the image as a JPEG file.

        :param f: the file or file-like object to save to
        :param quality: the image quality
        :param progressive: whether to save as progressive JPEG file.
        :param apply_optimizers: controls whether to run any configured optimizer libraries
        :return: JPEGImageFile
        """
        with self.image.convert("pjpeg" if progressive else "jpeg") as converted:
            converted.compression_quality = quality

            icc_profile = self.get_icc_profile()
            if icc_profile is not None:
                converted.profiles["icc"] = icc_profile

            exif_data = self.get_exif_data()
            if exif_data is not None:
                converted.profiles["exif"] = exif_data

            converted.save(file=f)

        if apply_optimizers:
            self.optimize(f, "jpeg")
        return JPEGImageFile(f)

    @Image.operation
    def save_as_png(self, f, apply_optimizers: bool = True, **kwargs):
        """
        Save the image as a PNG file.

        :param f: the file or file-like object to save to
        :param apply_optimizers: controls whether to run any configured optimizer libraries
        :return: PNGImageFile
        """
        with self.image.convert("png") as converted:
            exif_data = self.get_exif_data()
            if exif_data is not None:
                converted.profiles["exif"] = exif_data

            converted.save(file=f)

        if apply_optimizers:
            self.optimize(f, "png")
        return PNGImageFile(f)

    @Image.operation
    def save_as_gif(self, f, apply_optimizers: bool = True):
        with self.image.convert("gif") as converted:
            converted.save(file=f)

        if apply_optimizers:
            self.optimize(f, "gif")
        return GIFImageFile(f)

    @Image.operation
    def save_as_webp(
        self,
        f,
        quality: int = 80,
        lossless: bool = False,
        apply_optimizers: bool = True,
    ):
        """
        Save the image as a WEBP file.

        :param f: the file or file-like object to save to
        :param quality: the image quality
        :param lossless: whether to save as lossless WEBP file.
        :param apply_optimizers: controls whether to run any configured optimizer libraries.
            Note that when lossless=True, this will be ignored.
        :return: WebPImageFile
        """
        with self.image.convert("webp") as converted:
            if lossless:
                library = _wand_api().library
                library.MagickSetOption.argtypes = [c_void_p, c_char_p, c_char_p]
                library.MagickSetOption(
                    converted.wand,
                    b"webp:lossless",
                    b"true",
                )
            else:
                converted.compression_quality = quality

            icc_profile = self.get_icc_profile()
            if icc_profile is not None:
                converted.profiles["icc"] = icc_profile

            converted.save(file=f)

        if not lossless and apply_optimizers:
            self.optimize(f, "webp")
        return WebPImageFile(f)

    @Image.operation
    def save_as_avif(self, f, quality=80, lossless=False, apply_optimizers=True):
        with self.image.convert("avif") as converted:
            if lossless:
                converted.compression_quality = 100
                library = _wand_api().library
                library.MagickSetOption.argtypes = [c_void_p, c_char_p, c_char_p]
                library.MagickSetOption(
                    converted.wand,
                    b"heic:lossless",
                    b"true",
                )
            else:
                converted.compression_quality = quality
            converted.save(file=f)

        if not lossless and apply_optimizers:
            self.optimize(f, "avif")

        return AvifImageFile(f)

    @Image.operation
    def save_as_ico(self, f, apply_optimizers=True):
        with self.image.convert("ico") as converted:
            converted.save(file=f)

        if apply_optimizers:
            self.optimize(f, "ico")

        return IcoImageFile(f)

    @Image.operation
    def auto_orient(self):
        image = self.image

        if image.orientation not in ["top_left", "undefined"]:
            image = image.clone()
            if hasattr(image, "auto_orient"):
                # Wand 0.4.1 +
                image.auto_orient()
            else:
                orientation_ops = {
                    "top_right": [image.flop],
                    "bottom_right": [functools.partial(image.rotate, degree=180.0)],
                    "bottom_left": [image.flip],
                    "left_top": [
                        image.flip,
                        functools.partial(image.rotate, degree=90.0),
                    ],
                    "right_top": [functools.partial(image.rotate, degree=90.0)],
                    "right_bottom": [
                        image.flop,
                        functools.partial(image.rotate, degree=90.0),
                    ],
                    "left_bottom": [functools.partial(image.rotate, degree=270.0)],
                }
                fns = orientation_ops.get(image.orientation)

                if fns:
                    for fn in fns:
                        fn()

                    image.orientation = "top_left"

        return WandImage(image)

    @Image.operation
    def get_wand_image(self):
        return self.image

    @classmethod
    @Image.converter_from(JPEGImageFile, cost=150)
    @Image.converter_from(PNGImageFile, cost=150)
    @Image.converter_from(GIFImageFile, cost=150)
    @Image.converter_from(BMPImageFile, cost=150)
    @Image.converter_from(TIFFImageFile, cost=150)
    @Image.converter_from(WebPImageFile, cost=150)
    @Image.converter_from(HeicImageFile, cost=150)
    @Image.converter_from(AvifImageFile, cost=150)
    @Image.converter_from(IcoImageFile, cost=150)
    def open(cls, image_file):
        image_file.f.seek(0)
        image = _wand_image().Image(file=image_file.f)
        image.wand = _wand_api().library.MagickCoalesceImages(image.wand)

        return cls(image)

    @Image.converter_to(RGBImageBuffer)
    def to_buffer_rgb(self):
        return RGBImageBuffer(self.image.size, self.image.make_blob("RGB"))

    @Image.converter_to(RGBAImageBuffer)
    def to_buffer_rgba(self):
        return RGBImageBuffer(self.image.size, self.image.make_blob("RGBA"))


willow_image_classes = [WandImage]
