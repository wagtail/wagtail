from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django import forms
from django.utils.http import is_safe_url
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST

from wagtail.admin import messages, widgets
from wagtail.admin.edit_handlers import ObjectList, FieldPanel, InlinePanel, get_edit_handler, PageChooserPanel
from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.admin.views.generic import CreateView, DeleteView, EditView, IndexView
from wagtail.core.models import Page, Workflow
from wagtail.admin.views.pages import get_valid_next_url_from_request
from wagtail.core.permissions import workflow_permission_policy
from django.shortcuts import get_object_or_404, redirect, render

Workflow.panels = [
                    FieldPanel("name"),
                    FieldPanel("active"),
                    InlinePanel("workflow_tasks", heading="Tasks"),
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
    edit_url_name = 'wagtailadmin_workflows:edit'
    page_title = _("Workflows")
    add_item_label = _("Add a workflow")
    header_icon = 'placeholder'


def create(request):
    if not request.user.is_superuser:
        raise PermissionDenied
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
        'title': _("Workflows"),
        'next': next_url,
    })


def edit(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied
    workflow = get_object_or_404(Workflow, pk=pk)
    edit_handler = Workflow.get_edit_handler()
    edit_handler = edit_handler.bind_to(request=request, instance=workflow)
    form_class = edit_handler.get_form_class()
    pages = Page.objects.filter(workflow=workflow)

    next_url = get_valid_next_url_from_request(request)

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=workflow)
        if form.is_valid():
            workflow = form.save()
    else:
        form = form_class(instance=workflow)

    edit_handler = edit_handler.bind_to(form=form)
    pages.paginator = Paginator(pages, 5)
    page_number = int(request.GET.get('p', 1))
    page = pages.paginator.page(page_number)


    return render(request, 'wagtailadmin/workflows/edit.html', {
        'edit_handler': edit_handler,
        'workflow': workflow,
        'form': form,
        'icon': 'placeholder',
        'title': _("Workflows"),
        'subtitle': _("Edit Workflow"),
        'next': next_url,
        'pages': page,
        'paginator': pages.paginator,
    })

@require_POST
def remove_workflow(request, pk):
    # Get the page
    page = get_object_or_404(Page, id=pk).specific

    # Check permissions
    if not request.user.is_superuser:
        raise PermissionDenied

    # Unlock the page
    if page.workflow:
        page.workflow = None
        page.save()

        messages.success(request, _("Workflow unassigned from Page '{0}'.").format(page.get_admin_display_title()))

    # Redirect
    redirect_to = request.POST.get('next', None)
    if redirect_to and is_safe_url(url=redirect_to, allowed_hosts={request.get_host()}):
        return redirect(redirect_to)
    else:
        return redirect('wagtailadmin_explore', page.get_parent().id)


class AddWorkflowToPageForm(forms.Form):
    page = forms.ModelChoiceField(queryset=Page.objects.all(), widget=widgets.AdminPageChooser(
            target_models=[Page],
            can_choose_root=True))
    workflow = forms.ModelChoiceField(queryset=Workflow.objects.active(), widget=forms.HiddenInput())
    override_existing = forms.BooleanField(widget=forms.HiddenInput(), initial=False, required=False)

    def clean(self):
        page = self.cleaned_data.get('page')
        if page:
            existing_workflow = self.cleaned_data.get('page').workflow
            if not self.errors and existing_workflow != self.cleaned_data['workflow'] and not self.cleaned_data['override_existing']:
                self.add_error('page', ValidationError(_("This page already has workflow '{0}' assigned. Do you want to override?").format(existing_workflow), code='needs_confirmation'))

    def save(self):
        page = self.cleaned_data['page']
        workflow = self.cleaned_data['workflow']
        page.workflow = workflow
        page.save()
        return page


def add_to_page(request, workflow_pk):
    if not request.user.is_superuser:
        raise PermissionDenied
    workflow = get_object_or_404(Workflow, pk=workflow_pk)
    form_class = AddWorkflowToPageForm

    next_url = get_valid_next_url_from_request(request)
    if request.method == 'POST':
        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            form = form_class(initial={'workflow': workflow.pk, 'override_existing': False})

    else:
        form = form_class(initial={'workflow': workflow.pk, 'override_existing': False})

    confirm = form.has_error('page', 'needs_confirmation')

    return render(request, 'wagtailadmin/workflows/add_to_page.html', {
        'form': form,
        'icon': 'placeholder',
        'title': _("Workflows"),
        'next': next_url,
        'confirm': confirm
    })
