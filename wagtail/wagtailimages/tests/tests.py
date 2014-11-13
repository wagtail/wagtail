import datetime

from mock import MagicMock

from django.test import TestCase
from django import template
from django.utils import six
from django.core.urlresolvers import reverse

from wagtail.wagtailimages.utils import generate_signature, verify_signature
from wagtail.wagtailimages.rect import Rect
from wagtail.wagtailimages.formats import Format, get_image_format, register_image_format

from .utils import Image, get_test_image_file


class TestImageTag(TestCase):
    def setUp(self):
        # Create an image for running tests on
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def render_image_tag(self, image, filter_spec):
        temp = template.Template('{% load wagtailimages_tags %}{% image image_obj ' + filter_spec + '%}')
        context = template.Context({'image_obj': image})
        return temp.render(context)

    def test_image_tag(self):
        result = self.render_image_tag(self.image, 'width-400')

        # Check that all the required HTML attributes are set
        self.assertTrue('width="400"' in result)
        self.assertTrue('height="300"' in result)
        self.assertTrue('alt="Test image"' in result)

    def render_image_tag_as(self, image, filter_spec):
        temp = template.Template('{% load wagtailimages_tags %}{% image image_obj ' + filter_spec + ' as test_img %}<img {{ test_img.attrs }} />')
        context = template.Context({'image_obj': image})
        return temp.render(context)

    def test_image_tag_attrs(self):
        result = self.render_image_tag_as(self.image, 'width-400')

        # Check that all the required HTML attributes are set
        self.assertTrue('width="400"' in result)
        self.assertTrue('height="300"' in result)
        self.assertTrue('alt="Test image"' in result)

    def render_image_tag_with_extra_attributes(self, image, title):
        temp = template.Template('{% load wagtailimages_tags %}{% image image_obj width-400 class="photo" title=title|lower %}')
        context = template.Context({'image_obj': image, 'title': title})
        return temp.render(context)

    def test_image_tag_with_extra_attributes(self):
        result = self.render_image_tag_with_extra_attributes(self.image, 'My Wonderful Title')

        # Check that all the required HTML attributes are set
        self.assertTrue('width="400"' in result)
        self.assertTrue('height="300"' in result)
        self.assertTrue('class="photo"' in result)
        self.assertTrue('title="my wonderful title"' in result)


class TestMissingImage(TestCase):
    """
    Missing image files in media/original_images should be handled gracefully, to cope with
    pulling live databases to a development instance without copying the corresponding image files.
    In this case, it's acceptable to render broken images, but not to fail rendering the page outright.
    """
    fixtures = ['test.json']

    def test_image_tag_with_missing_image(self):
        # the page /events/christmas/ has a missing image as the feed image
        response = self.client.get('/events/christmas/')
        self.assertContains(response, '<img src="/media/not-found" width="0" height="0" alt="A missing image" class="feed-image">', html=True)

    def test_rich_text_with_missing_image(self):
        # the page /events/final-event/ has a missing image in the rich text body
        response = self.client.get('/events/final-event/')
        self.assertContains(response, '<img class="richtext-image full-width" src="/media/not-found" width="0" height="0" alt="where did my image go?">', html=True)


class TestFormat(TestCase):
    def setUp(self):
        # test format
        self.format = Format(
            'test name',
            'test label',
            'test classnames',
            'test filter spec'
        )
        # test image
        self.image = MagicMock()
        self.image.id = 0

    def test_editor_attributes(self):
        result = self.format.editor_attributes(
            self.image,
            'test alt text'
        )
        self.assertEqual(result,
                         'data-embedtype="image" data-id="0" data-format="test name" data-alt="test alt text" ')

    def test_image_to_editor_html(self):
        result = self.format.image_to_editor_html(
            self.image,
            'test alt text'
        )
        six.assertRegex(self, result,
            '<img data-embedtype="image" data-id="0" data-format="test name" data-alt="test alt text" class="test classnames" src="[^"]+" width="1" height="1" alt="test alt text">',
        )

    def test_image_to_html_no_classnames(self):
        self.format.classnames = None
        result = self.format.image_to_html(self.image, 'test alt text')
        six.assertRegex(self, result,
            '<img src="[^"]+" width="1" height="1" alt="test alt text">'
        )
        self.format.classnames = 'test classnames'

    def test_get_image_format(self):
        register_image_format(self.format)
        result = get_image_format('test name')
        self.assertEqual(result, self.format)


class TestSignatureGeneration(TestCase):
    def test_signature_generation(self):
        self.assertEqual(generate_signature(100, 'fill-800x600'), b'xnZOzQyUg6pkfciqcfRJRosOrGg=')

    def test_signature_verification(self):
        self.assertTrue(verify_signature(b'xnZOzQyUg6pkfciqcfRJRosOrGg=', 100, 'fill-800x600'))

    def test_signature_changes_on_image_id(self):
        self.assertFalse(verify_signature(b'xnZOzQyUg6pkfciqcfRJRosOrGg=', 200, 'fill-800x600'))

    def test_signature_changes_on_filter_spec(self):
        self.assertFalse(verify_signature(b'xnZOzQyUg6pkfciqcfRJRosOrGg=', 100, 'fill-800x700'))


class TestFrontendServeView(TestCase):
    def setUp(self):
        # Create an image for running tests on
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def test_get(self):
        """
        Test a valid GET request to the view
        """
        # Generate signature
        signature = generate_signature(self.image.id, 'fill-800x600')

        # Get the image
        response = self.client.get(reverse('wagtailimages_serve', args=(signature, self.image.id, 'fill-800x600')))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/jpeg')

    def test_get_invalid_signature(self):
        """
        Test that an invalid signature returns a 403 response
        """
        # Generate a signature for the incorrect image id
        signature = generate_signature(self.image.id + 1, 'fill-800x600')

        # Get the image
        response = self.client.get(reverse('wagtailimages_serve', args=(signature, self.image.id, 'fill-800x600')))

        # Check response
        self.assertEqual(response.status_code, 403)

    def test_get_invalid_filter_spec(self):
        """
        Test that an invalid filter spec returns a 400 response

        This is very unlikely to happen in reality. A user would have
        to create signature for the invalid filter spec which can't be
        done with Wagtails built in URL generator. We should test it
        anyway though.
        """
        # Generate a signature with the invalid filterspec
        signature = generate_signature(self.image.id, 'bad-filter-spec')

        # Get the image
        response = self.client.get(reverse('wagtailimages_serve', args=(signature, self.image.id, 'bad-filter-spec')))

        # Check response
        self.assertEqual(response.status_code, 400)


class TestRect(TestCase):
    def test_init(self):
        rect = Rect(100, 150, 200, 250)
        self.assertEqual(rect.left, 100)
        self.assertEqual(rect.top, 150)
        self.assertEqual(rect.right, 200)
        self.assertEqual(rect.bottom, 250)

    def test_equality(self):
        self.assertEqual(Rect(100, 150, 200, 250), Rect(100, 150, 200, 250))
        self.assertNotEqual(Rect(100, 150, 200, 250), Rect(10, 15, 20, 25))

    def test_getitem(self):
        rect = Rect(100, 150, 200, 250)
        self.assertEqual(rect[0], 100)
        self.assertEqual(rect[1], 150)
        self.assertEqual(rect[2], 200)
        self.assertEqual(rect[3], 250)
        self.assertRaises(IndexError, rect.__getitem__, 4)

    def test_as_tuple(self):
        rect = Rect(100, 150, 200, 250)
        self.assertEqual(rect.as_tuple(), (100, 150, 200, 250))

    def test_size(self):
        rect = Rect(100, 150, 200, 350)
        self.assertEqual(rect.size, (100, 200))
        self.assertEqual(rect.width, 100)
        self.assertEqual(rect.height, 200)

    def test_centroid(self):
        rect = Rect(100, 150, 200, 350)
        self.assertEqual(rect.centroid, (150, 250))
        self.assertEqual(rect.centroid_x, 150)
        self.assertEqual(rect.centroid_y, 250)

    def test_repr(self):
        rect = Rect(100, 150, 200, 250)
        self.assertEqual(repr(rect), "Rect(left: 100, top: 150, right: 200, bottom: 250)")

    def test_from_point(self):
        rect = Rect.from_point(100, 200, 50, 20)
        self.assertEqual(rect, Rect(75, 190, 125, 210))

    def test_get_key(self):
        rect = Rect(100, 150, 200, 250)
        self.assertEqual(rect.get_key(), '150-200-100x100')
