from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from wagtail.admin import widgets
from wagtail.documents.views.bulk_actions.document_bulk_action import DocumentBulkAction


class TagForm(forms.Form):
    tags = forms.Field(label=_("Tags"), widget=widgets.AdminTagWidget)


class AddTagsBulkAction(DocumentBulkAction):
    display_name = _("Tag")
    action_type = "add_tags"
    aria_label = _("Add tags to the selected documents")
    template_name = "wagtaildocs/bulk_actions/confirm_bulk_add_tags.html"
    action_priority = 20
    form_class = TagForm

    def check_perm(self, document):
        return self.permission_policy.user_has_permission_for_instance(
            self.request.user, "change", document
        )

    def get_execution_context(self):
        return {"tags": self.cleaned_form.cleaned_data["tags"].split(",")}

    @classmethod
    def execute_action(cls, objects, tags=[], **kwargs):
        num_parent_objects = 0
        if not tags:
            return
        for document in objects:
            num_parent_objects += 1
            document.tags.add(*tags)
        return num_parent_objects, 0

    def get_success_message(self, num_parent_objects, num_child_objects):
        return ngettext(
            "New tags have been added to %(num_parent_objects)d document",
            "New tags have been added to %(num_parent_objects)d documents",
            num_parent_objects,
        ) % {"num_parent_objects": num_parent_objects}
