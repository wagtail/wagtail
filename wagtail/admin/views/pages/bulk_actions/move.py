from django import forms
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from wagtail.admin import widgets
from wagtail.admin.views.pages.bulk_actions.page_bulk_action import PageBulkAction
from wagtail.models import Page


class MoveForm(forms.Form):
    def __init__(self, *args, **kwargs):
        destination = kwargs.pop("destination")
        target_parent_models = kwargs.pop("target_parent_models")
        pages_to_move = kwargs.pop("pages_to_move")
        super().__init__(*args, **kwargs)
        self.fields["chooser"] = forms.ModelChoiceField(
            initial=destination,
            queryset=Page.objects.all(),
            widget=widgets.AdminPageMoveChooser(
                can_choose_root=True,
                user_perms="bulk_move_to",
                target_models=target_parent_models,
                pages_to_move=pages_to_move,
            ),
            label=_("Select a new parent page"),
        )


class MoveBulkAction(PageBulkAction):
    display_name = _("Move")
    action_type = "move"
    aria_label = _("Move selected pages")
    template_name = "wagtailadmin/pages/bulk_actions/confirm_bulk_move.html"
    action_priority = 10
    form_class = MoveForm
    destination = None

    def __init__(self, request, model):
        super().__init__(request, model)
        self.target_parent_models = set()
        self.pages_to_move = []

    def get_form_kwargs(self):
        ctx = super().get_form_kwargs()
        ctx["destination"] = self.destination or Page.get_first_root_node()
        ctx["target_parent_models"] = self.target_parent_models
        ctx["pages_to_move"] = self.pages_to_move
        return ctx

    def check_perm(self, page):
        return page.permissions_for_user(self.request.user).can_move()

    def get_success_message(self, num_parent_objects, num_child_objects):
        success_message = ngettext(
            "%(num_pages)d page has been moved",
            "%(num_pages)d pages have been moved",
            num_parent_objects,
        ) % {"num_pages": num_parent_objects}
        return success_message

    def object_context(self, obj):
        context = super().object_context(obj)
        context["child_pages"] = context["item"].get_descendants().count()
        return context

    def get_actionable_objects(self):
        objects, objects_without_access = super().get_actionable_objects()
        request = self.request

        if objects:
            self.target_parent_models = set(
                objects[0].specific_class.allowed_parent_page_models()
            )
            for obj in objects:
                self.target_parent_models.intersection_update(
                    set(obj.specific_class.allowed_parent_page_models())
                )

        self.pages_to_move = [page.id for page in objects]

        if self.cleaned_form is None:
            if len(self.target_parent_models) == 0:
                return [], {
                    **objects_without_access,
                    "pages_without_common_parent_page": [
                        {
                            "item": page,
                            "can_edit": page.permissions_for_user(
                                self.request.user
                            ).can_edit(),
                        }
                        for page in objects
                    ],
                }
            return objects, objects_without_access

        destination = self.cleaned_form.cleaned_data["chooser"]
        pages = []
        pages_without_destination_access = []
        pages_with_duplicate_slugs = []

        for page in objects:
            if not page.permissions_for_user(request.user).can_move_to(destination):
                pages_without_destination_access.append(page)
            elif not Page._slug_is_available(page.slug, destination, page=page):
                pages_with_duplicate_slugs.append(page)
            else:
                pages.append(page)

        return pages, {
            **objects_without_access,
            "pages_without_destination_access": [
                {
                    "item": page,
                    "can_edit": page.permissions_for_user(self.request.user).can_edit(),
                }
                for page in pages_without_destination_access
            ],
            "pages_with_duplicate_slugs": [
                {
                    "item": page,
                    "can_edit": page.permissions_for_user(self.request.user).can_edit(),
                }
                for page in pages_with_duplicate_slugs
            ],
        }

    def prepare_action(self, pages, pages_without_access):
        request = self.request
        destination = self.cleaned_form.cleaned_data["chooser"]
        if (
            pages_without_access["pages_without_destination_access"]
            or pages_without_access["pages_with_duplicate_slugs"]
        ):
            # this will be picked up by the form
            self.destination = destination
            return TemplateResponse(
                request,
                self.template_name,
                {"destination": destination, **self.get_context_data()},
            )

    def get_execution_context(self):
        return {
            **super().get_execution_context(),
            "destination": self.cleaned_form.cleaned_data["chooser"],
        }

    @classmethod
    def execute_action(cls, objects, destination=None, user=None, **kwargs):
        num_parent_objects = 0
        if destination is None:
            return
        for page in objects:
            page.move(destination, pos="last-child", user=user)
            num_parent_objects += 1
        return num_parent_objects, 0
