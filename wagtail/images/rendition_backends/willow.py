import logging
import os.path
import time
from typing import Optional

from contextlib import contextmanager
from io import BytesIO
from tempfile import SpooledTemporaryFile
from typing import TYPE_CHECKING

import willow
from django.conf import settings
from django.core.files import File

from wagtail.images.exceptions import UnknownOutputImageFormatError

from wagtail.images.filter import Filter

if TYPE_CHECKING:
    from wagtail.images.models import AbstractImage

logger = logging.getLogger("wagtail.images")


IMAGE_FORMAT_EXTENSIONS = {
    "avif": ".avif",
    "jpeg": ".jpg",
    "png": ".png",
    "gif": ".gif",
    "webp": ".webp",
    "svg": ".svg",
}


class WillowRenditionBackendMixin:
    """
    A mixin for rendition backends that use Willow to generate new versions
    of images from the original source image.
    """

    @contextmanager
    def get_willow_image(self, image: "AbstractImage", source: File = None):
        if source is not None:
            yield willow.Image.open(source)
        else:
            with image.get_willow_image() as willow_image:
                yield willow_image

    def generate_rendition_file(
        self, image: "AbstractImage", filter: Filter, *, source: File = None
    ) -> File:
        """
        Generates an in-memory image matching the supplied ``filter`` value
        and focal point value from the provided image, wraps it in a ``File``
        object with a suitable filename, and returns it. The return value is
        used as the ``file`` field value for rendition objects saved by
        ``"AbstractImage".create_rendition()``.

        If the contents of ``self.file`` has already been read into memory, the
        ``source`` keyword can be used to provide a reference to the in-memory
        ``File``, bypassing the need to reload the image contents from storage.
        """
        cache_key = filter.get_cache_key(image)

        logger.debug(
            "Generating '%s' rendition for image %d",
            filter.spec,
            image.pk,
        )

        start_time = time.time()

        try:
            generated_image = self._generate_file(
                image,
                filter,
                SpooledTemporaryFile(max_size=settings.FILE_UPLOAD_MAX_MEMORY_SIZE),
                source=source,
            )

            logger.debug(
                "Generated '%s' rendition for image %d in %.1fms",
                filter.spec,
                image.pk,
                (time.time() - start_time) * 1000,
            )
        except:  # noqa:B901,E722
            logger.debug(
                "Failed to generate '%s' rendition for image %d",
                filter.spec,
                image.pk,
            )
            raise

        filename = self._generate_filename(
            image=image,
            filter=filter,
            target_extension=IMAGE_FORMAT_EXTENSIONS[generated_image.format_name],
            cache_key=cache_key,
        )
        return File(generated_image.f, name=filename)

    def _generate_file(
        self,
        image: "AbstractImage",
        filter: Filter,
        output: BytesIO,
        source: File = None,
    ):
        with self.get_willow_image(image, source) as willow:
            original_format = willow.format_name

            # Fix orientation of image
            willow = willow.auto_orient()

            # Transform the image
            transform = filter.get_transform(
                image, (willow.image.width, willow.image.height)
            )
            willow = willow.crop(transform.get_rect().round())
            willow = willow.resize(transform.size)

            # Apply filters
            env = {
                "original-format": original_format,
            }
            for operation in filter.filter_operations:
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
            elif output_format == "svg":
                return willow.save_as_svg(output)
            raise UnknownOutputImageFormatError(
                f"Unknown output image format '{output_format}'"
            )

    def _generate_filename(
        self,
        image: AbstractImage,
        filter: filter,
        target_extension: Optional[str] = None,
        cache_key: Optional[str] = None,
    ) -> str:
        filename, original_extension = os.path.splitext(
            os.path.basename(image.file.name)
        )
        extension = (
            filter.spec.replace("|", ".") + target_extension or original_extension
        )
        if cache_key:
            extension = cache_key + "." + extension

        # Truncate filename to prevent it going over 60 chars
        filename = filename[: (59 - len(extension))]
        return filename + "." + extension
