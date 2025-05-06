from rest_framework import serializers

from wagtail.models.media import Collection


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = '__all__'
    
    @staticmethod
    def natural_key(collection:Collection):
        return (collection.name)
