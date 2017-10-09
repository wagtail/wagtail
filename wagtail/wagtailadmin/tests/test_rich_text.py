from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from wagtail.tests.testapp.models import SingleEventPage
from wagtail.tests.testapp.rich_text import CustomRichTextArea
from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailadmin.rich_text import HalloRichTextArea, get_rich_text_editor_widget
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

        block_page_edit_handler = DefaultRichBlockFieldPage.get_edit_handler()
        if block_page_edit_handler._form_class:
            rich_text_block = block_page_edit_handler._form_class.base_fields['body'].block.child_blocks['rich_text']
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
        self.assertContains(response, 'makeHalloRichTextEditable("id_body");')

    def test_default_editor_in_rich_text_block(self):
        response = self.client.get(reverse(
            'wagtailadmin_pages:add', args=('tests', 'defaultrichblockfieldpage', self.root_page.id)
        ))

        # Check status code
        self.assertEqual(response.status_code, 200)

        # Check that hallo (default editor by now)
        self.assertContains(response, 'makeHalloRichTextEditable("__PREFIX__-value");')


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
