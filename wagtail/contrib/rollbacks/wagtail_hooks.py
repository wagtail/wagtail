"""
Contains Wagtail CMS integration hooks.
"""
from django.conf.urls import include
from django.conf.urls import url
from django.utils.html import format_html

from wagtail.wagtailcore import hooks

from . import admin_urls


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^rollback/', include(admin_urls, namespace='wagtailrollbacks')),
    ]

@hooks.register('insert_editor_js')
def editor_js():
    return """<script>
        $(function () {
            $('#revisions a.disabled').click(function(e) {
                e.preventDefault();
            });
            $('#revisions').on('click', '.pagination a', function(e) {
                e.preventDefault();
                $('#revisions').load($(this).attr('href'));
            });
        });
    </script>"""
