import json

from django.apps import apps
from django.test import TestCase
from django.db import models

from wagtail.tests.testapp.models import StreamModel
from wagtail.wagtailcore import blocks
from wagtail.wagtailcore.fields import StreamField
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

class TestSystemCheck(TestCase):
    def tearDown(self):
        # unregister InvalidStreamModel from the overall model registry
        # so that it doesn't break tests elsewhere
        for package in ('wagtailcore', 'wagtail.wagtailcore.tests'):
            try:
                del apps.all_models[package]['invalidstreammodel']
            except KeyError:
                pass
        apps.clear_cache()

    def test_system_check_validates_block(self):
        class InvalidStreamModel(models.Model):
            body = StreamField([
                ('heading', blocks.CharBlock()),
                ('rich text', blocks.RichTextBlock()),
            ])

        errors = InvalidStreamModel.check()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].id, 'wagtailcore.E001')
        self.assertEqual(errors[0].hint, "Block names cannot contain spaces")
