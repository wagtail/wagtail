from mock import patch
import urllib2

try:
    from embedly import Embedly
    patch_me = 'embedly.Embedly.oembed'
except ImportError:
    patch_me = 'wagtail.wagtailembeds.embeds.MockEmbedly.oembed'

from django.test import TestCase
from django.test.client import Client

from wagtail.tests.utils import login
from wagtail.wagtailembeds import get_embed
from wagtail.wagtailembeds.embeds import (
    embedly,
    EmbedNotFoundException,
    EmbedlyException,
    AccessDeniedEmbedlyException,
    MockEmbedly
)
from wagtail.wagtailembeds.embeds import oembed as wagtail_oembed


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


class TestChooser(TestCase):
    def setUp(self):
        # login
        login(self.client)

    def test_chooser(self):
        r = self.client.get('/admin/embeds/chooser/')
        self.assertEqual(r.status_code, 200)

        # TODO: Test submitting


class TestEmbedly(TestCase):
    @patch(patch_me)
    def test_embedly_oembed_called_with_correct_arguments(self, oembed):
        oembed.return_value = {'type': 'photo',
                               'url': 'http://www.example.com'}

        embedly('http://www.example.com', key='foo')
        oembed.assert_called_with('http://www.example.com', better=False)

        embedly('http://www.example.com', max_width=100, key='foo')
        oembed.assert_called_with('http://www.example.com', maxwidth=100, better=False)

    @patch(patch_me)
    def test_embedly_errors(self, oembed):
        oembed.return_value = {'type': 'photo',
                               'url': 'http://www.example.com',
                               'error': True,
                               'error_code': 401}
        self.assertRaises(AccessDeniedEmbedlyException,
                          embedly, 'http://www.example.com', key='foo')

        oembed.return_value['error_code'] = 403
        self.assertRaises(AccessDeniedEmbedlyException,
                          embedly, 'http://www.example.com', key='foo')

        oembed.return_value['error_code'] = 404
        self.assertRaises(EmbedNotFoundException,
                          embedly, 'http://www.example.com', key='foo')

        oembed.return_value['error_code'] = 999
        self.assertRaises(EmbedlyException, embedly,
                          'http://www.example.com', key='foo')

    @patch(patch_me)
    def test_embedly_html_conversion(self, oembed):
        oembed.return_value = {'type': 'photo',
                               'url': 'http://www.example.com'}
        result = embedly('http://www.example.com', key='foo')
        self.assertEqual(result['html'], '<img src="http://www.example.com" />')

        oembed.return_value = {'type': 'something else',
                               'html': '<foo>bar</foo>'}
        result = embedly('http://www.example.com', key='foo')
        self.assertEqual(result['html'], '<foo>bar</foo>')

    @patch(patch_me)
    def test_embedly_return_value(self, oembed):
        oembed.return_value = {'type': 'something else',
                               'html': '<foo>bar</foo>'}
        result = embedly('http://www.example.com', key='foo')
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
        result = embedly('http://www.example.com', key='foo')
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
        config = {'side_effect': urllib2.URLError('foo')}
        with patch.object(urllib2, 'urlopen', **config) as urlopen:
            self.assertRaises(EmbedNotFoundException, wagtail_oembed,
                              "http://www.youtube.com/watch/")

    @patch('urllib2.urlopen')
    @patch('json.loads')
    def test_oembed_photo_request(self, loads, urlopen) :
        urlopen.return_value = self.dummy_response
        loads.return_value = {'type': 'photo',
                              'url': 'http://www.example.com'}
        result = wagtail_oembed("http://www.youtube.com/watch/")
        self.assertEqual(result['type'], 'photo')
        self.assertEqual(result['html'], '<img src="http://www.example.com" />')
        loads.assert_called_with("foo")

    @patch('urllib2.urlopen')
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
