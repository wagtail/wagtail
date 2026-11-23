from django.utils.functional import cached_property

from wagtail.admin.views.bulk_action import BulkAction
from wagtail.images import get_image_model
from wagtail.permissions import policy_registry


class ImageBulkAction(BulkAction):
    models = [get_image_model()]

    @cached_property
    def permission_policy(self):
        return policy_registry.get_by_type(self.model)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["items_with_no_access"] = [
            {
                "item": image,
                "can_edit": self.permission_policy.user_has_permission_for_instance(
                    self.request.user, "change", image
                ),
            }
            for image in context["items_with_no_access"]
        ]
        return context
