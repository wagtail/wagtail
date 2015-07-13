from django.conf import settings
from django.utils.html import format_html, format_html_join

from wagtail.wagtailcore import hooks


@hooks.register('insert_richtexteditor_js')
def docs_richtexteditor_js():
    js_files = [
        'wagtailrichtexteditor/js/hallo-plugins/hallo-wagtaildoclink.js',
    ]
    js_includes = format_html_join('\n', '<script src="{0}{1}"></script>',
        ((settings.STATIC_URL, filename) for filename in js_files)
    )
    return js_includes + format_html(
        """
        <script>
            registerHalloPlugin('hallowagtaildoclink');
        </script>
        """
    )


# embeds


@hooks.register('insert_richtexteditor_js')
def embeds_richtexteditor_js():
    return format_html("""
            <script src="{0}{1}"></script>
            <script>
                registerHalloPlugin('hallowagtailembeds');
            </script>
        """,
        settings.STATIC_URL,
        'wagtailrichtexteditor/js/hallo-plugins/hallo-wagtailembeds.js',
    )


@hooks.register('insert_richtexteditor_js')
def images_richtexteditor_js():
    js_files = [
        'wagtailrichtexteditor/js/hallo-plugins/hallo-wagtailimage.js',
    ]
    js_includes = format_html_join('\n', '<script src="{0}{1}"></script>',
        ((settings.STATIC_URL, filename) for filename in js_files)
    )
    return js_includes + format_html(
        """
        <script>
            registerHalloPlugin('hallowagtailimage');
        </script>
        """,
    )
