from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext as _
from django.views.decorators.vary import vary_on_headers
from django.core.urlresolvers import reverse

from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailsearch.backends import get_search_backends

from wagtail.wagtaildocs.models import Document
from wagtail.wagtaildocs.forms import DocumentForm


@permission_required('wagtaildocs.add_document')
@vary_on_headers('X-Requested-With')
def index(request):
    # Get documents
    documents = Document.objects.all()

    # Ordering
    if 'ordering' in request.GET and request.GET['ordering'] in ['title', '-created_at']:
        ordering = request.GET['ordering']
    else:
        ordering = '-created_at'
    documents = documents.order_by(ordering)

    # Permissions
    if not request.user.has_perm('wagtaildocs.change_document'):
        # restrict to the user's own documents
        documents = documents.filter(uploaded_by_user=request.user)

    # Search
    query_string = None
    if 'q' in request.GET:
        form = SearchForm(request.GET, placeholder=_("Search documents"))
        if form.is_valid():
            query_string = form.cleaned_data['q']
            if not request.user.has_perm('wagtaildocs.change_document'):
                # restrict to the user's own documents
                documents = Document.search(query_string, filters={'uploaded_by_user_id': request.user.id})
            else:
                documents = Document.search(query_string)
    else:
        form = SearchForm(placeholder=_("Search documents"))

    # Pagination
    p = request.GET.get('p', 1)
    paginator = Paginator(documents, 20)

    try:
        documents = paginator.page(p)
    except PageNotAnInteger:
        documents = paginator.page(1)
    except EmptyPage:
        documents = paginator.page(paginator.num_pages)

    # Create response
    if request.is_ajax():
        return render(request, 'wagtaildocs/documents/results.html', {
            'ordering': ordering,
            'documents': documents,
            'query_string': query_string,
            'is_searching': bool(query_string),
        })
    else:
        return render(request, 'wagtaildocs/documents/index.html', {
            'ordering': ordering,
            'documents': documents,
            'query_string': query_string,
            'is_searching': bool(query_string),

            'search_form': form,
            'popular_tags': Document.popular_tags(),
        })


@permission_required('wagtaildocs.add_document')
def add(request):
    if request.POST:
        doc = Document(uploaded_by_user=request.user)
        form = DocumentForm(request.POST, request.FILES, instance=doc)
        if form.is_valid():
            form.save()

            # Reindex the document to make sure all tags are indexed
            for backend in get_search_backends():
                backend.add(doc)

            messages.success(request, _("Document '{0}' added.").format(doc.title))
            return redirect('wagtaildocs_index')
        else:
            messages.error(request, _("The document could not be saved due to errors."))
    else:
        form = DocumentForm()

    return render(request, "wagtaildocs/documents/add.html", {
        'form': form,
    })


@permission_required('wagtailadmin.access_admin')  # more specific permission tests are applied within the view
def edit(request, document_id):
    doc = get_object_or_404(Document, id=document_id)

    if not doc.is_editable_by_user(request.user):
        raise PermissionDenied

    if request.POST:
        original_file = doc.file
        form = DocumentForm(request.POST, request.FILES, instance=doc)
        if form.is_valid():
            if 'file' in form.changed_data:
                # if providing a new document file, delete the old one.
                # NB Doing this via original_file.delete() clears the file field,
                # which definitely isn't what we want...
                original_file.storage.delete(original_file.name)
            doc = form.save()

            # Reindex the document to make sure all tags are indexed
            for backend in get_search_backends():
                backend.add(doc)

            messages.success(request, _("Document '{0}' updated").format(doc.title))
            return redirect('wagtaildocs_index')
        else:
            messages.error(request, _("The document could not be saved due to errors."))
    else:
        form = DocumentForm(instance=doc)

    return render(request, "wagtaildocs/documents/edit.html", {
        'document': doc,
        'form': form
    })


@permission_required('wagtailadmin.access_admin')  # more specific permission tests are applied within the view
def delete(request, document_id):
    doc = get_object_or_404(Document, id=document_id)

    if not doc.is_editable_by_user(request.user):
        raise PermissionDenied

    if request.POST:
        doc.delete()
        messages.success(request, _("Document '{0}' deleted.").format(doc.title))
        return redirect('wagtaildocs_index')

    return render(request, "wagtaildocs/documents/confirm_delete.html", {
        'document': doc,
    })


@permission_required('wagtailadmin.access_admin')
def usage(request, document_id):
    doc = get_object_or_404(Document, id=document_id)

    # Pagination
    p = request.GET.get('p', 1)
    paginator = Paginator(doc.get_usage(), 20)

    try:
        used_by = paginator.page(p)
    except PageNotAnInteger:
        used_by = paginator.page(1)
    except EmptyPage:
        used_by = paginator.page(paginator.num_pages)

    return render(request, "wagtaildocs/documents/usage.html", {
        'document': doc,
        'used_by': used_by
    })
