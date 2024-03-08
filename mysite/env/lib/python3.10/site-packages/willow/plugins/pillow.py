from io import BytesIO

try:
    from pillow_heif import AvifImagePlugin, HeifImagePlugin  # noqa: F401
except ImportError:
    pass

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


def _PIL_Image():
    import PIL.Image

    return PIL.Image


def _PIL_ImageCms():
    import PIL.ImageCms

    return PIL.ImageCms


class PillowImage(Image):
    def __init__(self, image):
        self.image = image

    @classmethod
    def check(cls):
        _PIL_Image()

    @classmethod
    def is_format_supported(cls, image_format):
        formats = _PIL_Image().registered_extensions()
        return image_format in formats.values()

    @Image.operation
    def get_size(self):
        return self.image.size

    @Image.operation
    def get_frame_count(self):
        # Animation is not supported by PIL
        return 1

    @Image.operation
    def has_alpha(self):
        img = self.image
        return img.mode in ("RGBA", "LA") or (
            img.mode == "P" and "transparency" in img.info
        )

    @Image.operation
    def has_animation(self):
        # Animation is not supported by PIL
        return False

    @Image.operation
    def resize(self, size):
        # Convert 1 and P images to RGB to improve resize quality
        # (palleted images don't get antialiased or filtered when minified)
        if self.image.mode in ["1", "P"]:
            if self.has_alpha():
                image = self.image.convert("RGBA")
            else:
                image = self.image.convert("RGB")
        else:
            image = self.image

        # LANCZOS was previously known as ANTIALIAS
        return PillowImage(image.resize(size, _PIL_Image().Resampling.LANCZOS))

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

        # clamp to image boundaries
        clamped_rect = (
            max(0, left),
            max(0, top),
            min(right, width),
            min(bottom, height),
        )

        return PillowImage(self.image.crop(clamped_rect))

    @Image.operation
    def rotate(self, angle):
        """
        Accept a multiple of 90 to pass to the underlying Pillow function
        to rotate the image.
        """

        Image = _PIL_Image()
        ORIENTATION_TO_TRANSPOSE = {
            90: Image.Transpose.ROTATE_90,
            180: Image.Transpose.ROTATE_180,
            270: Image.Transpose.ROTATE_270,
        }

        modulo_angle = angle % 360

        # is we're rotating a multiple of 360, it's the same as a no-op
        if not modulo_angle:
            return self

        transpose_code = ORIENTATION_TO_TRANSPOSE.get(modulo_angle)

        if not transpose_code:
            raise UnsupportedRotation(
                "Sorry - we only support right angle rotations - i.e. multiples of 90 degrees"
            )

        # We call "transpose", as it rotates the image,
        # updating the height and width, whereas using 'rotate'
        # only changes the contents of the image.
        rotated = self.image.transpose(transpose_code)

        return PillowImage(rotated)

    @Image.operation
    def set_background_color_rgb(self, color):
        if not self.has_alpha():
            # Don't change image that doesn't have an alpha channel
            return self

        # Check type of color
        if not isinstance(color, (tuple, list)) or not len(color) == 3:
            raise TypeError("the 'color' argument must be a 3-element tuple or list")

        # Convert non-RGB colour formats to RGB
        # As we only allow the background color to be passed in as RGB, we
        # convert the format of the original image to match.
        image = self.image.convert("RGBA")

        # Generate a new image with background colour and draw existing image on top of it
        # The new image must temporarily be RGBA in order for alpha_composite to work
        new_image = _PIL_Image().new(
            "RGBA", self.image.size, (color[0], color[1], color[2], 255)
        )

        if hasattr(new_image, "alpha_composite"):
            new_image.alpha_composite(image)
        else:
            # Pillow < 4.2.0 fallback
            # This method may be slower as the operation generates a new image
            new_image = _PIL_Image().alpha_composite(new_image, image)

        return PillowImage(new_image.convert("RGB"))

    def get_icc_profile(self):
        return self.image.info.get("icc_profile")

    def get_exif_data(self):
        return self.image.info.get("exif")

    @Image.operation
    def transform_colorspace_to_srgb(self, rendering_intent=0):
        """
        Transforms the color of the image to fit inside sRGB color gamut using the
        embedded ICC profile. The resulting image will always be in RGB(A) mode
        and will have a small generic sRGB ICC profile embedded.

        If the image does not have an ICC profile this operation is a no-op.
        Images without a profile are commonly assumed to be in sRGB color space
        already.

        :param rendering_intent: Controls how out-of-gamut colors and handled.
        Defaults to 0 (perceptual) because this is what Pillow defaults to.
        :return: PillowImage in RGB mode
        :raises: PIL.ImageCms.PyCMSError

        Further reading:
            * https://pillow.readthedocs.io/en/stable/reference/ImageCms.html#PIL.ImageCms.profileToProfile
            * https://www.permajet.com/blog/rendering-intents-explained/
        """
        icc_profile = self.get_icc_profile()

        # Can't transform if there is no profile, no-op
        if icc_profile is None:
            return self

        ImageCms = _PIL_ImageCms()
        # ImageCmsProfile expects profile data to be file-like, give it BytesIO that quacks like a file 🦆
        icc_profile = ImageCms.ImageCmsProfile(BytesIO(icc_profile))

        # Output mode should always be RGB, unless the image has an alpha channel.
        output_mode = "RGBA" if self.has_alpha() else "RGB"

        # Attempt to convert from the embedded profile of the image to a generic sRGB one
        image = ImageCms.profileToProfile(
            self.image,
            icc_profile,
            ImageCms.createProfile("sRGB"),
            renderingIntent=rendering_intent,
            outputMode=output_mode,
        )
        return PillowImage(image)

    @Image.operation
    def save_as_jpeg(
        self,
        f,
        quality: int = 85,
        optimize: bool = False,
        progressive: bool = False,
        apply_optimizers: bool = True,
    ):
        """
        Save the image as a JPEG file.

        :param f: the file or file-like object to save to
        :param quality: the image quality
        :param optimize: Whether Pillow should optimize the file. When True, Pillow will
            attempt to compress the palette by eliminating unused colors.
        :param progressive: whether to save as progressive JPEG file.
        :param apply_optimizers: controls whether to run any configured optimizer libraries
        :return: JPEGImageFile
        """
        if self.image.mode in ["1", "P"]:
            image = self.image.convert("RGB")
        else:
            image = self.image

        kwargs = {"quality": quality}
        if optimize:
            kwargs["optimize"] = True
        if progressive:
            kwargs["progressive"] = True

        icc_profile = self.get_icc_profile()
        if icc_profile is not None:
            kwargs["icc_profile"] = icc_profile

        exif_data = self.get_exif_data()
        if exif_data is not None:
            kwargs["exif"] = exif_data

        image.save(f, "JPEG", **kwargs)
        if apply_optimizers:
            self.optimize(f, "jpeg")
        return JPEGImageFile(f)

    @Image.operation
    def save_as_png(self, f, optimize: bool = False, apply_optimizers: bool = True):
        """
        Save the image as a PNG file.

        :param f: the file or file-like object to save to
        :param optimize: Whether Pillow should optimize the file. When True, Pillow will
            attempt to compress the palette by eliminating unused colors.
        :param apply_optimizers: controls whether to run any configured optimizer libraries
        :return: PNGImageFile
        """

        kwargs = {}
        image = self.image
        icc_profile = self.get_icc_profile()
        if icc_profile is not None:
            # If the image is in CMYK mode *and* has an ICC profile, we need to be more diligent
            # about how we handle the color conversion to RGB. We don't want to retain
            # the color profile as-is because it is not meant for RGB images and
            # will result in inaccurate colors. The transformation to sRGB should result
            # in a more accurate representation of the original image, though
            # it will likely not be perfect.
            if self.image.mode == "CMYK":
                pillow_image = self.transform_colorspace_to_srgb()
                image = pillow_image.image
                kwargs["icc_profile"] = pillow_image.get_icc_profile()
            else:
                kwargs["icc_profile"] = icc_profile

        elif image.mode == "CMYK":
            image = image.convert("RGB")

        # Pillow only checks presence of optimize kwarg, not its value
        if optimize:
            kwargs["optimize"] = True

        exif_data = self.get_exif_data()
        if exif_data is not None:
            kwargs["exif"] = exif_data

        image.save(f, "PNG", **kwargs)
        if apply_optimizers:
            self.optimize(f, "png")
        return PNGImageFile(f)

    @Image.operation
    def save_as_gif(self, f, apply_optimizers: bool = True):
        image = self.image

        # All gif files use either the L or P mode but we sometimes convert them
        # to RGB/RGBA to improve the quality of resizing. We must make sure that
        # they are converted back before saving.
        if image.mode not in ["L", "P"]:
            image = image.convert("P", palette=_PIL_Image().Palette.ADAPTIVE)

        kwargs = {}
        if "transparency" in image.info:
            kwargs["transparency"] = image.info["transparency"]

        image.save(f, "GIF", **kwargs)
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

        kwargs = {"quality": quality, "lossless": lossless}

        image = self.image
        icc_profile = self.get_icc_profile()
        if icc_profile is not None:
            # If the image is in CMYK mode *and* has an ICC profile, we need to be more diligent
            # about how we handle the color space. WEBP will encode as RGB so we need to do extra
            # work to ensure the colors are as accurate as possible. We don't want to retain
            # the color profile as-is because it is not meant for RGB images and
            # will result in inaccurate colors. The transformation to sRGB should result
            # in a more accurate representation of the original image, though
            # it will likely not be perfect.
            if image.mode == "CMYK":
                pillow_image = self.transform_colorspace_to_srgb()
                image = pillow_image.image
                kwargs["icc_profile"] = pillow_image.get_icc_profile()
            else:
                kwargs["icc_profile"] = icc_profile

        image.save(f, "WEBP", **kwargs)
        if apply_optimizers and not lossless:
            self.optimize(f, "webp")
        return WebPImageFile(f)

    @Image.operation
    def save_as_heic(
        self,
        f,
        quality: int = 80,
        lossless: bool = False,
        apply_optimizers: bool = True,
    ):
        """
        Save the image as a HEIC file.

        :param f: the file or file-like object to save to
        :param quality: the image quality
        :param lossless: whether to save as lossless HEIC/HEIF file.
        :param apply_optimizers: controls whether to run any configured optimizer libraries.
            Note that when lossless=True, this will be ignored.
        :return: HeicImageFile
        """
        kwargs = {"quality": quality}
        if lossless:
            kwargs = {"quality": -1, "chroma": 444}

        image = self.image
        icc_profile = self.get_icc_profile()
        if icc_profile is not None:
            # If the image is in CMYK mode *and* has an ICC profile, we need to be more diligent
            # about how we handle the color space. HEIC will encode as RGB so we need to do extra
            # work to ensure the colors are as accurate as possible. We don't want to retain
            # the color profile as-is because it is not meant for RGB images and
            # will result in inaccurate colors. The transformation to sRGB should result
            # in a more accurate representation of the original image, though
            # it will likely not be perfect.
            if image.mode == "CMYK":
                pillow_image = self.transform_colorspace_to_srgb()
                image = pillow_image.image
                kwargs["icc_profile"] = pillow_image.get_icc_profile()
            else:
                kwargs["icc_profile"] = icc_profile

        image.save(f, "HEIF", **kwargs)

        if not lossless and apply_optimizers:
            self.optimize(f, "heic")

        return HeicImageFile(f)

    @Image.operation
    def save_as_avif(self, f, quality=80, lossless=False, apply_optimizers=True):
        kwargs = {"quality": quality}
        if lossless:
            kwargs = {"quality": -1, "chroma": 444}

        image = self.image
        icc_profile = self.get_icc_profile()
        if icc_profile is not None:
            # If the image is in CMYK mode *and* has an ICC profile, we need to be more diligent
            # about how we handle the color space. AVIF will encode as RGB so we need to do extra
            # work to ensure the colors are as accurate as possible. We don't want to retain
            # the color profile as-is because it is not meant for RGB images and
            # will result in inaccurate colors. The transformation to sRGB should result
            # in a more accurate representation of the original image, though
            # it will likely not be perfect.
            if image.mode == "CMYK":
                pillow_image = self.transform_colorspace_to_srgb()
                image = pillow_image.image
                kwargs["icc_profile"] = pillow_image.get_icc_profile()
            else:
                kwargs["icc_profile"] = icc_profile

        image.save(f, "AVIF", **kwargs)

        if not lossless and apply_optimizers:
            self.optimize(f, "heic")

        return AvifImageFile(f)

    @Image.operation
    def save_as_ico(self, f, apply_optimizers=True):
        self.image.save(f, "ICO")

        if apply_optimizers:
            self.optimize(f, "ico")

        return IcoImageFile(f)

    @Image.operation
    def auto_orient(self):
        # JPEG files can be orientated using an EXIF tag.
        # Make sure this orientation is applied to the data
        from PIL import ImageOps

        image = ImageOps.exif_transpose(self.image)

        return PillowImage(image)

    @Image.operation
    def get_pillow_image(self):
        return self.image

    @classmethod
    @Image.converter_from(JPEGImageFile)
    @Image.converter_from(PNGImageFile)
    @Image.converter_from(GIFImageFile, cost=200)
    @Image.converter_from(BMPImageFile)
    @Image.converter_from(TIFFImageFile)
    @Image.converter_from(WebPImageFile)
    @Image.converter_from(HeicImageFile)
    @Image.converter_from(AvifImageFile)
    @Image.converter_from(IcoImageFile)
    def open(cls, image_file):
        image_file.f.seek(0)
        image = _PIL_Image().open(image_file.f)
        image.load()

        return cls(image)

    @Image.converter_to(RGBImageBuffer)
    def to_buffer_rgb(self):
        image = self.image

        if image.mode != "RGB":
            image = image.convert("RGB")

        return RGBImageBuffer(image.size, image.tobytes())

    @Image.converter_to(RGBAImageBuffer)
    def to_buffer_rgba(self):
        image = self.image

        if image.mode != "RGBA":
            image = image.convert("RGBA")

        return RGBAImageBuffer(image.size, image.tobytes())


willow_image_classes = [PillowImage]
