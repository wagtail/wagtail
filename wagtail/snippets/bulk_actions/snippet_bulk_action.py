from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.admin.views.bulk_action import BulkAction
from wagtail.snippets.models import get_snippet_models


class SnippetBulkAction(BulkAction):
    @classmethod
    def get_models(cls):
        # We used to set `models = get_snippet_models()` directly on the class,
        # but this is problematic because it means that the list of models is
        # evaluated at import time.

        # Bulk actions are normally registered in wagtail_hooks.py, but snippets
        # can also be registered in wagtail_hooks.py. Evaluating
        # get_snippet_models() at import time could result in either a circular
        # import or an incomplete list of models.

        # Update the models list with the latest registered snippets in case
        # there is user code that still accesses cls.models instead of calling
        # this get_models() method.
        cls.models = get_snippet_models()
        return cls.models

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
