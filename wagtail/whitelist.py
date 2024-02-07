"""
A generic HTML whitelisting engine, designed to accommodate subclassing to override
specific rules.
"""
import re

from bs4 import BeautifulSoup, Comment, NavigableString, Tag
from django.utils.html import escape

ALLOWED_URL_SCHEMES = ["http", "https", "ftp", "mailto", "tel"]

PROTOCOL_RE = re.compile("^[a-z0-9][-+.a-z0-9]*:")


def check_url(url_string):
    # Remove control characters and other disallowed characters
    # Browsers sometimes ignore these, so that 'jav\tascript:alert("XSS")'
    # is treated as a valid javascript: link

    unescaped = url_string.lower()
    unescaped = unescaped.replace("&lt;", "<")
    unescaped = unescaped.replace("&gt;", ">")
    unescaped = unescaped.replace("&amp;", "&")
    unescaped = re.sub(r"[`\000-\040\177-\240\s]+", "", unescaped)
    unescaped = unescaped.replace("\ufffd", "")
    if PROTOCOL_RE.match(unescaped):
        protocol = unescaped.split(":", 1)[0]
        if protocol not in ALLOWED_URL_SCHEMES:
            return None
    return url_string


def attribute_rule(allowed_attrs):
    """
    Generator for functions that can be used as entries in Whitelister.element_rules.
    These functions accept a tag, and modify its attributes by looking each attribute
    up in the 'allowed_attrs' dict defined here:
    * if the lookup fails, drop the attribute
    * if the lookup returns a callable, replace the attribute with the result of calling
      it - for example `{'title': uppercase}` will replace 'title' with the result of
      uppercasing the title. If the callable returns None, the attribute is dropped.
    * if the lookup returns a truthy value, keep the attribute; if falsy, drop it
    """

    def fn(tag):
        for attr, val in list(tag.attrs.items()):
            rule = allowed_attrs.get(attr)
            if rule:
                if callable(rule):
                    new_val = rule(val)
                    if new_val is None:
                        del tag[attr]
                    else:
                        tag[attr] = new_val
                else:
                    # rule is not callable, just truthy - keep the attribute
                    pass
            else:
                # rule is falsy or absent - remove the attribute
                del tag[attr]

    return fn


allow_without_attributes = attribute_rule({})


DEFAULT_ELEMENT_RULES = {
    "[document]": allow_without_attributes,
    "a": attribute_rule({"href": check_url}),
    "b": allow_without_attributes,
    "br": allow_without_attributes,
    "div": allow_without_attributes,
    "em": allow_without_attributes,
    "h1": allow_without_attributes,
    "h2": allow_without_attributes,
    "h3": allow_without_attributes,
    "h4": allow_without_attributes,
    "h5": allow_without_attributes,
    "h6": allow_without_attributes,
    "hr": allow_without_attributes,
    "i": allow_without_attributes,
    "img": attribute_rule(
        {"src": check_url, "width": True, "height": True, "alt": True}
    ),
    "li": allow_without_attributes,
    "ol": allow_without_attributes,
    "p": allow_without_attributes,
    "strong": allow_without_attributes,
    "sub": allow_without_attributes,
    "sup": allow_without_attributes,
    "ul": allow_without_attributes,
}


class Whitelister:
    element_rules = DEFAULT_ELEMENT_RULES

    def clean(self, html):
        """Clean up an HTML string to contain just the allowed elements /
        attributes"""
        doc = BeautifulSoup(html, "html.parser")
        self.clean_node(doc, doc)

        # Pass strings through django.utils.html.escape when generating the final HTML.
        # This differs from BeautifulSoup's default EntitySubstitution.substitute_html formatter
        # in that it escapes " to &quot; as well as escaping < > & - if we don't do this, then
        # BeautifulSoup will try to be clever and use single-quotes to wrap attribute values,
        # which confuses our regexp-based db-HTML-to-real-HTML conversion.
        return doc.decode(formatter=escape)

    def clean_node(self, doc, node):
        """Clean a BeautifulSoup document in-place"""
        if isinstance(node, NavigableString):
            self.clean_string_node(doc, node)
        elif isinstance(node, Tag):
            self.clean_tag_node(doc, node)
        # This branch is here in case node is a BeautifulSoup object that does
        # not inherit from NavigableString or Tag. I can't find any examples
        # of such a thing at the moment, so this branch is untested.
        else:  # pragma: no cover
            self.clean_unknown_node(doc, node)

    def clean_string_node(self, doc, node):
        # Remove comments
        if isinstance(node, Comment):
            node.extract()
            return

        # by default, nothing needs to be done to whitelist string nodes
        pass

    def clean_tag_node(self, doc, tag):
        # first, whitelist the contents of this tag

        # NB tag.contents will change while this iteration is running, so we need
        # to capture the initial state into a static list() and iterate over that
        # to avoid losing our place in the sequence.
        for child in list(tag.contents):
            self.clean_node(doc, child)

        # see if there is a rule in element_rules for this tag type
        try:
            rule = self.element_rules[tag.name]
        except KeyError:
            # don't recognise this tag name, so KILL IT WITH FIRE
            tag.unwrap()
            return

        # apply the rule
        rule(tag)

    def clean_unknown_node(self, doc, node):
        # don't know what type of object this is, so KILL IT WITH FIRE
        node.decompose()
