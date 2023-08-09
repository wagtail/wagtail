from ..fields import ImageRenditionField
from ..v2.serializers import ImageSerializer


class AdminImageSerializer(ImageSerializer):
    thumbnail = ImageRenditionField("max-165x165", source="*", read_only=True)
