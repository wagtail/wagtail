from unittest.mock import patch

from django.test import TestCase, override_settings

from wagtail.embeds.exceptions import EmbedNotFoundException
from wagtail.embeds.models import Embed
from wagtail.embeds.rich_text import MediaEmbedHandler as FrontendMediaEmbedHandler
from wagtail.embeds.rich_text.editor_html import (
    MediaEmbedHandler as EditorHtmlMediaEmbedHandler,
)
from wagtail.rich_text import expand_db_html
from wagtail.test.utils import WagtailTestUtils


class TestEditorHtmlMediaEmbedHandler(WagtailTestUtils, TestCase):
    def test_get_db_attributes(self):
        soup = self.get_soup('<b data-url="test-url">foo</b>')
        tag = soup.b
        result = EditorHtmlMediaEmbedHandler.get_db_attributes(tag)
        self.assertEqual(result, {"url": "test-url"})

    @patch("wagtail.embeds.embeds.get_embed")
    def test_expand_db_attributes_for_editor(self, get_embed):
        get_embed.return_value = Embed(
            url="http://www.youtube.com/watch/",
            max_width=None,
            type="video",
            html="test html",
            title="test title",
            author_name="test author name",
            provider_name="test provider name",
            thumbnail_url="http://test/thumbnail.url",
            width=1000,
            height=1000,
        )

        result = EditorHtmlMediaEmbedHandler.expand_db_attributes(
            {
                "url": "http://www.youtube.com/watch/",
            }
        )
        self.assertIn(
            (
                '<div class="embed-placeholder" contenteditable="false" data-embedtype="media"'
                ' data-url="http://www.youtube.com/watch/">'
            ),
            result,
        )
        self.assertIn("<h3>test title</h3>", result)
        self.assertIn("<p>URL: http://www.youtube.com/watch/</p>", result)
        self.assertIn("<p>Provider: test provider name</p>", result)
        self.assertIn("<p>Author: test author name</p>", result)
        self.assertIn('<img src="http://test/thumbnail.url" alt="test title">', result)

    @patch("wagtail.embeds.embeds.get_embed")
    def test_expand_db_attributes_for_editor_catches_embed_not_found(self, get_embed):
        get_embed.side_effect = EmbedNotFoundException
        result = EditorHtmlMediaEmbedHandler.expand_db_attributes(
            {
                "url": "http://www.youtube.com/watch/",
            }
        )
        self.assertEqual(result, "")


class TestFrontendMediaEmbedHandler(TestCase):
    @override_settings(WAGTAILEMBEDS_RESPONSIVE_HTML=True)
    @patch("wagtail.embeds.embeds.get_embed")
    def test_expand_db_attributes_for_frontend_responsive(self, get_embed):
        get_embed.return_value = Embed(
            url="http://www.youtube.com/watch/",
            max_width=None,
            type="video",
            html="test html",
            title="test title",
            author_name="test author name",
            provider_name="test provider name",
            thumbnail_url="http://test/thumbnail.url",
            width=1000,
            height=1000,
        )

        result = FrontendMediaEmbedHandler.expand_db_attributes(
            {
                "url": "http://www.youtube.com/watch/",
            }
        )
        self.assertIn("test html", result)
        self.assertIn('class="responsive-object"', result)

    @patch("wagtail.embeds.embeds.get_embed")
    def test_expand_db_attributes_for_frontend_nonresponsive(self, get_embed):
        get_embed.return_value = Embed(
            url="http://www.youtube.com/watch/",
            max_width=None,
            type="video",
            html="test html",
            title="test title",
            author_name="test author name",
            provider_name="test provider name",
            thumbnail_url="http://test/thumbnail.url",
            width=1000,
            height=1000,
        )

        result = FrontendMediaEmbedHandler.expand_db_attributes(
            {
                "url": "http://www.youtube.com/watch/",
            }
        )
        self.assertIn("test html", result)
        self.assertNotIn('class="responsive-object"', result)

    @patch("wagtail.embeds.embeds.get_embed")
    def test_expand_db_attributes_for_frontend_catches_embed_not_found(self, get_embed):
        get_embed.side_effect = EmbedNotFoundException
        result = FrontendMediaEmbedHandler.expand_db_attributes(
            {
                "url": "http://www.youtube.com/watch/",
            }
        )
        self.assertEqual(result, "")

    @patch("wagtail.embeds.embeds.get_embed")
    def test_expand_html_escaping_end_to_end(self, get_embed):
        get_embed.return_value = Embed(
            url="http://www.youtube.com/watch/",
            max_width=None,
            type="video",
            html="test html",
            title="test title",
            author_name="test author name",
            provider_name="test provider name",
            thumbnail_url="http://test/thumbnail.url",
            width=1000,
            height=1000,
        )

        result = expand_db_html(
            '<p>1 2 <embed embedtype="media" url="https://www.youtube.com/watch?v=O7D-1RG-VRk&amp;t=25" /> 3 4</p>'
        )
        self.assertIn("test html", result)
        get_embed.assert_called_with(
            "https://www.youtube.com/watch?v=O7D-1RG-VRk&t=25", None, None
        )
