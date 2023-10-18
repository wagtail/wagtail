from django.conf import settings
from django.db.models import Q

from wagtail.admin.ui.components import Component
from wagtail.permission_policies.pages import PagePermissionPolicy


def get_scheduled_pages_for_user(user):
    user_pages = PagePermissionPolicy().instances_user_has_permission_for(
        user, "publish"
    )
    pages = (
        user_pages.annotate_approved_schedule()
        .filter(Q(_approved_schedule=True) | Q(expire_at__isnull=False))
        .prefetch_related("content_type")
        .prefetch_related("latest_revision", "latest_revision__user")
        .order_by("-first_published_at")
    )

    if getattr(settings, "WAGTAIL_I18N_ENABLED", False):
        pages = pages.select_related("locale")
    return pages


class ScheduledPagesPanel(Component):
    name = "scheduled_pages"
    template_name = "wagtailadmin/home/scheduled_pages.html"
    order = 200

    def get_context_data(self, parent_context):
        request = parent_context["request"]
        context = super().get_context_data(parent_context)
        context["pages_to_be_scheduled"] = get_scheduled_pages_for_user(request.user)[
            :5
        ]
        context["request"] = request
        return context
