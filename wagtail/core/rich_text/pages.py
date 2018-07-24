from wagtail.core.models import Page
from .feature_registry import LinkHandler


class PageLinkHandler(LinkHandler):
    link_type = 'page'

    @staticmethod
    def get_model():
        return Page

    @classmethod
    def get_instance(cls, attrs):
        page = super().get_instance(attrs)
        if page is None:
            return
        return page.specific

    @classmethod
    def get_html_attributes(cls, instance, for_editor):
        attrs = super().get_html_attributes(instance, for_editor)
        attrs['href'] = instance.specific.url
        if for_editor:
            parent_page = instance.get_parent()
            if parent_page:
                attrs['data-parent-id'] = parent_page.id
        return attrs
