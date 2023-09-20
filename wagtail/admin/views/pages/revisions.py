from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from wagtail.admin import messages
from wagtail.admin.action_menu import PageActionMenu
from wagtail.admin.auth import user_has_any_page_permission, user_passes_test
from wagtail.admin.ui.components import MediaContainer
from wagtail.admin.ui.side_panels import (
    CommentsSidePanel,
    PageStatusSidePanel,
    PreviewSidePanel,
)
from wagtail.admin.views.generic.models import (
    RevisionsCompareView,
    RevisionsUnscheduleView,
)
from wagtail.admin.views.generic.preview import PreviewRevision
from wagtail.models import Page
from wagtail.utils.timestamps import render_timestamp


def revisions_index(request, page_id):
    return redirect("wagtailadmin_pages:history", page_id)


def revisions_revert(request, page_id, revision_id):
    page = get_object_or_404(Page, id=page_id).specific
    page_perms = page.permissions_for_user(request.user)
    if not page_perms.can_edit():
        raise PermissionDenied

    revision = get_object_or_404(page.revisions, id=revision_id)
    revision_page = revision.as_object()

    scheduled_page = page.get_scheduled_revision_as_object()

    content_type = ContentType.objects.get_for_model(page)
    page_class = content_type.model_class()

    if getattr(settings, "WAGTAIL_I18N_ENABLED", False):
        locale = page.locale
        translations = [
            {
                "locale": translation.locale,
                "url": reverse("wagtailadmin_pages:edit", args=[translation.id]),
            }
            for translation in page.get_translations()
            .only("id", "locale", "depth")
            .select_related("locale")
            if translation.permissions_for_user(request.user).can_edit()
        ]
    else:
        locale = None
        translations = []

    edit_handler = page_class.get_edit_handler()
    form_class = edit_handler.get_form_class()

    form = form_class(instance=revision_page, for_user=request.user)
    edit_handler = edit_handler.get_bound_panel(
        instance=revision_page, request=request, form=form
    )

    preview_url = reverse("wagtailadmin_pages:preview_on_edit", args=[page.id])
    lock = page.get_lock()

    action_menu = PageActionMenu(
        request,
        view="revisions_revert",
        page=page,
        lock=lock,
        locked_for_user=lock is not None and lock.for_user(request.user),
    )
    side_panels = [
        PageStatusSidePanel(
            revision_page,
            request,
            show_schedule_publishing_toggle=form.show_schedule_publishing_toggle,
            live_object=page,
            scheduled_object=scheduled_page,
            locale=locale,
            translations=translations,
        ),
    ]
    if page.is_previewable():
        side_panels.append(PreviewSidePanel(page, request, preview_url=preview_url))
    if form.show_comments_toggle:
        side_panels.append(CommentsSidePanel(page, request))
    side_panels = MediaContainer(side_panels)

    media = MediaContainer([edit_handler, form, action_menu, side_panels]).media

    user_avatar = render_to_string(
        "wagtailadmin/shared/user_avatar.html", {"user": revision.user}
    )

    messages.warning(
        request,
        mark_safe(
            _(
                "You are viewing a previous version of this page from <b>%(created_at)s</b> by %(user)s"
            )
            % {
                "created_at": render_timestamp(revision.created_at),
                "user": user_avatar,
            }
        ),
    )

    return TemplateResponse(
        request,
        "wagtailadmin/pages/edit.html",
        {
            "page": page,
            "revision": revision,
            "is_revision": True,
            "content_type": content_type,
            "edit_handler": edit_handler,
            "errors_debug": None,
            "action_menu": action_menu,
            "side_panels": side_panels,
            "form": form,  # Used in unit tests
            "media": media,
        },
    )


@method_decorator(user_passes_test(user_has_any_page_permission), name="dispatch")
class RevisionsView(PreviewRevision):
    model = Page

    def setup(self, request, page_id, revision_id, *args, **kwargs):
        # Rename path kwargs from pk to page_id
        return super().setup(request, page_id, revision_id, *args, **kwargs)

    def get_object(self):
        page = get_object_or_404(Page, id=self.pk).specific

        perms = page.permissions_for_user(self.request.user)
        if not (perms.can_publish() or perms.can_edit()):
            raise PermissionDenied

        return page


class RevisionsCompare(RevisionsCompareView):
    history_label = gettext_lazy("Page history")
    edit_label = gettext_lazy("Edit this page")
    history_url_name = "wagtailadmin_pages:history"
    edit_url_name = "wagtailadmin_pages:edit"
    header_icon = "doc-empty-inverse"

    @method_decorator(user_passes_test(user_has_any_page_permission))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return get_object_or_404(Page, id=self.pk).specific

    def get_edit_handler(self):
        return self.object.get_edit_handler()

    def get_page_subtitle(self):
        return self.object.get_admin_display_title()


class RevisionsUnschedule(RevisionsUnscheduleView):
    model = Page
    edit_url_name = "wagtailadmin_pages:edit"
    history_url_name = "wagtailadmin_pages:history"
    revisions_unschedule_url_name = "wagtailadmin_pages:revisions_unschedule"
    header_icon = "doc-empty-inverse"

    def setup(self, request, page_id, revision_id, *args, **kwargs):
        # Rename path kwargs from pk to page_id
        return super().setup(request, page_id, revision_id, *args, **kwargs)

    def get_object(self, queryset=None):
        page = get_object_or_404(Page, id=self.pk).specific

        if not page.permissions_for_user(self.request.user).can_unschedule():
            raise PermissionDenied
        return page

    def get_object_display_title(self):
        return self.object.get_admin_display_title()
