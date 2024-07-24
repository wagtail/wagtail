from unittest import TestCase

from wagtail.images.image_operations import ImageTransform
from wagtail.images.rect import Rect, Vector


class TestTransform(TestCase):
    def test_resize(self):
        context = ImageTransform((640, 480))
        resized = context.resize((320, 240))

        vector = Vector(100, 200)
        transformed = resized.transform_vector(vector)

        self.assertEqual(transformed, Vector(50, 100))

        untransformed = resized.untransform_vector(transformed)

        self.assertEqual(untransformed, vector)

    def test_crop(self):
        context = ImageTransform((640, 480))
        cropped = context.crop(Rect(200, 100, 300, 200))

        vector = Vector(250, 150)
        transformed = cropped.transform_vector(vector)

        self.assertEqual(transformed, Vector(50, 50))

        untransformed = cropped.untransform_vector(transformed)

        self.assertEqual(untransformed, vector)

    def test_resize_then_crop(self):
        context = ImageTransform((640, 480))
        resized = context.resize((320, 240))
        cropped = resized.crop(Rect(200, 100, 300, 200))

        vector = Vector(500, 300)
        transformed = cropped.transform_vector(vector)

        self.assertEqual(transformed, Vector(50, 50))

        untransformed = cropped.untransform_vector(transformed)

        self.assertEqual(untransformed, vector)

    def test_crop_then_resize(self):
        context = ImageTransform((640, 480))
        cropped = context.crop(Rect(200, 100, 300, 200))
        resized = cropped.resize((50, 50))

        vector = Vector(250, 150)
        transformed = resized.transform_vector(vector)

        self.assertEqual(transformed, Vector(25, 25))

        untransformed = resized.untransform_vector(transformed)

        self.assertEqual(untransformed, vector)
