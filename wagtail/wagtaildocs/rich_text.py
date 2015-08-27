from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin.link_choosers import LinkChooser
from wagtail.wagtaildocs.models import get_document_model


class DocumentLinkHandler(LinkChooser):

    id = 'document'
    title = _('Document')
    url_name = 'wagtaildocs:chooser'
    priority = 400

    @staticmethod
    def get_db_attributes(tag):
        return {'id': tag['data-id']}

    @staticmethod
    def expand_db_attributes(attrs, for_editor):
        Document = get_document_model()
        try:
            doc = Document.objects.get(id=attrs['id'])
        except Document.DoesNotExist:
            return {}

        attrs = {'href': doc.url}
        if for_editor:
            attrs['data-id'] = doc.id
        return attrs
