from django import forms

from wagtail.wagtailcore.models import Collection
from wagtail.wagtaildocs.models import Document
from wagtail.wagtaildocs.permissions import is_using_collections, collections_with_add_permission_for_user


class DocumentForm(forms.ModelForm):
    required_css_class = "required"

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)

        super(DocumentForm, self).__init__(*args, **kwargs)

        if is_using_collections:
            if user is None:
                self.collections = Collection.objects.all()
            else:
                self.collections = collections_with_add_permission_for_user(user)

            if len(self.collections) == 0:
                raise Exception("Cannot construct DocumentForm for a user with no document collection permissions")
            elif len(self.collections) == 1:
                # don't show collection field if only one collection is available
                del self.fields['collection']
            else:
                self.fields['collection'].queryset = self.collections

    def save(self, commit=True):
        if is_using_collections and len(self.collections) == 1:
            # populate the instance's collection field with the one available collection
            self.instance.collection = self.collections[0]

        return super(DocumentForm, self).save(commit=commit)

    class Meta:
        model = Document
        if is_using_collections:
            fields = ('title', 'file', 'collection', 'tags')
        else:
            fields = ('title', 'file', 'tags')
        widgets = {
            'file': forms.FileInput()
        }
