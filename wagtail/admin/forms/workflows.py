from django import forms
from django.core.exceptions import ValidationError
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as __

from wagtail.admin import widgets
from wagtail.core.models import Page, Task, Workflow, WorkflowPage
from wagtail.core.utils import get_model_string


class TaskChooserSearchForm(forms.Form):
    q = forms.CharField(label=__("Search term"), widget=forms.TextInput(), required=False)

    def __init__(self, *args, task_type_choices=None, **kwargs):
        placeholder = kwargs.pop('placeholder', _("Search"))
        super().__init__(*args, **kwargs)
        self.fields['q'].widget.attrs = {'placeholder': placeholder}

        # Add task type filter if there is more than one task type option
        if task_type_choices and len(task_type_choices) > 1:
            self.fields['task_type'] = forms.ChoiceField(
                choices=(
                    # Append an "All types" choice to the beginning
                    [(None, _("All types"))]

                    # The task type choices that are passed in use the models as values, we need
                    # to convert these to something that can be represented in HTML
                    + [
                        (get_model_string(model), verbose_name)
                        for model, verbose_name in task_type_choices
                    ]
                ),
                required=False
            )

        # Save a mapping of task_type values back to the model that we can reference later
        self.task_type_choices = {
            get_model_string(model): model
            for model, verbose_name in task_type_choices
        }

    def is_searching(self):
        """
        Returns True if the user typed a search query
        """
        return self.is_valid() and bool(self.cleaned_data.get('q'))

    @cached_property
    def task_model(self):
        """
        Returns the selected task model.

        This looks for the task model in the following order:
         1) If there's only one task model option, return it
         2) If a task model has been selected, return it
         3) Return the generic Task model
        """
        models = list(self.task_type_choices.values())
        if len(models) == 1:
            return models[0]

        elif self.is_valid():
            model_name = self.cleaned_data.get('task_type')
            if model_name and model_name in self.task_type_choices:
                return self.task_type_choices[model_name]

        return Task

    def specific_task_model_selected(self):
        return self.task_model is not Task


class WorkflowPageForm(forms.ModelForm):
    page = forms.ModelChoiceField(
        queryset=Page.objects.all(),
        widget=widgets.AdminPageChooser(
            target_models=[Page],
            can_choose_root=True
        )
    )

    class Meta:
        model = WorkflowPage
        fields = ['page']

    def clean(self):
        page = self.cleaned_data.get('page')
        try:
            existing_workflow = page.workflowpage.workflow
            if not self.errors and existing_workflow != self.cleaned_data['workflow']:
                # If the form has no errors, Page has an existing Workflow assigned, that Workflow is not
                # the selected Workflow, and overwrite_existing is not True, add a new error. This should be used to
                # trigger the confirmation message in the view. This is why this error is only added if there are no
                # other errors - confirmation should be the final step.
                self.add_error('page', ValidationError(_("This page already has workflow '{0}' assigned.").format(existing_workflow), code='existing_workflow'))
        except AttributeError:
            pass

    def save(self, commit=False):
        page = self.cleaned_data['page']

        if commit:
            WorkflowPage.objects.update_or_create(
                page=page,
                defaults={'workflow': self.cleaned_data['workflow']},
            )


class BaseWorkflowPagesFormSet(forms.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for form in self.forms:
            form.fields['DELETE'].widget = forms.HiddenInput()

    @property
    def empty_form(self):
        empty_form = super().empty_form
        empty_form.fields['DELETE'].widget = forms.HiddenInput()
        return empty_form

    def clean(self):
        """Checks that no two forms refer to the same page object"""
        if any(self.errors):
            # Don't bother validating the formset unless each form is valid on its own
            return

        pages = [
            form.cleaned_data['page']
            for form in self.forms
            # need to check for presence of 'page' in cleaned_data,
            # because a completely blank form passes validation
            if form not in self.deleted_forms and 'page' in form.cleaned_data
        ]
        if len(set(pages)) != len(pages):
            # pages list contains duplicates
            raise forms.ValidationError(_("You cannot assign this workflow to the same page multiple times."))


WorkflowPagesFormSet = forms.inlineformset_factory(
    Workflow, WorkflowPage, form=WorkflowPageForm, formset=BaseWorkflowPagesFormSet, extra=1, can_delete=True, fields=['page']
)
