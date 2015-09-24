from django import forms

from wagtail.wagtailcore.models import Collection
from wagtail.wagtaildocs.models import Document
from wagtail.wagtaildocs.permissions import is_using_collections, collections_with_add_permission_for_user


class DocumentForm(forms.ModelForm):
    required_css_class = "required"

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)

        super(DocumentForm, self).__init__(*args, **kwargs)
        if is_using_collections and user is not None:
            self.fields['collection'].queryset = collections_with_add_permission_for_user(user)

    class Meta:
        model = Document
        if is_using_collections:
            fields = ('title', 'file', 'collection', 'tags')
        else:
            fields = ('title', 'file', 'tags')
        widgets = {
            'file': forms.FileInput()
        }
