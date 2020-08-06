from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlquote
from django.utils.translation import gettext as _
from django.views.generic.base import ContextMixin, TemplateResponseMixin, View

from wagtail.admin import messages, signals
from wagtail.admin.action_menu import PageActionMenu
from wagtail.admin.views.pages.utils import get_valid_next_url_from_request
from wagtail.core import hooks
from wagtail.core.models import Page


def add_subpage(request, parent_page_id):
    parent_page = get_object_or_404(Page, id=parent_page_id).specific
    if not parent_page.permissions_for_user(request.user).can_add_subpage():
        raise PermissionDenied

    page_types = [
        (model.get_verbose_name(), model._meta.app_label, model._meta.model_name)
        for model in type(parent_page).creatable_subpage_models()
        if model.can_create_at(parent_page)
    ]
    # sort by lower-cased version of verbose name
    page_types.sort(key=lambda page_type: page_type[0].lower())

    if len(page_types) == 1:
        # Only one page type is available - redirect straight to the create form rather than
        # making the user choose
        verbose_name, app_label, model_name = page_types[0]
        return redirect('wagtailadmin_pages:add', app_label, model_name, parent_page.id)

    return TemplateResponse(request, 'wagtailadmin/pages/add_subpage.html', {
        'parent_page': parent_page,
        'page_types': page_types,
        'next': get_valid_next_url_from_request(request),
    })


class CreateView(TemplateResponseMixin, ContextMixin, View):
    template_name = 'wagtailadmin/pages/create.html'

    def dispatch(self, request, content_type_app_name, content_type_model_name, parent_page_id):
        self.parent_page = get_object_or_404(Page, id=parent_page_id).specific
        self.parent_page_perms = self.parent_page.permissions_for_user(self.request.user)
        if not self.parent_page_perms.can_add_subpage():
            raise PermissionDenied

        try:
            self.content_type = ContentType.objects.get_by_natural_key(content_type_app_name, content_type_model_name)
        except ContentType.DoesNotExist:
            raise Http404

        # Get class
        self.page_class = self.content_type.model_class()

        # Make sure the class is a descendant of Page
        if not issubclass(self.page_class, Page):
            raise Http404

        # page must be in the list of allowed subpage types for this parent ID
        if self.page_class not in self.parent_page.creatable_subpage_models():
            raise PermissionDenied

        if not self.page_class.can_create_at(self.parent_page):
            raise PermissionDenied

        for fn in hooks.get_hooks('before_create_page'):
            result = fn(self.request, self.parent_page, self.page_class)
            if hasattr(result, 'status_code'):
                return result

        self.page = self.page_class(owner=self.request.user)
        self.edit_handler = self.page_class.get_edit_handler()
        self.edit_handler = self.edit_handler.bind_to(request=self.request, instance=self.page)
        self.form_class = self.edit_handler.get_form_class()

        self.next_url = get_valid_next_url_from_request(self.request)

        return super().dispatch(request)

    def post(self, request):
        self.form = self.form_class(
            self.request.POST, self.request.FILES, instance=self.page, parent_page=self.parent_page
        )

        if self.form.is_valid():
            self.page = self.form.save(commit=False)

            is_publishing = bool(self.request.POST.get('action-publish')) and self.parent_page_perms.can_publish_subpage()
            is_submitting = bool(self.request.POST.get('action-submit')) and self.parent_page.has_workflow

            if not is_publishing:
                self.page.live = False

            # Save page
            self.parent_page.add_child(instance=self.page)

            # Save revision
            revision = self.page.save_revision(user=self.request.user, log_action=False)

            # Publish
            if is_publishing:
                for fn in hooks.get_hooks('before_publish_page'):
                    result = fn(self.request, self.page)
                    if hasattr(result, 'status_code'):
                        return result

                revision.publish(user=self.request.user)

                for fn in hooks.get_hooks('after_publish_page'):
                    result = fn(self.request, self.page)
                    if hasattr(result, 'status_code'):
                        return result

            # Submit
            if is_submitting:
                workflow = self.page.get_workflow()
                workflow.start(self.page, self.request.user)

            # Notifications
            if is_publishing:
                if self.page.go_live_at and self.page.go_live_at > timezone.now():
                    messages.success(
                        self.request,
                        _("Page '{0}' created and scheduled for publishing.").format(self.page.get_admin_display_title()),
                        buttons=[
                            messages.button(reverse('wagtailadmin_pages:edit', args=(self.page.id,)), _('Edit'))
                        ]
                    )
                else:
                    buttons = []
                    if self.page.url is not None:
                        buttons.append(messages.button(self.page.url, _('View live'), new_window=True))
                    buttons.append(messages.button(reverse('wagtailadmin_pages:edit', args=(self.page.id,)), _('Edit')))
                    messages.success(
                        self.request,
                        _("Page '{0}' created and published.").format(self.page.get_admin_display_title()),
                        buttons=buttons
                    )

            elif is_submitting:
                buttons = []
                if self.page.is_previewable():
                    buttons.append(
                        messages.button(
                            reverse('wagtailadmin_pages:view_draft', args=(self.page.id,)),
                            _('View draft'),
                            new_window=True
                        ),
                    )

                buttons.append(
                    messages.button(
                        reverse('wagtailadmin_pages:edit', args=(self.page.id,)),
                        _('Edit')
                    )
                )

                messages.success(
                    self.request,
                    _("Page '{0}' created and submitted for moderation.").format(self.page.get_admin_display_title()),
                    buttons=buttons
                )
            else:
                messages.success(self.request, _("Page '{0}' created.").format(self.page.get_admin_display_title()))

            for fn in hooks.get_hooks('after_create_page'):
                result = fn(self.request, self.page)
                if hasattr(result, 'status_code'):
                    return result

            if is_publishing or is_submitting:
                # we're done here
                if self.next_url:
                    # redirect back to 'next' url if present
                    return redirect(self.next_url)
                # redirect back to the explorer
                return redirect('wagtailadmin_explore', self.page.get_parent().id)
            else:
                # Just saving - remain on edit page for further edits
                target_url = reverse('wagtailadmin_pages:edit', args=[self.page.id])
                if self.next_url:
                    # Ensure the 'next' url is passed through again if present
                    target_url += '?next=%s' % urlquote(self.next_url)
                return redirect(target_url)
        else:
            messages.validation_error(
                self.request, _("The page could not be created due to validation errors"), self.form
            )
            self.has_unsaved_changes = True

        self.edit_handler = self.edit_handler.bind_to(form=self.form)

        return self.render_to_response(self.get_context_data())

    def get(self, request):
        signals.init_new_page.send(sender=CreateView, page=self.page, parent=self.parent_page)
        self.form = self.form_class(instance=self.page, parent_page=self.parent_page)
        self.has_unsaved_changes = False
        self.edit_handler = self.edit_handler.bind_to(form=self.form)

        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'content_type': self.content_type,
            'page_class': self.page_class,
            'parent_page': self.parent_page,
            'edit_handler': self.edit_handler,
            'action_menu': PageActionMenu(self.request, view='create', parent_page=self.parent_page),
            'preview_modes': self.page.preview_modes,
            'form': self.form,
            'next': self.next_url,
            'has_unsaved_changes': self.has_unsaved_changes,
        })
        return context
