from six.moves.urllib.request import urlopen
import six.moves.urllib.request
from six.moves.urllib.error import URLError

from mock import patch

try:
    import embedly
    no_embedly = False
except ImportError:
    no_embedly = True

from django import template
from django.test import TestCase

from wagtail.tests.utils import WagtailTestUtils, unittest

from wagtail.wagtailembeds import get_embed
from wagtail.wagtailembeds.embeds import (
    EmbedNotFoundException,
    EmbedlyException,
    AccessDeniedEmbedlyException,
)
from wagtail.wagtailembeds.embeds import embedly as wagtail_embedly, oembed as wagtail_oembed
from wagtail.wagtailembeds.templatetags.wagtailembeds_tags import embed as embed_filter, embedly as embedly_filter


class TestEmbeds(TestCase):
    def setUp(self):
        self.hit_count = 0

    def dummy_finder(self, url, max_width=None):
        # Up hit count
        self.hit_count += 1

        # Return a pretend record
        return {
            'title': "Test: " + url,
            'type': 'video',
            'thumbnail_url': '',
            'width': max_width if max_width else 640,
            'height': 480,
            'html': "<p>Blah blah blah</p>",
        }

    def test_get_embed(self):
        embed = get_embed('www.test.com/1234', max_width=400, finder=self.dummy_finder)

        # Check that the embed is correct
        self.assertEqual(embed.title, "Test: www.test.com/1234")
        self.assertEqual(embed.type, 'video')
        self.assertEqual(embed.width, 400)

        # Check that there has only been one hit to the backend
        self.assertEqual(self.hit_count, 1)

        # Look for the same embed again and check the hit count hasn't increased
        embed = get_embed('www.test.com/1234', max_width=400, finder=self.dummy_finder)
        self.assertEqual(self.hit_count, 1)

        # Look for a different embed, hit count should increase
        embed = get_embed('www.test.com/4321', max_width=400, finder=self.dummy_finder)
        self.assertEqual(self.hit_count, 2)

        # Look for the same embed with a different width, this should also increase hit count
        embed = get_embed('www.test.com/4321', finder=self.dummy_finder)
        self.assertEqual(self.hit_count, 3)

    def dummy_finder_invalid_width(self, url, max_width=None):
        # Return a record with an invalid width
        return {
            'title': "Test: " + url,
            'type': 'video',
            'thumbnail_url': '',
            'width': '100%',
            'height': 480,
            'html': "<p>Blah blah blah</p>",
        }

    def test_invalid_width(self):
        embed = get_embed('www.test.com/1234', max_width=400, finder=self.dummy_finder_invalid_width)

        # Width must be set to None
        self.assertEqual(embed.width, None)

    def test_no_html(self) :
        def no_html_finder(url, max_width=None):
            """
            A finder which returns everything but HTML
            """
            embed = self.dummy_finder(url, max_width)
            embed['html'] = None
            return embed

        embed = get_embed('www.test.com/1234', max_width=400, finder=no_html_finder)

        self.assertEqual(embed.html, '')


class TestChooser(TestCase, WagtailTestUtils):
    def setUp(self):
        # login
        self.login()

    def test_chooser(self):
        r = self.client.get('/admin/embeds/chooser/')
        self.assertEqual(r.status_code, 200)

        # TODO: Test submitting

class TestEmbedly(TestCase):
    @unittest.skipIf(no_embedly, "Embedly is not installed")
    def test_embedly_oembed_called_with_correct_arguments(self):
        with patch('embedly.Embedly.oembed') as oembed:
            oembed.return_value = {'type': 'photo',
                                   'url': 'http://www.example.com'}

            wagtail_embedly('http://www.example.com', key='foo')
            oembed.assert_called_with('http://www.example.com', better=False)

            wagtail_embedly('http://www.example.com', max_width=100, key='foo')
            oembed.assert_called_with('http://www.example.com', maxwidth=100, better=False)

    @unittest.skipIf(no_embedly, "Embedly is not installed")
    def test_embedly_401(self):
        with patch('embedly.Embedly.oembed') as oembed:
            oembed.return_value = {'type': 'photo',
                                   'url': 'http://www.example.com',
                                   'error': True,
                                   'error_code': 401}
            self.assertRaises(AccessDeniedEmbedlyException,
                              wagtail_embedly, 'http://www.example.com', key='foo')

    @unittest.skipIf(no_embedly, "Embedly is not installed")
    def test_embedly_403(self):
        with patch('embedly.Embedly.oembed') as oembed:
            oembed.return_value = {'type': 'photo',
                                   'url': 'http://www.example.com',
                                   'error': True,
                                   'error_code': 403}
            self.assertRaises(AccessDeniedEmbedlyException,
                              wagtail_embedly, 'http://www.example.com', key='foo')

    @unittest.skipIf(no_embedly, "Embedly is not installed")
    def test_embedly_404(self):
        with patch('embedly.Embedly.oembed') as oembed:
            oembed.return_value = {'type': 'photo',
                                   'url': 'http://www.example.com',
                                   'error': True,
                                   'error_code': 404}
            self.assertRaises(EmbedNotFoundException,
                              wagtail_embedly, 'http://www.example.com', key='foo')

    @unittest.skipIf(no_embedly, "Embedly is not installed")
    def test_embedly_other_error(self):
        with patch('embedly.Embedly.oembed') as oembed:
            oembed.return_value = {'type': 'photo',
                                   'url': 'http://www.example.com',
                                   'error': True,
                                   'error_code': 999}
            self.assertRaises(EmbedlyException, wagtail_embedly,
                              'http://www.example.com', key='foo')

    @unittest.skipIf(no_embedly, "Embedly is not installed")
    def test_embedly_html_conversion(self):
        with patch('embedly.Embedly.oembed') as oembed:
            oembed.return_value = {'type': 'photo',
                                   'url': 'http://www.example.com'}
            result = wagtail_embedly('http://www.example.com', key='foo')
            self.assertEqual(result['html'], '<img src="http://www.example.com" />')

            oembed.return_value = {'type': 'something else',
                                   'html': '<foo>bar</foo>'}
            result = wagtail_embedly('http://www.example.com', key='foo')
            self.assertEqual(result['html'], '<foo>bar</foo>')

    @unittest.skipIf(no_embedly, "Embedly is not installed")
    def test_embedly_return_value(self):
        with patch('embedly.Embedly.oembed') as oembed:
            oembed.return_value = {'type': 'something else',
                                   'html': '<foo>bar</foo>'}
            result = wagtail_embedly('http://www.example.com', key='foo')
            self.assertEqual(result, {
                'title': '',
                'author_name': '',
                'provider_name': '',
                'type': 'something else',
                'thumbnail_url': None,
                'width': None,
                'height': None,
                'html': '<foo>bar</foo>'})

            oembed.return_value = {'type': 'something else',
                                   'author_name': 'Alice',
                                   'provider_name': 'Bob',
                                   'title': 'foo',
                                   'thumbnail_url': 'http://www.example.com',
                                   'width': 100,
                                   'height': 100,
                                   'html': '<foo>bar</foo>'}
            result = wagtail_embedly('http://www.example.com', key='foo')
            self.assertEqual(result, {'type': 'something else',
                                      'author_name': 'Alice',
                                      'provider_name': 'Bob',
                                      'title': 'foo',
                                      'thumbnail_url': 'http://www.example.com',
                                      'width': 100,
                                      'height': 100,
                                      'html': '<foo>bar</foo>'})


class TestOembed(TestCase):
    def setUp(self):
        class DummyResponse(object):
            def read(self):
                return "foo"
        self.dummy_response = DummyResponse()

    def test_oembed_invalid_provider(self):
        self.assertRaises(EmbedNotFoundException, wagtail_oembed, "foo")

    def test_oembed_invalid_request(self):
        config = {'side_effect': URLError('foo')}
        with patch.object(six.moves.urllib.request, 'urlopen', **config) as urlopen:
            self.assertRaises(EmbedNotFoundException, wagtail_oembed,
                              "http://www.youtube.com/watch/")

    @patch('six.moves.urllib.request.urlopen')
    @patch('json.loads')
    def test_oembed_photo_request(self, loads, urlopen) :
        urlopen.return_value = self.dummy_response
        loads.return_value = {'type': 'photo',
                              'url': 'http://www.example.com'}
        result = wagtail_oembed("http://www.youtube.com/watch/")
        self.assertEqual(result['type'], 'photo')
        self.assertEqual(result['html'], '<img src="http://www.example.com" />')
        loads.assert_called_with("foo")

    @patch('six.moves.urllib.request.urlopen')
    @patch('json.loads')
    def test_oembed_return_values(self, loads, urlopen):
        urlopen.return_value = self.dummy_response
        loads.return_value = {
            'type': 'something',
            'url': 'http://www.example.com',
            'title': 'test_title',
            'author_name': 'test_author',
            'provider_name': 'test_provider_name',
            'thumbnail_url': 'test_thumbail_url',
            'width': 'test_width',
            'height': 'test_height',
            'html': 'test_html'
        }
        result = wagtail_oembed("http://www.youtube.com/watch/")
        self.assertEqual(result, {
            'type': 'something',
            'title': 'test_title',
            'author_name': 'test_author',
            'provider_name': 'test_provider_name',
            'thumbnail_url': 'test_thumbail_url',
            'width': 'test_width',
            'height': 'test_height',
            'html': 'test_html'
        })


class TestEmbedFilter(TestCase):
    def setUp(self):
        class DummyResponse(object):
            def read(self):
                return "foo"
        self.dummy_response = DummyResponse()

    @patch('six.moves.urllib.request.urlopen')
    @patch('json.loads')
    def test_valid_embed(self, loads, urlopen):
        urlopen.return_value = self.dummy_response
        loads.return_value = {'type': 'photo',
                              'url': 'http://www.example.com'}
        result = embed_filter('http://www.youtube.com/watch/')
        self.assertEqual(result, '<img src="http://www.example.com" />')

    @patch('six.moves.urllib.request.urlopen')
    @patch('json.loads')
    def test_render_filter(self, loads, urlopen):
        urlopen.return_value = self.dummy_response
        loads.return_value = {'type': 'photo',
                              'url': 'http://www.example.com'}
        temp = template.Template('{% load wagtailembeds_tags %}{{ "http://www.youtube.com/watch/"|embed }}')
        context = template.Context()
        result = temp.render(context)
        self.assertEqual(result, '<img src="http://www.example.com" />')

    @patch('six.moves.urllib.request.urlopen')
    @patch('json.loads')
    def test_render_filter_nonexistent_type(self, loads, urlopen):
        urlopen.return_value = self.dummy_response
        loads.return_value = {'type': 'foo',
                              'url': 'http://www.example.com'}
        temp = template.Template('{% load wagtailembeds_tags %}{{ "http://www.youtube.com/watch/"|embed }}')
        context = template.Context()
        result = temp.render(context)
        self.assertEqual(result, '')


class TestEmbedlyFilter(TestEmbedFilter):
    def setUp(self):
        class DummyResponse(object):
            def read(self):
                return "foo"
        self.dummy_response = DummyResponse()

    @patch('six.moves.urllib.request.urlopen')
    @patch('json.loads')
    def test_valid_embed(self, loads, urlopen):
        urlopen.return_value = self.dummy_response
        loads.return_value = {'type': 'photo',
                              'url': 'http://www.example.com'}
        result = embedly_filter('http://www.youtube.com/watch/')
        self.assertEqual(result, '<img src="http://www.example.com" />')

    @patch('six.moves.urllib.request.urlopen')
    @patch('json.loads')
    def test_render_filter(self, loads, urlopen):
        urlopen.return_value = self.dummy_response
        loads.return_value = {'type': 'photo',
                              'url': 'http://www.example.com'}
        temp = template.Template('{% load embed_filters %}{{ "http://www.youtube.com/watch/"|embedly }}')
        context = template.Context()
        result = temp.render(context)
        self.assertEqual(result, '<img src="http://www.example.com" />')

    @patch('six.moves.urllib.request.urlopen')
    @patch('json.loads')
    def test_render_filter_nonexistent_type(self, loads, urlopen):
        urlopen.return_value = self.dummy_response
        loads.return_value = {'type': 'foo',
                              'url': 'http://www.example.com'}
        temp = template.Template('{% load embed_filters %}{{ "http://www.youtube.com/watch/"|embedly }}')
        context = template.Context()
        result = temp.render(context)
        self.assertEqual(result, '')
