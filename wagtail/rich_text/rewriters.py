"""
Utility classes for rewriting elements of HTML-like strings
"""

import re
from collections import defaultdict
from itertools import chain
from typing import Callable, Tuple

FIND_A_TAG = re.compile(r"<a(\b[^>]*)>")
FIND_EMBED_TAG = re.compile(r"<embed(\b[^>]*)/>")
FIND_ATTRS = re.compile(r'([\w-]+)\="([^"]*)"')


def extract_attrs(attr_string: str) -> dict:
    """
    helper method to extract tag attributes, as a dict of un-escaped strings
    """
    attributes = {}
    for name, val in FIND_ATTRS.findall(attr_string):
        val = (
            val.replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&quot;", '"')
            .replace("&amp;", "&")
        )
        attributes[name] = val
    return attributes


class TagRewriter:
    def __init__(self, rules=None, bulk_rules=None, reference_extractors=None):
        self.rules = rules or {}
        self.bulk_rules = bulk_rules or {}
        self.reference_extractors = reference_extractors or {}

    def get_opening_tag_regex(self):
        raise NotImplementedError

    def get_tag_type_from_attrs(self, attrs):
        raise NotImplementedError

    def get_tag_replacements(self, tag_type, attrs_list):
        # Note: return an empty list for cases when you don't want any replacements made
        raise NotImplementedError

    def __call__(self, html: str) -> str:
        matches_by_tag_type, attrs_by_tag_type = self.extract_tags(html)

        replacements = [
            self.get_tag_replacements(tag_type, attrs_list)
            for tag_type, attrs_list in attrs_by_tag_type.items()
        ]

        offset = 0
        for match, replacement in zip(
            chain(*matches_by_tag_type.values()), chain(*replacements)
        ):
            html = (
                html[: match.start() + offset]
                + replacement
                + html[match.end() + offset :]
            )

            offset += len(replacement) - match.end() + match.start()

        return html

    def extract_tags(self, html: str) -> Tuple[dict, dict]:
        """Helper method to extract and group HTML tags and their attributes.

        Returns the full list of regex matches grouped by tag type as well as
        the tag attribute dictionaries grouped by tag type.
        """
        matches_by_tag_type = defaultdict(list)
        attrs_by_tag_type = defaultdict(list)

        # Regex used to match <tag ...> tags in the HTML.
        re_pattern = self.get_opening_tag_regex()

        for match in re_pattern.finditer(html):
            attrs = extract_attrs(match.group(1))
            tag_type = self.get_tag_type_from_attrs(attrs)

            matches_by_tag_type[tag_type].append(match)
            attrs_by_tag_type[tag_type].append(attrs)

        return matches_by_tag_type, attrs_by_tag_type

    def convert_rule_to_bulk_rule(self, rule: Callable) -> Callable:
        def bulk_rule(args):
            return list(map(rule, args))

        return bulk_rule

    def extract_references(self, html):
        re_pattern = self.get_opening_tag_regex()
        for match in re_pattern.findall(html):
            attrs = extract_attrs(match)
            tag_type = self.get_tag_type_from_attrs(attrs)

            if tag_type not in self.reference_extractors:
                continue

            yield from self.reference_extractors[tag_type](attrs)

        return []


class EmbedRewriter(TagRewriter):
    """
    Rewrites <embed embedtype="foo" /> tags within rich text into the HTML
    fragment given by the embed rule for 'foo'. Each embed rule is a function
    that takes a dict of attributes and returns the HTML fragment.
    """

    def get_opening_tag_regex(self):
        return FIND_EMBED_TAG

    def get_tag_type_from_attrs(self, attrs):
        return attrs.get("embedtype")

    def get_tag_replacements(self, tag_type, attrs_list):
        try:
            rule = self.bulk_rules[tag_type]
        except KeyError:
            rule = None

        if not rule:
            try:
                rule = self.rules[tag_type]
            except KeyError:
                pass
            else:
                rule = self.convert_rule_to_bulk_rule(rule)

        # Silently drop any tags with an unrecognised or missing embedtype attribute.
        return rule(attrs_list) if rule else [""] * len(attrs_list)


class LinkRewriter(TagRewriter):
    """
    Rewrites <a linktype="foo"> tags within rich text into the HTML fragment
    given by the rule for 'foo'. Each link rule is a function that takes a dict
    of attributes and returns the HTML fragment for the opening tag (only).
    """

    def get_opening_tag_regex(self):
        return FIND_A_TAG

    def get_tag_type_from_attrs(self, attrs):
        try:
            return attrs["linktype"]
        except KeyError:
            href = attrs.get("href", None)
            if href:
                # From href attribute we try to detect only the linktypes that we
                # currently support (`external` & `email`, `page` has a default handler)
                # from the link chooser.
                if href.startswith(("http:", "https:")):
                    return "external"
                elif href.startswith("mailto:"):
                    return "email"
                elif href.startswith("#"):
                    return "anchor"

    def get_tag_replacements(self, tag_type, attrs_list):
        if not tag_type:
            # We want to leave links without a linktype attribute unchanged,
            # for example <a name="important-anchor">, so we return an empty
            # list here so that no tag replacements are made.
            return []

        try:
            rule = self.bulk_rules[tag_type]
        except KeyError:
            rule = None

        if not rule:
            try:
                rule = self.rules[tag_type]
            except KeyError:
                if tag_type in ["email", "external", "anchor"]:
                    # We also want to leave links with certain known linktype
                    # attributes alone even if there are no richtext rules
                    # registered for those types, for example
                    # <a href="https://wagtail.org">, so we return an empty
                    # list here so that no tag replacements are made.
                    return []
            else:
                rule = self.convert_rule_to_bulk_rule(rule)

        # Replace unrecognised link types with an empty link.
        return rule(attrs_list) if rule else ["<a>"] * len(attrs_list)


class MultiRuleRewriter:
    """Rewrites HTML by applying a sequence of rewriter functions"""

    def __init__(self, rewriters):
        self.rewriters = rewriters

    def __call__(self, html):
        for rewrite in self.rewriters:
            html = rewrite(html)
        return html

    def extract_references(self, html):
        for rewriter in self.rewriters:
            yield from rewriter.extract_references(html)
