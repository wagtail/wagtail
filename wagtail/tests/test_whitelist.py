from bs4 import BeautifulSoup
from django.test import TestCase

from wagtail.whitelist import (
    Whitelister,
    allow_without_attributes,
    attribute_rule,
    check_url,
)


class TestCheckUrl(TestCase):
    def test_allowed_url_schemes(self):
        for url_scheme in ["", "http", "https", "ftp", "mailto", "tel"]:
            url = url_scheme + "://www.example.com"
            self.assertTrue(bool(check_url(url)))

    def test_disallowed_url_scheme(self):
        self.assertFalse(bool(check_url("invalid://url")))

    def test_crafty_disallowed_url_scheme(self):
        """
        Some URL parsers do not parse 'jav\tascript:' as a valid scheme.
        Browsers, however, do. The checker needs to catch these crafty schemes
        """
        self.assertFalse(bool(check_url("jav\tascript:alert('XSS')")))


class TestAttributeRule(TestCase):
    def setUp(self):
        self.soup = BeautifulSoup('<b foo="bar">baz</b>', "html5lib")

    def test_no_rule_for_attr(self):
        """
        Test that attribute_rule() drops attributes for
        which no rule has been defined.
        """
        tag = self.soup.b
        fn = attribute_rule({"snowman": "barbecue"})
        fn(tag)
        self.assertEqual(str(tag), "<b>baz</b>")

    def test_rule_true_for_attr(self):
        """
        Test that attribute_rule() does not change attributes
        when the corresponding rule returns True
        """
        tag = self.soup.b
        fn = attribute_rule({"foo": True})
        fn(tag)
        self.assertEqual(str(tag), '<b foo="bar">baz</b>')

    def test_rule_false_for_attr(self):
        """
        Test that attribute_rule() drops attributes
        when the corresponding rule returns False
        """
        tag = self.soup.b
        fn = attribute_rule({"foo": False})
        fn(tag)
        self.assertEqual(str(tag), "<b>baz</b>")

    def test_callable_called_on_attr(self):
        """
        Test that when the rule returns a callable,
        attribute_rule() replaces the attribute with
        the result of calling the callable on the attribute.
        """
        tag = self.soup.b
        fn = attribute_rule({"foo": len})
        fn(tag)
        self.assertEqual(str(tag), '<b foo="3">baz</b>')

    def test_callable_returns_None(self):
        """
        Test that when the rule returns a callable,
        attribute_rule() replaces the attribute with
        the result of calling the callable on the attribute.
        """
        tag = self.soup.b
        fn = attribute_rule({"foo": lambda x: None})
        fn(tag)
        self.assertEqual(str(tag), "<b>baz</b>")

    def test_allow_without_attributes(self):
        """
        Test that attribute_rule() with will drop all
        attributes.
        """
        soup = BeautifulSoup(
            '<b foo="bar" baz="quux" snowman="barbecue"></b>', "html5lib"
        )
        tag = soup.b
        allow_without_attributes(tag)
        self.assertEqual(str(tag), "<b></b>")


class TestWhitelister(TestCase):
    def setUp(self):
        self.whitelister = Whitelister()

    def test_clean_unknown_node(self):
        """
        Unknown node should remove a node from the parent document
        """
        soup = BeautifulSoup("<foo><bar>baz</bar>quux</foo>", "html5lib")
        tag = soup.foo
        self.whitelister.clean_unknown_node("", soup.bar)
        self.assertEqual(str(tag), "<foo>quux</foo>")

    def test_clean_tag_node_cleans_nested_recognised_node(self):
        """
        <b> tags are allowed without attributes. This remains true
        when tags are nested.
        """
        soup = BeautifulSoup('<b><b class="delete me">foo</b></b>', "html5lib")
        tag = soup.b
        self.whitelister.clean_tag_node(tag, tag)
        self.assertEqual(str(tag), "<b><b>foo</b></b>")

    def test_clean_tag_node_disallows_nested_unrecognised_node(self):
        """
        <foo> tags should be removed, even when nested.
        """
        soup = BeautifulSoup("<b><foo>bar</foo></b>", "html5lib")
        tag = soup.b
        self.whitelister.clean_tag_node(tag, tag)
        self.assertEqual(str(tag), "<b>bar</b>")

    def test_clean_string_node_does_nothing(self):
        soup = BeautifulSoup("<b>bar</b>", "html5lib")
        string = soup.b.string
        self.whitelister.clean_string_node(string, string)
        self.assertEqual(str(string), "bar")

    def test_clean_node_does_not_change_navigable_strings(self):
        soup = BeautifulSoup("<b>bar</b>", "html5lib")
        string = soup.b.string
        self.whitelister.clean_node(string, string)
        self.assertEqual(str(string), "bar")

    def test_clean(self):
        """
        Whitelister.clean should remove disallowed tags and attributes from
        a string
        """
        string = '<b foo="bar">snowman <barbecue>Yorkshire</barbecue></b>'
        cleaned_string = self.whitelister.clean(string)
        self.assertEqual(cleaned_string, "<b>snowman Yorkshire</b>")

    def test_clean_comments(self):
        string = "<b>snowman Yorkshire<!--[if gte mso 10]>MS word junk<![endif]--></b>"
        cleaned_string = self.whitelister.clean(string)
        self.assertEqual(cleaned_string, "<b>snowman Yorkshire</b>")

    def test_quoting(self):
        string = '<img alt="Arthur &quot;two sheds&quot; Jackson" sheds="2">'
        cleaned_string = self.whitelister.clean(string)
        self.assertEqual(
            cleaned_string, '<img alt="Arthur &quot;two sheds&quot; Jackson"/>'
        )
