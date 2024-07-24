from wagtail.images.models import SourceImageIOError


def get_rendition_or_not_found(image, specs):
    """
    Tries to get / create the rendition for the image or renders a not-found image if it does not exist.

    :param image: AbstractImage
    :param specs: str or Filter
    :return: Rendition
    """
    try:
        return image.get_rendition(specs)
    except SourceImageIOError:
        # Image file is (probably) missing from /media/original_images - generate a dummy
        # rendition so that we just output a broken image, rather than crashing out completely
        # during rendering.
        Rendition = (
            image.renditions.model
        )  # pick up any custom Image / Rendition classes that may be in use
        rendition = Rendition(image=image, width=0, height=0)
        rendition.file.name = "not-found"
        return rendition


def get_renditions_or_not_found(image, specs):
    """
    Like get_rendition_or_not_found, but for multiple renditions.
    Tries to get / create the renditions for the image or renders not-found images if the image does not exist.

    :param image: AbstractImage
    :param specs: iterable of str or Filter
    """
    try:
        return image.get_renditions(*specs)
    except SourceImageIOError:
        Rendition = image.renditions.model
        rendition = Rendition(image=image, width=0, height=0)
        rendition.file.name = "not-found"
        return {
            spec if isinstance(spec, str) else spec.spec: rendition for spec in specs
        }
