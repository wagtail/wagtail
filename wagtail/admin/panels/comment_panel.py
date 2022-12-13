from django.contrib.auth import get_user_model
from modelcluster.models import get_serializable_data_for_fields

from wagtail.admin.forms.comments import CommentForm
from wagtail.admin.templatetags.wagtailadmin_tags import avatar_url, user_display_name
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
                    "form": CommentForm,
                    "fields": ["text", "contentpath", "position"],
                    "formset_name": "comments",
                    "inherit_kwargs": ["for_user"],
                }
            },
        }

    @property
    def clean_name(self):
        return super().clean_name or "commments"

    class BoundPanel(Panel.BoundPanel):
        template_name = "wagtailadmin/panels/comments/comment_panel.html"

        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)

            def user_data(user):
                return {"name": user_display_name(user), "avatar_url": avatar_url(user)}

            user = getattr(self.request, "user", None)
            user_pks = {user.pk}
            serialized_comments = []
            bound = self.form.is_bound
            comment_formset = self.form.formsets.get("comments")
            comment_forms = comment_formset.forms if comment_formset else []
            for form in comment_forms:
                # iterate over comments to retrieve users (to get display names) and serialized versions
                replies = []
                for reply_form in form.formsets["replies"].forms:
                    user_pks.add(reply_form.instance.user_id)
                    reply_data = get_serializable_data_for_fields(reply_form.instance)
                    reply_data["deleted"] = (
                        reply_form.cleaned_data.get("DELETE", False) if bound else False
                    )
                    replies.append(reply_data)
                user_pks.add(form.instance.user_id)
                data = get_serializable_data_for_fields(form.instance)
                data["deleted"] = (
                    form.cleaned_data.get("DELETE", False) if bound else False
                )
                data["resolved"] = (
                    form.cleaned_data.get("resolved", False)
                    if bound
                    else form.instance.resolved_at is not None
                )
                data["replies"] = replies
                serialized_comments.append(data)

            authors = {
                str(user.pk): user_data(user)
                for user in get_user_model()
                .objects.filter(pk__in=user_pks)
                .select_related("wagtail_userprofile")
            }

            comments_data = {
                "comments": serialized_comments,
                "user": user.pk,
                "authors": authors,
            }

            context["comments_data"] = comments_data
            return context

        def show_panel_furniture(self):
            return False
