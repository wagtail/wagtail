import unittest

from bs4 import BeautifulSoup
from django.conf import settings
from django.test import SimpleTestCase, TestCase
from django.test.utils import override_settings
from django.urls import reverse

from wagtail.admin.rich_text import DraftailRichTextArea, get_rich_text_editor_widget
from wagtail.admin.rich_text.converters.editor_html import PageLinkHandler
from wagtail.admin.rich_text.editors.draftail.features import Feature
from wagtail.blocks import RichTextBlock
from wagtail.models import Page, get_page_models
from wagtail.rich_text import RichText
from wagtail.test.testapp.models import SingleEventPage
from wagtail.test.testapp.rich_text import CustomRichTextArea, LegacyRichTextArea
from wagtail.test.utils import WagtailTestUtils


class BaseRichTextEditHandlerTestCase(TestCase):
    def _clear_edit_handler_cache(self):
        """
        These tests generate new panel definitions with different settings. The
        cached edit handlers should be cleared before and after each test run
        to ensure that no changes leak through to other tests.
        """
        from wagtail.test.testapp.models import DefaultRichBlockFieldPage

        rich_text_block = (
            DefaultRichBlockFieldPage.get_edit_handler()
            .get_form_class()
            .base_fields["body"]
            .block.child_blocks["rich_text"]
        )
        if hasattr(rich_text_block, "field"):
            del rich_text_block.field

        for page_class in get_page_models():
            page_class.get_edit_handler.cache_clear()

    def setUp(self):
        super().setUp()
        self._clear_edit_handler_cache()

    def tearDown(self):
        self._clear_edit_handler_cache()
        super().tearDown()


class TestGetRichTextEditorWidget(TestCase):
    @override_settings()  # create temporary copy of settings so we can remove WAGTAILADMIN_RICH_TEXT_EDITORS
    def test_default(self):
        # Simulate the absence of a setting
        if hasattr(settings, "WAGTAILADMIN_RICH_TEXT_EDITORS"):
            del settings.WAGTAILADMIN_RICH_TEXT_EDITORS

        self.assertIsInstance(get_rich_text_editor_widget(), DraftailRichTextArea)

    @override_settings(
        WAGTAILADMIN_RICH_TEXT_EDITORS={
            "default": {"WIDGET": "wagtail.test.testapp.rich_text.CustomRichTextArea"},
        }
    )
    def test_overridden_default_editor(self):
        self.assertIsInstance(get_rich_text_editor_widget(), CustomRichTextArea)

    @override_settings(
        WAGTAILADMIN_RICH_TEXT_EDITORS={
            "custom": {"WIDGET": "wagtail.test.testapp.rich_text.CustomRichTextArea"},
        }
    )
    def test_custom_editor_without_default(self):
        self.assertIsInstance(get_rich_text_editor_widget(), DraftailRichTextArea)
        self.assertIsInstance(get_rich_text_editor_widget("custom"), CustomRichTextArea)

    @override_settings(
        WAGTAILADMIN_RICH_TEXT_EDITORS={
            "default": {"WIDGET": "wagtail.test.testapp.rich_text.LegacyRichTextArea"},
            "custom": {"WIDGET": "wagtail.test.testapp.rich_text.CustomRichTextArea"},
        }
    )
    def test_custom_editor_with_default(self):
        self.assertIsInstance(get_rich_text_editor_widget(), LegacyRichTextArea)
        self.assertIsInstance(get_rich_text_editor_widget("custom"), CustomRichTextArea)


class TestDefaultRichText(BaseRichTextEditHandlerTestCase, WagtailTestUtils):
    def setUp(self):
        super().setUp()
        # Find root page
        self.root_page = Page.objects.get(id=2)

        self.login()

    @override_settings()  # create temporary copy of settings so we can remove WAGTAILADMIN_RICH_TEXT_EDITORS
    def test_default_editor_in_rich_text_field(self):
        # Simulate the absence of a setting
        if hasattr(settings, "WAGTAILADMIN_RICH_TEXT_EDITORS"):
            del settings.WAGTAILADMIN_RICH_TEXT_EDITORS

        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "defaultrichtextfieldpage", self.root_page.id),
            )
        )

        # Check status code
        self.assertEqual(response.status_code, 200)

        # Check that draftail (default editor) initialisation is applied
        self.assertContains(response, "window.draftail.initEditor('#id_body',")

        # check that media for draftail is being imported
        self.assertContains(response, "wagtailadmin/js/draftail.js")

        # check that media for non-active features is not being imported
        self.assertNotContains(response, "testapp/js/draftail-blockquote.js")
        self.assertNotContains(response, "testapp/css/draftail-blockquote.css")

    @unittest.expectedFailure  # TODO(telepath)
    @override_settings()  # create temporary copy of settings so we can remove WAGTAILADMIN_RICH_TEXT_EDITORS
    def test_default_editor_in_rich_text_block(self):
        # Simulate the absence of a setting
        if hasattr(settings, "WAGTAILADMIN_RICH_TEXT_EDITORS"):
            del settings.WAGTAILADMIN_RICH_TEXT_EDITORS

        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "defaultrichblockfieldpage", self.root_page.id),
            )
        )

        # Check status code
        self.assertEqual(response.status_code, 200)

        # Check that draftail (default editor) initialisation is applied
        self.assertContains(
            response, "window.draftail.initEditor('#__PREFIX__\\u002Dvalue',"
        )

        # check that media for draftail is being imported
        self.assertContains(response, "wagtailadmin/js/draftail.js")

        # check that media for non-active features is not being imported
        self.assertNotContains(response, "testapp/js/draftail-blockquote.js")
        self.assertNotContains(response, "testapp/css/draftail-blockquote.css")


@override_settings(
    WAGTAILADMIN_RICH_TEXT_EDITORS={
        "default": {
            "WIDGET": "wagtail.admin.rich_text.DraftailRichTextArea",
            "OPTIONS": {"features": ["h2", "quotation"]},
        },
    }
)
class TestDraftailFeatureMedia(BaseRichTextEditHandlerTestCase, WagtailTestUtils):
    """
    Features that define additional js/css imports (blockquote, in this case) should
    have those loaded on the page
    """

    def setUp(self):
        super().setUp()
        # Find root page
        self.root_page = Page.objects.get(id=2)

        self.login()

    def test_feature_media_on_rich_text_field(self):
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "defaultrichtextfieldpage", self.root_page.id),
            )
        )

        self.assertContains(response, "wagtailadmin/js/draftail.js")
        self.assertContains(response, "testapp/js/draftail-quotation.js")
        self.assertContains(response, "testapp/css/draftail-quotation.css")

    def test_feature_media_on_rich_text_block(self):
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "defaultrichblockfieldpage", self.root_page.id),
            )
        )

        self.assertContains(response, "wagtailadmin/js/draftail.js")
        self.assertContains(response, "testapp/js/draftail-quotation.js")
        self.assertContains(response, "testapp/css/draftail-quotation.css")


@override_settings(
    WAGTAILADMIN_RICH_TEXT_EDITORS={
        "default": {"WIDGET": "wagtail.test.testapp.rich_text.LegacyRichTextArea"},
    }
)
class TestOverriddenDefaultRichText(BaseRichTextEditHandlerTestCase, WagtailTestUtils):
    def setUp(self):
        super().setUp()

        # Find root page
        self.root_page = Page.objects.get(id=2)

        self.login()

    def test_overridden_default_editor_in_rich_text_field(self):
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "defaultrichtextfieldpage", self.root_page.id),
            )
        )

        # Check status code
        self.assertEqual(response.status_code, 200)

        # Check that custom editor (default editor by now) was replaced with fake editor
        self.assertNotContains(response, 'customEditorInitScript("id_body");')
        self.assertContains(response, 'legacyEditorInitScript("id_body");')

    @unittest.expectedFailure  # TODO(telepath)
    def test_overridden_default_editor_in_rich_text_block(self):
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "defaultrichblockfieldpage", self.root_page.id),
            )
        )

        # Check status code
        self.assertEqual(response.status_code, 200)

        # Check that custom editor (default editor by now) was replaced with fake editor
        self.assertNotContains(response, 'customEditorInitScript("__PREFIX__-value");')
        self.assertContains(response, 'legacyEditorInitScript("__PREFIX__-value");')


@override_settings(
    WAGTAILADMIN_RICH_TEXT_EDITORS={
        "default": {
            "WIDGET": "wagtail.admin.tests.test_rich_text.TestCustomDefaultRichText"
        },
        "custom": {"WIDGET": "wagtail.test.testapp.rich_text.CustomRichTextArea"},
    }
)
class TestCustomDefaultRichText(BaseRichTextEditHandlerTestCase, WagtailTestUtils):
    def setUp(self):
        super().setUp()

        # Find root page
        self.root_page = Page.objects.get(id=2)

        self.login()

    def test_custom_editor_in_rich_text_field(self):
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "customrichtextfieldpage", self.root_page.id),
            )
        )

        # Check status code
        self.assertEqual(response.status_code, 200)

        # Check that custom editor (default editor by now) was replaced with fake editor
        self.assertNotContains(response, 'legacyEditorInitScript("id_body");')
        self.assertContains(response, 'customEditorInitScript("id_body");')

    @unittest.expectedFailure  # TODO(telepath)
    def test_custom_editor_in_rich_text_block(self):
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "customrichblockfieldpage", self.root_page.id),
            )
        )

        # Check status code
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'customEditorInitScript("__PREFIX__-value");')


class TestRichTextValue(TestCase):
    def setUp(self):
        self.root_page = Page.objects.get(id=2)

        self.single_event_page = SingleEventPage(
            title="foo",
            location="the moon",
            audience="public",
            cost="free",
            date_from="2001-01-01",
        )
        self.root_page.add_child(instance=self.single_event_page)

    def test_render(self):
        text = '<p>To the <a linktype="page" id="{}">moon</a>!</p>'.format(
            self.single_event_page.id
        )
        value = RichText(text)
        result = str(value)
        expected = '<p>To the <a href="/foo/pointless-suffix/">moon</a>!</p>'
        self.assertEqual(result, expected)


@override_settings(
    WAGTAILADMIN_RICH_TEXT_EDITORS={
        "default": {
            "WIDGET": "wagtail.admin.rich_text.DraftailRichTextArea",
            "OPTIONS": {"features": ["h2", "image"]},
        },
    }
)
class TestDraftailWithFeatureOptions(BaseRichTextEditHandlerTestCase, WagtailTestUtils):
    def setUp(self):
        super().setUp()

        # Find root page
        self.root_page = Page.objects.get(id=2)

        self.login()

    def test_settings_features_option_on_rich_text_field(self):
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "defaultrichtextfieldpage", self.root_page.id),
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"type": "header-two"')
        self.assertContains(response, '"type": "IMAGE"')
        self.assertNotContains(response, '"type": "ordered-list-item"')

    @unittest.expectedFailure  # TODO(telepath)
    def test_features_option_on_rich_text_block(self):
        # a 'features' list passed on the RichTextBlock
        # should override the list in OPTIONS
        block = RichTextBlock(features=["h2", "embed"])

        form_html = block.render_form(block.to_python("<p>hello</p>"), "body")

        self.assertIn('"type": "header-two"', form_html)
        self.assertIn('"type": "EMBED"', form_html)
        self.assertNotIn('"type": "IMAGE""', form_html)
        self.assertNotIn('"type": "ordered-list-item""', form_html)


class TestDraftailWithAdditionalFeatures(
    BaseRichTextEditHandlerTestCase, WagtailTestUtils
):
    def setUp(self):
        super().setUp()

        # Find root page
        self.root_page = Page.objects.get(id=2)

        self.login()

    @override_settings(
        WAGTAILADMIN_RICH_TEXT_EDITORS={
            "default": {
                "WIDGET": "wagtail.admin.rich_text.DraftailRichTextArea",
            },
        }
    )
    def test_additional_features_should_not_be_included_by_default(self):
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "defaultrichtextfieldpage", self.root_page.id),
            )
        )

        self.assertEqual(response.status_code, 200)
        # default ones are there
        self.assertContains(response, '"type": "header-two"')
        self.assertContains(response, '"type": "LINK"')
        self.assertContains(response, '"type": "ITALIC"')

        # not the additional ones.
        self.assertNotContains(response, '"type": "CODE"')
        self.assertNotContains(response, '"type": "blockquote"')
        self.assertNotContains(response, '"type": "SUPERSCRIPT"')
        self.assertNotContains(response, '"type": "SUBSCRIPT"')
        self.assertNotContains(response, '"type": "STRIKETHROUGH"')

    @override_settings(
        WAGTAILADMIN_RICH_TEXT_EDITORS={
            "default": {
                "WIDGET": "wagtail.admin.rich_text.DraftailRichTextArea",
                "OPTIONS": {
                    "features": [
                        "h2",
                        "code",
                        "blockquote",
                        "strikethrough",
                        "subscript",
                        "superscript",
                    ]
                },
            },
        }
    )
    def test_additional_features_included(self):
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "defaultrichtextfieldpage", self.root_page.id),
            )
        )

        self.assertEqual(response.status_code, 200)
        # Added features are there
        self.assertContains(response, '"type": "header-two"')
        self.assertContains(response, '"type": "CODE"')
        self.assertContains(response, '"type": "blockquote"')
        self.assertContains(response, '"type": "SUPERSCRIPT"')
        self.assertContains(response, '"type": "SUBSCRIPT"')
        self.assertContains(response, '"type": "STRIKETHROUGH"')

        # But not the unprovided default ones.
        self.assertNotContains(response, '"type": "LINK"')
        self.assertNotContains(response, '"type": "ITALIC"')


class TestPageLinkHandler(TestCase):
    fixtures = ["test.json"]

    def test_get_db_attributes(self):
        soup = BeautifulSoup('<a data-id="test-id">foo</a>', "html5lib")
        tag = soup.a
        result = PageLinkHandler.get_db_attributes(tag)
        self.assertEqual(result, {"id": "test-id"})

    def test_expand_db_attributes_for_editor(self):
        result = PageLinkHandler.expand_db_attributes({"id": 1})
        self.assertEqual(result, '<a data-linktype="page" data-id="1" href="None">')

        events_page_id = Page.objects.get(url_path="/home/events/").pk
        result = PageLinkHandler.expand_db_attributes({"id": events_page_id})
        self.assertEqual(
            result,
            '<a data-linktype="page" data-id="%d" data-parent-id="2" href="/events/">'
            % events_page_id,
        )


class TestWidgetNotHidden(SimpleTestCase):
    def test_draftail(self):
        self.assertIs(
            DraftailRichTextArea().is_hidden,
            False,
        )


class TestDraftailFeature(SimpleTestCase):
    def test_versioned_static_media(self):
        feature = Feature(
            js=["wagtailadmin/js/example/feature.js"],
            css={
                "all": ["wagtailadmin/css/example/feature.css"],
            },
        )
        media_html = str(feature.media)
        self.assertRegex(media_html, r"feature.js\?v=(\w+)")
        self.assertRegex(media_html, r"feature.css\?v=(\w+)")
