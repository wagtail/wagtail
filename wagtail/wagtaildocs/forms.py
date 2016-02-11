from django import forms
from django.forms.models import modelform_factory

from wagtail.wagtailadmin import widgets
from wagtail.wagtailcore.models import Collection
from wagtail.wagtaildocs.permissions import permission_policy


class BaseDocumentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)

        super(BaseDocumentForm, self).__init__(*args, **kwargs)

        if user is None:
            self.collections = Collection.objects.all()
        else:
            self.collections = (
                permission_policy.collections_user_has_permission_for(user, 'add')
            )

        if self.instance.pk:
            # editing an existing document; ensure that the list of available collections
            # includes its current collection
            self.collections = (
                self.collections | Collection.objects.filter(id=self.instance.collection_id)
            )

        if len(self.collections) == 0:
            raise Exception(
                "Cannot construct DocumentForm for a user with no document collection permissions"
            )
        elif len(self.collections) == 1:
            # don't show collection field if only one collection is available
            del self.fields['collection']
        else:
            self.fields['collection'].queryset = self.collections

    def save(self, commit=True):
        if len(self.collections) == 1:
            # populate the instance's collection field with the one available collection
            self.instance.collection = self.collections[0]

        return super(BaseDocumentForm, self).save(commit=commit)


def get_document_form(model):
    fields = model.admin_form_fields
    if 'collection' not in fields:
        # force addition of the 'collection' field, because leaving it out can
        # cause dubious results when multiple collections exist (e.g adding the
        # document to the root collection where the user may not have permission) -
        # and when only one collection exists, it will get hidden anyway.
        fields = list(fields) + ['collection']

    return modelform_factory(
        model,
        form=BaseDocumentForm,
        fields=fields,
        widgets={
            'tags': widgets.AdminTagWidget,
            'file': forms.FileInput()
        })


def get_document_multi_form(model):
    return modelform_factory(
        model,
        fields=['title', 'tags'],
        widgets={
            'tags': widgets.AdminTagWidget,
            'file': forms.FileInput()
        })
