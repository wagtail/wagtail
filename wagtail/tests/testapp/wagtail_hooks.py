from django.http import HttpResponse

from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.whitelist import attribute_rule, check_url, allow_without_attributes
from wagtail.wagtailadmin.menu import MenuItem


# Register one hook using decorators...
@hooks.register('insert_editor_css')
def editor_css():
    return """<link rel="stylesheet" href="/path/to/my/custom.css">"""


def editor_js():
    return """<script src="/path/to/my/custom.js"></script>"""
hooks.register('insert_editor_js', editor_js)
# And the other using old-style function calls


def whitelister_element_rules():
    return {
        'blockquote': allow_without_attributes,
        'a': attribute_rule({'href': check_url, 'target': True}),
    }
hooks.register('construct_whitelister_element_rules', whitelister_element_rules)


def block_googlebot(page, request, serve_args, serve_kwargs):
    if request.META.get('HTTP_USER_AGENT') == 'GoogleBot':
        return HttpResponse("<h1>bad googlebot no cookie</h1>")
hooks.register('before_serve_page', block_googlebot)


class KittensMenuItem(MenuItem):
    def is_shown(self, request):
        return not request.GET.get('hide-kittens', False)

@hooks.register('register_admin_menu_item')
def register_kittens_menu_item():
    return KittensMenuItem('Kittens!', 'http://www.tomroyal.com/teaandkittens/', classnames='icon icon-kitten', attrs={'data-fluffy': 'yes'}, order=10000)
