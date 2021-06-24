from django import forms
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from wagtail.admin import widgets
from wagtail.admin.views.pages.bulk_actions.page_bulk_action import PageBulkAction
from wagtail.core import hooks
from wagtail.core.models import Page


class MoveForm(forms.Form):
    def __init__(self, *args, **kwargs):
        destination = kwargs.pop('destination')
        super().__init__(*args, **kwargs)
        self.fields['chooser'] = forms.ModelChoiceField(
            initial=destination,
            queryset=Page.objects.all(),
            widget=widgets.AdminPageChooser(can_choose_root=True, user_perms='move_to'),
            label=_("Select a new parent page"),
        )


def before_bulk_move(request, action_type, pages, action_instance):
    if action_type != 'move':
        return
    move_applicable = request.POST.dict().get("move_applicable", False)
    if move_applicable:
        return
    destination_page_id = request.POST.dict()['chooser']
    destination = get_object_or_404(Page, id=destination_page_id)
    pages_without_destination_access = []
    pages_with_duplicate_slugs = []
    for page in pages:
        if not page.permissions_for_user(request.user).can_move_to(destination):
            pages_without_destination_access.append(page)
        if not Page._slug_is_available(page.slug, destination, page=page):
            pages_with_duplicate_slugs.append(page)
    if pages_without_destination_access or pages_with_duplicate_slugs:
        return TemplateResponse(request, action_instance.template_name, {
            'pages_without_destination_access': pages_without_destination_access,
            "pages_with_duplicate_slugs": pages_with_duplicate_slugs,
            'destination': destination,
            **action_instance.get_context_data(destination=destination)
        })


class MoveBulkAction(PageBulkAction):
    display_name = _("Move")
    action_type = "move"
    aria_label = "Move pages"
    template_name = "wagtailadmin/pages/bulk_actions/confirm_bulk_move.html"

    def check_perm(self, page):
        return page.permissions_for_user(self.request.user).can_move()

    def get_success_message(self):
        success_message = ngettext(
            "%(num_pages)d page has been moved",
            "%(num_pages)d pages have been moved",
            self.num_parent_objects
        ) % {
            'num_pages': self.num_parent_objects
        }
        return success_message

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        destination = kwargs.get('destination', Page.get_first_root_node())
        context['form'] = MoveForm(destination=destination)
        return context

    def execute_action(cls, pages):
        destination_page_id = cls.request.POST.dict().pop("chooser")
        destination = get_object_or_404(Page, id=destination_page_id)

        for page in pages:
            if not page.permissions_for_user(cls.request.user).can_move_to(destination):
                continue
            if not Page._slug_is_available(page.slug, destination, page=page):
                continue
            page.move(destination, pos='last-child', user=cls.request.user)
            cls.num_parent_objects += 1

    # register temporary hook to check for move related permissions
    @hooks.register_temporarily('before_bulk_action', before_bulk_move)
    def post(self, request):
        return super().post(request)


@hooks.register('register_page_bulk_action')
def move(request):
    return MoveBulkAction(request)
