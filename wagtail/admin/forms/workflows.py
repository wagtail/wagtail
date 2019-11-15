from django import forms
from django.core.exceptions import ValidationError

from wagtail.admin import widgets
from wagtail.core.models import Page, Workflow, WorkflowPage


class AddWorkflowToPageForm(forms.Form):
    """
    A form to assign a Workflow instance to a Page. It is designed to work with a confirmation step if a the chosen Page
    is assigned to an existing Workflow - the result of which is stored in overwrite_existing.
    """
    page = forms.ModelChoiceField(queryset=Page.objects.all(), widget=widgets.AdminPageChooser(
            target_models=[Page],
            can_choose_root=True))
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
