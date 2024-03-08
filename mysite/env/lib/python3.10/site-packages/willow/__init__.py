from willow.image import Image  # noqa: F401


def setup():
    from xml.etree import ElementTree

    from willow.image import (
        AvifImageFile,
        BMPImageFile,
        GIFImageFile,
        HeicImageFile,
        IcoImageFile,
        JPEGImageFile,
        PNGImageFile,
        RGBAImageBuffer,
        RGBImageBuffer,
        SvgImageFile,
        TIFFImageFile,
        WebPImageFile,
    )
    from willow.optimizers import Cwebp, Gifsicle, Jpegoptim, Optipng, Pngquant
    from willow.plugins import opencv, pillow, wand
    from willow.registry import registry
    from willow.svg import SvgImage

    registry.register_image_class(JPEGImageFile)
    registry.register_image_class(PNGImageFile)
    registry.register_image_class(GIFImageFile)
    registry.register_image_class(BMPImageFile)
    registry.register_image_class(TIFFImageFile)
    registry.register_image_class(WebPImageFile)
    registry.register_image_class(HeicImageFile)
    registry.register_image_class(RGBImageBuffer)
    registry.register_image_class(RGBAImageBuffer)
    registry.register_image_class(SvgImageFile)
    registry.register_image_class(SvgImage)
    registry.register_image_class(AvifImageFile)
    registry.register_image_class(IcoImageFile)

    registry.register_plugin(pillow)
    registry.register_plugin(wand)
    registry.register_plugin(opencv)

    registry.register_optimizer(Cwebp)
    registry.register_optimizer(Gifsicle)
    registry.register_optimizer(Jpegoptim)
    registry.register_optimizer(Optipng)
    registry.register_optimizer(Pngquant)

    # Prevents etree from prefixing XML tag names with anonymous
    # namespaces, e.g. "<ns0:svg ..."
    ElementTree.register_namespace("", "http://www.w3.org/2000/svg")


setup()


__version__ = "1.8.0"
