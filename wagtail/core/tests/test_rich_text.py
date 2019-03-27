from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from wagtail.core.rich_text import RichText, expand_db_html
from wagtail.core.rich_text.feature_registry import FeatureRegistry
from wagtail.core.rich_text.pages import PageLinkHandler
from wagtail.core.rich_text.rewriters import LinkRewriter, extract_attrs


class TestPageLinktypeHandler(TestCase):
    fixtures = ['test.json']

    def test_expand_db_attributes_page_does_not_exist(self):
        result = PageLinkHandler.expand_db_attributes({'id': 0})
        self.assertEqual(result, '<a>')

    def test_expand_db_attributes_not_for_editor(self):
        result = PageLinkHandler.expand_db_attributes({'id': 1})
        self.assertEqual(result, '<a href="None">')


class TestExtractAttrs(TestCase):
    def test_extract_attr(self):
        html = '<a foo="bar" baz="quux">snowman</a>'
        result = extract_attrs(html)
        self.assertEqual(result, {'foo': 'bar', 'baz': 'quux'})


class TestExpandDbHtml(TestCase):
    def test_expand_db_html_with_linktype(self):
        html = '<a id="1" linktype="document">foo</a>'
        result = expand_db_html(html)
        self.assertEqual(result, '<a>foo</a>')

    def test_expand_db_html_no_linktype(self):
        html = '<a id="1">foo</a>'
        result = expand_db_html(html)
        self.assertEqual(result, '<a id="1">foo</a>')

    @patch('wagtail.embeds.embeds.get_embed')
    def test_expand_db_html_with_embed(self, get_embed):
        from wagtail.embeds.models import Embed
        get_embed.return_value = Embed(html='test html')
        html = '<embed embedtype="media" url="http://www.youtube.com/watch" />'
        result = expand_db_html(html)
        self.assertIn('test html', result)


class TestRichTextValue(TestCase):
    fixtures = ['test.json']

    def test_construct_with_none(self):
        value = RichText(None)
        self.assertEqual(value.source, '')

    def test_construct_with_empty_string(self):
        value = RichText('')
        self.assertEqual(value.source, '')

    def test_construct_with_nonempty_string(self):
        value = RichText('<p>hello world</p>')
        self.assertEqual(value.source, '<p>hello world</p>')

    def test_render(self):
        value = RichText('<p>Merry <a linktype="page" id="4">Christmas</a>!</p>')
        result = str(value)
        self.assertEqual(
            result,
            '<div class="rich-text"><p>Merry <a href="/events/christmas/">Christmas</a>!</p></div>'
        )

    def test_evaluate_value(self):
        value = RichText(None)
        self.assertFalse(value)

        value = RichText('<p>wagtail</p>')
        self.assertTrue(value)


class TestFeatureRegistry(TestCase):
    def test_register_rich_text_features_hook(self):
        # testapp/wagtail_hooks.py defines a 'blockquote' rich text feature with a hallo.js
        # plugin, via the register_rich_text_features hook; test that we can retrieve it here
        features = FeatureRegistry()
        quotation = features.get_editor_plugin('hallo', 'quotation')
        self.assertEqual(quotation.name, 'halloquotation')

    def test_missing_editor_plugin_returns_none(self):
        features = FeatureRegistry()
        self.assertIsNone(
            features.get_editor_plugin('made_up_editor', 'blockquote')
        )
        self.assertIsNone(
            features.get_editor_plugin('hallo', 'made_up_feature')
        )

    def test_legacy_register_link_type(self):
        User = get_user_model()
        User.objects.create(username='wagtail', email='hello@wagtail.io')

        def user_expand_db_attributes(attrs):
            user = User.objects.get(username=attrs['username'])
            return '<a href="mailto:%s">' % user.email

        features = FeatureRegistry()
        features.register_link_type('user', user_expand_db_attributes)

        handler = features.get_link_types()['user']
        self.assertEqual(
            handler.expand_db_attributes({'username': 'wagtail'}),
            '<a href="mailto:hello@wagtail.io">'
        )

    def test_legacy_register_embed_type(self):
        def embed_expand_db_attributes(attrs):
            return '<div>embedded content: %s</div>' % attrs['content']

        features = FeatureRegistry()
        features.register_embed_type('mock_embed', embed_expand_db_attributes)

        handler = features.get_embed_types()['mock_embed']
        self.assertEqual(
            handler.expand_db_attributes({'content': 'foo'}),
            '<div>embedded content: foo</div>'
        )


class TestLinkRewriterTagReplacing(TestCase):
    def test_should_follow_default_behaviour(self):
        # we always have default `page` rules registered.
        rules = {
            'page': lambda attrs: '<a href="/article/{}">'.format(attrs['id'])
        }
        rewriter = LinkRewriter(rules)

        page_type_link = rewriter('<a linktype="page" id="3">')
        self.assertEqual(page_type_link, '<a href="/article/3">')

        # but it should also be able to handle other supported
        # link types (email, external) even if no rules is provided
        external_type_link = rewriter('<a href="https://wagtail.io/">')
        self.assertEqual(external_type_link, '<a href="https://wagtail.io/">')
        email_type_link = rewriter('<a href="mailto:test@wagtail.io">')
        self.assertEqual(email_type_link, '<a href="mailto:test@wagtail.io">')

        # As well as link which don't have any linktypes
        link_without_linktype = rewriter('<a data-link="https://wagtail.io">')
        self.assertEqual(link_without_linktype, '<a data-link="https://wagtail.io">')

        # But should not handle if a custom linktype is mentioned but no
        # associate rules are registered.
        link_with_custom_linktype = rewriter('<a linktype="custom" href="https://wagtail.io">')
        self.assertNotEqual(link_with_custom_linktype, '<a href="https://wagtail.io">')
        self.assertEqual(link_with_custom_linktype, '<a>')


    def test_supported_type_should_follow_given_rules(self):
        # we always have `page` rules by default
        rules = {
            'page': lambda attrs: '<a href="/article/{}">'.format(attrs['id']),
            'external': lambda attrs: '<a rel="nofollow" href="{}">'.format(attrs['href']),
            'email': lambda attrs: '<a data-email="true" href="{}">'.format(attrs['href']),
            'custom': lambda attrs: '<a data-phone="true" href="{}">'.format(attrs['href']),
        }
        rewriter = LinkRewriter(rules)

        page_type_link = rewriter('<a linktype="page" id="3">')
        self.assertEqual(page_type_link, '<a href="/article/3">')

        # It should call appropriate rule supported linktypes (external or email)
        # based on the href value
        external_type_link = rewriter('<a href="https://wagtail.io/">')
        self.assertEqual(external_type_link, '<a rel="nofollow" href="https://wagtail.io/">')
        external_type_link_http = rewriter('<a href="http://wagtail.io/">')
        self.assertEqual(external_type_link_http, '<a rel="nofollow" href="http://wagtail.io/">')
        email_type_link = rewriter('<a href="mailto:test@wagtail.io">')
        self.assertEqual(email_type_link, '<a data-email="true" href="mailto:test@wagtail.io">')

        # But not the unsupported ones.
        link_with_no_linktype = rewriter('<a href="tel:+4917640206387">')
        self.assertEqual(link_with_no_linktype, '<a href="tel:+4917640206387">')

        # Also call the rule if a custom linktype is mentioned.
        link_with_custom_linktype = rewriter('<a linktype="custom" href="tel:+4917640206387">')
        self.assertEqual(link_with_custom_linktype, '<a data-phone="true" href="tel:+4917640206387">')
