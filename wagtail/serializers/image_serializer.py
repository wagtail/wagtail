from rest_framework import serializers

from wagtail.images import get_image_model

Image = get_image_model()

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = '__all__'
    
    @staticmethod
    def natural_key(image):
        return (image.file.name)