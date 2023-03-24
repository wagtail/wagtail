from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.admin.views.bulk_action import BulkAction
from wagtail.snippets.models import get_snippet_models


class SnippetBulkAction(BulkAction):
    models = get_snippet_models()

    def object_context(self, snippet):
        return {
            "item": snippet,
            "edit_url": AdminURLFinder(self.request.user).get_edit_url(snippet),
        }

    def get_context_data(self, **kwargs):
        kwargs.update(
            {
                "model_opts": self.model._meta,
                "header_icon": self.model.snippet_viewset.icon,
            }
        )
        return super().get_context_data(**kwargs)

    def get_execution_context(self):
        return {**super().get_execution_context(), "self": self}
