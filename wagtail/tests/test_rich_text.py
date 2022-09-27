from unittest.mock import patch

from django.forms.models import modelform_factory
from django.test import TestCase, override_settings
from django.utils import translation

from wagtail.fields import RichTextField
from wagtail.models import Locale, Page
from wagtail.rich_text import RichText, RichTextMaxLengthValidator, expand_db_html
from wagtail.rich_text.feature_registry import FeatureRegistry
from wagtail.rich_text.pages import PageLinkHandler
from wagtail.rich_text.rewriters import LinkRewriter, extract_attrs
from wagtail.test.testapp.models import EventIndex, EventPage
from wagtail.test.utils.form_data import rich_text


class TestPageLinktypeHandler(TestCase):
    fixtures = ["test.json"]

    def test_expand_db_attributes(self):
        result = PageLinkHandler.expand_db_attributes(
            {"id": Page.objects.get(url_path="/home/events/christmas/").id}
        )
        self.assertEqual(result, '<a href="/events/christmas/">')

    def test_expand_db_attributes_page_does_not_exist(self):
        result = PageLinkHandler.expand_db_attributes({"id": 0})
        self.assertEqual(result, "<a>")

    def test_expand_db_attributes_not_for_editor(self):
        result = PageLinkHandler.expand_db_attributes({"id": 1})
        self.assertEqual(result, '<a href="None">')


@override_settings(
    WAGTAIL_I18N_ENABLED=True,
    WAGTAIL_CONTENT_LANGUAGES=[
        ("en", "English"),
        ("fr", "French"),
    ],
    ROOT_URLCONF="wagtail.test.urls_multilang",
)
class TestPageLinktypeHandlerWithI18N(TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.fr_locale = Locale.objects.create(language_code="fr")
        self.event_page = Page.objects.get(url_path="/home/events/christmas/")
        self.fr_event_page = self.event_page.copy_for_translation(
            self.fr_locale, copy_parents=True
        )
        self.fr_event_page.slug = "noel"
        self.fr_event_page.save(update_fields=["slug"])
        self.fr_event_page.save_revision().publish()

    def test_expand_db_attributes(self):
        result = PageLinkHandler.expand_db_attributes({"id": self.event_page.id})
        self.assertEqual(result, '<a href="/en/events/christmas/">')

    def test_expand_db_attributes_autolocalizes(self):
        # Even though it's linked to the english page in rich text.
        # The link should be to the local language version if it's available
        with translation.override("fr"):
            result = PageLinkHandler.expand_db_attributes({"id": self.event_page.id})
            self.assertEqual(result, '<a href="/fr/events/noel/">')

    def test_expand_db_attributes_doesnt_autolocalize_unpublished_page(self):
        # We shouldn't autolocalize if the translation is unpublished
        self.fr_event_page.unpublish()
        self.fr_event_page.save()

        with translation.override("fr"):
            result = PageLinkHandler.expand_db_attributes({"id": self.event_page.id})
            self.assertEqual(result, '<a href="/en/events/christmas/">')


class TestExtractAttrs(TestCase):
    def test_extract_attr(self):
        html = '<a foo="bar" baz="quux">snowman</a>'
        result = extract_attrs(html)
        self.assertEqual(result, {"foo": "bar", "baz": "quux"})


class TestExpandDbHtml(TestCase):
    def test_expand_db_html_with_linktype(self):
        html = '<a id="1" linktype="document">foo</a>'
        result = expand_db_html(html)
        self.assertEqual(result, "<a>foo</a>")

    def test_expand_db_html_no_linktype(self):
        html = '<a id="1">foo</a>'
        result = expand_db_html(html)
        self.assertEqual(result, '<a id="1">foo</a>')

    @patch("wagtail.embeds.embeds.get_embed")
    def test_expand_db_html_with_embed(self, get_embed):
        from wagtail.embeds.models import Embed

        get_embed.return_value = Embed(html="test html")
        html = '<embed embedtype="media" url="http://www.youtube.com/watch" />'
        result = expand_db_html(html)
        self.assertIn("test html", result)


class TestRichTextValue(TestCase):
    fixtures = ["test.json"]

    def test_construct_with_none(self):
        value = RichText(None)
        self.assertEqual(value.source, "")

    def test_construct_with_empty_string(self):
        value = RichText("")
        self.assertEqual(value.source, "")

    def test_construct_with_nonempty_string(self):
        value = RichText("<p>hello world</p>")
        self.assertEqual(value.source, "<p>hello world</p>")

    def test_render(self):
        value = RichText('<p>Merry <a linktype="page" id="4">Christmas</a>!</p>')
        result = str(value)
        self.assertEqual(
            result, '<p>Merry <a href="/events/christmas/">Christmas</a>!</p>'
        )

    def test_evaluate_value(self):
        value = RichText(None)
        self.assertFalse(value)

        value = RichText("<p>wagtail</p>")
        self.assertTrue(value)


class TestFeatureRegistry(TestCase):
    def test_register_rich_text_features_hook(self):
        # testapp/wagtail_hooks.py defines a 'blockquote' rich text feature with a Draftail
        # plugin, via the register_rich_text_features hook; test that we can retrieve it here
        features = FeatureRegistry()
        quotation = features.get_editor_plugin("draftail", "quotation")
        self.assertEqual(quotation.js, ["testapp/js/draftail-quotation.js"])

    def test_missing_editor_plugin_returns_none(self):
        features = FeatureRegistry()
        self.assertIsNone(features.get_editor_plugin("made_up_editor", "blockquote"))
        self.assertIsNone(features.get_editor_plugin("draftail", "made_up_feature"))


class TestLinkRewriterTagReplacing(TestCase):
    def test_should_follow_default_behaviour(self):
        # we always have default `page` rules registered.
        rules = {"page": lambda attrs: '<a href="/article/{}">'.format(attrs["id"])}
        rewriter = LinkRewriter(rules)

        page_type_link = rewriter('<a linktype="page" id="3">')
        self.assertEqual(page_type_link, '<a href="/article/3">')

        # but it should also be able to handle other supported
        # link types (email, external, anchor) even if no rules is provided
        external_type_link = rewriter('<a href="https://wagtail.org/">')
        self.assertEqual(external_type_link, '<a href="https://wagtail.org/">')
        email_type_link = rewriter('<a href="mailto:test@wagtail.org">')
        self.assertEqual(email_type_link, '<a href="mailto:test@wagtail.org">')
        anchor_type_link = rewriter('<a href="#test">')
        self.assertEqual(anchor_type_link, '<a href="#test">')

        # As well as link which don't have any linktypes
        link_without_linktype = rewriter('<a data-link="https://wagtail.org">')
        self.assertEqual(link_without_linktype, '<a data-link="https://wagtail.org">')

        # But should not handle if a custom linktype is mentioned but no
        # associate rules are registered.
        link_with_custom_linktype = rewriter(
            '<a linktype="custom" href="https://wagtail.org">'
        )
        self.assertNotEqual(link_with_custom_linktype, '<a href="https://wagtail.org">')
        self.assertEqual(link_with_custom_linktype, "<a>")

    def test_supported_type_should_follow_given_rules(self):
        # we always have `page` rules by default
        rules = {
            "page": lambda attrs: '<a href="/article/{}">'.format(attrs["id"]),
            "external": lambda attrs: '<a rel="nofollow" href="{}">'.format(
                attrs["href"]
            ),
            "email": lambda attrs: '<a data-email="true" href="{}">'.format(
                attrs["href"]
            ),
            "anchor": lambda attrs: '<a data-anchor="true" href="{}">'.format(
                attrs["href"]
            ),
            "custom": lambda attrs: '<a data-phone="true" href="{}">'.format(
                attrs["href"]
            ),
        }
        rewriter = LinkRewriter(rules)

        page_type_link = rewriter('<a linktype="page" id="3">')
        self.assertEqual(page_type_link, '<a href="/article/3">')

        # It should call appropriate rule supported linktypes (external or email)
        # based on the href value
        external_type_link = rewriter('<a href="https://wagtail.org/">')
        self.assertEqual(
            external_type_link, '<a rel="nofollow" href="https://wagtail.org/">'
        )
        external_type_link_http = rewriter('<a href="http://wagtail.org/">')
        self.assertEqual(
            external_type_link_http, '<a rel="nofollow" href="http://wagtail.org/">'
        )
        email_type_link = rewriter('<a href="mailto:test@wagtail.org">')
        self.assertEqual(
            email_type_link, '<a data-email="true" href="mailto:test@wagtail.org">'
        )
        anchor_type_link = rewriter('<a href="#test">')
        self.assertEqual(anchor_type_link, '<a data-anchor="true" href="#test">')

        # But not the unsupported ones.
        link_with_no_linktype = rewriter('<a href="tel:+4917640206387">')
        self.assertEqual(link_with_no_linktype, '<a href="tel:+4917640206387">')

        # Also call the rule if a custom linktype is mentioned.
        link_with_custom_linktype = rewriter(
            '<a linktype="custom" href="tel:+4917640206387">'
        )
        self.assertEqual(
            link_with_custom_linktype, '<a data-phone="true" href="tel:+4917640206387">'
        )


class TestRichTextField(TestCase):
    fixtures = ["test.json"]

    def test_get_searchable_content(self):
        christmas_page = EventPage.objects.get(url_path="/home/events/christmas/")
        christmas_page.body = '<p><b>Merry Christmas from <a href="https://wagtail.org/">Wagtail!</a></b> &amp; co.</p>'
        christmas_page.save_revision(submitted_for_moderation=False)

        body_field = christmas_page._meta.get_field("body")
        value = body_field.value_from_object(christmas_page)
        result = body_field.get_searchable_content(value)
        self.assertEqual(result, ["Merry Christmas from Wagtail! & co."])

    def test_get_searchable_content_whitespace(self):
        christmas_page = EventPage.objects.get(url_path="/home/events/christmas/")
        christmas_page.body = "<p>buttery<br />mashed</p><p>po<i>ta</i>toes</p>"
        christmas_page.save_revision(submitted_for_moderation=False)

        body_field = christmas_page._meta.get_field("body")
        value = body_field.value_from_object(christmas_page)
        result = body_field.get_searchable_content(value)
        self.assertEqual(result, ["buttery mashed potatoes"])

    def test_max_length_validation(self):
        EventIndexForm = modelform_factory(model=EventIndex, fields=["intro"])

        form = EventIndexForm(
            {"intro": rich_text("<p><i>less</i> than 50 characters</p>")}
        )
        self.assertTrue(form.is_valid())

        form = EventIndexForm(
            {
                "intro": rich_text(
                    "<p>a piece of text that is considerably longer than the limit of fifty characters of text</p>"
                )
            }
        )
        self.assertFalse(form.is_valid())

        form = EventIndexForm(
            {
                "intro": rich_text(
                    '<p><a href="http://a-domain-name-that-would-put-us-over-the-limit-if-we-were-counting-it.example.com/">less</a> than 50 characters</p>'
                )
            }
        )
        self.assertTrue(form.is_valid())

    def test_extract_references(self):
        self.assertEqual(
            list(
                RichTextField().extract_references(
                    '<a linktype="page" id="1">Link to an internal page</a>'
                )
            ),
            [(Page, "1", "", "")],
        )


class TestRichTextMaxLengthValidator(TestCase):
    def test_count_characters(self):
        """Keep those tests up-to-date with MaxLength tests client-side."""
        validator = RichTextMaxLengthValidator(50)
        self.assertEqual(validator.clean("<p>Plain text</p>"), 10)
        # HTML entities should be un-escaped.
        self.assertEqual(validator.clean("<p>There&#x27;s quote</p>"), 13)
        # BR should be ignored.
        self.assertEqual(validator.clean("<p>Line<br/>break</p>"), 9)
        # Content over multiple blocks should be treated as a single line of text with no joiner.
        self.assertEqual(validator.clean("<p>Multi</p><p>blocks</p>"), 11)
        # Empty blocks should be ignored.
        self.assertEqual(validator.clean("<p>Empty</p><p></p><p>blocks</p>"), 11)
        # HR should be ignored.
        self.assertEqual(validator.clean("<p>With</p><hr/><p>HR</p>"), 6)
        # Embed blocks should be ignored.
        self.assertEqual(validator.clean("<p>With</p><embed/><p>embed</p>"), 9)
        # Counts symbols with multiple code units (heart unicode + variation selector).
        self.assertEqual(validator.clean("<p>U+2764 U+FE0F ❤️</p>"), 16)
        # Counts symbols with zero-width joiners.
        self.assertEqual(validator.clean("<p>👨‍👨‍👧</p>"), 5)
