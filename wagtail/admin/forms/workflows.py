from django import forms
from django.core.exceptions import ValidationError
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as __

from wagtail.admin import widgets
from wagtail.core.models import Page, Task, Workflow, WorkflowPage


def model_name(model):
    return model._meta.app_label + '.' + model.__name__


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
                        (model_name(model), verbose_name)
                        for model, verbose_name in task_type_choices
                    ]
                ),
                required=False
            )

        # Save a mapping of task_type values back to the model that we can reference later
        self.task_type_choices = {
            model_name(model): model
            for model, _ in task_type_choices
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


class AddWorkflowToPageForm(forms.Form):
    """
    A form to assign a Workflow instance to a Page. It is designed to work with a confirmation step if a the chosen Page
    is assigned to an existing Workflow - the result of which is stored in overwrite_existing.
    """
    page = forms.ModelChoiceField(
        queryset=Page.objects.all(),
        widget=widgets.AdminPageChooser(
            target_models=[Page],
            can_choose_root=True
        )
    )
    workflow = forms.ModelChoiceField(queryset=Workflow.objects.active(), widget=forms.HiddenInput())
    overwrite_existing = forms.BooleanField(widget=forms.HiddenInput(), initial=False, required=False)

    def clean(self):
        page = self.cleaned_data.get('page')
        try:
            existing_workflow = page.workflowpage.workflow
            if not self.errors and existing_workflow != self.cleaned_data['workflow'] and not self.cleaned_data['overwrite_existing']:
                # If the form has no errors, Page has an existing Workflow assigned, that Workflow is not
                # the selected Workflow, and overwrite_existing is not True, add a new error. This should be used to
                # trigger the confirmation message in the view. This is why this error is only added if there are no
                # other errors - confirmation should be the final step.
                self.add_error('page', ValidationError(_("This page already has workflow '{0}' assigned. Do you want to overwrite the existing workflow?").format(existing_workflow), code='needs_confirmation'))
        except AttributeError:
            pass

    def save(self):
        page = self.cleaned_data['page']
        workflow = self.cleaned_data['workflow']
        WorkflowPage.objects.update_or_create(
            page=page,
            defaults={'workflow': workflow},
        )
