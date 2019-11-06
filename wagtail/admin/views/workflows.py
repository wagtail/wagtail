from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext_lazy

from wagtail.admin import messages
from wagtail.admin.forms.workflows import WorkflowForm
from wagtail.admin.views.generic import CreateView, DeleteView, EditView, IndexView
from wagtail.core import hooks
from wagtail.core.models import Workflow
from wagtail.core.permissions import workflow_permission_policy


class Index(IndexView):
    permission_policy = workflow_permission_policy
    model = Workflow
    context_object_name = 'workflows'
    template_name = 'wagtailadmin/workflows/index.html'
    add_url_name = 'wagtailadmin_workflows:add'
    page_title = ugettext_lazy("Workflows")
    add_item_label = ugettext_lazy("Add a workflow")
    header_icon = 'placeholder'

    def get_queryset(self):
        return Workflow.objects.all()


class Create(CreateView):
    permission_policy = workflow_permission_policy
    form_class = WorkflowForm
    page_title = ugettext_lazy("Add workflow")
    success_message = ugettext_lazy("Workflow '{0}' created.")
    add_url_name = 'wagtailadmin_workflows:add'
    edit_url_name = 'wagtailadmin_workflows:edit'
    index_url_name = 'wagtailadmin_workflows:index'
    header_icon = 'placeholder'
