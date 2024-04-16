import unittest

from django.conf import settings
from django.test import SimpleTestCase, TestCase
from django.test.utils import override_settings
from django.urls import reverse, reverse_lazy

from wagtail.admin.rich_text import DraftailRichTextArea, get_rich_text_editor_widget
from wagtail.admin.rich_text.converters.editor_html import (
    EditorHTMLConverter,
    PageLinkHandler,
)
from wagtail.admin.rich_text.editors.draftail.features import Feature
from wagtail.blocks import RichTextBlock
from wagtail.models import Page, get_page_models
from wagtail.rich_text import RichText
from wagtail.rich_text.feature_registry import FeatureRegistry
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


class TestDefaultRichText(WagtailTestUtils, BaseRichTextEditHandlerTestCase):
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
        # Check that data-controller and data-w-init-event-value were added after initialization
        self.assertContains(response, 'data-controller="w-init"')
        self.assertContains(response, 'data-w-init-event-value="w-draftail:init"')

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
class TestDraftailFeatureMedia(WagtailTestUtils, BaseRichTextEditHandlerTestCase):
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
class TestOverriddenDefaultRichText(WagtailTestUtils, BaseRichTextEditHandlerTestCase):
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
        self.assertNotContains(
            response,
            '<template data-controller="custom-editor" data-id="id_body"',
        )
        self.assertContains(
            response,
            '<template data-controller="legacy-editor" data-id="id_body"',
        )

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
        self.assertNotContains(
            response,
            '<template data-controller="custom-editor" data-id="__PREFIX__-value"',
        )
        self.assertContains(
            response,
            '<template data-controller="legacy-editor" data-id="__PREFIX__-value"',
        )


@override_settings(
    WAGTAILADMIN_RICH_TEXT_EDITORS={
        "default": {
            "WIDGET": "wagtail.admin.tests.test_rich_text.TestCustomDefaultRichText"
        },
        "custom": {"WIDGET": "wagtail.test.testapp.rich_text.CustomRichTextArea"},
    }
)
class TestCustomDefaultRichText(WagtailTestUtils, BaseRichTextEditHandlerTestCase):
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
        self.assertNotContains(
            response,
            '<template data-controller="legacy-editor" data-id="id_body"',
        )
        self.assertContains(
            response,
            '<template data-controller="custom-editor" data-id="id_body"',
        )

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

        self.assertContains(
            response, '<template data-controller="custom-editor" data-id="id_body"'
        )


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
class TestDraftailWithFeatureOptions(WagtailTestUtils, BaseRichTextEditHandlerTestCase):
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
        soup = self.get_soup(response.content)
        input = soup.find(
            "input",
            {
                "data-draftail-input": "",
                "data-controller": "w-init",
                "data-w-init-event-value": "w-draftail:init",
            },
        )
        data = input["data-w-init-detail-value"]

        self.assertIn('"type": "header-two"', data)
        self.assertIn('"type": "IMAGE"', data)
        self.assertNotIn('"type": "ordered-list-item"', data)

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
    WagtailTestUtils, BaseRichTextEditHandlerTestCase
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

        soup = self.get_soup(response.content)
        input = soup.find(
            "input",
            {
                "data-draftail-input": "",
                "data-controller": "w-init",
                "data-w-init-event-value": "w-draftail:init",
            },
        )
        data = input["data-w-init-detail-value"]

        self.assertIn('"type": "header-two"', data)
        self.assertIn('"type": "LINK"', data)
        self.assertIn('"type": "ITALIC"', data)

        # not the additional ones.
        self.assertNotIn('"type": "CODE"', data)
        self.assertNotIn('"type": "blockquote"', data)
        self.assertNotIn('"type": "SUPERSCRIPT"', data)
        self.assertNotIn('"type": "SUBSCRIPT"', data)
        self.assertNotIn('"type": "STRIKETHROUGH"', data)

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

        soup = self.get_soup(response.content)
        input = soup.find(
            "input",
            {
                "data-draftail-input": "",
                "data-controller": "w-init",
                "data-w-init-event-value": "w-draftail:init",
            },
        )

        data = input["data-w-init-detail-value"]
        # Added features are there
        self.assertIn('"type": "header-two"', data)
        self.assertIn('"type": "CODE"', data)
        self.assertIn('"type": "blockquote"', data)
        self.assertIn('"type": "SUPERSCRIPT"', data)
        self.assertIn('"type": "SUBSCRIPT"', data)
        self.assertIn('"type": "STRIKETHROUGH"', data)

        # But not the unprovided default ones.
        self.assertNotIn('"type": "LINK"', data)
        self.assertNotIn('"type": "ITALIC"', data)


class TestPageLinkHandler(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def test_get_db_attributes(self):
        soup = self.get_soup('<a data-id="test-id">foo</a>')
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

    def test_editorhtmlconverter_from_database_format(self):
        events_page_id = Page.objects.get(url_path="/home/events/").pk
        db_html = '<a linktype="page" id="%d">foo</a>' % events_page_id
        converter = EditorHTMLConverter(features=["link"])
        editor_html = converter.from_database_format(db_html)
        self.assertEqual(
            editor_html,
            '<a data-linktype="page" data-id="%d" data-parent-id="2" href="/events/">foo</a>'
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


class TestRichTextChooserUrls(WagtailTestUtils, BaseRichTextEditHandlerTestCase):
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
    def test_chooser_urls_exist(self):
        features = FeatureRegistry()
        link = features.get_editor_plugin("draftail", "link")

        self.assertIsNotNone(link.data.get("chooserUrls"))
        self.assertEqual(
            link.data["chooserUrls"]["pageChooser"],
            reverse_lazy("wagtailadmin_choose_page"),
        )
        self.assertEqual(
            link.data["chooserUrls"]["externalLinkChooser"],
            reverse_lazy("wagtailadmin_choose_page_external_link"),
        )
        self.assertEqual(
            link.data["chooserUrls"]["emailLinkChooser"],
            reverse_lazy("wagtailadmin_choose_page_email_link"),
        )
        self.assertEqual(
            link.data["chooserUrls"]["phoneLinkChooser"],
            reverse_lazy("wagtailadmin_choose_page_phone_link"),
        )
        self.assertEqual(
            link.data["chooserUrls"]["anchorLinkChooser"],
            reverse_lazy("wagtailadmin_choose_page_anchor_link"),
        )

    def test_lazy_chooser_urls_resolved_correctly(self):
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "defaultrichtextfieldpage", self.root_page.id),
            )
        )

        soup = self.get_soup(response.content)
        input = soup.find(
            "input",
            {
                "data-draftail-input": "",
                "data-controller": "w-init",
                "data-w-init-event-value": "w-draftail:init",
            },
        )

        data = input["data-w-init-detail-value"]

        self.assertIn(
            '"chooserUrls": {"imageChooser": "/admin/images/chooser/"}',
            data,
        )
        self.assertIn(
            '"chooserUrls": {"embedsChooser": "/admin/embeds/chooser/"}',
            data,
        )
        self.assertIn(
            '"chooserUrls": {"documentChooser": "/admin/documents/chooser/"}',
            data,
        )

        self.assertIn(
            '"chooserUrls": {"pageChooser": "/admin/choose-page/", "externalLinkChooser": "/admin/choose-external-link/", "emailLinkChooser": "/admin/choose-email-link/", "phoneLinkChooser": "/admin/choose-phone-link/", "anchorLinkChooser": "/admin/choose-anchor-link/"}',
            data,
        )

    def test_lazy_urls_resolution(self):
        """
        Check that the lazy URLs have been resolved correctly in the rendered widget HTML data attributes.
        """

        widget = DraftailRichTextArea()
        html = widget.render("test_chooserUrls", "", {})

        self.assertIn("/admin/choose-page/", html)
        self.assertIn("/admin/images/chooser/", html)
        self.assertIn("/admin/embeds/chooser/", html)
        self.assertIn("/admin/documents/chooser/", html)
