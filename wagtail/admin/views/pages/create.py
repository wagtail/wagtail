from urllib.parse import quote, urlencode

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic.base import ContextMixin, TemplateResponseMixin, View

from wagtail.admin import messages, signals
from wagtail.admin.action_menu import PageActionMenu
from wagtail.admin.ui.side_panels import PageSidePanels
from wagtail.admin.utils import get_valid_next_url_from_request
from wagtail.admin.views.generic import HookResponseMixin
from wagtail.models import Locale, Page, PageSubscription, UserPagePermissionsProxy


def add_subpage(request, parent_page_id):
    parent_page = get_object_or_404(Page, id=parent_page_id).specific
    if not parent_page.permissions_for_user(request.user).can_add_subpage():
        raise PermissionDenied

    page_types = [
        (
            model.get_verbose_name(),
            model._meta.app_label,
            model._meta.model_name,
            model.get_page_description(),
        )
        for model in type(parent_page).creatable_subpage_models()
        if model.can_create_at(parent_page)
    ]
    # sort by lower-cased version of verbose name
    page_types.sort(key=lambda page_type: page_type[0].lower())

    if len(page_types) == 1:
        # Only one page type is available - redirect straight to the create form rather than
        # making the user choose
        verbose_name, app_label, model_name, description = page_types[0]
        return redirect("wagtailadmin_pages:add", app_label, model_name, parent_page.id)

    return TemplateResponse(
        request,
        "wagtailadmin/pages/add_subpage.html",
        {
            "parent_page": parent_page,
            "page_types": page_types,
            "next": get_valid_next_url_from_request(request),
        },
    )


class CreateView(TemplateResponseMixin, ContextMixin, HookResponseMixin, View):
    template_name = "wagtailadmin/pages/create.html"

    def dispatch(
        self, request, content_type_app_name, content_type_model_name, parent_page_id
    ):
        self.parent_page = get_object_or_404(Page, id=parent_page_id).specific
        self.parent_page_perms = self.parent_page.permissions_for_user(
            self.request.user
        )
        if not self.parent_page_perms.can_add_subpage():
            raise PermissionDenied

        try:
            self.page_content_type = ContentType.objects.get_by_natural_key(
                content_type_app_name, content_type_model_name
            )
        except ContentType.DoesNotExist:
            raise Http404

        # Get class
        self.page_class = self.page_content_type.model_class()

        # Make sure the class is a descendant of Page
        if not issubclass(self.page_class, Page):
            raise Http404

        # page must be in the list of allowed subpage types for this parent ID
        if self.page_class not in self.parent_page.creatable_subpage_models():
            raise PermissionDenied

        if not self.page_class.can_create_at(self.parent_page):
            raise PermissionDenied

        response = self.run_hook(
            "before_create_page", self.request, self.parent_page, self.page_class
        )
        if response:
            return response

        self.locale = self.parent_page.locale

        # If the parent page is the root page. The user may specify any locale they like
        if self.parent_page.is_root():
            selected_locale = request.GET.get("locale", None) or request.POST.get(
                "locale", None
            )
            if selected_locale:
                self.locale = get_object_or_404(Locale, language_code=selected_locale)

        self.page = self.page_class(owner=self.request.user)
        self.page.locale = self.locale
        self.edit_handler = self.page_class.get_edit_handler()
        self.form_class = self.edit_handler.get_form_class()

        # Note: Comment notifications should be enabled by default for pages that a user creates
        self.subscription = PageSubscription(
            page=self.page, user=self.request.user, comment_notifications=True
        )

        self.next_url = get_valid_next_url_from_request(self.request)

        return super().dispatch(request)

    def post(self, request):
        self.form = self.form_class(
            self.request.POST,
            self.request.FILES,
            instance=self.page,
            subscription=self.subscription,
            parent_page=self.parent_page,
            for_user=self.request.user,
        )

        if self.form.is_valid():
            return self.form_valid(self.form)
        else:
            return self.form_invalid(self.form)

    def form_valid(self, form):
        if (
            bool(self.request.POST.get("action-publish"))
            and self.parent_page_perms.can_publish_subpage()
        ):
            return self.publish_action()
        elif (
            bool(self.request.POST.get("action-submit"))
            and self.parent_page.has_workflow
        ):
            return self.submit_action()
        else:
            return self.save_action()

    def get_edit_message_button(self):
        return messages.button(
            reverse("wagtailadmin_pages:edit", args=(self.page.id,)), _("Edit")
        )

    def get_view_draft_message_button(self):
        return messages.button(
            reverse("wagtailadmin_pages:view_draft", args=(self.page.id,)),
            _("View draft"),
            new_window=False,
        )

    def get_view_live_message_button(self):
        return messages.button(self.page.url, _("View live"), new_window=False)

    def save_action(self):
        self.page = self.form.save(commit=False)
        self.page.live = False

        # Save page
        self.parent_page.add_child(instance=self.page)

        # Save revision
        self.page.save_revision(user=self.request.user, log_action=True)

        # Save subscription settings
        self.subscription.page = self.page
        self.subscription.save()

        # Notification
        messages.success(
            self.request,
            _("Page '%(page_title)s' created.")
            % {"page_title": self.page.get_admin_display_title()},
        )

        response = self.run_hook("after_create_page", self.request, self.page)
        if response:
            return response

        # remain on edit page for further edits
        return self.redirect_and_remain()

    def publish_action(self):
        self.page = self.form.save(commit=False)

        # Save page
        self.parent_page.add_child(instance=self.page)

        # Save revision
        revision = self.page.save_revision(user=self.request.user, log_action=True)

        # Save subscription settings
        self.subscription.page = self.page
        self.subscription.save()

        # Publish
        response = self.run_hook("before_publish_page", self.request, self.page)
        if response:
            return response

        revision.publish(user=self.request.user)

        # get a fresh copy so that any changes coming from revision.publish() are passed on
        self.page.refresh_from_db()

        response = self.run_hook("after_publish_page", self.request, self.page)
        if response:
            return response

        # Notification
        if self.page.go_live_at and self.page.go_live_at > timezone.now():
            messages.success(
                self.request,
                _("Page '%(page_title)s' created and scheduled for publishing.")
                % {"page_title": self.page.get_admin_display_title()},
                buttons=[self.get_edit_message_button()],
            )
        else:
            buttons = []
            if self.page.url is not None:
                buttons.append(self.get_view_live_message_button())
            buttons.append(self.get_edit_message_button())
            messages.success(
                self.request,
                _("Page '%(page_title)s' created and published.")
                % {"page_title": self.page.get_admin_display_title()},
                buttons=buttons,
            )

        response = self.run_hook("after_create_page", self.request, self.page)
        if response:
            return response

        return self.redirect_away()

    def submit_action(self):
        self.page = self.form.save(commit=False)
        self.page.live = False

        # Save page
        self.parent_page.add_child(instance=self.page)

        # Save revision
        self.page.save_revision(user=self.request.user, log_action=True)

        # Submit
        workflow = self.page.get_workflow()
        workflow.start(self.page, self.request.user)

        # Save subscription settings
        self.subscription.page = self.page
        self.subscription.save()

        # Notification
        buttons = []
        if self.page.is_previewable():
            buttons.append(self.get_view_draft_message_button())

        buttons.append(self.get_edit_message_button())

        messages.success(
            self.request,
            _("Page '%(page_title)s' created and submitted for moderation.")
            % {"page_title": self.page.get_admin_display_title()},
            buttons=buttons,
        )

        response = self.run_hook("after_create_page", self.request, self.page)
        if response:
            return response

        return self.redirect_away()

    def redirect_away(self):
        if self.next_url:
            # redirect back to 'next' url if present
            return redirect(self.next_url)
        else:
            # redirect back to the explorer
            return redirect("wagtailadmin_explore", self.page.get_parent().id)

    def redirect_and_remain(self):
        target_url = reverse("wagtailadmin_pages:edit", args=[self.page.id])
        if self.next_url:
            # Ensure the 'next' url is passed through again if present
            target_url += "?next=%s" % quote(self.next_url)
        return redirect(target_url)

    def form_invalid(self, form):
        messages.validation_error(
            self.request,
            _("The page could not be created due to validation errors"),
            self.form,
        )
        self.has_unsaved_changes = True

        return self.render_to_response(self.get_context_data())

    def get(self, request):
        signals.init_new_page.send(
            sender=CreateView, page=self.page, parent=self.parent_page
        )
        self.form = self.form_class(
            instance=self.page,
            subscription=self.subscription,
            parent_page=self.parent_page,
            for_user=self.request.user,
        )
        self.has_unsaved_changes = False

        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bound_panel = self.edit_handler.get_bound_panel(
            request=self.request, instance=self.page, form=self.form
        )
        action_menu = PageActionMenu(
            self.request,
            view="create",
            parent_page=self.parent_page,
            lock=None,
            locked_for_user=False,
        )
        side_panels = PageSidePanels(
            self.request,
            self.page,
            preview_enabled=True,
            comments_enabled=self.form.show_comments_toggle,
            show_schedule_publishing_toggle=self.form.show_schedule_publishing_toggle,
        )

        context.update(
            {
                "content_type": self.page_content_type,
                "page_class": self.page_class,
                "parent_page": self.parent_page,
                "edit_handler": bound_panel,
                "action_menu": action_menu,
                "side_panels": side_panels,
                "form": self.form,
                "next": self.next_url,
                "has_unsaved_changes": self.has_unsaved_changes,
                "locale": None,
                "translations": [],
                "media": bound_panel.media
                + self.form.media
                + action_menu.media
                + side_panels.media,
            }
        )

        if getattr(settings, "WAGTAIL_I18N_ENABLED", False):
            # Pages can be created in any language at the root level
            if self.parent_page.is_root():
                translations = [
                    {
                        "locale": locale,
                        "url": reverse(
                            "wagtailadmin_pages:add",
                            args=[
                                self.page_content_type.app_label,
                                self.page_content_type.model,
                                self.parent_page.id,
                            ],
                        )
                        + "?"
                        + urlencode({"locale": locale.language_code}),
                    }
                    for locale in Locale.objects.all()
                ]

            else:
                user_perms = UserPagePermissionsProxy(self.request.user)
                translations = [
                    {
                        "locale": translation.locale,
                        "url": reverse(
                            "wagtailadmin_pages:add",
                            args=[
                                self.page_content_type.app_label,
                                self.page_content_type.model,
                                translation.id,
                            ],
                        ),
                    }
                    for translation in self.parent_page.get_translations()
                    .only("id", "locale")
                    .select_related("locale")
                    if user_perms.for_page(translation).can_add_subpage()
                    and self.page_class
                    in translation.specific_class.creatable_subpage_models()
                    and self.page_class.can_create_at(translation)
                ]

            context.update(
                {
                    "locale": self.locale,
                    "translations": translations,
                }
            )

        return context
