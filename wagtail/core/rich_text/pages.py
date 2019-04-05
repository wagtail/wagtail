from django.utils.html import escape

from wagtail.core.models import Page


class PageLinkHandler:
    @staticmethod
    def expand_db_attributes(attrs):
        try:
            page = Page.objects.get(id=attrs['id'])
            return '<a href="%s">' % escape(page.specific.url)
        except Page.DoesNotExist:
            return "<a>"
