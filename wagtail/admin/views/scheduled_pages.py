from datetime import timedelta

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _

from wagtail.admin import messages
from wagtail.admin.ui.components import Component
from wagtail.core.models import Page, UserPagePermissionsProxy


def get_scheduled_pages_for_user(request):
    user_perms = UserPagePermissionsProxy(request.user)
    pages = (
        Page.objects.annotate_approved_schedule()
        .filter(_approved_schedule=True)
        .prefetch_related("content_type")
        .order_by("-first_published_at")
        & user_perms.publishable_pages()
    )

    if getattr(settings, "WAGTAIL_I18N_ENABLED", False):
        pages = pages.select_related("locale")
    return pages


class ScheduledPagesPanel(Component):
    name = "scheduled_pages"
    template_name = "wagtailadmin/scheduled_pages/panel.html"
    order = 200

    def get_context_data(self, parent_context):
        request = parent_context["request"]
        context = super().get_context_data(parent_context)
        context["pages_to_be_scheduled"] = get_scheduled_pages_for_user(request)
        context["request"] = request
        context["csrf_token"] = parent_context["csrf_token"]
        return context


def publish(request, page_id):
    page = get_object_or_404(Page, id=page_id).specific
    if not page.permissions_for_user(request.user).can_publish():
        raise PermissionDenied

    new_go_live_timestamp = timezone.now() - timedelta(seconds=1)
    page.go_live_at = new_go_live_timestamp
    page.save()

    # Save revision
    revision = page.save_revision(user=request.user, log_action=True)
    revision.publish()

    messages.success(
        request,
        _("Page '{0}' has been published.").format(page.get_admin_display_title()),
        extra_tags="time",
    )

    # Redirect
    redirect_to = request.POST.get("next", None)
    if redirect_to and url_has_allowed_host_and_scheme(
        url=redirect_to, allowed_hosts={request.get_host()}
    ):
        return redirect(redirect_to)
    else:
        return redirect("wagtailadmin_explore", page.get_parent().id)


def publish_all_scheduled_confirm(request):

    revisions_to_publish = get_scheduled_pages_for_user(request)

    return TemplateResponse(
        request,
        "wagtailadmin/scheduled_pages/publish_all_confirm.html",
        {
            "revisions_to_publish": revisions_to_publish,
        },
    )


def publish_all_scheduled(request):
    if request.method == "POST":
        new_go_live_timestamp = timezone.now() - timedelta(seconds=1)
        revisions_to_publish = get_scheduled_pages_for_user(request)
        for page in revisions_to_publish:
            page.go_live_at = new_go_live_timestamp
            page.save()
            revision = page.specific.save_revision(user=request.user, log_action=True)
            revision.publish()

        messages.success(
            request,
            _("{0} pages have been published.").format(len(revisions_to_publish)),
            extra_tags="time",
        )

        # Redirect
        redirect_to = request.POST.get("next", None)
        if redirect_to and url_has_allowed_host_and_scheme(
            url=redirect_to, allowed_hosts={request.get_host()}
        ):
            return redirect(redirect_to)
        else:
            return redirect("wagtailadmin_reports:scheduled_pages")
