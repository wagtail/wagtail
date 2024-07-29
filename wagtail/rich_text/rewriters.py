"""
Utility classes for rewriting elements of HTML-like strings
"""

import re
from collections import defaultdict
from typing import Callable

from django.utils.functional import cached_property

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


class TagMatch:
    """Represents a single matched tag in a rich text string"""

    def __init__(self, match):
        self.match = match  # a regexp match object
        self.replacement = None  # to be filled in by the rewriter

    @cached_property
    def attrs(self):
        return extract_attrs(self.match.group(1))

    @property
    def start(self):
        return self.match.start()

    @property
    def end(self):
        return self.match.end()


class TagRewriter:
    def __init__(self, rules=None, bulk_rules=None, reference_extractors=None):
        self.rules = rules or {}
        self.bulk_rules = bulk_rules or {}
        self.reference_extractors = reference_extractors or {}

    def get_opening_tag_regex(self):
        raise NotImplementedError

    def get_tag_type_from_attrs(self, attrs):
        """Given a dict of attributes from a tag, return the tag type."""
        raise NotImplementedError

    def get_tag_replacements(self, tag_type, attrs_list):
        """Given a list of attribute dicts, all taken from tags of the same type, return a
        corresponding list of replacement strings to replace the tags with.

        Return an empty list for cases when you don't want any replacements made.
        """
        raise NotImplementedError

    def __call__(self, html: str) -> str:
        matches_by_tag_type = self.extract_tags(html)
        matches_to_replace = []

        # For each tag type, get the list of replacement strings for all tags of that type
        for tag_type, tag_matches in matches_by_tag_type.items():
            attr_dicts = [match.attrs for match in tag_matches]
            replacements = self.get_tag_replacements(tag_type, attr_dicts)

            if not replacements:
                continue

            for match, replacement in zip(tag_matches, replacements):
                match.replacement = replacement
                matches_to_replace.append(match)

        # Replace the tags in order of appearance in the string, so that offsets remain valid
        matches_to_replace.sort(key=lambda match: match.start)

        offset = 0
        for match in matches_to_replace:
            html = (
                html[: match.start + offset]
                + match.replacement
                + html[match.end + offset :]
            )

            offset += len(match.replacement) - match.end + match.start

        return html

    def extract_tags(self, html: str) -> dict[str, list[TagMatch]]:
        """Helper method to extract and group HTML tags and their attributes.

        Returns a dict of TagMatch objects, mapping tag types to a list of all TagMatch objects of that tag type.
        """
        matches_by_tag_type = defaultdict(list)

        # Regex used to match <tag ...> tags in the HTML.
        re_pattern = self.get_opening_tag_regex()

        for re_match in re_pattern.finditer(html):
            tag_match = TagMatch(re_match)
            tag_type = self.get_tag_type_from_attrs(tag_match.attrs)

            matches_by_tag_type[tag_type].append(tag_match)

        return matches_by_tag_type

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
