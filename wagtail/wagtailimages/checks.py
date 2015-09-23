import os

from django.core.checks import register, Warning

from willow.image import Image


def has_jpeg_support():
    wagtail_jpg = os.path.join(os.path.dirname(__file__), 'check_files', 'wagtail.jpg')
    is_ok = True
    f = open(wagtail_jpg, 'rb')

    try:
        Image.open(f)
    except (IOError, Image.LoaderError):
        is_ok = False
    finally:
        f.close()

    return is_ok


def has_png_support():
    wagtail_png = os.path.join(os.path.dirname(__file__), 'check_files', 'wagtail.png')
    is_ok = True
    f = open(wagtail_png, 'rb')

    try:
        Image.open(f)
    except (IOError, Image.LoaderError):
        is_ok = False
    finally:
        f.close()

    return is_ok


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
