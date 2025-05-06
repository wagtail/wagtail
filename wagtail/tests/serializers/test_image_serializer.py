import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from wagtail.images import get_image_model
from wagtail.serializers.image_serializer import ImageSerializer

from PIL import Image as PilImage
import tempfile

def generate_test_image():
    with tempfile.NamedTemporaryFile(suffix=".jpg") as f:
        image = PilImage.new('RGB', (100, 100), color='red')
        image.save(f, format='JPEG')
        f.seek(0)
        return SimpleUploadedFile(name='test.jpg', content=f.read(), content_type='image/jpeg')

Image = get_image_model()

@pytest.mark.django_db
def test_image_serializer():
    image_file = generate_test_image()
    image = Image.objects.create(
        title = "test image",
        file = image_file,
    )
    serializer = ImageSerializer(instance = image)
    assert serializer.data['title'] == "test image"
    assert "file" in serializer.data