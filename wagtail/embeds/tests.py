import json
import unittest
import urllib.request
from urllib.error import URLError

from bs4 import BeautifulSoup
from django import template
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from mock import patch

from wagtail.core import blocks
from wagtail.core.rich_text import expand_db_html
from wagtail.embeds import oembed_providers
from wagtail.embeds.blocks import EmbedBlock, EmbedValue
from wagtail.embeds.embeds import get_embed
from wagtail.embeds.exceptions import EmbedNotFoundException, EmbedUnsupportedProviderException
from wagtail.embeds.finders import get_finders
from wagtail.embeds.finders.embedly import EmbedlyFinder as EmbedlyFinder
from wagtail.embeds.finders.embedly import AccessDeniedEmbedlyException, EmbedlyException
from wagtail.embeds.finders.oembed import OEmbedFinder as OEmbedFinder
from wagtail.embeds.models import Embed
from wagtail.embeds.rich_text import MediaEmbedHandler, media_embedtype_handler
from wagtail.embeds.templatetags.wagtailembeds_tags import embed_tag
from wagtail.tests.utils import WagtailTestUtils

try:
    import embedly  # noqa
    no_embedly = False
except ImportError:
    no_embedly = True


class TestGetFinders(TestCase):
    def test_defaults_to_oembed(self):
        finders = get_finders()

        self.assertEqual(len(finders), 1)
        self.assertIsInstance(finders[0], OEmbedFinder)

    # New WAGTAILEMBEDS_FINDERS setting

    @override_settings(WAGTAILEMBEDS_FINDERS=[
        {
            'class': 'wagtail.embeds.finders.oembed'
        }
    ])
    def test_new_find_oembed(self):
        finders = get_finders()

        self.assertEqual(len(finders), 1)
        self.assertIsInstance(finders[0], OEmbedFinder)

    @override_settings(WAGTAILEMBEDS_FINDERS=[
        {
            'class': 'wagtail.embeds.finders.embedly',
            'key': 'foo',
        }
    ])
    def test_new_find_embedly(self):
        finders = get_finders()

        self.assertEqual(len(finders), 1)
        self.assertIsInstance(finders[0], EmbedlyFinder)
        self.assertEqual(finders[0].get_key(), 'foo')

    @override_settings(WAGTAILEMBEDS_FINDERS=[
        {
            'class': 'wagtail.embeds.finders.oembed',
            'options': {'foo': 'bar'}
        }
    ])
    def test_new_find_oembed_with_options(self):
        finders = get_finders()

        self.assertEqual(len(finders), 1)
        self.assertIsInstance(finders[0], OEmbedFinder)
        self.assertEqual(finders[0].options, {'foo': 'bar'})


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

        # Check ratio calculations
        self.assertEqual(embed.ratio, 480 / 400)
        self.assertEqual(embed.ratio_css, '120.0%')
        self.assertTrue(embed.is_responsive)

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

    def test_no_html(self):
        def no_html_finder(url, max_width=None):
            """
            A finder which returns everything but HTML
            """
            embed = self.dummy_finder(url, max_width)
            embed['html'] = None
            return embed

        embed = get_embed('www.test.com/1234', max_width=400, finder=no_html_finder)

        self.assertEqual(embed.html, '')

    @override_settings(WAGTAILEMBEDS_FINDERS=[])
    def test_no_finders_available(self):
        with self.assertRaises(EmbedUnsupportedProviderException):
            get_embed('www.test.com/1234', max_width=400)


class TestChooser(TestCase, WagtailTestUtils):
    def setUp(self):
        # login
        self.login()

    def test_chooser(self):
        r = self.client.get('/admin/embeds/chooser/')
        self.assertEqual(r.status_code, 200)

    def test_chooser_with_edit_params(self):
        r = self.client.get('/admin/embeds/chooser/?url=http://example2.com')
        self.assertEqual(r.status_code, 200)
        response_json = json.loads(r.content.decode())
        self.assertEqual(response_json['step'], 'chooser')
        self.assertIn('value="http://example2.com"', response_json['html'])

    @patch('wagtail.embeds.embeds.get_embed')
    def test_submit_valid_embed(self, get_embed):
        get_embed.return_value = Embed(html='<img src="http://www.example.com" />', title="An example embed")

        response = self.client.post(reverse('wagtailembeds:chooser_upload'), {
            'url': 'http://www.example.com/'
        })
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['step'], 'embed_chosen')
        self.assertEqual(response_json['embed_data']['title'], "An example embed")

    @patch('wagtail.embeds.embeds.get_embed')
    def test_submit_unrecognised_embed(self, get_embed):
        get_embed.side_effect = EmbedNotFoundException

        response = self.client.post(reverse('wagtailembeds:chooser_upload'), {
            'url': 'http://www.example.com/'
        })
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['step'], 'chooser')
        self.assertIn("Cannot find an embed for this URL.", response_json['html'])


class TestEmbedly(TestCase):
    @unittest.skipIf(no_embedly, "Embedly is not installed")
    def test_embedly_oembed_called_with_correct_arguments(self):
        with patch('embedly.Embedly.oembed') as oembed:
            oembed.return_value = {'type': 'photo',
                                   'url': 'http://www.example.com'}

            EmbedlyFinder(key='foo').find_embed('http://www.example.com')
            oembed.assert_called_with('http://www.example.com', better=False)

            EmbedlyFinder(key='foo').find_embed('http://www.example.com', max_width=100)
            oembed.assert_called_with('http://www.example.com', maxwidth=100, better=False)

    @unittest.skipIf(no_embedly, "Embedly is not installed")
    def test_embedly_401(self):
        with patch('embedly.Embedly.oembed') as oembed:
            oembed.return_value = {'type': 'photo',
                                   'url': 'http://www.example.com',
                                   'error': True,
                                   'error_code': 401}
            self.assertRaises(AccessDeniedEmbedlyException,
                              EmbedlyFinder(key='foo').find_embed, 'http://www.example.com')

    @unittest.skipIf(no_embedly, "Embedly is not installed")
    def test_embedly_403(self):
        with patch('embedly.Embedly.oembed') as oembed:
            oembed.return_value = {'type': 'photo',
                                   'url': 'http://www.example.com',
                                   'error': True,
                                   'error_code': 403}
            self.assertRaises(AccessDeniedEmbedlyException,
                              EmbedlyFinder(key='foo').find_embed, 'http://www.example.com')

    @unittest.skipIf(no_embedly, "Embedly is not installed")
    def test_embedly_404(self):
        with patch('embedly.Embedly.oembed') as oembed:
            oembed.return_value = {'type': 'photo',
                                   'url': 'http://www.example.com',
                                   'error': True,
                                   'error_code': 404}
            self.assertRaises(EmbedNotFoundException,
                              EmbedlyFinder(key='foo').find_embed, 'http://www.example.com')

    @unittest.skipIf(no_embedly, "Embedly is not installed")
    def test_embedly_other_error(self):
        with patch('embedly.Embedly.oembed') as oembed:
            oembed.return_value = {'type': 'photo',
                                   'url': 'http://www.example.com',
                                   'error': True,
                                   'error_code': 999}
            self.assertRaises(EmbedlyException, EmbedlyFinder(key='foo').find_embed,
                              'http://www.example.com')

    @unittest.skipIf(no_embedly, "Embedly is not installed")
    def test_embedly_html_conversion(self):
        with patch('embedly.Embedly.oembed') as oembed:
            oembed.return_value = {'type': 'photo',
                                   'url': 'http://www.example.com'}
            result = EmbedlyFinder(key='foo').find_embed('http://www.example.com')
            self.assertEqual(result['html'], '<img src="http://www.example.com" />')

            oembed.return_value = {'type': 'something else',
                                   'html': '<foo>bar</foo>'}
            result = EmbedlyFinder(key='foo').find_embed('http://www.example.com')
            self.assertEqual(result['html'], '<foo>bar</foo>')

    @unittest.skipIf(no_embedly, "Embedly is not installed")
    def test_embedly_return_value(self):
        with patch('embedly.Embedly.oembed') as oembed:
            oembed.return_value = {'type': 'something else',
                                   'html': '<foo>bar</foo>'}
            result = EmbedlyFinder(key='foo').find_embed('http://www.example.com')
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
            result = EmbedlyFinder(key='foo').find_embed('http://www.example.com')
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
        class DummyResponse:
            def read(self):
                return b"foo"
        self.dummy_response = DummyResponse()

    def test_oembed_invalid_provider(self):
        self.assertRaises(EmbedNotFoundException, OEmbedFinder().find_embed, "foo")

    def test_oembed_invalid_request(self):
        config = {'side_effect': URLError('foo')}
        with patch.object(urllib.request, 'urlopen', **config):
            self.assertRaises(EmbedNotFoundException, OEmbedFinder().find_embed,
                              "http://www.youtube.com/watch/")

    @patch('urllib.request.urlopen')
    @patch('json.loads')
    def test_oembed_photo_request(self, loads, urlopen):
        urlopen.return_value = self.dummy_response
        loads.return_value = {'type': 'photo',
                              'url': 'http://www.example.com'}
        result = OEmbedFinder().find_embed("http://www.youtube.com/watch/")
        self.assertEqual(result['type'], 'photo')
        self.assertEqual(result['html'], '<img src="http://www.example.com" />')
        loads.assert_called_with("foo")

    @patch('urllib.request.urlopen')
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
        result = OEmbedFinder().find_embed("http://www.youtube.com/watch/")
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

    def test_oembed_accepts_known_provider(self):
        finder = OEmbedFinder(providers=[oembed_providers.youtube])
        self.assertTrue(finder.accept("http://www.youtube.com/watch/"))

    def test_oembed_doesnt_accept_unknown_provider(self):
        finder = OEmbedFinder(providers=[oembed_providers.twitter])
        self.assertFalse(finder.accept("http://www.youtube.com/watch/"))

    @patch('urllib.request.urlopen')
    @patch('json.loads')
    def test_endpoint_with_format_param(self, loads, urlopen):
        urlopen.return_value = self.dummy_response
        loads.return_value = {'type': 'video',
                              'url': 'http://www.example.com'}
        result = OEmbedFinder().find_embed("https://vimeo.com/217403396")
        self.assertEqual(result['type'], 'video')
        request = urlopen.call_args[0][0]
        self.assertEqual(request.get_full_url().split('?')[0], "http://www.vimeo.com/api/oembed.json")


class TestEmbedTag(TestCase):
    @patch('wagtail.embeds.embeds.get_embed')
    def test_direct_call(self, get_embed):
        get_embed.return_value = Embed(html='<img src="http://www.example.com" />')

        result = embed_tag('http://www.youtube.com/watch/')

        self.assertEqual(result, '<img src="http://www.example.com" />')

    @patch('wagtail.embeds.embeds.get_embed')
    def test_call_from_template(self, get_embed):
        get_embed.return_value = Embed(html='<img src="http://www.example.com" />')

        temp = template.Template('{% load wagtailembeds_tags %}{% embed "http://www.youtube.com/watch/" %}')
        result = temp.render(template.Context())

        self.assertEqual(result, '<img src="http://www.example.com" />')

    @patch('wagtail.embeds.embeds.get_embed')
    def test_catches_embed_not_found(self, get_embed):
        get_embed.side_effect = EmbedNotFoundException

        temp = template.Template('{% load wagtailembeds_tags %}{% embed "http://www.youtube.com/watch/" %}')
        result = temp.render(template.Context())

        self.assertEqual(result, '')


class TestEmbedBlock(TestCase):
    def test_deserialize(self):
        """
        Deserialising the JSONish value of an EmbedBlock (a URL) should give us an EmbedValue
        for that URL
        """
        block = EmbedBlock(required=False)

        block_val = block.to_python('http://www.example.com/foo')
        self.assertIsInstance(block_val, EmbedValue)
        self.assertEqual(block_val.url, 'http://www.example.com/foo')

        # empty values should yield None
        empty_block_val = block.to_python('')
        self.assertEqual(empty_block_val, None)

    def test_serialize(self):
        block = EmbedBlock(required=False)

        block_val = EmbedValue('http://www.example.com/foo')
        serialized_val = block.get_prep_value(block_val)
        self.assertEqual(serialized_val, 'http://www.example.com/foo')

        serialized_empty_val = block.get_prep_value(None)
        self.assertEqual(serialized_empty_val, '')

    @patch('wagtail.embeds.embeds.get_embed')
    def test_render(self, get_embed):
        get_embed.return_value = Embed(html='<h1>Hello world!</h1>')

        block = EmbedBlock()
        block_val = block.to_python('http://www.example.com/foo')

        temp = template.Template('embed: {{ embed }}')
        context = template.Context({'embed': block_val})
        result = temp.render(context)

        # Check that the embed was in the returned HTML
        self.assertIn('<h1>Hello world!</h1>', result)

        # Check that get_embed was called correctly
        get_embed.assert_any_call('http://www.example.com/foo')

    @patch('wagtail.embeds.embeds.get_embed')
    def test_render_within_structblock(self, get_embed):
        """
        When rendering the value of an EmbedBlock directly in a template
        (as happens when accessing it as a child of a StructBlock), the
        proper embed output should be rendered, not the URL.
        """
        get_embed.return_value = Embed(html='<h1>Hello world!</h1>')

        block = blocks.StructBlock([
            ('title', blocks.CharBlock()),
            ('embed', EmbedBlock()),
        ])

        block_val = block.to_python({'title': 'A test', 'embed': 'http://www.example.com/foo'})

        temp = template.Template('embed: {{ self.embed }}')
        context = template.Context({'self': block_val})
        result = temp.render(context)

        self.assertIn('<h1>Hello world!</h1>', result)

        # Check that get_embed was called correctly
        get_embed.assert_any_call('http://www.example.com/foo')

    def test_render_form(self):
        """
        The form field for an EmbedBlock should be a text input containing
        the URL
        """
        block = EmbedBlock()

        form_html = block.render_form(EmbedValue('http://www.example.com/foo'), prefix='myembed')
        self.assertIn('<input ', form_html)
        self.assertIn('value="http://www.example.com/foo"', form_html)

    def test_value_from_form(self):
        """
        EmbedBlock should be able to turn a URL submitted as part of a form
        back into an EmbedValue
        """
        block = EmbedBlock(required=False)

        block_val = block.value_from_datadict({'myembed': 'http://www.example.com/foo'}, {}, prefix='myembed')
        self.assertIsInstance(block_val, EmbedValue)
        self.assertEqual(block_val.url, 'http://www.example.com/foo')

        # empty value should result in None
        empty_val = block.value_from_datadict({'myembed': ''}, {}, prefix='myembed')
        self.assertEqual(empty_val, None)

    def test_default(self):
        block1 = EmbedBlock()
        self.assertEqual(block1.get_default(), None)

        block2 = EmbedBlock(default='')
        self.assertEqual(block2.get_default(), None)

        block3 = EmbedBlock(default=None)
        self.assertEqual(block3.get_default(), None)

        block4 = EmbedBlock(default='http://www.example.com/foo')
        self.assertIsInstance(block4.get_default(), EmbedValue)
        self.assertEqual(block4.get_default().url, 'http://www.example.com/foo')

        block5 = EmbedBlock(default=EmbedValue('http://www.example.com/foo'))
        self.assertIsInstance(block5.get_default(), EmbedValue)
        self.assertEqual(block5.get_default().url, 'http://www.example.com/foo')

    def test_clean(self):
        required_block = EmbedBlock()
        nonrequired_block = EmbedBlock(required=False)

        # a valid EmbedValue should return the same value on clean
        cleaned_value = required_block.clean(EmbedValue('http://www.example.com/foo'))
        self.assertIsInstance(cleaned_value, EmbedValue)
        self.assertEqual(cleaned_value.url, 'http://www.example.com/foo')

        cleaned_value = nonrequired_block.clean(EmbedValue('http://www.example.com/foo'))
        self.assertIsInstance(cleaned_value, EmbedValue)
        self.assertEqual(cleaned_value.url, 'http://www.example.com/foo')

        # None should only be accepted for nonrequired blocks
        cleaned_value = nonrequired_block.clean(None)
        self.assertEqual(cleaned_value, None)

        with self.assertRaises(ValidationError):
            required_block.clean(None)


class TestMediaEmbedHandler(TestCase):
    def test_get_db_attributes(self):
        soup = BeautifulSoup('<b data-url="test-url">foo</b>', 'html5lib')
        tag = soup.b
        result = MediaEmbedHandler.get_db_attributes(tag)
        self.assertEqual(result,
                         {'url': 'test-url'})

    @patch('wagtail.embeds.embeds.get_embed')
    def test_expand_db_attributes_for_editor(self, get_embed):
        get_embed.return_value = Embed(
            url='http://www.youtube.com/watch/',
            max_width=None,
            type='video',
            html='test html',
            title='test title',
            author_name='test author name',
            provider_name='test provider name',
            thumbnail_url='http://test/thumbnail.url',
            width=1000,
            height=1000,
        )

        result = MediaEmbedHandler.expand_db_attributes(
            {'url': 'http://www.youtube.com/watch/'}
        )
        self.assertIn(
            (
                '<div class="embed-placeholder" contenteditable="false" data-embedtype="media"'
                ' data-url="http://www.youtube.com/watch/">'
            ),
            result
        )
        self.assertIn('<h3>test title</h3>', result)
        self.assertIn('<p>URL: http://www.youtube.com/watch/</p>', result)
        self.assertIn('<p>Provider: test provider name</p>', result)
        self.assertIn('<p>Author: test author name</p>', result)
        self.assertIn('<img src="http://test/thumbnail.url" alt="test title">', result)

    @patch('wagtail.embeds.embeds.get_embed')
    def test_test_expand_db_attributes_for_editor_catches_embed_not_found(self, get_embed):
        get_embed.side_effect = EmbedNotFoundException

        result = MediaEmbedHandler.expand_db_attributes(
            {'url': 'http://www.youtube.com/watch/'},
        )

        self.assertEqual(result, '')

    @patch('wagtail.embeds.embeds.get_embed')
    def test_expand_db_attributes(self, get_embed):
        get_embed.return_value = Embed(
            url='http://www.youtube.com/watch/',
            max_width=None,
            type='video',
            html='test html',
            title='test title',
            author_name='test author name',
            provider_name='test provider name',
            thumbnail_url='htto://test/thumbnail.url',
            width=1000,
            height=1000,
        )

        result = media_embedtype_handler(
            {'url': 'http://www.youtube.com/watch/'}
        )
        self.assertIn('test html', result)

    @patch('wagtail.embeds.embeds.get_embed')
    def test_expand_db_attributes_catches_embed_not_found(self, get_embed):
        get_embed.side_effect = EmbedNotFoundException

        result = media_embedtype_handler(
            {'url': 'http://www.youtube.com/watch/'}
        )

        self.assertEqual(result, '')

    @patch('wagtail.embeds.embeds.get_embed')
    def test_expand_html_escaping_end_to_end(self, get_embed):
        get_embed.return_value = Embed(
            url='http://www.youtube.com/watch/',
            max_width=None,
            type='video',
            html='test html',
            title='test title',
            author_name='test author name',
            provider_name='test provider name',
            thumbnail_url='htto://test/thumbnail.url',
            width=1000,
            height=1000,
        )

        result = expand_db_html('<p>1 2 <embed embedtype="media" url="https://www.youtube.com/watch?v=O7D-1RG-VRk&amp;t=25" /> 3 4</p>')
        self.assertIn('test html', result)
        get_embed.assert_called_with('https://www.youtube.com/watch?v=O7D-1RG-VRk&t=25')
