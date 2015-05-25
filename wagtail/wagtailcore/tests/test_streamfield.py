import json

from django.test import TestCase

from wagtail.tests.testapp.models import StreamModel
from wagtail.wagtailimages.models import Image
from wagtail.wagtailimages.tests.utils import get_test_image_file


class TestLazyStreamField(TestCase):
    def setUp(self):
        self.image = Image.objects.create(
            title='Test image',
            file=get_test_image_file())
        self.with_image = StreamModel.objects.create(body=json.dumps([
            {'type': 'image', 'value': self.image.pk},
            {'type': 'text', 'value': 'foo'}]))
        self.no_image = StreamModel.objects.create(body=json.dumps([
            {'type': 'text', 'value': 'foo'}]))

    def test_lazy_load(self):
        """
        Getting a single item should lazily load the StreamField, only
        accessing the database once the StreamField is accessed
        """
        with self.assertNumQueries(1):
            # Get the instance. The StreamField should *not* load the image yet
            instance = StreamModel.objects.get(pk=self.with_image.pk)

        with self.assertNumQueries(0):
            # Access the body. The StreamField should still not get the image.
            body = instance.body

        with self.assertNumQueries(1):
            # Access the image item from the stream. The image is fetched now
            body[0].value

        with self.assertNumQueries(0):
            # Everything has been fetched now, no further database queries.
            self.assertEqual(body[0].value, self.image)
            self.assertEqual(body[1].value, 'foo')

    def test_lazy_load_no_images(self):
        """
        Getting a single item whose StreamField never accesses the database
        should behave as expected.
        """
        with self.assertNumQueries(1):
            # Get the instance, nothing else
            instance = StreamModel.objects.get(pk=self.no_image.pk)

        with self.assertNumQueries(0):
            # Access the body. The StreamField has no images, so nothing should
            # happen
            body = instance.body
            self.assertEqual(body[0].value, 'foo')

    def test_lazy_load_queryset(self):
        """
        Ensure that lazy loading StreamField works when gotten as part of a
        queryset list
        """
        with self.assertNumQueries(1):
            instances = StreamModel.objects.filter(
                pk__in=[self.with_image.pk, self.no_image.pk])
            instances_lookup = {instance.pk: instance for instance in instances}

        with self.assertNumQueries(1):
            instances_lookup[self.with_image.pk].body[0]

        with self.assertNumQueries(0):
            instances_lookup[self.no_image.pk].body[0]
