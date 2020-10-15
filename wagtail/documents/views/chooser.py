from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext as _

from wagtail.admin.auth import PermissionPolicyChecker
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.core import hooks
from wagtail.core.models import Collection
from wagtail.documents import get_document_model
from wagtail.documents.forms import get_document_form
from wagtail.documents.permissions import permission_policy
from wagtail.search import index as search_index

permission_checker = PermissionPolicyChecker(permission_policy)


def get_chooser_json_data():
    """construct context variables needed by the chooser JS"""
    return {
        'step': 'chooser',
        'error_label': _("Server Error"),
        'error_message': _("Report this error to your webmaster with the following information:"),
        'tag_autocomplete_url': reverse('wagtailadmin_tag_autocomplete'),
    }


def get_document_result_data(document):
    """
    helper function: given a document, return the json data to pass back to the
    chooser panel
    """

    return {
        'id': document.id,
        'title': document.title,
        'url': document.url,
        'filename': document.filename,
        'edit_link': reverse('wagtaildocs:edit', args=(document.id,)),
    }


def get_chooser_context(request, documents, uploadform, **kwargs):
    """Helper function to return common template context variables for the main chooser view"""
    context = {
        'uploadform': uploadform,
        'is_searching': False,
    }

    for hook in hooks.get_hooks('construct_document_chooser_queryset'):
        documents = hook(documents, request)

    collection_id = request.GET.get('collection_id')
    if collection_id:
        documents = documents.filter(collection=collection_id)
        context['collection_id'] = collection_id
    else:
        collections = Collection.objects.all()
        if len(collections) > 2:
            context['collections'] = collections
        else:
            context['collections'] = None

    context['documents_exist'] = documents.exists()

    searchform = SearchForm(request.GET)
    if searchform.is_valid():
        q = searchform.cleaned_data['q']
        documents = documents.search(q)

        context['query_string'] = q
        context['is_searching'] = True
    else:
        context['searchform'] = SearchForm

    paginator = Paginator(documents, per_page=10)
    documents = paginator.get_page(request.GET.get('p'))

    context['documents'] = documents
    context.update(**kwargs)
    return context


def chooser(request):
    Document = get_document_model()

    if permission_policy.user_has_permission(request.user, 'add'):
        DocumentForm = get_document_form(Document)
        uploadform = DocumentForm(user=request.user, prefix='document-chooser-upload')
    else:
        uploadform = None

    documents = Document.objects.order_by('-created_at')
    context = get_chooser_context(request, documents, uploadform)

    if 'q' in request.GET or 'p' in request.GET or 'collection_id' in request.GET:
        return TemplateResponse(request, "wagtaildocs/chooser/results.html", context)
    else:
        return render_modal_workflow(
            request, 'wagtaildocs/chooser/chooser.html', None,
            context, json_data=get_chooser_json_data()
        )


def document_chosen(request, document_id):
    document = get_object_or_404(get_document_model(), id=document_id)

    return render_modal_workflow(
        request, None, None,
        None, json_data={'step': 'document_chosen', 'result': get_document_result_data(document)}
    )


@permission_checker.require('add')
def chooser_upload(request):
    Document = get_document_model()
    DocumentForm = get_document_form(Document)

    if request.method == 'POST':
        document = Document(uploaded_by_user=request.user)
        uploadform = DocumentForm(
            request.POST, request.FILES, instance=document, user=request.user, prefix='document-chooser-upload'
        )

        if uploadform.is_valid():
            document.file_size = document.file.size

            # Set new document file hash
            document.file.seek(0)
            document._set_file_hash(document.file.read())
            document.file.seek(0)

            uploadform.save()

            # Reindex the document to make sure all tags are indexed
            search_index.insert_or_update_object(document)

            return render_modal_workflow(
                request, None, None,
                None, json_data={'step': 'document_chosen', 'result': get_document_result_data(document)}
            )
    else:
        uploadform = DocumentForm(user=request.user, prefix='document-chooser-upload')

    documents = Document.objects.order_by('-created_at')

    context = get_chooser_context(request, documents, uploadform)
    return render_modal_workflow(
        request, 'wagtaildocs/chooser/chooser.html', None,
        context, json_data=get_chooser_json_data()
    )
