from django import forms
from django.core.exceptions import ValidationError

from wagtail.admin import widgets
from wagtail.core.models import Page, Workflow, WorkflowPage


class AddWorkflowToPageForm(forms.Form):
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
