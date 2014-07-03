import re  # parsing HTML with regexes LIKE A BOSS.

from django.utils.html import escape

from wagtail.wagtailcore.whitelist import Whitelister
from wagtail.wagtailcore.models import Page

from wagtail.wagtaildocs.models import Document

# FIXME: we don't really want to import wagtailimages within core.
# For that matter, we probably don't want core to be concerned about translating
# HTML for the benefit of the hallo.js editor...
from wagtail.wagtailimages.models import get_image_model
from wagtail.wagtailimages.formats import get_image_format

from wagtail.wagtailcore import hooks


# Define a set of 'embed handlers' and 'link handlers'. These handle the translation
# of 'special' HTML elements in rich text - ones which we do not want to include
# verbatim in the DB representation because they embed information which is stored
# elsewhere in the database and is liable to change - from real HTML representation
# to DB representation and back again.

class ImageEmbedHandler(object):
    """
    ImageEmbedHandler will be invoked whenever we encounter an element in HTML content
    with an attribute of data-embedtype="image". The resulting element in the database
    representation will be:
    <embed embedtype="image" id="42" format="thumb" alt="some custom alt text">
    """
    @staticmethod
    def get_db_attributes(tag):
        """
        Given a tag that we've identified as an image embed (because it has a
        data-embedtype="image" attribute), return a dict of the attributes we should
        have on the resulting <embed> element.
        """
        return {
            'id': tag['data-id'],
            'format': tag['data-format'],
            'alt': tag['data-alt'],
        }

    @staticmethod
    def expand_db_attributes(attrs, for_editor):
        """
        Given a dict of attributes from the <embed> tag, return the real HTML
        representation.
        """
        Image = get_image_model()
        try:
            image = Image.objects.get(id=attrs['id'])
            format = get_image_format(attrs['format'])

            if for_editor:
                try:
                    return format.image_to_editor_html(image, attrs['alt'])
                except:
                    return ''
            else:
                return format.image_to_html(image, attrs['alt'])

        except Image.DoesNotExist:
            return "<img>"


class MediaEmbedHandler(object):
    """
    MediaEmbedHandler will be invoked whenever we encounter an element in HTML content
    with an attribute of data-embedtype="media". The resulting element in the database
    representation will be:
    <embed embedtype="media" url="http://vimeo.com/XXXXX">
    """
    @staticmethod
    def get_db_attributes(tag):
        """
        Given a tag that we've identified as a media embed (because it has a
        data-embedtype="media" attribute), return a dict of the attributes we should
        have on the resulting <embed> element.
        """
        return {
            'url': tag['data-url'],
        }

    @staticmethod
    def expand_db_attributes(attrs, for_editor):
        """
        Given a dict of attributes from the <embed> tag, return the real HTML
        representation.
        """
        from wagtail.wagtailembeds import format
        if for_editor:
            return format.embed_to_editor_html(attrs['url'])
        else:
            return format.embed_to_frontend_html(attrs['url'])


class PageLinkHandler(object):
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
    def expand_db_attributes(attrs, for_editor):
        try:
            page = Page.objects.get(id=attrs['id'])

            if for_editor:
                editor_attrs = 'data-linktype="page" data-id="%d" ' % page.id
            else:
                editor_attrs = ''

            return '<a %shref="%s">' % (editor_attrs, escape(page.url))
        except Page.DoesNotExist:
            return "<a>"


class DocumentLinkHandler(object):
    @staticmethod
    def get_db_attributes(tag):
        return {'id': tag['data-id']}

    @staticmethod
    def expand_db_attributes(attrs, for_editor):
        try:
            doc = Document.objects.get(id=attrs['id'])

            if for_editor:
                editor_attrs = 'data-linktype="document" data-id="%d" ' % doc.id
            else:
                editor_attrs = ''

            return '<a %shref="%s">' % (editor_attrs, escape(doc.url))
        except Document.DoesNotExist:
            return "<a>"


EMBED_HANDLERS = {
    'image': ImageEmbedHandler,
    'media': MediaEmbedHandler,
}
LINK_HANDLERS = {
    'page': PageLinkHandler,
    'document': DocumentLinkHandler,
}


# Prepare a whitelisting engine with custom behaviour:
# rewrite any elements with a data-embedtype or data-linktype attribute
class DbWhitelister(Whitelister):
    has_loaded_custom_whitelist_rules = False

    @classmethod
    def clean(cls, html):
        if not cls.has_loaded_custom_whitelist_rules:
            for fn in hooks.get_hooks('construct_whitelister_element_rules'):
                cls.element_rules = cls.element_rules.copy()
                cls.element_rules.update(fn())
            cls.has_loaded_custom_whitelist_rules = True

        return super(DbWhitelister, cls).clean(html)

    @classmethod
    def clean_tag_node(cls, doc, tag):
        if 'data-embedtype' in tag.attrs:
            embed_type = tag['data-embedtype']
            # fetch the appropriate embed handler for this embedtype
            embed_handler = EMBED_HANDLERS[embed_type]
            embed_attrs = embed_handler.get_db_attributes(tag)
            embed_attrs['embedtype'] = embed_type

            embed_tag = doc.new_tag('embed', **embed_attrs)
            embed_tag.can_be_empty_element = True
            tag.replace_with(embed_tag)
        elif tag.name == 'a' and 'data-linktype' in tag.attrs:
            # first, whitelist the contents of this tag
            for child in tag.contents:
                cls.clean_node(doc, child)

            link_type = tag['data-linktype']
            link_handler = LINK_HANDLERS[link_type]
            link_attrs = link_handler.get_db_attributes(tag)
            link_attrs['linktype'] = link_type
            tag.attrs.clear()
            tag.attrs.update(**link_attrs)
        elif tag.name == 'div':
            tag.name = 'p'
        else:
            super(DbWhitelister, cls).clean_tag_node(doc, tag)


FIND_A_TAG = re.compile(r'<a(\b[^>]*)>')
FIND_EMBED_TAG = re.compile(r'<embed(\b[^>]*)/>')
FIND_ATTRS = re.compile(r'([\w-]+)\="([^"]*)"')


def extract_attrs(attr_string):
    """
    helper method to extract tag attributes as a dict. Does not escape HTML entities!
    """
    attributes = {}
    for name, val in FIND_ATTRS.findall(attr_string):
        attributes[name] = val
    return attributes


def expand_db_html(html, for_editor=False):
    """
    Expand database-representation HTML into proper HTML usable in either
    templates or the rich text editor
    """
    def replace_a_tag(m):
        attrs = extract_attrs(m.group(1))
        if 'linktype' not in attrs:
            # return unchanged
            return m.group(0)
        handler = LINK_HANDLERS[attrs['linktype']]
        return handler.expand_db_attributes(attrs, for_editor)

    def replace_embed_tag(m):
        attrs = extract_attrs(m.group(1))
        handler = EMBED_HANDLERS[attrs['embedtype']]
        return handler.expand_db_attributes(attrs, for_editor)

    html = FIND_A_TAG.sub(replace_a_tag, html)
    html = FIND_EMBED_TAG.sub(replace_embed_tag, html)
    return html
