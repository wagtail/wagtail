from wagtail.admin.forms.comments import CommentForm, CommentFormSet
from wagtail.models import COMMENTS_RELATION_NAME

from .base import Panel


class CommentPanel(Panel):
    def get_form_options(self):
        # add the comments formset
        return {
            # Adds the comment notifications field to the form.
            # Note, this field is defined directly on WagtailAdminPageForm.
            "fields": ["comment_notifications"],
            "formsets": {
                COMMENTS_RELATION_NAME: {
                    "formset": CommentFormSet,
                    "form": CommentForm,
                    "fields": ["text", "contentpath", "position"],
                    "formset_name": "comments",
                    "inherit_kwargs": ["for_user"],
                }
            },
        }

    @property
    def clean_name(self):
        return super().clean_name or "comments"

    class BoundPanel(Panel.BoundPanel):
        template_name = "wagtailadmin/panels/comments/comment_panel.html"

        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)

            user = getattr(self.request, "user", None)
            bound = self.form.is_bound
            if comment_formset := self.form.formsets.get("comments"):
                comments_data = comment_formset.serialize(bound, user)
            else:
                comments_data = {"comments": [], "user": user.pk, "authors": {}}

            context["comments_data"] = comments_data
            return context

        def show_panel_furniture(self):
            return False
