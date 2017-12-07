from django.utils.html import escape

from wagtail.core.models import Page


class PageLinkHandler:
    """
    PageLinkHandler will be invoked whenever we encounter an <a> element in HTML content
    with an attribute of data-linktype="page". The resulting element in the database
    representation will be:
    <a linktype="page" id="42">hello world</a>
    """
    @staticmethod
    def get_db_attributes(tag):
        """
        Given an <a> tag that we've identified as a page link embed (because it has a
        data-linktype="page" attribute), return a dict of the attributes we should
        have on the resulting <a linktype="page"> element.
        """
        return {'id': tag['data-id']}

    @staticmethod
    def expand_db_attributes(attrs):
        try:
            page = Page.objects.get(id=attrs['id'])

            attrs = 'data-linktype="page" data-id="%d" ' % page.id
            parent_page = page.get_parent()
            if parent_page:
                attrs += 'data-parent-id="%d" ' % parent_page.id

            return '<a %shref="%s">' % (attrs, escape(page.specific.url))
        except Page.DoesNotExist:
            return "<a>"


def page_linktype_handler(attrs):
    try:
        page = Page.objects.get(id=attrs['id'])
        return '<a href="%s">' % escape(page.specific.url)
    except Page.DoesNotExist:
        return "<a>"
