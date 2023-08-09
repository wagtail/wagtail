from io import BytesIO

import PIL.Image
from django.core.files.images import ImageFile

from wagtail.images import get_image_model

Image = get_image_model()


def get_test_image_file(filename="test.png", colour="white", size=(640, 480)):
    f = BytesIO()
    image = PIL.Image.new("RGBA", size, colour)
    image.save(f, "PNG")
    return ImageFile(f, name=filename)


def get_test_image_file_avif(filename="test.png", colour="white", size=(640, 480)):
    f = BytesIO()
    image = PIL.Image.new("RGBA", size, colour)
    image.save(f, "AVIF")
    return ImageFile(f, name=filename)


def get_test_image_file_jpeg(filename="test.jpg", colour="white", size=(640, 480)):
    f = BytesIO()
    image = PIL.Image.new("RGB", size, colour)
    image.save(f, "JPEG")
    return ImageFile(f, name=filename)


def get_test_image_file_webp(filename="test.webp", colour="white", size=(640, 480)):
    f = BytesIO()
    image = PIL.Image.new("RGB", size, colour)
    image.save(f, "WEBP")
    return ImageFile(f, name=filename)


def get_test_image_file_tiff(filename="test.tiff", colour="white", size=(640, 480)):
    f = BytesIO()
    image = PIL.Image.new("RGB", size, colour)
    image.save(f, "TIFF")
    return ImageFile(f, name=filename)


def get_test_image_file_svg(
    filename="test.svg", width=100, height=100, view_box="0 0 100 100"
):
    img = f"""
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="{view_box}">
</svg>
    """
    f = BytesIO(img.strip().encode("utf-8"))
    return ImageFile(f, filename)
