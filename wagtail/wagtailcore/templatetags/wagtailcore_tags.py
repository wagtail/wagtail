from __future__ import absolute_import, unicode_literals

from django import template
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe

from wagtail.wagtailcore import __version__
from wagtail.wagtailcore.models import Page
from wagtail.wagtailcore.rich_text import RichText, expand_db_html

register = template.Library()


@register.simple_tag(takes_context=True)
def pageurl(context, page):
    """
    Outputs a page's URL as relative (/foo/bar/) if it's within the same site as the
    current page, or absolute (http://example.com/foo/bar/) if not.
    """
    return page.relative_url(context['request'].site)


@register.simple_tag(takes_context=True)
def slugurl(context, slug):
    """Returns the URL for the page that has the given slug."""
    page = Page.objects.filter(slug=slug).first()

    if page:
        return page.relative_url(context['request'].site)
    else:
        return None


@register.simple_tag
def wagtail_version():
    return __version__


@register.filter
def richtext(value):
    if isinstance(value, RichText):
        # passing a RichText value through the |richtext filter should have no effect
        return value
    elif value is None:
        html = ''
    else:
        html = expand_db_html(value)

    return mark_safe('<div class="rich-text">' + html + '</div>')


@register.simple_tag(takes_context=True)
def include_block(context, value):
    """
    Render the passed item of StreamField content, passing the current template context
    if there's an identifiable way of doing so (i.e. if it has a `render_as_block` method).
    """
    if hasattr(value, 'render_as_block'):
        return value.render_as_block(context=context.flatten())
    else:
        return force_text(value)
