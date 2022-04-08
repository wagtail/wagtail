from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from wagtail.documents.views.bulk_actions.document_bulk_action import DocumentBulkAction


class CollectionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["collection"] = forms.ModelChoiceField(
            queryset=DocumentBulkAction.permission_policy.collections_user_has_permission_for(
                user, "add"
            )
        )


class AddToCollectionBulkAction(DocumentBulkAction):
    display_name = _("Add to collection")
    action_type = "add_to_collection"
    aria_label = _("Add selected documents to collection")
    template_name = "wagtaildocs/bulk_actions/confirm_bulk_add_to_collection.html"
    action_priority = 30
    form_class = CollectionForm
    collection = None

    def check_perm(self, document):
        return self.permission_policy.user_has_permission_for_instance(
            self.request.user, "change", document
        )

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "user": self.request.user}

    def get_execution_context(self):
        return {"collection": self.cleaned_form.cleaned_data["collection"]}

    @classmethod
    def execute_action(cls, objects, collection=None, **kwargs):
        if collection is None:
            return
        num_parent_objects = (
            cls.get_default_model()
            .objects.filter(pk__in=[obj.pk for obj in objects])
            .update(collection=collection)
        )
        return num_parent_objects, 0

    def get_success_message(self, num_parent_objects, num_child_objects):
        collection = self.cleaned_form.cleaned_data["collection"]
        return ngettext(
            "%(num_parent_objects)d document has been added to %(collection)s",
            "%(num_parent_objects)d documents have been added to %(collection)s",
            num_parent_objects,
        ) % {"num_parent_objects": num_parent_objects, "collection": collection}
