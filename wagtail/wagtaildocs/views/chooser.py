import json

from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render

from wagtail.utils.pagination import paginate
from wagtail.wagtailadmin.modal_workflow import render_modal_workflow
from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailadmin.utils import permission_required
from wagtail.wagtailsearch.backends import get_search_backends

from wagtail.wagtaildocs.models import get_document_model
from wagtail.wagtaildocs.forms import get_document_form


def get_document_json(document):
    """
    helper function: given a document, return the json to pass back to the
    chooser panel
    """

    return json.dumps({
        'id': document.id,
        'title': document.title,
        'edit_link': reverse('wagtaildocs:edit', args=(document.id,)),
    })


def chooser(request):
    Document = get_document_model()

    if request.user.has_perm('wagtaildocs.add_document'):
        DocumentForm = get_document_form(Document)
        uploadform = DocumentForm()
    else:
        uploadform = None

    documents = []

    q = None
    is_searching = False
    if 'q' in request.GET or 'p' in request.GET:
        searchform = SearchForm(request.GET)
        if searchform.is_valid():
            q = searchform.cleaned_data['q']

            documents = Document.objects.search(q)
            is_searching = True
        else:
            documents = Document.objects.order_by('-created_at')
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

        documents = Document.objects.order_by('-created_at')
        paginator, documents = paginate(request, documents, per_page=10)

    return render_modal_workflow(request, 'wagtaildocs/chooser/chooser.html', 'wagtaildocs/chooser/chooser.js', {
        'documents': documents,
        'uploadform': uploadform,
        'searchform': searchform,
        'is_searching': False,
    })


def document_chosen(request, document_id):
    document = get_object_or_404(get_document_model(), id=document_id)

    return render_modal_workflow(
        request, None, 'wagtaildocs/chooser/document_chosen.js',
        {'document_json': get_document_json(document)}
    )


@permission_required('wagtaildocs.add_document')
def chooser_upload(request):
    Document = get_document_model()
    DocumentForm = get_document_form(Document)

    if request.POST:
        document = Document(uploaded_by_user=request.user)
        form = DocumentForm(request.POST, request.FILES, instance=document)

        if form.is_valid():
            form.save()

            # Reindex the document to make sure all tags are indexed
            for backend in get_search_backends():
                backend.add(document)

            return render_modal_workflow(
                request, None, 'wagtaildocs/chooser/document_chosen.js',
                {'document_json': get_document_json(document)}
            )
    else:
        form = DocumentForm()

    documents = Document.objects.order_by('title')

    return render_modal_workflow(
        request, 'wagtaildocs/chooser/chooser.html', 'wagtaildocs/chooser/chooser.js',
        {'documents': documents, 'uploadform': form}
    )
