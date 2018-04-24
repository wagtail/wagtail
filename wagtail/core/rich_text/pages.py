from django.utils.html import escape

from wagtail.core.models import Page


def page_linktype_handler(attrs):
    try:
        page = Page.objects.get(id=attrs['id'])
        return '<a href="%s">' % escape(page.specific.url)
    except Page.DoesNotExist:
        return "<a>"
