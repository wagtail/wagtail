from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext_lazy

from wagtail.admin import messages
from wagtail.admin.edit_handlers import ObjectList, FieldPanel, InlinePanel, get_edit_handler
from wagtail.admin.views.generic import CreateView, DeleteView, EditView, IndexView
from wagtail.core import hooks
from wagtail.core.models import Workflow
from wagtail.admin.views.pages import get_valid_next_url_from_request
from wagtail.core.permissions import workflow_permission_policy
from django.shortcuts import get_object_or_404, redirect, render

Workflow.panels = [
                    FieldPanel("name"),
                    InlinePanel("workflow_tasks"),
                    ]

def get_handler():
    handler = ObjectList(Workflow.panels)
    handler.bind_to(model=Workflow)
    return handler


Workflow.get_edit_handler = get_handler


class Index(IndexView):
    permission_policy = workflow_permission_policy
    model = Workflow
    context_object_name = 'workflows'
    template_name = 'wagtailadmin/workflows/index.html'
    add_url_name = 'wagtailadmin_workflows:add'
    page_title = ugettext_lazy("Workflows")
    add_item_label = ugettext_lazy("Add a workflow")
    header_icon = 'placeholder'


def create(request):
    workflow = Workflow()
    edit_handler = Workflow.get_edit_handler()
    edit_handler = edit_handler.bind_to(request=request, instance=workflow)
    form_class = edit_handler.get_form_class()

    next_url = get_valid_next_url_from_request(request)

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=workflow)
        if form.is_valid():
            workflow = form.save()
    else:
        form = form_class(instance=workflow)

    edit_handler = edit_handler.bind_to(form=form)

    return render(request, 'wagtailadmin/workflows/create.html', {
        'edit_handler': edit_handler,
        'form': form,
        'icon': 'placeholder',
        'title': ugettext_lazy("Workflows"),
        'next': next_url,
    })


def edit(request, pk):
    workflow = get_object_or_404(Workflow, pk=pk)
    edit_handler = Workflow.get_edit_handler()
    edit_handler = edit_handler.bind_to(request=request, instance=workflow)
    form_class = edit_handler.get_form_class()

    next_url = get_valid_next_url_from_request(request)

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=workflow)
        if form.is_valid():
            workflow = form.save()
    else:
        form = form_class(instance=workflow)

    edit_handler = edit_handler.bind_to(form=form)

    return render(request, 'wagtailadmin/workflows/create.html', {
        'edit_handler': edit_handler,
        'form': form,
        'icon': 'placeholder',
        'title': ugettext_lazy("Workflows"),
        'subtitle': ugettext_lazy("Edit Workflow"),
        'next': next_url,
    })
