from django.conf import settings
from django.utils.html import format_html_join

from wagtail.wagtailadmin.templatetags.wagtailadmin_tags import hook_output
from wagtail.wagtailcore import hooks


@hooks.register('insert_editor_css')
def insert_editor_css():
    css_files = [
    ]
    css_includes = format_html_join('\n', '<link rel="stylesheet" href="{0}/{1}">',
        ((settings.STATIC_URL, filename) for filename in css_files),
    )
    return css_includes + hook_output('insert_hallo_css')


@hooks.register('insert_editor_js')
def insert_editor_js():
    js_files = [
        'wagtailhalloeditor/js/vendor/hallo.js',
        'wagtailhalloeditor/js/hallo-plugins/hallo-wagtaillink.js',
        'wagtailhalloeditor/js/hallo-plugins/hallo-hr.js',
        'wagtailhalloeditor/js/hallo-plugins/hallo-requireparagraphs.js',
        'wagtailhalloeditor/js/rich-text-editor.js',
    ]
    js_includes = format_html_join('\n', '<script src="{0}{1}"></script>',
        ((settings.STATIC_URL, filename) for filename in js_files)
    )
    return js_includes + hook_output('insert_hallo_js')
