import json

from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import permission_required

from wagtail.wagtailadmin.modal_workflow import render_modal_workflow
from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailsearch.backends import get_search_backends

from wagtail.wagtaildocs.models import Document
from wagtail.wagtaildocs.forms import DocumentForm


@permission_required('wagtailadmin.access_admin')
def chooser(request):
    if request.user.has_perm('wagtaildocs.add_document'):
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

            # page number
            p = request.GET.get("p", 1)

            documents = Document.search(q, results_per_page=10, prefetch_tags=True)

            is_searching = True

        else:
            documents = Document.objects.order_by('-created_at')

            p = request.GET.get("p", 1)
            paginator = Paginator(documents, 10)

            try:
                documents = paginator.page(p)
            except PageNotAnInteger:
                documents = paginator.page(1)
            except EmptyPage:
                documents = paginator.page(paginator.num_pages)

            is_searching = False

        return render(request, "wagtaildocs/chooser/results.html", {
            'documents': documents,
            'query_string': q,
            'is_searching': is_searching,
        })
    else:
        searchform = SearchForm()

        documents = Document.objects.order_by('-created_at')
        p = request.GET.get("p", 1)
        paginator = Paginator(documents, 10)

        try:
            documents = paginator.page(p)
        except PageNotAnInteger:
            documents = paginator.page(1)
        except EmptyPage:
            documents = paginator.page(paginator.num_pages)

    return render_modal_workflow(request, 'wagtaildocs/chooser/chooser.html', 'wagtaildocs/chooser/chooser.js', {
        'documents': documents,
        'uploadform': uploadform,
        'searchform': searchform,
        'is_searching': False,
    })


@permission_required('wagtailadmin.access_admin')
def document_chosen(request, document_id):
    document = get_object_or_404(Document, id=document_id)

    document_json = json.dumps({'id': document.id, 'title': document.title})

    return render_modal_workflow(
        request, None, 'wagtaildocs/chooser/document_chosen.js',
        {'document_json': document_json}
    )


@permission_required('wagtaildocs.add_document')
def chooser_upload(request):
    if request.POST:
        document = Document(uploaded_by_user=request.user)
        form = DocumentForm(request.POST, request.FILES, instance=document)

        if form.is_valid():
            form.save()

            # Reindex the document to make sure all tags are indexed
            for backend in get_search_backends():
                backend.add(document)

            document_json = json.dumps({'id': document.id, 'title': document.title})
            return render_modal_workflow(
                request, None, 'wagtaildocs/chooser/document_chosen.js',
                {'document_json': document_json}
            )
    else:
        form = DocumentForm()

    documents = Document.objects.order_by('title')

    return render_modal_workflow(
        request, 'wagtaildocs/chooser/chooser.html', 'wagtaildocs/chooser/chooser.js',
        {'documents': documents, 'uploadform': form}
    )
