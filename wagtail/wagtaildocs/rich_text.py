from django.utils.html import escape

from wagtail.wagtaildocs.models import get_document_model


class DocumentLinkHandler(object):
    @staticmethod
    def get_db_attributes(tag):
        return {'id': tag['data-id']}

    @staticmethod
    def expand_db_attributes(attrs, for_editor):
        Document = get_document_model()
        try:
            doc = Document.objects.get(id=attrs['id'])

            if for_editor:
                editor_attrs = 'data-linktype="document" data-id="%d" ' % doc.id
            else:
                editor_attrs = ''

            return '<a %shref="%s">' % (editor_attrs, escape(doc.url))
        except Document.DoesNotExist:
            return "<a>"
