from collections import OrderedDict

from wagtail.api.v2.serializers import (
    PageMetaField, PageSerializer,
    MetaField, ImageSerializer,
)

from wagtail.wagtailimages.models import SourceImageIOError


class AdminPageMetaField(PageMetaField):
    """
    A subclass of PageMetaField for the admin API.

    This adds the "status" and "has_children" fields

    Example:

    "meta": {
        ...

        "status": {
            "status": "live",
            "live": true,
            "has_unpublished_changes": false
        },
        "has_children": true
    }
    """
    def to_representation(self, page):
        data = super(AdminPageMetaField, self).to_representation(page)
        data['status'] = OrderedDict([
            ('status', page.status_string),
            ('live', page.live),
            ('has_unpublished_changes', page.has_unpublished_changes),
        ])

        data['has_children'] = page.numchild > 0
        return data


class AdminPageSerializer(PageSerializer):
    meta = AdminPageMetaField()


class AdminImageMetaField(MetaField):
    """
    A subclass of ImageMetaField for the admin API.

    This adds the "thumbnail" field contain a URL/width/height of a max-165x165
    rendition of the image.

    Example:
    "meta": {
        ...

        "thumbnail": {
            "url": "/media/images/myimage.max-165x165.jpg",
            "width": 165,
            "height": 100
        }
    }

    If there is an error with the source image. The "thumbnail" field will be
    set to null and a new field "source_image_error" will be added and set to
    true.

    "meta": {
        ...

        "thumbnail": null,
        "source_image_error": true
    }
    """
    def to_representation(self, image):
        data = super(AdminImageMetaField, self).to_representation(image)

        try:
            thumbnail = image.get_rendition('max-165x165')

            data['thumbnail'] = OrderedDict([
                ('url', thumbnail.url),
                ('width', thumbnail.width),
                ('height', thumbnail.height),
            ])
        except SourceImageIOError:
            data['thumbnail'] = None
            data['source_image_error'] = True

        return data


class AdminImageSerializer(ImageSerializer):
    meta = AdminImageMetaField()
