from django.test import TestCase
from wagtail.images import get_image_model
from django.core.files.base import ContentFile

Image = get_image_model()

class ImageSelectorTests(TestCase):
    def setUp(self):
        # Create dummy images with required 'file' field
        for i in range(5):
            img_file = ContentFile(
                b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00'
                b'\x00\x00\x00\xFF\xFF\xFF\x21\xF9\x04\x01\x0A\x00\x01'
                b'\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02'
                b'\x4C\x01\x00',
                name=f'image_{i}.gif'
            )
            Image.objects.create(title=f'Test Image {i}', file=img_file)

    def test_image_selector_query(self):
        images = Image.objects.all().select_related('collection')
        self.assertEqual(images.count(), 5)
