from collections import Mapping
import re

ELEMENT_SELECTOR = re.compile(r'^([\w-]+)$')
ELEMENT_WITH_ATTR_SELECTOR = re.compile(r'^([\w-]+)\[([\w-]+)\]$')
ELEMENT_WITH_ATTR_EXACT_SELECTOR = re.compile(r'^([\w-]+)\[([\w-]+)="(.*)"\]$')


class HTMLRuleset():
    """
    Maintains a set of rules for matching HTML elements.
    Each rule defines a mapping from a CSS-like selector to an arbitrary result object.

    The following forms of rule are currently supported:
    'a' = matches any <a> element
    'a[href]' = matches any <a> element with an 'href' attribute
    'a[linktype="page"]' = matches any <a> element with a 'linktype' attribute equal to 'page'
    """
    def __init__(self, rules=None):
        # mapping of element name to a list of (attr_check, result) tuples
        # where attr_check is a callable that takes an attr dict and returns True if they match
        self.element_rules = {}

        if rules:
            self.add_rules(rules)

    def add_rules(self, rules):
        # accepts either a dict of {selector: result}, or a list of (selector, result) tuples
        if isinstance(rules, Mapping):
            rules = rules.items()

        for selector, result in rules:
            self.add_rule(selector, result)

    def add_rule(self, selector, result):
        match = ELEMENT_SELECTOR.match(selector)
        if match:
            name = match.group(1)
            self.element_rules.setdefault(name, []).append(
                ((lambda attrs: True), result)
            )
            return

        match = ELEMENT_WITH_ATTR_SELECTOR.match(selector)
        if match:
            name, attr = match.groups()
            self.element_rules.setdefault(name, []).append(
                ((lambda attrs: attr in attrs), result)
            )
            return

        match = ELEMENT_WITH_ATTR_EXACT_SELECTOR.match(selector)
        if match:
            name, attr, value = match.groups()
            self.element_rules.setdefault(name, []).append(
                ((lambda attrs: attr in attrs and attrs[attr] == value), result)
            )
            return

    def match(self, name, attrs):
        """
        Look for a rule matching an HTML element with the given name and attribute dict,
        and return the corresponding result object. If no rule matches, return None.
        If multiple rules match, the one chosen is undetermined.
        """
        try:
            rules_to_test = self.element_rules[name]
        except KeyError:
            return None

        for attr_check, result in rules_to_test:
            if attr_check(attrs):
                return result
