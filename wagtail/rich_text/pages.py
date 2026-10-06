import swapper
from django.conf import settings
from django.db.models import Model
from django.utils.html import escape

from wagtail.models import Locale, Site
from wagtail.rich_text import LinkHandler

Page = swapper.load_model("wagtailcore", "Page")


class PageLinkHandler(LinkHandler):
    identifier = "page"

    @staticmethod
    def get_model():
        return Page

    @classmethod
    def get_many(cls, attrs_list: list[dict]) -> list[Model]:
        # Override LinkHandler.get_many to reduce database queries through the
        # use of PageQuerySet.specific() instead of QuerySet.in_bulk().
        instance_ids = [attrs.get("id") for attrs in attrs_list]
        qs = Page.objects.filter(id__in=instance_ids).defer_streamfields().specific()
        pages_by_str_id = {str(page.id): page for page in qs}
        return [pages_by_str_id.get(str(id_)) for id_ in instance_ids]

    @classmethod
    def expand_db_attributes(cls, attrs: dict) -> str:
        return cls.expand_db_attributes_many([attrs])[0]

    @classmethod
    def expand_db_attributes_many(cls, attrs_list: list[dict]) -> list[str]:
        pages = cls.get_many(attrs_list)

        if getattr(settings, "WAGTAIL_I18N_ENABLED", False):
            try:
                locale = Locale.get_active()
            except (LookupError, Locale.DoesNotExist):
                locale = None

            if locale is not None:
                pages = [
                    page._get_localized_for_locale(locale) if page else None
                    for page in pages
                ]

        if any(pages):
            site_root_paths = Site.get_site_root_paths()
            for page in pages:
                if page:
                    page._wagtail_cached_site_root_paths = site_root_paths

        return ['<a href="%s">' % escape(page.url) if page else "<a>" for page in pages]

    @classmethod
    def extract_references(self, attrs):
        # Yields tuples of (content_type_id, object_id, model_path, content_path)
        yield Page, attrs["id"], "", ""
