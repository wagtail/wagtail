"""Sphinx Wagtail theme"""

import os
from importlib.metadata import version


__version__ = version("sphinx-wagtail-theme")
__version_full__ = __version__


def get_html_theme_path():
    """Return absolute path to parent folder of installed theme."""

    return os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def update_context(app, pagename, templatename, context, doctree):
    """Update the rendering context for a page.

    This function makes the theme version available in the Jinja2 html
    templates as `{{ theme_version }}`.

    Additionally we tweak the rendering context in an unconventional way. We
    are inspecting the context to see whether the page meta data has an entry
    `template`. If so, we expect the value of that entry to be the name of a
    template file that should be used for rendering instead of the default
    template `page.html`.

    A field field list near the top of a reST source file is passed on by
    Sphinx as file metadata. For example, a line `:template: sitemap.html'
    right at the beginning of a reST file will tell Sphinx to use the template
    file `sitemap.html` for this page instead of the default template file
    `page.html`.

    """
    context['theme_version'] = __version__
    return app.builder.env.metadata.get(pagename, {}).get('template')


def setup(app):
    """Setup functionality called by Sphinx"""
    app.connect('html-page-context', update_context)
    if hasattr(app, 'add_html_theme'):
        theme_path = os.path.abspath(os.path.dirname(__file__))
        app.add_html_theme("sphinx_wagtail_theme", theme_path)
    # unconfirmed: just assuming that parallel_write_safe is ok
    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
