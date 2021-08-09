from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from wagtail.admin import widgets
from wagtail.core import hooks
from wagtail.documents.views.bulk_actions.document_bulk_action import DocumentBulkAction


class TagForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tags'] = forms.Field(
            widget=widgets.AdminTagWidget
        )


class AddTagsBulkAction(DocumentBulkAction):
    display_name = _("Tag")
    action_type = "add_tags"
    aria_label = _("Add tags to documents")
    template_name = "wagtaildocs/bulk_actions/confirm_bulk_add_tags.html"
    action_priority = 20
    form_class = TagForm

    def check_perm(self, document):
        return self.permission_policy.user_has_permission_for_instance(self.request.user, 'change', document)

    def get_execution_context(self):
        return {
            'tags': self.cleaned_form.cleaned_data['tags'].split(',')
        }

    @classmethod
    def execute_action(cls, objects, **kwargs):
        tags = kwargs.get('tags', [])
        for document in objects:
            cls.num_parent_objects += 1
            document.tags.add(*tags)

    def get_success_message(self):
        return ngettext(
            "New tags have been added to %(num_parent_objects)d document",
            "New tags have been added to %(num_parent_objects)d documents",
            self.num_parent_objects
        ) % {
            'num_parent_objects': self.num_parent_objects
        }


@hooks.register('register_document_bulk_action')
def add_tags(request):
    return AddTagsBulkAction(request)
