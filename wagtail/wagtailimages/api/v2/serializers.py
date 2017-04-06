from __future__ import absolute_import, unicode_literals

from wagtail.api.v2.serializers import BaseSerializer


class ImageSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        fields = BaseSerializer.Meta.fields + ['title', 'width', 'height', 'tags']
        meta_fields = BaseSerializer.Meta.meta_fields + ['tags']
        listing_default_fields = BaseSerializer.Meta.listing_default_fields + ['title', 'tags']
        nested_default_fields = BaseSerializer.Meta.nested_default_fields + ['title']
