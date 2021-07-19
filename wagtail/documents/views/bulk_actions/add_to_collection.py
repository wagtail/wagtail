from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from wagtail.core import hooks
from wagtail.core.models.collections import Collection
from wagtail.documents.permissions import permission_policy
from wagtail.documents.views.bulk_actions.document_bulk_action import DocumentBulkAction


class CollectionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['collection'] = forms.ModelChoiceField(
            queryset=Collection.objects.all()
        )


class AddToCollectionBulkAction(DocumentBulkAction):
    display_name = _("Add to collection")
    action_type = "add_to_collection"
    aria_label = _("Add documents to collection")
    template_name = "wagtaildocs/bulk_actions/confirm_bulk_add_to_collection.html"
    action_priority = 30

    def check_perm(self, document):
        return permission_policy.user_has_permission_for_instance(self.request.user, 'change', document)

    def execute_action(cls, documents):
        collection_id = int(cls.request.POST.get('collection'))
        cls.collection_name = Collection.objects.get(id=collection_id).name
        for document in documents:
            cls.num_parent_objects += 1
            document.collection_id = collection_id
            document.save()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CollectionForm()
        return context

    def get_success_message(self):
        return ngettext(
            "%(num_parent_objects)d document has been added to %(collection)s",
            "%(num_parent_objects)d documents have been added to %(collection)s",
            self.num_parent_objects
        ) % {
            'num_parent_objects': self.num_parent_objects,
            'collection': self.collection_name
        }


@hooks.register('register_document_bulk_action')
def add_to_collection(request):
    return AddToCollectionBulkAction(request)
