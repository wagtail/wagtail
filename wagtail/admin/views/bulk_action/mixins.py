from django.core.exceptions import PermissionDenied

from wagtail.models import ReferenceIndex


class ReferenceIndexMixin:
    def annotate_items(self, items):
        items = super().annotate_items(items)
        self.object_references = ReferenceIndex.get_grouped_references_to_in_bulk(items)
        self.is_protected = False
        for item in self.object_references:
            item._usage_references = self.object_references.get(item)
            self.is_protected = self.is_protected or item._usage_references.is_protected
        return items

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_protected"] = self.is_protected
        return context

    def get_usage_url(self, item):
        return None

    def object_context(self, item):
        context = super().object_context(item)
        context.update(
            {
                "usage_count": (item._usage_references.count()),
                "usage_url": self.get_usage_url(item),
                "is_protected": item._usage_references.is_protected,
            }
        )
        return context

    def prepare_action(self, objects, objects_without_access):
        super().prepare_action(objects, objects_without_access)
        if self.is_protected:
            raise PermissionDenied
