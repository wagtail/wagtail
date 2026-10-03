from django.test import SimpleTestCase

from wagtail.admin.rich_text.converters.db_html import (
    DbHTMLConverter,
    RichTextRemoval,
)

#: A feature set matching the ticket's default set plus entity features.
FEATURES = [
    "hr",
    "link",
    "bold",
    "italic",
    "h2",
    "h3",
    "h4",
    "ol",
    "ul",
    "image",
    "embed",
    "document-link",
]


class TestDbHTMLConverterRoundTrip(SimpleTestCase):
    def clean(self, html, features=FEATURES):
        return DbHTMLConverter(features).clean(html)

    def test_clean_html_is_byte_stable(self):
        html = "<p>Hello <strong>world</strong></p>"
        cleaned, removals = self.clean(html)
        self.assertEqual(cleaned, html)
        self.assertEqual(removals, [])

    def test_page_link_reference_preserved(self):
        # Note: handlers rebuild attributes, so the output attribute order is
        # id, linktype — see DbWhitelister's link branch.
        cleaned, removals = self.clean('<p><a linktype="page" id="3">about</a></p>')
        self.assertEqual(cleaned, '<p><a id="3" linktype="page">about</a></p>')
        self.assertEqual(removals, [])

    def test_document_link_reference_preserved(self):
        cleaned, removals = self.clean('<p><a linktype="document" id="5">spec</a></p>')
        self.assertEqual(cleaned, '<p><a id="5" linktype="document">spec</a></p>')
        self.assertEqual(removals, [])

    def test_external_link_preserved(self):
        cleaned, removals = self.clean(
            '<p><a href="https://wagtail.org/">Wagtail</a></p>'
        )
        self.assertEqual(cleaned, '<p><a href="https://wagtail.org/">Wagtail</a></p>')
        self.assertEqual(removals, [])

    def test_image_embed_preserved(self):
        cleaned, removals = self.clean(
            '<embed embedtype="image" id="9" alt="A test image" format="left"/>'
        )
        # Attribute order follows ImageEmbedHandler.get_db_attributes + embedtype
        self.assertEqual(
            cleaned,
            '<embed alt="A test image" embedtype="image" format="left" id="9"/>',
        )
        self.assertEqual(removals, [])

    def test_media_embed_preserved(self):
        cleaned, removals = self.clean(
            '<embed embedtype="media" url="https://vimeo.com/1"/>'
        )
        self.assertEqual(
            cleaned, '<embed embedtype="media" url="https://vimeo.com/1"/>'
        )
        self.assertEqual(removals, [])

    def test_full_document_round_trip(self):
        html = (
            "<h2>Title</h2><p>Text with <b>bold</b> and <i>italic</i></p>"
            "<ol><li>one</li><li>two</li></ol><hr/>"
        )
        cleaned, removals = self.clean(html)
        self.assertEqual(cleaned, html)
        self.assertEqual(removals, [])


class TestDbHTMLConverterStripping(SimpleTestCase):
    def clean(self, html, features=FEATURES):
        return DbHTMLConverter(features).clean(html)

    def test_out_of_feature_element_unwrapped_and_reported(self):
        cleaned, removals = self.clean("<h1>Big title</h1><p>text</p>")
        self.assertEqual(cleaned, "Big title<p>text</p>")
        self.assertEqual(len(removals), 1)
        removal = removals[0]
        self.assertIsInstance(removal, RichTextRemoval)
        self.assertEqual(removal.tag, "h1")
        self.assertEqual(removal.action, "unwrapped")
        self.assertEqual(removal.reason, "feature_disabled")
        self.assertEqual(removal.detail, "<h1>Big title</h1>")

    def test_feature_subset_enforced(self):
        cleaned, removals = self.clean(
            "<p><b>bold</b> <i>italic</i></p>", features=["bold"]
        )
        self.assertEqual(cleaned, "<p><b>bold</b> italic</p>")
        self.assertEqual([r.tag for r in removals], ["i"])

    def test_unknown_linktype_unwrapped_and_reported(self):
        cleaned, removals = self.clean('<p><a linktype="ftp" id="3">x</a></p>')
        self.assertEqual(cleaned, "<p>x</p>")
        self.assertEqual(
            [(r.tag, r.action, r.reason) for r in removals],
            [("a", "unwrapped", "unknown_linktype")],
        )

    def test_unknown_embedtype_removed_and_reported(self):
        cleaned, removals = self.clean(
            '<p>before</p><embed embedtype="video" id="1"/><p>after</p>'
        )
        self.assertEqual(cleaned, "<p>before</p><p>after</p>")
        self.assertEqual(
            [(r.tag, r.action, r.reason) for r in removals],
            [("embed", "removed", "unknown_embedtype")],
        )

    def test_disabled_entity_feature_is_reported(self):
        # 'link' feature not enabled: a page link unwraps like any unknown <a>
        cleaned, removals = self.clean(
            '<p><a linktype="page" id="3">about</a></p>', features=["bold"]
        )
        self.assertEqual(cleaned, "<p>about</p>")
        self.assertEqual(
            [(r.action, r.reason) for r in removals],
            [("unwrapped", "unknown_linktype")],
        )

    def test_link_missing_id_unwrapped_and_reported(self):
        # The editor never produces this, but API clients can; the handler's
        # get_db_attributes would KeyError without the guard.
        cleaned, removals = self.clean('<p><a linktype="page">about</a></p>')
        self.assertEqual(cleaned, "<p>about</p>")
        self.assertEqual(
            [(r.action, r.reason) for r in removals],
            [("unwrapped", "missing_attribute")],
        )

    def test_image_embed_missing_id_removed_and_reported(self):
        cleaned, removals = self.clean(
            '<embed embedtype="image" alt="x" format="left"/>'
        )
        self.assertEqual(cleaned, "")
        self.assertEqual(
            [(r.action, r.reason) for r in removals], [("removed", "missing_attribute")]
        )

    def test_dangling_page_id_preserved(self):
        # Editor parity: broken references are kept for the editor to flag.
        cleaned, removals = self.clean('<p><a linktype="page" id="9999">gone</a></p>')
        self.assertEqual(cleaned, '<p><a id="9999" linktype="page">gone</a></p>')
        self.assertEqual(removals, [])

    def test_div_normalised_to_p_without_report(self):
        cleaned, removals = self.clean("<div>text</div>")
        self.assertEqual(cleaned, "<p>text</p>")
        self.assertEqual(removals, [])


class TestDbHTMLConverterSecurity(SimpleTestCase):
    def clean(self, html, features=FEATURES):
        return DbHTMLConverter(features).clean(html)

    def test_script_tag_never_survives(self):
        cleaned, removals = self.clean("<p>x</p><script>alert(1)</script>")
        self.assertNotIn("<script", cleaned)
        self.assertEqual([r.tag for r in removals], ["script"])

    def test_unwrapped_script_body_with_markup_is_escaped(self):
        # After a <script> is unwrapped, its body survives as a text node;
        # safety depends on the serializer escaping it (formatter=escape in
        # DbHtmlInputWhitelister.clean). Lock that in with a markup-bearing
        # script body.
        cleaned, removals = self.clean(
            "<p>x</p><script>document.write('<img src=x onerror=alert(1)>')</script>"
        )
        self.assertNotIn("<script", cleaned)
        self.assertNotIn("<img", cleaned)
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", cleaned)
        self.assertEqual([r.tag for r in removals], ["script"])

    def test_event_handler_attributes_dropped(self):
        cleaned, removals = self.clean('<p onclick="alert(1)">x</p>')
        self.assertEqual(cleaned, "<p>x</p>")
        # attribute-level drops are silent (editor behaviour)
        self.assertEqual(removals, [])

    def test_javascript_href_dropped(self):
        cleaned, removals = self.clean('<p><a href="javascript:alert(1)">x</a></p>')
        self.assertEqual(cleaned, "<p><a>x</a></p>")

    def test_obfuscated_javascript_href_dropped(self):
        cleaned, _ = self.clean('<p><a href="jav\tascript:alert(1)">x</a></p>')
        self.assertEqual(cleaned, "<p><a>x</a></p>")

    def test_entity_link_surplus_attributes_dropped(self):
        cleaned, removals = self.clean(
            '<p><a linktype="page" id="3" class="evil" href="https://x.test/">a</a></p>'
        )
        self.assertEqual(cleaned, '<p><a id="3" linktype="page">a</a></p>')
        self.assertEqual(removals, [])

    def test_malformed_html_does_not_raise(self):
        cleaned, removals = self.clean("<p>unclosed <b>bold")
        self.assertEqual(cleaned, "<p>unclosed <b>bold</b></p>")


class TestDbHTMLConverterDefaults(SimpleTestCase):
    def test_none_features_uses_registry_defaults(self):
        cleaned, removals = DbHTMLConverter(None).clean("<p><b>x</b></p><h1>y</h1>")
        # bold is a default feature; h1 is not
        self.assertEqual(cleaned, "<p><b>x</b></p>y")
        self.assertEqual([r.tag for r in removals], ["h1"])


class TestDbHTMLConverterNestedContent(SimpleTestCase):
    """Regression tests: unwrapped elements must still have their children cleaned."""

    def clean(self, html, features=FEATURES):
        return DbHTMLConverter(features).clean(html)

    def test_script_inside_unknown_linktype_link_is_stripped(self):
        cleaned, removals = self.clean(
            '<p><a linktype="evil"><script>alert(1)</script></a></p>'
        )
        self.assertEqual(cleaned, "<p>alert(1)</p>")
        self.assertNotIn("<script", cleaned)
        self.assertEqual(
            [(r.tag, r.action, r.reason) for r in removals],
            [
                ("a", "unwrapped", "unknown_linktype"),
                ("script", "unwrapped", "feature_disabled"),
            ],
        )

    def test_img_onerror_inside_unknown_linktype_link_is_stripped(self):
        # img is out-of-features in this feature set (the "image" feature only
        # whitelists <embed embedtype="image">), so the whole tag is unwrapped.
        cleaned, removals = self.clean(
            '<p><a linktype="evil"><img src=x onerror=alert(1)></a></p>'
        )
        self.assertEqual(cleaned, "<p></p>")
        self.assertNotIn("onerror", cleaned)
        self.assertEqual(
            [(r.tag, r.reason) for r in removals],
            [("a", "unknown_linktype"), ("img", "feature_disabled")],
        )

    def test_unknown_linktype_inside_feature_disabled_element(self):
        cleaned, removals = self.clean(
            '<h1><a linktype="evil"><script>alert(1)</script></a></h1>'
        )
        self.assertEqual(cleaned, "alert(1)")
        self.assertNotIn("<script", cleaned)
        self.assertEqual(
            [(r.tag, r.reason) for r in removals],
            [
                ("h1", "feature_disabled"),
                ("a", "unknown_linktype"),
                ("script", "feature_disabled"),
            ],
        )

    def test_embed_without_embedtype_unwrapped_and_reported(self):
        cleaned, removals = self.clean("<p>x</p><embed/>")
        self.assertEqual(cleaned, "<p>x</p>")
        self.assertEqual(
            [(r.tag, r.action, r.reason) for r in removals],
            [("embed", "unwrapped", "feature_disabled")],
        )

    def test_repeated_clean_does_not_accumulate_removals(self):
        converter = DbHTMLConverter(FEATURES)
        converter.clean("<h1>first</h1>")
        cleaned, removals = converter.clean("<h1>second</h1>")
        self.assertEqual(cleaned, "second")
        self.assertEqual(len(removals), 1)
        self.assertEqual(removals[0].detail, "<h1>second</h1>")
