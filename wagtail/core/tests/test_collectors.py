from django.test import TestCase

from wagtail.core.collectors import ModelStreamFieldsCollector
from wagtail.images.blocks import ImageChooserBlock
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.tests.testapp.models import StreamModel


class ModelStreamFieldCollectorTest(TestCase):
    def setUp(self):
        self.collector = ModelStreamFieldsCollector(StreamModel)

        self.image0 = Image.objects.create(title='Test image 0',
                                           file=get_test_image_file())
        self.image1 = Image.objects.create(title='Test image 1',
                                           file=get_test_image_file())
        self.image2 = Image.objects.create(title='Test image 2',
                                           file=get_test_image_file())
        self.image3 = Image.objects.create(title='Test image 3',
                                           file=get_test_image_file())
        self.image4 = Image.objects.create(title='Test image 4',
                                           file=get_test_image_file())
        self.image5 = Image.objects.create(title='Test image 5',
                                           file=get_test_image_file())
        self.image6 = Image.objects.create(title='Test image 6',
                                           file=get_test_image_file())
        self.image7 = Image.objects.create(title='Test image 7',
                                           file=get_test_image_file())
        self.image8 = Image.objects.create(title='Test image 8',
                                           file=get_test_image_file())
        self.image9 = Image.objects.create(title='Test image 9',
                                           file=get_test_image_file())
        self.image10 = Image.objects.create(title='Test image 10',
                                            file=get_test_image_file())

        self.obj_empty = StreamModel.objects.create()
        self.obj_text = StreamModel.objects.create(body=[
            ('text', 'foo')])
        self.obj1 = StreamModel.objects.create(body=[
            ('image', self.image1)])
        self.obj2 = StreamModel.objects.create(body=[
            ('text', 'foo'),
            ('image', self.image2),
            ('text', 'bar')])
        self.obj3 = StreamModel.objects.create(body=[
            ('struct', {'image': self.image3})])
        self.obj4 = StreamModel.objects.create(body=[
            ('struct', {'image_list': [self.image4]})])
        self.obj5 = StreamModel.objects.create(body=[
            ('struct', {'struct_list': [{'image': self.image5}]})])
        self.obj6 = StreamModel.objects.create(body=[
            ('text', 'foo'),
            ('image', self.image6),
            ('struct', {
                'image': self.image7,
                'image_list': [self.image8],
                'struct_list': [{'image': self.image9}]}),
            ('image', self.image10),
            ('text', 'bar')])
        self.obj7 = StreamModel.objects.create(body=[
            ('image', self.image9)])
        self.obj8 = StreamModel.objects.create(body=[
            ('struct', {'image': self.image8})])
        self.obj9 = StreamModel.objects.create(body=[
            ('struct', {'image_list': [self.image7]})])
        self.obj10 = StreamModel.objects.create(body=[
            ('struct', {'struct_list': [{'image': self.image6}]})])

    def get_image_usages(self, *images):
        return list(self.collector.find_objects_for(ImageChooserBlock,
                                                    images))

    def test_empty(self):
        with self.assertNumQueries(1):
            usages = self.get_image_usages(self.image0)
            self.assertListEqual(usages, [])

    def test_single_root(self):
        with self.assertNumQueries(2):
            usages = self.get_image_usages(self.image1)
            self.assertListEqual(usages, [(self.obj1, self.image1)])

    def test_multiple_roots(self):
        with self.assertNumQueries(2):
            usages = self.get_image_usages(self.image2)
            self.assertListEqual(usages, [(self.obj2, self.image2)])

    def test_simple_struct(self):
        with self.assertNumQueries(2):
            usages = self.get_image_usages(self.image3)
            self.assertListEqual(usages, [(self.obj3, self.image3)])

    def test_list(self):
        with self.assertNumQueries(2):
            usages = self.get_image_usages(self.image4)
            self.assertListEqual(usages, [(self.obj4, self.image4)])

    def test_nested_structs(self):
        with self.assertNumQueries(2):
            usages = self.get_image_usages(self.image5)
            self.assertListEqual(usages, [(self.obj5, self.image5)])

    def test_multiple(self):
        with self.assertNumQueries(6):
            usages = self.get_image_usages(self.image6)
            self.assertListEqual(usages, [(self.obj6, self.image6),
                                          (self.obj10, self.image6)])
        with self.assertNumQueries(6):
            usages = self.get_image_usages(self.image7)
            self.assertListEqual(usages, [(self.obj6, self.image7),
                                          (self.obj9, self.image7)])
        with self.assertNumQueries(6):
            usages = self.get_image_usages(self.image8)
            self.assertListEqual(usages, [(self.obj6, self.image8),
                                          (self.obj8, self.image8)])
        with self.assertNumQueries(6):
            usages = self.get_image_usages(self.image9)
            self.assertListEqual(usages, [(self.obj6, self.image9),
                                          (self.obj7, self.image9)])
        with self.assertNumQueries(9):
            usages = self.get_image_usages(self.image6, self.image7,
                                           self.image8, self.image9,
                                           self.image10)
            self.assertListEqual(usages, [(self.obj6, self.image6),
                                          (self.obj6, self.image10),
                                          (self.obj6, self.image7),
                                          (self.obj6, self.image8),
                                          (self.obj6, self.image9),
                                          (self.obj7, self.image9),
                                          (self.obj8, self.image8),
                                          (self.obj9, self.image7),
                                          (self.obj10, self.image6)])
