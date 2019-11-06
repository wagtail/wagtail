from django import forms

from wagtail.core.models import Workflow


class WorkflowForm(forms.ModelForm):
    class Meta:
        model = Workflow
        fields = ('name', 'tasks')
