from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from wagtail.admin.views.pages.bulk_actions.page_bulk_action import PageBulkAction


class PublishBulkAction(PageBulkAction):
    display_name = _("Publish")
    action_type = "publish"
    aria_label = _("Publish selected pages")
    template_name = "wagtailadmin/pages/bulk_actions/confirm_bulk_publish.html"
    action_priority = 40

    def check_perm(self, page):
        return page.permissions_for_user(self.request.user).can_publish()

    def object_context(self, obj):
        context = super().object_context(obj)
        context["draft_descendant_count"] = (
            context["item"].get_descendants().not_live().count()
        )
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["has_draft_descendants"] = any(
            item["draft_descendant_count"] for item in context["items"]
        )
        return context

    def get_execution_context(self):
        return {
            **super().get_execution_context(),
            "include_descendants": self.cleaned_form.cleaned_data[
                "include_descendants"
            ],
        }

    @classmethod
    def execute_action(cls, objects, include_descendants=False, user=None, **kwargs):
        num_parent_objects, num_child_objects = 0, 0
        for page in objects:
            revision = page.get_latest_revision() or page.specific.save_revision(
                user=user
            )
            revision.publish(user=user)
            num_parent_objects += 1

            if include_descendants:
                for draft_descendant_page in (
                    page.get_descendants()
                    .not_live()
                    .defer_streamfields()
                    .specific()
                    .iterator()
                ):
                    if (
                        user is None
                        or draft_descendant_page.permissions_for_user(
                            user
                        ).can_publish()
                    ):
                        draft_descendant_revision = (
                            draft_descendant_page.get_latest_revision()
                            or draft_descendant_page.save_revision(user=user)
                        )
                        draft_descendant_revision.publish(user=user)
                        num_child_objects += 1

        return num_parent_objects, num_child_objects

    def get_success_message(self, num_parent_objects, num_child_objects):
        include_descendants = self.cleaned_form.cleaned_data["include_descendants"]
        if include_descendants and num_child_objects > 0:
            # Translators: This forms a message such as "1 page and 3 child pages have been published"
            return _("%(parent_pages)s and %(child_pages)s have been published") % {
                "parent_pages": self.get_parent_page_text(num_parent_objects),
                "child_pages": self.get_child_page_text(num_child_objects),
            }
        else:
            return ngettext(
                "%(num_parent_objects)d page has been published",
                "%(num_parent_objects)d pages have been published",
                num_parent_objects,
            ) % {"num_parent_objects": num_parent_objects}
