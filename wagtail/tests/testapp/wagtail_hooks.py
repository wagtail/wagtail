from django import forms
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.http import HttpResponse

from wagtail.admin.menu import MenuItem
from wagtail.admin.rich_text import HalloPlugin
from wagtail.admin.search import SearchArea
from wagtail.core import hooks
from wagtail.core.whitelist import allow_without_attributes, attribute_rule, check_url


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
    @property
    def media(self):
        return forms.Media(js=[static('testapp/js/kittens.js')])

    def is_shown(self, request):
        return not request.GET.get('hide-kittens', False)


@hooks.register('register_admin_menu_item')
def register_kittens_menu_item():
    return KittensMenuItem(
        'Kittens!',
        'http://www.tomroyal.com/teaandkittens/',
        classnames='icon icon-kitten',
        attrs={'data-fluffy': 'yes'},
        order=10000
    )


# Admin Other Searches hook
class MyCustomSearchArea(SearchArea):
    def is_shown(self, request):
        return not request.GET.get('hide-option', False)

    def is_active(self, request, current=None):
        return request.GET.get('active-option', False)


@hooks.register('register_admin_search_area')
def register_custom_search_area():
    return MyCustomSearchArea(
        'My Search',
        '/customsearch/',
        classnames='icon icon-custom',
        attrs={'is-custom': 'true'},
        order=10000)


@hooks.register('construct_explorer_page_queryset')
def polite_pages_only(parent_page, pages, request):
    # if the URL parameter polite_pages_only is set,
    # only return pages with a slug that starts with 'hello'
    if request.GET.get('polite_pages_only'):
        pages = pages.filter(slug__startswith='hello')

    return pages


@hooks.register('construct_explorer_page_queryset')
def hide_hidden_pages(parent_page, pages, request):
    # Pages with 'hidden' in their title are hidden. Magic!
    return pages.exclude(title__icontains='hidden')


# register 'blockquote' as a rich text feature supported by a hallo.js plugin
@hooks.register('register_rich_text_features')
def register_blockquote_feature(features):
    features.register_editor_plugin(
        'hallo', 'blockquote', HalloPlugin(
            name='halloblockquote',
            js=['testapp/js/hallo-blockquote.js'],
            css={'all': ['testapp/css/hallo-blockquote.css']},
        )
    )
