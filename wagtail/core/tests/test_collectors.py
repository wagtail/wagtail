from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test import TestCase

from wagtail.core.collectors import (
    ModelRichTextCollector, ModelStreamFieldsCollector, Use, get_all_uses)
from wagtail.core.models import Page
from wagtail.core.rich_text import RichText
from wagtail.documents.models import Document
from wagtail.embeds.embeds import get_embed
from wagtail.images.blocks import ImageChooserBlock
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.tests.testapp.models import DefaultRichTextFieldPage, PageChooserModel, StreamModel


class ModelRichTextCollectorTest(TestCase):
    def setUp(self):
        self.collector = ModelRichTextCollector(DefaultRichTextFieldPage)
        i = 0

        def create_page(body):
            nonlocal i
            home = Page.objects.get(depth=2)
            page = DefaultRichTextFieldPage(
                title='%s' % i, body=body, slug='%s' % i)
            home.add_child(instance=page)
            i += 1
            return page

        self.obj0 = create_page('<p>Nothing interesting here</p>')
        self.obj1 = create_page('<p>Nothing interesting here</p>')
        self.obj2 = create_page(
            '<a linktype="page" id="%s">1</a>' % self.obj1.pk)
        self.obj3 = create_page(
            '<p><a id="%s" linktype="page">2</a></p>' % self.obj2.pk)
        self.obj4 = create_page(
            '<p>A link to the <a linktype="page" id="%s">3</a> page.</p>'
            % self.obj3.pk)
        self.obj5 = create_page(
            '<div><p>A link <span>to the '
            '<a linktype="page" id="%s">4</a></span> page.</p><div>'
            % self.obj4.pk)
        self.obj6 = create_page('<p>Nothing interesting here</p>')
        self.obj7 = create_page(
            '<p><a linktype="page" id="%s">5</a>'
            '<a linktype="page" id="%s">6</a></p>'
            % (self.obj5.pk, self.obj6.pk))
        self.image = Image.objects.create(title='Test image',
                                          file=get_test_image_file())
        self.obj8 = create_page('<embed alt="bodyline" embedtype="image" '
                                'format="centered" id="%s"/>' % self.image.pk)
        self.document = Document.objects.create(title='Test document',
                                                file=get_test_image_file())
        self.obj9 = create_page(
            '<a id="%s" linktype="document">Test document</a>'
            % self.document.pk)
        self.video = get_embed('https://www.youtube.com/watch?v=6adGK7fXZX8')
        self.obj10 = create_page('<embed embedtype="media" url="%s"/>'
                                 % self.video.url)

        # For query count consistency.
        ContentType.objects.clear_cache()

    def get_pairs(self, *objects):
        """
        Finds pairs between ``objects`` and related objects.
        """
        return list(self.collector.find_objects(*objects))

    def get_all_pairs(self, *objects):
        return list(self.collector.find_all_objects())

    def test_empty(self):
        with self.assertNumQueries(1):
            pairs = self.get_pairs(self.obj0)
            self.assertListEqual(pairs, [])

    def test_simple(self):
        with self.assertNumQueries(4):
            pairs = self.get_pairs(self.obj1)
            self.assertListEqual(pairs, [(self.obj2, self.obj1)])

    def test_wrapped_and_swapped(self):
        with self.assertNumQueries(4):
            pairs = self.get_pairs(self.obj2)
            self.assertListEqual(pairs, [(self.obj3, self.obj2)])

        with self.assertNumQueries(3):
            pairs = self.get_pairs(self.obj3)
            self.assertListEqual(pairs, [(self.obj4, self.obj3)])

    def test_nested(self):
        with self.assertNumQueries(4):
            pairs = self.get_pairs(self.obj4)
            self.assertListEqual(pairs, [(self.obj5, self.obj4)])

    def test_find_all(self):
        with self.assertNumQueries(17):
            pairs = self.get_all_pairs()
            self.assertListEqual(pairs, [(self.obj2, self.obj1),
                                         (self.obj3, self.obj2),
                                         (self.obj4, self.obj3),
                                         (self.obj5, self.obj4),
                                         (self.obj7, self.obj5),
                                         (self.obj7, self.obj6),
                                         (self.obj8, self.image),
                                         (self.obj9, self.document),
                                         (self.obj10, self.video)])

    def test_multiple(self):
        with self.assertNumQueries(0):
            pairs = self.get_pairs()
            self.assertListEqual(pairs, [])

        with self.assertNumQueries(6):
            pairs = self.get_pairs(self.obj5)
            self.assertListEqual(pairs, [(self.obj7, self.obj5)])

        with self.assertNumQueries(5):
            pairs = self.get_pairs(self.obj5, self.obj6)
            self.assertListEqual(pairs, [(self.obj7, self.obj5),
                                         (self.obj7, self.obj6)])

    def test_other_types(self):
        with self.assertNumQueries(2):
            pairs = self.get_pairs(self.image)
            self.assertListEqual(pairs, [(self.obj8, self.image)])

        with self.assertNumQueries(2):
            pairs = self.get_pairs(self.document)
            self.assertListEqual(pairs, [(self.obj9, self.document)])

        with self.assertNumQueries(2):
            pairs = self.get_pairs(self.video)
            self.assertListEqual(pairs, [(self.obj10, self.video)])


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
        self.image11 = Image.objects.create(title='Test image 11',
                                            file=get_test_image_file())
        self.image12 = Image.objects.create(title='Test image 12',
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
        self.obj11 = StreamModel.objects.create(body=[
            ('rich_text',
             RichText('<p><embed alt="bodyline" embedtype="image" '
                      'format="centered" id="%s"/></p>' % self.image11.pk))])

        self.obj12 = StreamModel()
        stream_value = StreamModel._meta.get_field('body').to_python('''[
            {"type": "gallery", "value": [
                {"type": "image", "value": %d}
            ]}
        ]''' % self.image12.id)
        self.obj12.body = stream_value
        self.obj12.save()

        self.obj13 = StreamModel()
        stream_value = StreamModel._meta.get_field('body').to_python('''[
            {"type": "gallery", "value": [
                {"type": "image_with_caption", "value": {
                    "image": %d, "caption": "a Scotsman on a horse"
                }}
            ]}
        ]''' % self.image12.id)
        self.obj13.body = stream_value
        self.obj13.save()

        # For query count consistency.
        ContentType.objects.clear_cache()

    def get_image_pairs(self, *images):
        return list(self.collector.find_objects(
            *images, block_types=(ImageChooserBlock,)))

    def test_empty(self):
        with self.assertNumQueries(1):
            pairs = self.get_image_pairs(self.image0)
            self.assertListEqual(pairs, [])

    def test_single_root(self):
        with self.assertNumQueries(2):
            pairs = self.get_image_pairs(self.image1)
            self.assertListEqual(pairs, [(self.obj1, self.image1)])

    def test_multiple_roots(self):
        with self.assertNumQueries(2):
            pairs = self.get_image_pairs(self.image2)
            self.assertListEqual(pairs, [(self.obj2, self.image2)])

    def test_simple_struct(self):
        with self.assertNumQueries(2):
            pairs = self.get_image_pairs(self.image3)
            self.assertListEqual(pairs, [(self.obj3, self.image3)])

    def test_list(self):
        with self.assertNumQueries(2):
            pairs = self.get_image_pairs(self.image4)
            self.assertListEqual(pairs, [(self.obj4, self.image4)])

    def test_nested_structs(self):
        with self.assertNumQueries(2):
            pairs = self.get_image_pairs(self.image5)
            self.assertListEqual(pairs, [(self.obj5, self.image5)])

    def test_nested_stream(self):
        pairs = self.get_image_pairs(self.image12)
        self.assertListEqual(pairs, [(self.obj12, self.image12), (self.obj13, self.image12)])

    def test_multiple(self):
        with self.assertNumQueries(6):
            pairs = self.get_image_pairs(self.image6)
            self.assertListEqual(pairs, [(self.obj6, self.image6),
                                         (self.obj10, self.image6)])
        with self.assertNumQueries(6):
            pairs = self.get_image_pairs(self.image7)
            self.assertListEqual(pairs, [(self.obj6, self.image7),
                                         (self.obj9, self.image7)])
        with self.assertNumQueries(6):
            pairs = self.get_image_pairs(self.image8)
            self.assertListEqual(pairs, [(self.obj6, self.image8),
                                         (self.obj8, self.image8)])
        with self.assertNumQueries(6):
            pairs = self.get_image_pairs(self.image9)
            self.assertListEqual(pairs, [(self.obj6, self.image9),
                                         (self.obj7, self.image9)])
        with self.assertNumQueries(9):
            pairs = self.get_image_pairs(self.image6, self.image7,
                                         self.image8, self.image9,
                                         self.image10)
            self.assertListEqual(pairs, [(self.obj6, self.image6),
                                         (self.obj6, self.image10),
                                         (self.obj6, self.image7),
                                         (self.obj6, self.image8),
                                         (self.obj6, self.image9),
                                         (self.obj7, self.image9),
                                         (self.obj8, self.image8),
                                         (self.obj9, self.image7),
                                         (self.obj10, self.image6)])

    def test_rich_text_block(self):
        with self.assertNumQueries(2):
            pairs = list(self.collector.find_objects(self.image11))
            self.assertListEqual(pairs, [(self.obj11, self.image11)])


class GetAllUsesTest(TestCase):
    def setUp(self):
        self.is_sqlite = connection.vendor == 'sqlite'
        self.has_postgres_search = connection.vendor == 'postgresql' and any(
            conf['BACKEND'] == 'wagtail.contrib.postgres_search.backend'
            for conf in settings.WAGTAILSEARCH_BACKENDS.values())

        i = 0

        def create_page(body):
            nonlocal i
            home = Page.objects.get(depth=2)
            page = DefaultRichTextFieldPage(
                title='%s' % i, body=body, slug='%s' % i)
            home.add_child(instance=page)
            i += 1
            return page

        self.obj0 = create_page('<p>Nothing worth of interest.</p>')
        self.obj1 = create_page('<p>Nothing worth of interest.</p>')
        self.obj2 = PageChooserModel.objects.create(page=self.obj1)
        self.obj3 = create_page('<p>Nothing worth of interest.</p>')
        self.obj4 = create_page('<p><a linktype="page" id="%s">3</a></p>'
                                % self.obj3.pk)
        self.obj5 = Image.objects.create(title='Test image 1',
                                         file=get_test_image_file())
        self.obj6 = StreamModel.objects.create(body=[('image', self.obj5)])
        self.obj7 = Image.objects.create(title='Test image',
                                         file=get_test_image_file())
        self.obj8 = self.obj7.get_rendition('original')
        self.obj9 = StreamModel.objects.create(body=[('image', self.obj7)])
        self.obj10 = create_page(
            '<p><embed alt="bodyline" embedtype="image" '
            'format="centered" id="%s"/></p>' % self.obj7.pk)

        # For query count consistency.
        ContentType.objects.clear_cache()

    def to_uses(self, objects):
        """
        Converts nested Model instances into Use instances following the same structure.
        """
        if isinstance(objects, (tuple, list)):
            return type(objects)(self.to_uses(obj) for obj in objects)
        return Use(objects)

    def assert_uses(self, uses, objects):
        self.assertListEqual(uses, self.to_uses(objects))

    def test_empty(self):
        with self.assertNumQueries(57 if self.has_postgres_search else 55):
            uses = list(get_all_uses(self.obj0))
            self.assert_uses(uses, [])

    def test_foreign_key(self):
        with self.assertNumQueries(57 if self.has_postgres_search
                                   else (56 if self.is_sqlite else 55)):
            uses = list(get_all_uses(self.obj1))
            self.assert_uses(uses, [self.obj2])

    def test_rich_text(self):
        with self.assertNumQueries(59 if self.has_postgres_search else 58):
            uses = list(get_all_uses(self.obj3))
            self.assert_uses(uses, [self.obj4])

    def test_streamfield(self):
        with self.assertNumQueries(59 if self.has_postgres_search else 58):
            uses = list(get_all_uses(self.obj3))
            self.assert_uses(uses, [self.obj4])

    def test_multiple(self):
        with self.assertNumQueries(50 if self.has_postgres_search or self.is_sqlite else 49):
            uses = list(get_all_uses(self.obj7))
            self.assert_uses(uses, [self.obj8, self.obj9, self.obj10])
