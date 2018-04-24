from wagtail.images import get_image_model
from wagtail.images.formats import get_image_format


# Front-end conversion

def image_embedtype_handler(attrs):
    """
    Given a dict of attributes from the <embed> tag, return the real HTML
    representation for use on the front-end.
    """
    Image = get_image_model()
    try:
        image = Image.objects.get(id=attrs['id'])
    except Image.DoesNotExist:
        return "<img>"

    image_format = get_image_format(attrs['format'])
    return image_format.image_to_html(image, attrs.get('alt', ''))
