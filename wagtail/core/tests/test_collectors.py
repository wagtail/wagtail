from django.test import TestCase

from wagtail.core.collectors import ModelRichTextCollector, ModelStreamFieldsCollector, get_all_uses
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

    def get_uses(self, *objects):
        return list(self.collector.find_objects(*objects))

    def test_empty(self):
        uses = self.get_uses(self.obj0)
        self.assertListEqual(uses, [])

    def test_simple(self):
        uses = self.get_uses(self.obj1)
        self.assertListEqual(uses, [(self.obj2, self.obj1)])

    def test_wrapped_and_swapped(self):
        uses = self.get_uses(self.obj2)
        self.assertListEqual(uses, [(self.obj3, self.obj2)])

        uses = self.get_uses(self.obj3)
        self.assertListEqual(uses, [(self.obj4, self.obj3)])

    def test_nested(self):
        uses = self.get_uses(self.obj4)
        self.assertListEqual(uses, [(self.obj5, self.obj4)])

    def test_multiple(self):
        uses = self.get_uses()
        self.assertListEqual(uses, [(self.obj2, self.obj1),
                                    (self.obj3, self.obj2),
                                    (self.obj4, self.obj3),
                                    (self.obj5, self.obj4),
                                    (self.obj7, self.obj5),
                                    (self.obj7, self.obj6),
                                    (self.obj8, self.image),
                                    (self.obj9, self.document),
                                    (self.obj10, self.video)])

        uses = self.get_uses(self.obj5)
        self.assertListEqual(uses, [(self.obj7, self.obj5)])

        uses = self.get_uses(self.obj5, self.obj6)
        self.assertListEqual(uses, [(self.obj7, self.obj5),
                                    (self.obj7, self.obj6)])

    def test_other_types(self):
        uses = self.get_uses(self.image)
        self.assertListEqual(uses, [(self.obj8, self.image)])

        uses = self.get_uses(self.document)
        self.assertListEqual(uses, [(self.obj9, self.document)])

        uses = self.get_uses(self.video)
        self.assertListEqual(uses, [(self.obj10, self.video)])


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

    def get_image_uses(self, *images):
        return list(self.collector.find_objects(
            *images, block_types=(ImageChooserBlock,)))

    def test_empty(self):
        with self.assertNumQueries(1):
            uses = self.get_image_uses(self.image0)
            self.assertListEqual(uses, [])

    def test_single_root(self):
        with self.assertNumQueries(2):
            uses = self.get_image_uses(self.image1)
            self.assertListEqual(uses, [(self.obj1, self.image1)])

    def test_multiple_roots(self):
        with self.assertNumQueries(2):
            uses = self.get_image_uses(self.image2)
            self.assertListEqual(uses, [(self.obj2, self.image2)])

    def test_simple_struct(self):
        with self.assertNumQueries(2):
            uses = self.get_image_uses(self.image3)
            self.assertListEqual(uses, [(self.obj3, self.image3)])

    def test_list(self):
        with self.assertNumQueries(2):
            uses = self.get_image_uses(self.image4)
            self.assertListEqual(uses, [(self.obj4, self.image4)])

    def test_nested_structs(self):
        with self.assertNumQueries(2):
            uses = self.get_image_uses(self.image5)
            self.assertListEqual(uses, [(self.obj5, self.image5)])

    def test_multiple(self):
        with self.assertNumQueries(6):
            uses = self.get_image_uses(self.image6)
            self.assertListEqual(uses, [(self.obj6, self.image6),
                                        (self.obj10, self.image6)])
        with self.assertNumQueries(6):
            uses = self.get_image_uses(self.image7)
            self.assertListEqual(uses, [(self.obj6, self.image7),
                                        (self.obj9, self.image7)])
        with self.assertNumQueries(6):
            uses = self.get_image_uses(self.image8)
            self.assertListEqual(uses, [(self.obj6, self.image8),
                                        (self.obj8, self.image8)])
        with self.assertNumQueries(6):
            uses = self.get_image_uses(self.image9)
            self.assertListEqual(uses, [(self.obj6, self.image9),
                                        (self.obj7, self.image9)])
        with self.assertNumQueries(9):
            uses = self.get_image_uses(self.image6, self.image7,
                                       self.image8, self.image9,
                                       self.image10)
            self.assertListEqual(uses, [(self.obj6, self.image6),
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
            uses = list(self.collector.find_objects(self.image11))
            self.assertListEqual(uses, [(self.obj11, self.image11)])


class GetAllUsesTest(TestCase):
    def setUp(self):
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
        self.obj5 = Image.objects.create(title='Test image',
                                         file=get_test_image_file())
        self.obj6 = StreamModel.objects.create(body=[('image', self.obj5)])

    def test_empty(self):
        uses = list(get_all_uses(self.obj0))
        self.assertListEqual(uses, [])

    def test_foreign_key(self):
        uses = list(get_all_uses(self.obj1))
        self.assertListEqual(uses, [(self.obj2, self.obj1)])

    def test_rich_text(self):
        uses = list(get_all_uses(self.obj3))
        self.assertListEqual(uses, [(self.obj4, self.obj3)])

    def test_streamfield(self):
        uses = list(get_all_uses(self.obj3))
        self.assertListEqual(uses, [(self.obj4, self.obj3)])
