from django.test import TestCase

from wagtail.admin.rich_text.converters.html_ruleset import HTMLRuleset


class TestHTMLRuleset(TestCase):
    def test_html_ruleset(self):
        ruleset = HTMLRuleset(
            {
                "p": "paragraph",
                "a[href]": "link",
                "a[linktype=page]": "page-link",
                'a[linktype="silly page"]': "silly-page-link",
                "a[linktype='sensible page']": "sensible-page-link",
            }
        )

        self.assertIsNone(ruleset.match("div", {}))
        self.assertEqual(ruleset.match("p", {}), "paragraph")
        self.assertEqual(ruleset.match("p", {"class": "intro"}), "paragraph")
        self.assertIsNone(ruleset.match("a", {"class": "button"}))
        self.assertEqual(
            ruleset.match("a", {"class": "button", "href": "http://wagtail.org"}),
            "link",
        )
        self.assertIsNone(
            ruleset.match("a", {"class": "button", "linktype": "document"})
        )
        self.assertEqual(
            ruleset.match("a", {"class": "button", "linktype": "page"}), "page-link"
        )
        self.assertEqual(
            ruleset.match("a", {"class": "button", "linktype": "silly page"}),
            "silly-page-link",
        )
        self.assertEqual(
            ruleset.match("a", {"class": "button", "linktype": "sensible page"}),
            "sensible-page-link",
        )

    def test_precedence(self):
        ruleset = HTMLRuleset()
        ruleset.add_rule("p", "normal-paragraph")
        ruleset.add_rule('p[class="intro"]', "intro-paragraph")
        ruleset.add_rule("p", "normal-paragraph-again")

        self.assertEqual(ruleset.match("p", {"class": "intro"}), "intro-paragraph")
