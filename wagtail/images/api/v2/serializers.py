from rest_framework.fields import Field

from wagtail.api.v2.serializers import BaseSerializer


class ImageDownloadUrlField(Field):
    """
    Serializes the "download_url" field for images.

    Example:
    "download_url": "/media/images/a_test_image.jpg"
    """

    def get_attribute(self, instance):
        return instance

    def to_representation(self, image):
        return image.file.url


class ImageSerializer(BaseSerializer):
    download_url = ImageDownloadUrlField(read_only=True)
