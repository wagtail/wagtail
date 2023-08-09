import os
from functools import lru_cache

from django.core.checks import Warning, register
from willow.image import Image


@lru_cache
def has_jpeg_support():
    wagtail_jpg = os.path.join(os.path.dirname(__file__), "check_files", "wagtail.jpg")
    succeeded = True

    with open(wagtail_jpg, "rb") as f:
        try:
            Image.open(f)
        except OSError:
            succeeded = False

    return succeeded


@lru_cache
def has_png_support():
    wagtail_png = os.path.join(os.path.dirname(__file__), "check_files", "wagtail.png")
    succeeded = True

    with open(wagtail_png, "rb") as f:
        try:
            Image.open(f)
        except OSError:
            succeeded = False

    return succeeded


@register("files")
def image_library_check(app_configs, **kwargs):
    errors = []

    if not has_jpeg_support():
        errors.append(
            Warning(
                "JPEG image support is not available",
                hint="Check that the 'libjpeg' library is installed, then reinstall Pillow.",
            )
        )

    if not has_png_support():
        errors.append(
            Warning(
                "PNG image support is not available",
                hint="Check that the 'zlib' library is installed, then reinstall Pillow.",
            )
        )

    return errors
