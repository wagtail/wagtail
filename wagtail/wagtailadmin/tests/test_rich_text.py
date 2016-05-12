from __future__ import absolute_import, unicode_literals

import unittest

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailcore.models import Page

from wagtail.tests.testapp.rich_text import CustomRichTextArea
from wagtail.wagtailadmin.rich_text import get_rich_text_editor_widget, HalloRichTextArea


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
class TestDefaultRichText(TestCase, WagtailTestUtils):

    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        self.login()

        # Simulate the absence of a setting
        if hasattr(settings, 'WAGTAILADMIN_RICH_TEXT_EDITORS'):
            del settings.WAGTAILADMIN_RICH_TEXT_EDITORS

    def tearDown(self):
        from wagtail.tests.testapp.models import DefaultRichBlockFieldPage
        from wagtail.tests.testapp.models import DefaultRichTextFieldPage

        DefaultRichTextFieldPage.get_edit_handler()._form_class = None

        block_page_edit_handler = DefaultRichBlockFieldPage.get_edit_handler()
        if block_page_edit_handler._form_class:
            rich_text_block = block_page_edit_handler._form_class.base_fields['body'].block.child_blocks['rich_text']
            if hasattr(rich_text_block, 'field'):
                del rich_text_block.field
        block_page_edit_handler._form_class = None

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
class TestOverriddenDefaultRichText(TestCase, WagtailTestUtils):

    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        self.login()

    def tearDown(self):
        from wagtail.tests.testapp.models import DefaultRichBlockFieldPage
        from wagtail.tests.testapp.models import DefaultRichTextFieldPage

        DefaultRichTextFieldPage.get_edit_handler()._form_class = None

        block_page_edit_handler = DefaultRichBlockFieldPage.get_edit_handler()
        if block_page_edit_handler._form_class:
            rich_text_block = block_page_edit_handler._form_class.base_fields['body'].block.child_blocks['rich_text']
            if hasattr(rich_text_block, 'field'):
                del rich_text_block.field
        block_page_edit_handler._form_class = None

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
class TestCustomDefaultRichText(TestCase, WagtailTestUtils):

    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        self.login()

    def tearDown(self):
        from wagtail.tests.testapp.models import CustomRichBlockFieldPage
        from wagtail.tests.testapp.models import CustomRichTextFieldPage

        CustomRichBlockFieldPage.get_edit_handler()._form_class = None
        CustomRichTextFieldPage.get_edit_handler()._form_class = None

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
