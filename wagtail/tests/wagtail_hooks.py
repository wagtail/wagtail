from wagtail.wagtailadmin import hooks
from wagtail.wagtailcore.whitelist import attribute_rule, check_url, allow_without_attributes

def editor_css():
    return """<link rel="stylesheet" href="/path/to/my/custom.css">"""
hooks.register('insert_editor_css', editor_css)


def editor_js():
    return """<script src="/path/to/my/custom.js"></script>"""
hooks.register('insert_editor_js', editor_js)


def whitelister_element_rules():
    return {
        'blockquote': allow_without_attributes,
        'a': attribute_rule({'href': check_url, 'target': True}),
    }
hooks.register('construct_whitelister_element_rules', whitelister_element_rules)
