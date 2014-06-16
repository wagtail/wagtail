from django import forms
from django.forms.models import inlineformset_factory
from django.utils.translation import ugettext_lazy as _
import models


class QueryForm(forms.Form):
    query_string = forms.CharField(label=_('Search term(s)/phrase'), 
        help_text=_("""Enter the full search string to match. An 
        exact match is required for your Editors Picks to be 
        displayed, wildcards are NOT allowed."""), 
        required=True)


class EditorsPickForm(forms.ModelForm):
    sort_order = forms.IntegerField(required=False)

    def __init__(self, *args, **kwargs):
        super(EditorsPickForm, self).__init__(*args, **kwargs)
        self.fields['page'].widget = forms.HiddenInput()

    class Meta:
        model = models.EditorsPick

        widgets = {
            'description': forms.Textarea(attrs=dict(rows=3)),
        }


EditorsPickFormSetBase = inlineformset_factory(models.Query, models.EditorsPick, form=EditorsPickForm, can_order=True, can_delete=True, extra=0)


class EditorsPickFormSet(EditorsPickFormSetBase):
    minimum_forms = 1
    minimum_forms_message = _("Please specify at least one recommendation for this search term.")
    def add_fields(self, form, *args, **kwargs):
        super(EditorsPickFormSet, self).add_fields(form, *args, **kwargs)

        # Hide delete and order fields
        form.fields['DELETE'].widget = forms.HiddenInput()
        form.fields['ORDER'].widget = forms.HiddenInput()

        # Remove query field
        del form.fields['query']

    def clean(self):
        # Editors pick must have at least one recommended page to be valid
        # Check there is at least one non-deleted form.
        non_deleted_forms = self.total_form_count()
        non_empty_forms = 0
        for i in xrange(0, self.total_form_count()):
            form = self.forms[i]
            if self.can_delete and self._should_delete_form(form):
                non_deleted_forms -= 1
            if not (form.instance.id is None and not form.has_changed()):
                non_empty_forms += 1
        if (
            non_deleted_forms < self.minimum_forms
            or non_empty_forms < self.minimum_forms
        ):
            raise forms.ValidationError(self.minimum_forms_message)
