"""
A generic HTML whitelisting engine, designed to accommodate subclassing to override
specific rules.
"""
from bs4 import BeautifulSoup, NavigableString, Tag
from urlparse import urlparse


ALLOWED_URL_SCHEMES = ['', 'http', 'https', 'ftp', 'mailto', 'tel']


def check_url(url_string):
    # TODO: more paranoid checks (urlparse doesn't catch
    # "jav\tascript:alert('XSS')")
    url = urlparse(url_string)
    return (url_string if url.scheme in ALLOWED_URL_SCHEMES else None)


def attribute_rule(allowed_attrs):
    """
    Generator for functions that can be used as entries in Whitelister.element_rules.
    These functions accept a tag, and modify its attributes by looking each attribute
    up in the 'allowed_attrs' dict defined here:
    * if the lookup fails, drop the attribute
    * if the lookup returns a callable, replace the attribute with the result of calling
      it - e.g. {'title': uppercase} will replace 'title' with the result of uppercasing
      the title. If the callable returns None, the attribute is dropped
    * if the lookup returns a truthy value, keep the attribute; if falsy, drop it
    """
    def fn(tag):
        for attr, val in tag.attrs.items():
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


class Whitelister(object):
    element_rules = {
        '[document]': allow_without_attributes,
        'a': attribute_rule({'href': check_url}),
        'b': allow_without_attributes,
        'br': allow_without_attributes,
        'div': allow_without_attributes,
        'em': allow_without_attributes,
        'h1': allow_without_attributes,
        'h2': allow_without_attributes,
        'h3': allow_without_attributes,
        'h4': allow_without_attributes,
        'h5': allow_without_attributes,
        'h6': allow_without_attributes,
        'hr': allow_without_attributes,
        'i': allow_without_attributes,
        'img': attribute_rule({'src': check_url, 'width': True, 'height': True, 'alt': True}),
        'li': allow_without_attributes,
        'ol': allow_without_attributes,
        'p': allow_without_attributes,
        'strong': allow_without_attributes,
        'sub': allow_without_attributes,
        'sup': allow_without_attributes,
        'ul': allow_without_attributes,
    }

    @classmethod
    def clean(cls, html):
        """Clean up an HTML string to contain just the allowed elements / attributes"""
        doc = BeautifulSoup(html, 'lxml')
        cls.clean_node(doc, doc)
        return unicode(doc)

    @classmethod
    def clean_node(cls, doc, node):
        """Clean a BeautifulSoup document in-place"""
        if isinstance(node, NavigableString):
            cls.clean_string_node(doc, node)
        elif isinstance(node, Tag):
            cls.clean_tag_node(doc, node)
        else:
            cls.clean_unknown_node(doc, node)

    @classmethod
    def clean_string_node(cls, doc, str):
        # by default, nothing needs to be done to whitelist string nodes
        pass

    @classmethod
    def clean_tag_node(cls, doc, tag):
        # first, whitelist the contents of this tag

        # NB tag.contents will change while this iteration is running, so we need
        # to capture the initial state into a static list() and iterate over that
        # to avoid losing our place in the sequence.
        for child in list(tag.contents):
            cls.clean_node(doc, child)

        # see if there is a rule in element_rules for this tag type
        try:
            rule = cls.element_rules[tag.name]
        except KeyError:
            # don't recognise this tag name, so KILL IT WITH FIRE
            tag.unwrap()
            return

        # apply the rule
        rule(tag)

    @classmethod
    def clean_unknown_node(cls, doc, node):
        # don't know what type of object this is, so KILL IT WITH FIRE
        node.decompose()
