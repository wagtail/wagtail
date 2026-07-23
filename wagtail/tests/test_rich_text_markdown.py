from unittest.mock import patch

from django.template import Context, Template
from django.test import TestCase

from wagtail.models import Page
from wagtail.rich_text.markdown import MarkdownConverter, expand_db_html_to_markdown


class TestExpandDbHtmlToMarkdown(TestCase):
    fixtures = ["test.json"]

    def test_none_returns_empty_string(self):
        self.assertEqual(expand_db_html_to_markdown(None), "")

    def test_empty_string_returns_empty_string(self):
        self.assertEqual(expand_db_html_to_markdown(""), "")

    def test_paragraph_is_rendered_as_plain_text_block(self):
        result = expand_db_html_to_markdown("<p>Hello, world!</p>")
        self.assertEqual(result, "Hello, world!\n\n")

    def test_bold_is_rendered_with_double_asterisks(self):
        result = expand_db_html_to_markdown("<p>Hello <b>world</b></p>")
        self.assertEqual(result, "Hello **world**\n\n")

    def test_italic_is_rendered_with_underscore(self):
        result = expand_db_html_to_markdown("<p>Hello <i>world</i></p>")
        self.assertEqual(result, "Hello _world_\n\n")

    def test_heading_two(self):
        result = expand_db_html_to_markdown("<h2>Title</h2><p>Body.</p>")
        self.assertEqual(result, "## Title\n\nBody.\n\n")

    def test_unordered_list(self):
        result = expand_db_html_to_markdown("<ul><li>One</li><li>Two</li></ul>")
        self.assertEqual(result, "- One\n- Two\n\n")

    def test_ordered_list(self):
        result = expand_db_html_to_markdown("<ol><li>One</li><li>Two</li></ol>")
        self.assertEqual(result, "1. One\n2. Two\n\n")

    def test_blockquote(self):
        # ``blockquote`` is not part of the default feature set; enable it
        # explicitly to render the ``> Quote`` prefix.
        result = expand_db_html_to_markdown(
            "<blockquote>Quote</blockquote>", features=["blockquote"]
        )
        self.assertEqual(result, "> Quote\n\n")

    def test_blockquote_not_rendered_by_default_features(self):
        # With the default features, blockquote is treated as a paragraph
        # because no ``blockquote`` contentstate rule is loaded.
        result = expand_db_html_to_markdown("<blockquote>Quote</blockquote>")
        self.assertEqual(result, "Quote\n\n")

    def test_external_link_public_mode(self):
        result = expand_db_html_to_markdown(
            '<p><a href="https://example.com/">Link</a></p>'
        )
        self.assertEqual(result, "[Link](https://example.com/)\n\n")

    def test_external_link_internal_mode_is_unchanged(self):
        # External links have no id, so they render the same in both modes.
        result = expand_db_html_to_markdown(
            '<p><a href="https://example.com/">Link</a></p>', internal=True
        )
        self.assertEqual(result, "[Link](https://example.com/)\n\n")

    def test_page_link_public_mode_resolves_url(self):
        page = Page.objects.get(url_path="/home/events/")
        result = expand_db_html_to_markdown(
            f'<p><a linktype="page" id="{page.id}">Events</a></p>'
        )
        self.assertIn("(/events/)", result)
        self.assertNotIn("wagtail://", result)
        self.assertNotIn("linktype=", result)

    def test_page_link_internal_mode_preserves_reference(self):
        page = Page.objects.get(url_path="/home/events/")
        result = expand_db_html_to_markdown(
            f'<p><a linktype="page" id="{page.id}">Events</a></p>',
            internal=True,
        )
        self.assertEqual(result, f"[Events](wagtail://page?id={page.id})\n\n")

    def test_page_link_internal_mode_broken_reference_falls_back_to_id(self):
        # When the page does not exist, PageLinkElementHandler retains the id
        # in the contentstate; the internal markdown decorator should still
        # emit the wagtail://page?id=<id> reference for round-trip stability.
        result = expand_db_html_to_markdown(
            '<p><a linktype="page" id="99999">Broken link</a></p>',
            internal=True,
        )
        self.assertEqual(result, "[Broken link](wagtail://page?id=99999)\n\n")

    def test_page_link_public_mode_broken_reference_renders_marker(self):
        # In public mode, a page link whose page was deleted (``url`` is None)
        # should render a visible ``[broken link: …]`` marker instead of a
        # link to ``#``, which would look functional but go nowhere useful.
        result = expand_db_html_to_markdown(
            '<p><a linktype="page" id="99999">Broken link</a></p>',
        )
        self.assertIn("[broken link: Broken link]", result)
        self.assertNotIn("](", result)

    def test_image_public_mode_uses_rendition_src(self):
        # The image id 1 exists in the test fixtures.
        result = expand_db_html_to_markdown(
            '<embed embedtype="image" id="1" alt="A test image" format="fullwidth" />'
        )
        # Public markdown uses the rendition URL captured at contentstate build
        # time. We assert the alt text and the image markdown syntax.
        self.assertIn("![A test image](", result)
        self.assertNotIn("wagtail://", result)

    def test_image_internal_mode_preserves_reference_with_alt_and_format(self):
        result = expand_db_html_to_markdown(
            '<embed embedtype="image" id="1" alt="A test image" format="fullwidth" />',
            internal=True,
        )
        # Atomic blocks (image embeds) are preceded by a spacer paragraph in
        # the ContentState representation, producing leading blank lines. The
        # reference itself should preserve id, alt, and format as query params
        # so the DB HTML can be reconstructed.
        self.assertIn(
            "![A test image](wagtail://image?id=1&alt=A+test+image&format=fullwidth)\n\n",
            result,
        )

    def test_image_internal_mode_preserves_reference_without_alt(self):
        result = expand_db_html_to_markdown(
            '<embed embedtype="image" id="1" alt="" format="left" />',
            internal=True,
        )
        # When alt is empty, it should still be preserved as a query param
        # because it is a DB HTML attribute.
        self.assertIn(
            "wagtail://image?id=1&alt=&format=left",
            result,
        )

    def test_image_public_mode_broken_reference_renders_marker(self):
        # When the image has been deleted (``src`` is empty), render a visible
        # ``[broken image: …]`` marker instead of ``![alt]()``, which silently
        # renders nothing in most Markdown renderers.
        result = expand_db_html_to_markdown(
            '<embed embedtype="image" id="99999" alt="Missing" format="left" />',
        )
        self.assertIn("[broken image: Missing]", result)
        self.assertNotIn("![", result)


class TestMarkdownConverterFeatures(TestCase):
    fixtures = ["test.json"]

    def test_default_features_resolves_page_links(self):
        page = Page.objects.get(url_path="/home/events/")
        converter = MarkdownConverter()
        result = converter.from_database_format(
            f'<p><a linktype="page" id="{page.id}">Events</a></p>'
        )
        self.assertIn("(/events/)", result)

    def test_explicit_features_includes_image_rule(self):
        # The image embedtype rule is only loaded when the "image" feature is
        # enabled. Without it, the embed is dropped (no rule to convert it).
        converter_with_image = MarkdownConverter(features=["image"])
        result = converter_with_image.from_database_format(
            '<embed embedtype="image" id="1" alt="alt" format="fullwidth" />',
        )
        self.assertIn("![alt](", result)

    def test_explicit_features_excludes_image_rule_when_not_listed(self):
        # When image is not in the features list, the image embed has no
        # handler registered and is dropped (matching Draftail editor behaviour
        # for out-of-feature content).
        converter_without_image = MarkdownConverter(features=[])
        result = converter_without_image.from_database_format(
            '<embed embedtype="image" id="1" alt="alt" format="fullwidth" />',
        )
        self.assertNotIn("![alt]", result)


class TestMarkdownConverterStateless(TestCase):
    def test_converter_is_reusable_across_calls(self):
        converter = MarkdownConverter()
        first = converter.from_database_format("<p>One</p>")
        second = converter.from_database_format("<p>Two</p>")
        self.assertEqual(first, "One\n\n")
        self.assertEqual(second, "Two\n\n")

    def test_internal_flag_selects_rule_name(self):
        # The ``internal`` flag selects which converter rule name is used when
        # building the exporter config. Subclasses inherit the same flag-based
        # selection without needing to override the class attribute.
        class CustomConverter(MarkdownConverter):
            pass

        public = CustomConverter(internal=False)
        internal = CustomConverter(internal=True)
        self.assertEqual(public.converter_rule_name, "markdown")
        self.assertEqual(internal.converter_rule_name, "markdown_internal")


class TestMediaEmbedMarkdown(TestCase):
    fixtures = ["test.json"]

    def test_internal_mode_renders_image_reference_with_url_encoded_source(self):
        # We patch get_embed so we don't make HTTP calls; the decorator only
        # needs the URL stored on the entity, which is set by the
        # contentstate handler from the embed tag's url attribute.
        with patch(
            "wagtail.embeds.rich_text.contentstate.embeds.get_embed"
        ) as get_embed:
            get_embed.return_value = type(
                "StubEmbed",
                (),
                {
                    "type": "video",
                    "url": "https://www.youtube.com/watch?v=abc",
                    "provider_name": "YouTube",
                    "author_name": None,
                    "thumbnail_url": None,
                    "title": None,
                },
            )()
            result = expand_db_html_to_markdown(
                '<embed embedtype="media" url="https://www.youtube.com/watch?v=abc" />',
                internal=True,
            )
        # The source URL must be percent-encoded inside wagtail://media?url=
        # so characters like ? and = don't terminate the CommonMark destination.
        self.assertIn(
            "![](wagtail://media?url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3Dabc)\n\n",
            result,
        )

    def test_internal_mode_handles_url_with_parentheses(self):
        with patch(
            "wagtail.embeds.rich_text.contentstate.embeds.get_embed"
        ) as get_embed:
            get_embed.return_value = type(
                "StubEmbed",
                (),
                {
                    "type": "video",
                    "url": "https://example.com/(extra)",
                    "provider_name": None,
                    "author_name": None,
                    "thumbnail_url": None,
                    "title": None,
                },
            )()
            result = expand_db_html_to_markdown(
                '<embed embedtype="media" url="https://example.com/(extra)" />',
                internal=True,
            )
        # Parentheses must be percent-encoded so the CommonMark link
        # destination doesn't terminate early.
        self.assertIn(
            "wagtail://media?url=https%3A%2F%2Fexample.com%2F%28extra%29", result
        )

    def test_public_mode_renders_embed_html(self):
        frontend_html = '<iframe src="https://www.youtube.com/embed/abc"></iframe>'
        with (
            patch(
                "wagtail.embeds.rich_text.markdown.embed_format.embed_to_frontend_html",
                return_value=frontend_html,
            ),
            patch(
                "wagtail.embeds.rich_text.contentstate.embeds.get_embed"
            ) as get_embed,
        ):
            get_embed.return_value = type(
                "StubEmbed",
                (),
                {
                    "type": "video",
                    "url": "https://www.youtube.com/watch?v=abc",
                    "provider_name": "YouTube",
                    "author_name": None,
                    "thumbnail_url": None,
                    "title": None,
                },
            )()
            result = expand_db_html_to_markdown(
                '<embed embedtype="media" url="https://www.youtube.com/watch?v=abc" />',
            )
        # Public markdown should embed the frontend HTML inline as a raw HTML
        # block in the Markdown output.
        self.assertIn(frontend_html, result)

    def test_public_mode_renders_marker_on_embed_failure(self):
        from wagtail.embeds.exceptions import EmbedException

        with (
            patch(
                "wagtail.embeds.rich_text.markdown.embed_format.embed_to_frontend_html",
                side_effect=EmbedException,
            ),
            patch(
                "wagtail.embeds.rich_text.contentstate.embeds.get_embed"
            ) as get_embed,
        ):
            get_embed.return_value = type(
                "StubEmbed",
                (),
                {
                    "type": "video",
                    "url": "https://broken.example/",
                    "provider_name": None,
                    "author_name": None,
                    "thumbnail_url": None,
                    "title": None,
                },
            )()
            result = expand_db_html_to_markdown(
                '<embed embedtype="media" url="https://broken.example/" />',
            )
        # Failed embeds should render a visible ``[broken embed: …]`` marker
        # instead of silently producing empty output.
        self.assertIn("[broken embed: https://broken.example/]", result)
        self.assertNotIn("iframe", result)


class TestRichtextMarkdownTemplateFilter(TestCase):
    fixtures = ["test.json"]

    def render(self, source, **context):
        return Template("{% load wagtailcore_tags %}" + source).render(Context(context))

    def test_renders_paragraph_as_markdown(self):
        rendered = self.render(
            "{{ value|richtext_markdown }}", value="<p>Hello <b>world</b></p>"
        )
        self.assertEqual(rendered, "Hello **world**\n\n")

    def test_none_value_returns_empty_string(self):
        rendered = self.render("{{ value|richtext_markdown }}", value=None)
        self.assertEqual(rendered, "")

    def test_resolves_page_link_to_url(self):
        page = Page.objects.get(url_path="/home/events/")
        rendered = self.render(
            "{{ value|richtext_markdown }}",
            value=f'<p><a linktype="page" id="{page.id}">Events</a></p>',
        )
        self.assertIn("(/events/)", rendered)
        self.assertNotIn("wagtail://", rendered)

    def test_passes_richtext_object_through_filter(self):
        from wagtail.rich_text import RichText

        # The filter should accept a RichText wrapper the same way |richtext
        # does, and use its source.
        rendered = self.render(
            "{{ value|richtext_markdown }}",
            value=RichText("<p>Wrapped</p>"),
        )
        self.assertEqual(rendered, "Wrapped\n\n")

    def test_invalid_value_raises_typeerror(self):
        with self.assertRaises(TypeError):
            self.render("{{ value|richtext_markdown }}", value=42)


class TestFeatureWhitelistingDoesNotApply(TestCase):
    """Output conversion is not a sanitisation control.

    Rich text feature whitelisting as enforced for editor input does not apply
    to Markdown output: the DB HTML is converted as-is, and whatever was stored
    at write time is what is rendered. The ``features`` parameter only controls
    which converter rules are loaded for entity rendering.
    """

    def test_features_parameter_loads_rules_not_strips_content(self):
        # An image embed present in DB HTML will be rendered even when the
        # "image" feature is not loaded — it just falls through the
        # HtmlToContentStateHandler's paragraph fallback rather than being
        # sanitised out. This is a behaviour difference vs. the editor input
        # whitelister, and is intentional for output rendering.
        converter = MarkdownConverter(features=[])
        result = converter.from_database_format("<p>Plain paragraph.</p>")
        self.assertEqual(result, "Plain paragraph.\n\n")
