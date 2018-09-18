from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import ugettext as _

from wagtail.admin.forms import SearchForm
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.admin.utils import PermissionPolicyChecker
from wagtail.core import hooks
from wagtail.core.models import Collection
from wagtail.documents.forms import get_document_form
from wagtail.documents.models import get_document_model
from wagtail.documents.permissions import permission_policy
from wagtail.search import index as search_index
from wagtail.utils.pagination import paginate

permission_checker = PermissionPolicyChecker(permission_policy)


def get_chooser_context():
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


def chooser(request):
    Document = get_document_model()

    if permission_policy.user_has_permission(request.user, 'add'):
        DocumentForm = get_document_form(Document)
        uploadform = DocumentForm(user=request.user)
    else:
        uploadform = None

    documents = Document.objects.all()

    # allow hooks to modify the queryset
    for hook in hooks.get_hooks('construct_document_chooser_queryset'):
        documents = hook(documents, request)

    q = None
    if 'q' in request.GET or 'p' in request.GET or 'collection_id' in request.GET:

        collection_id = request.GET.get('collection_id')
        if collection_id:
            documents = documents.filter(collection=collection_id)

        searchform = SearchForm(request.GET)
        if searchform.is_valid():
            q = searchform.cleaned_data['q']

            documents = documents.search(q)
            is_searching = True
        else:
            documents = documents.order_by('-created_at')
            is_searching = False

        # Pagination
        paginator, documents = paginate(request, documents, per_page=10)

        return render(request, "wagtaildocs/chooser/results.html", {
            'documents': documents,
            'query_string': q,
            'is_searching': is_searching,
        })
    else:
        searchform = SearchForm()

        collections = Collection.objects.all()
        if len(collections) < 2:
            collections = None

        documents = documents.order_by('-created_at')
        paginator, documents = paginate(request, documents, per_page=10)

        return render_modal_workflow(request, 'wagtaildocs/chooser/chooser.html', None, {
            'documents': documents,
            'uploadform': uploadform,
            'searchform': searchform,
            'collections': collections,
            'is_searching': False,
        }, json_data=get_chooser_context())


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
        form = DocumentForm(request.POST, request.FILES, instance=document, user=request.user)

        if form.is_valid():
            document.file_size = document.file.size

            form.save()

            # Reindex the document to make sure all tags are indexed
            search_index.insert_or_update_object(document)

            return render_modal_workflow(
                request, None, None,
                None, json_data={'step': 'document_chosen', 'result': get_document_result_data(document)}
            )
    else:
        form = DocumentForm(user=request.user)

    documents = Document.objects.order_by('title')

    return render_modal_workflow(
        request, 'wagtaildocs/chooser/chooser.html', None,
        {'documents': documents, 'uploadform': form},
        json_data=get_chooser_context()
    )
