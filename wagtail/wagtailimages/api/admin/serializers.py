from __future__ import absolute_import, unicode_literals

from ..fields import ImageRenditionField
from ..v2.serializers import ImageSerializer


class AdminImageSerializer(ImageSerializer):
    thumbnail = ImageRenditionField('max-165x165', source='*', read_only=True)

    class Meta(ImageSerializer.Meta):
        fields = ImageSerializer.Meta.fields + ['thumbnail']
        listing_default_fields = ImageSerializer.Meta.listing_default_fields + [
            'width',
            'height',
            'thumbnail',
        ]
