import os

from django.core.checks import register, Warning

from willow.image import Image


_has_jpeg_support = None
_has_png_support = None


def has_jpeg_support():
    global _has_jpeg_support

    if _has_jpeg_support is None:
        wagtail_jpg = os.path.join(os.path.dirname(__file__), 'check_files', 'wagtail.jpg')
        succeeded = True
        f = open(wagtail_jpg, 'rb')

        try:
            Image.open(f)
        except (IOError, Image.LoaderError):
            succeeded = False
        finally:
            f.close()

        _has_jpeg_support = succeeded

    return _has_jpeg_support


def has_png_support():
    global _has_png_support

    if _has_png_support is None:
        wagtail_png = os.path.join(os.path.dirname(__file__), 'check_files', 'wagtail.png')
        succeeded = True
        f = open(wagtail_png, 'rb')

        try:
            Image.open(f)
        except (IOError, Image.LoaderError):
            succeeded = False
        finally:
            f.close()

        _has_png_support = succeeded

    return _has_png_support


@register()
def image_library_check(app_configs, **kwargs):
    errors = []

    if not has_jpeg_support():
        errors.append(
            Warning(
                'JPEG image support is not available',
                hint="Check that the 'libjpeg' library is installed, then reinstall Pillow."
            )
        )

    if not has_png_support():
        errors.append(
            Warning(
                'PNG image support is not available',
                hint="Check that the 'zlib' library is installed, then reinstall Pillow."
            )
        )

    return errors
