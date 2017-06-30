from __future__ import absolute_import, unicode_literals

from ..fields import ImageRenditionField
from ..v3.serializers import ImageSerializer


class AdminImageSerializer(ImageSerializer):
    thumbnail = ImageRenditionField('max-165x165', source='*', read_only=True)
