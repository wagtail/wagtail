from django import forms
from django.utils.translation import ugettext as _
from wagtail.wagtailcore.models import Page


class PageChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        bits = []
        for ancestor in obj.get_ancestors(inclusive=True).exclude(depth=1):
            bits.append(ancestor.title)
        return ' > '.join(bits)


class ParentChooserForm(forms.Form):
    parent_page = PageChoiceField(
        label=_('Choose parent page'),
        required=True,
        empty_label=None,
        queryset=Page.objects.none(),
        widget=forms.RadioSelect(),
    )

    def __init__(self, valid_parents_qs, *args, **kwargs):
        self.valid_parents_qs = valid_parents_qs
        super(ParentChooserForm, self).__init__(*args, **kwargs)
        self.fields['parent_page'].queryset = self.valid_parents_qs
