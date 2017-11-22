from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from wagtail.tests.testapp.models import SingleEventPage
from wagtail.tests.testapp.rich_text import CustomRichTextArea
from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailadmin.rich_text import HalloRichTextArea, get_rich_text_editor_widget
from wagtail.wagtailcore.blocks import RichTextBlock
from wagtail.wagtailcore.models import Page, get_page_models
from wagtail.wagtailcore.rich_text import RichText


class BaseRichTextEditHandlerTestCase(TestCase):
    def _clear_edit_handler_cache(self):
        """
        These tests generate new EditHandlers with different settings. The
        cached edit handlers should be cleared before and after each test run
        to ensure that no changes leak through to other tests.
        """
        from wagtail.tests.testapp.models import DefaultRichBlockFieldPage

        rich_text_block = (DefaultRichBlockFieldPage.get_edit_handler()
                           .get_form_class().base_fields['body'].block
                           .child_blocks['rich_text'])
        if hasattr(rich_text_block, 'field'):
            del rich_text_block.field

        for page_class in get_page_models():
            page_class.get_edit_handler.cache_clear()

    def setUp(self):
        super(BaseRichTextEditHandlerTestCase, self).setUp()
        self._clear_edit_handler_cache()

    def tearDown(self):
        self._clear_edit_handler_cache()
        super(BaseRichTextEditHandlerTestCase, self).tearDown()


class TestGetRichTextEditorWidget(TestCase):
    @override_settings()
    def test_default(self):
        # Simulate the absence of a setting
        if hasattr(settings, 'WAGTAILADMIN_RICH_TEXT_EDITORS'):
            del settings.WAGTAILADMIN_RICH_TEXT_EDITORS

        self.assertIsInstance(get_rich_text_editor_widget(), HalloRichTextArea)

    @override_settings(WAGTAILADMIN_RICH_TEXT_EDITORS={
        'default': {
            'WIDGET': 'wagtail.tests.testapp.rich_text.CustomRichTextArea'
        },
    })
    def test_overridden_default_editor(self):
        self.assertIsInstance(get_rich_text_editor_widget(), CustomRichTextArea)

    @override_settings(WAGTAILADMIN_RICH_TEXT_EDITORS={
        'custom': {
            'WIDGET': 'wagtail.tests.testapp.rich_text.CustomRichTextArea'
        },
    })
    def test_custom_editor_without_default(self):
        self.assertIsInstance(get_rich_text_editor_widget('custom'), CustomRichTextArea)

    @override_settings(WAGTAILADMIN_RICH_TEXT_EDITORS={
        'default': {
            'WIDGET': 'wagtail.wagtailadmin.rich_text.HalloRichTextArea'
        },
        'custom': {
            'WIDGET': 'wagtail.tests.testapp.rich_text.CustomRichTextArea'
        },
    })
    def test_custom_editor_with_default(self):
        self.assertIsInstance(get_rich_text_editor_widget(), HalloRichTextArea)
        self.assertIsInstance(get_rich_text_editor_widget('custom'), CustomRichTextArea)


@override_settings()
class TestDefaultRichText(BaseRichTextEditHandlerTestCase, WagtailTestUtils):

    def setUp(self):
        super(TestDefaultRichText, self).setUp()
        # Find root page
        self.root_page = Page.objects.get(id=2)

        self.login()

        # Simulate the absence of a setting
        if hasattr(settings, 'WAGTAILADMIN_RICH_TEXT_EDITORS'):
            del settings.WAGTAILADMIN_RICH_TEXT_EDITORS

    def test_default_editor_in_rich_text_field(self):
        response = self.client.get(reverse(
            'wagtailadmin_pages:add', args=('tests', 'defaultrichtextfieldpage', self.root_page.id)
        ))

        # Check status code
        self.assertEqual(response.status_code, 200)

        # Check that hallo (default editor by now)
        self.assertContains(response, 'makeHalloRichTextEditable("id_body",')

        # check that media for the default hallo features (but not others) is being imported
        self.assertContains(response, 'wagtaildocs/js/hallo-plugins/hallo-wagtaildoclink.js')
        self.assertNotContains(response, 'testapp/js/hallo-blockquote.js')

    def test_default_editor_in_rich_text_block(self):
        response = self.client.get(reverse(
            'wagtailadmin_pages:add', args=('tests', 'defaultrichblockfieldpage', self.root_page.id)
        ))

        # Check status code
        self.assertEqual(response.status_code, 200)

        # Check that hallo (default editor by now)
        self.assertContains(response, 'makeHalloRichTextEditable("__PREFIX__-value",')

        # check that media for the default hallo features (but not others) is being imported
        self.assertContains(response, 'wagtaildocs/js/hallo-plugins/hallo-wagtaildoclink.js')
        self.assertNotContains(response, 'testapp/js/hallo-blockquote.js')


@override_settings(WAGTAILADMIN_RICH_TEXT_EDITORS={
    'default': {
        'WIDGET': 'wagtail.tests.testapp.rich_text.CustomRichTextArea'
    },
})
class TestOverriddenDefaultRichText(BaseRichTextEditHandlerTestCase, WagtailTestUtils):

    def setUp(self):
        super(TestOverriddenDefaultRichText, self).setUp()

        # Find root page
        self.root_page = Page.objects.get(id=2)

        self.login()

    def test_overridden_default_editor_in_rich_text_field(self):
        response = self.client.get(reverse(
            'wagtailadmin_pages:add', args=('tests', 'defaultrichtextfieldpage', self.root_page.id)
        ))

        # Check status code
        self.assertEqual(response.status_code, 200)

        # Check that hallo (default editor by now) was replaced with fake editor
        self.assertNotContains(response, 'makeHalloRichTextEditable("id_body");')
        self.assertContains(response, 'customEditorInitScript("id_body");')

    def test_overridden_default_editor_in_rich_text_block(self):
        response = self.client.get(reverse(
            'wagtailadmin_pages:add', args=('tests', 'defaultrichblockfieldpage', self.root_page.id)
        ))

        # Check status code
        self.assertEqual(response.status_code, 200)

        # Check that hallo (default editor by now) was replaced with fake editor
        self.assertNotContains(response, 'makeHalloRichTextEditable("__PREFIX__-value");')
        self.assertContains(response, 'customEditorInitScript("__PREFIX__-value");')


@override_settings(WAGTAILADMIN_RICH_TEXT_EDITORS={
    'default': {
        'WIDGET': 'wagtail.wagtailadmin.rich_text.HalloRichTextArea'
    },
    'custom': {
        'WIDGET': 'wagtail.tests.testapp.rich_text.CustomRichTextArea'
    },
})
class TestCustomDefaultRichText(BaseRichTextEditHandlerTestCase, WagtailTestUtils):

    def setUp(self):
        super(TestCustomDefaultRichText, self).setUp()

        # Find root page
        self.root_page = Page.objects.get(id=2)

        self.login()

    def test_custom_editor_in_rich_text_field(self):
        response = self.client.get(reverse(
            'wagtailadmin_pages:add', args=('tests', 'customrichtextfieldpage', self.root_page.id)
        ))

        # Check status code
        self.assertEqual(response.status_code, 200)

        # Check that hallo (default editor by now) was replaced with fake editor
        self.assertNotContains(response, 'makeHalloRichTextEditable("id_body");')
        self.assertContains(response, 'customEditorInitScript("id_body");')

    def test_custom_editor_in_rich_text_block(self):
        response = self.client.get(reverse(
            'wagtailadmin_pages:add', args=('tests', 'customrichblockfieldpage', self.root_page.id)
        ))

        # Check status code
        self.assertEqual(response.status_code, 200)

        # Check that hallo (default editor by now) was replaced with fake editor
        self.assertNotContains(response, 'makeHalloRichTextEditable("__PREFIX__-value");')
        self.assertContains(response, 'customEditorInitScript("__PREFIX__-value");')


class TestRichTextValue(TestCase):

    def setUp(self):
        self.root_page = Page.objects.get(id=2)

        self.single_event_page = SingleEventPage(
            title="foo",
            location='the moon', audience='public',
            cost='free', date_from='2001-01-01',
        )
        self.root_page.add_child(instance=self.single_event_page)


    def test_render(self):
        text = '<p>To the <a linktype="page" id="{}">moon</a>!</p>'.format(
            self.single_event_page.id
        )
        value = RichText(text)
        result = str(value)
        expected = (
            '<div class="rich-text"><p>To the <a href="'
            '/foo/pointless-suffix/">moon</a>!</p></div>')
        self.assertEqual(result, expected)


@override_settings(WAGTAILADMIN_RICH_TEXT_EDITORS={
    'default': {
        'WIDGET': 'wagtail.wagtailadmin.rich_text.HalloRichTextArea'
    },
    'custom': {
        'WIDGET': 'wagtail.wagtailadmin.rich_text.HalloRichTextArea',
        'OPTIONS': {
            'plugins': {
                'halloheadings': {'formatBlocks': ['p', 'h2']},
            }
        }
    },
})
class TestHalloJsWithCustomPluginOptions(BaseRichTextEditHandlerTestCase, WagtailTestUtils):

    def setUp(self):
        super(TestHalloJsWithCustomPluginOptions, self).setUp()

        # Find root page
        self.root_page = Page.objects.get(id=2)

        self.login()

    def test_custom_editor_in_rich_text_field(self):
        response = self.client.get(reverse(
            'wagtailadmin_pages:add', args=('tests', 'customrichtextfieldpage', self.root_page.id)
        ))

        # Check status code
        self.assertEqual(response.status_code, 200)

        # Check that the custom plugin options are being passed in the hallo initialiser
        self.assertContains(response, 'makeHalloRichTextEditable("id_body", {"halloheadings": {"formatBlocks": ["p", "h2"]}});')

    def test_custom_editor_in_rich_text_block(self):
        block = RichTextBlock(editor='custom')

        form_html = block.render_form(block.to_python("<p>hello</p>"), 'body')

        # Check that the custom plugin options are being passed in the hallo initialiser
        self.assertIn('makeHalloRichTextEditable("body", {"halloheadings": {"formatBlocks": ["p", "h2"]}});', form_html)


class TestHalloJsWithFeaturesKwarg(BaseRichTextEditHandlerTestCase, WagtailTestUtils):

    def setUp(self):
        super(TestHalloJsWithFeaturesKwarg, self).setUp()

        # Find root page
        self.root_page = Page.objects.get(id=2)

        self.login()

    def test_features_list_on_rich_text_field(self):
        response = self.client.get(reverse(
            'wagtailadmin_pages:add', args=('tests', 'richtextfieldwithfeaturespage', self.root_page.id)
        ))

        # Check status code
        self.assertEqual(response.status_code, 200)

        # Check that the custom plugin options are being passed in the hallo initialiser
        self.assertContains(response, '"halloblockquote":')
        self.assertContains(response, '"hallowagtailembeds":')
        self.assertNotContains(response, '"hallolists":')
        self.assertNotContains(response, '"hallowagtailimage":')

        # check that media (js/css) from the features is being imported
        self.assertContains(response, 'testapp/js/hallo-blockquote.js')
        self.assertContains(response, 'testapp/css/hallo-blockquote.css')

        # check that we're NOT importing media for the default features we're not using
        self.assertNotContains(response, 'wagtaildocs/js/hallo-plugins/hallo-wagtaildoclink.js')

    def test_features_list_on_rich_text_block(self):
        block = RichTextBlock(features=['blockquote', 'embed', 'made-up-feature'])

        form_html = block.render_form(block.to_python("<p>hello</p>"), 'body')

        # Check that the custom plugin options are being passed in the hallo initialiser
        self.assertIn('"halloblockquote":', form_html)
        self.assertIn('"hallowagtailembeds":', form_html)
        self.assertNotIn('"hallolists":', form_html)
        self.assertNotIn('"hallowagtailimage":', form_html)

        # check that media (js/css) from the features is being imported
        media_html = str(block.media)
        self.assertIn('testapp/js/hallo-blockquote.js', media_html)
        self.assertIn('testapp/css/hallo-blockquote.css', media_html)
        # check that we're NOT importing media for the default features we're not using
        self.assertNotIn('wagtaildocs/js/hallo-plugins/hallo-wagtaildoclink.js', media_html)


@override_settings(WAGTAILADMIN_RICH_TEXT_EDITORS={
    'default': {
        'WIDGET': 'wagtail.wagtailadmin.rich_text.HalloRichTextArea',
        'OPTIONS': {
            'features': ['blockquote', 'image']
        }
    },
    'custom': {
        'WIDGET': 'wagtail.wagtailadmin.rich_text.HalloRichTextArea',
        'OPTIONS': {
            'features': ['blockquote', 'image']
        }
    },
})
class TestHalloJsWithCustomFeatureOptions(BaseRichTextEditHandlerTestCase, WagtailTestUtils):

    def setUp(self):
        super(TestHalloJsWithCustomFeatureOptions, self).setUp()

        # Find root page
        self.root_page = Page.objects.get(id=2)

        self.login()

    def test_custom_features_option_on_rich_text_field(self):
        response = self.client.get(reverse(
            'wagtailadmin_pages:add', args=('tests', 'customrichtextfieldpage', self.root_page.id)
        ))

        # Check status code
        self.assertEqual(response.status_code, 200)

        # Check that the custom plugin options are being passed in the hallo initialiser
        self.assertContains(response, '"halloblockquote":')
        self.assertContains(response, '"hallowagtailimage":')
        self.assertNotContains(response, '"hallolists":')
        self.assertNotContains(response, '"hallowagtailembeds":')

        # a 'features' list passed on the RichTextField (as we do in richtextfieldwithfeaturespage)
        # should override the list in OPTIONS
        response = self.client.get(reverse(
            'wagtailadmin_pages:add', args=('tests', 'richtextfieldwithfeaturespage', self.root_page.id)
        ))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"halloblockquote":')
        self.assertContains(response, '"hallowagtailembeds":')
        self.assertNotContains(response, '"hallolists":')
        self.assertNotContains(response, '"hallowagtailimage":')

        # check that media (js/css) from the features is being imported
        self.assertContains(response, 'testapp/js/hallo-blockquote.js')
        self.assertContains(response, 'testapp/css/hallo-blockquote.css')

        # check that we're NOT importing media for the default features we're not using
        self.assertNotContains(response, 'wagtaildocs/js/hallo-plugins/hallo-wagtaildoclink.js')

    def test_custom_features_option_on_rich_text_block(self):
        block = RichTextBlock(editor='custom')

        form_html = block.render_form(block.to_python("<p>hello</p>"), 'body')

        # Check that the custom plugin options are being passed in the hallo initialiser
        self.assertIn('"halloblockquote":', form_html)
        self.assertIn('"hallowagtailimage":', form_html)
        self.assertNotIn('"hallowagtailembeds":', form_html)
        self.assertNotIn('"hallolists":', form_html)

        # a 'features' list passed on the RichTextBlock
        # should override the list in OPTIONS
        block = RichTextBlock(editor='custom', features=['blockquote', 'embed'])

        form_html = block.render_form(block.to_python("<p>hello</p>"), 'body')

        self.assertIn('"halloblockquote":', form_html)
        self.assertIn('"hallowagtailembeds":', form_html)
        self.assertNotIn('"hallowagtailimage":', form_html)
        self.assertNotIn('"hallolists":', form_html)

        # check that media (js/css) from the features is being imported
        media_html = str(block.media)
        self.assertIn('testapp/js/hallo-blockquote.js', media_html)
        self.assertIn('testapp/css/hallo-blockquote.css', media_html)
        # check that we're NOT importing media for the default features we're not using
        self.assertNotIn('wagtaildocs/js/hallo-plugins/hallo-wagtaildoclink.js', media_html)
