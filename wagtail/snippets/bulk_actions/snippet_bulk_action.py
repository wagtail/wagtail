from django.urls import reverse

from wagtail.admin.views.bulk_action import BulkAction
from wagtail.snippets.models import get_snippet_models


def get_edit_url(app_label, model_name, snippet):
    return reverse(f"wagtailsnippets_{app_label}_{model_name}:edit", args=[snippet.pk])


class SnippetBulkAction(BulkAction):
    models = get_snippet_models()

    def object_context(self, snippet):
        return {
            "item": snippet,
            "edit_url": get_edit_url(
                self.model._meta.app_label, self.model._meta.model_name, snippet
            ),
        }

    def get_execution_context(self):
        return {**super().get_execution_context(), "self": self}
