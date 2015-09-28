from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext as _
from django.views.decorators.vary import vary_on_headers
from django.core.urlresolvers import reverse

from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailsearch.backends import get_search_backend, get_search_backends
from wagtail.wagtailadmin import messages

from wagtail.wagtaildocs.models import Document
from wagtail.wagtaildocs.permissions import document_permission_required, any_document_permission_required, user_can_edit_document, user_has_document_permission, documents_editable_by_user
from wagtail.wagtaildocs.forms import DocumentForm


@any_document_permission_required()
@vary_on_headers('X-Requested-With')
def index(request):
    # Get documents
    documents = documents_editable_by_user(request.user)

    # Ordering
    if 'ordering' in request.GET and request.GET['ordering'] in ['title', '-created_at']:
        ordering = request.GET['ordering']
    else:
        ordering = '-created_at'
    documents = documents.order_by(ordering)

    # Search
    query_string = None
    if 'q' in request.GET:
        form = SearchForm(request.GET, placeholder=_("Search documents"))
        if form.is_valid():
            s = get_search_backend()
            query_string = form.cleaned_data['q']
            documents = s.search(query_string, documents)
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

            'can_add_document': user_has_document_permission(request.user, 'wagtaildocs.add_document'),
            'search_form': form,
            'popular_tags': Document.popular_tags(),
        })


@document_permission_required('wagtaildocs.add_document')
def add(request):
    if request.POST:
        doc = Document(uploaded_by_user=request.user)
        form = DocumentForm(request.POST, request.FILES, instance=doc, user=request.user)
        if form.is_valid():
            form.save()

            # Reindex the document to make sure all tags are indexed
            for backend in get_search_backends():
                backend.add(doc)

            messages.success(request, _("Document '{0}' added.").format(doc.title), buttons=[
                messages.button(reverse('wagtaildocs:edit', args=(doc.id,)), _('Edit'))
            ])
            return redirect('wagtaildocs:index')
        else:
            messages.error(request, _("The document could not be saved due to errors."))
    else:
        form = DocumentForm(user=request.user)

    return render(request, "wagtaildocs/documents/add.html", {
        'form': form,
    })


def edit(request, document_id):
    doc = get_object_or_404(Document, id=document_id)

    if not user_can_edit_document(request.user, doc):
        raise PermissionDenied

    if request.POST:
        original_file = doc.file
        form = DocumentForm(request.POST, request.FILES, instance=doc, user=request.user)
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

            messages.success(request, _("Document '{0}' updated").format(doc.title), buttons=[
                messages.button(reverse('wagtaildocs:edit', args=(doc.id,)), _('Edit'))
            ])
            return redirect('wagtaildocs:index')
        else:
            messages.error(request, _("The document could not be saved due to errors."))
    else:
        form = DocumentForm(instance=doc, user=request.user)

    filesize = None

    # Get file size when there is a file associated with the Document object
    if doc.file:
        try:
            filesize = doc.file.size
        except OSError:
            # File doesn't exist
            pass

    if not filesize:
        messages.error(request, _("The file could not be found. Please change the source or delete the document"), buttons=[
            messages.button(reverse('wagtaildocs:delete', args=(doc.id,)), _('Delete'))
        ])

    return render(request, "wagtaildocs/documents/edit.html", {
        'document': doc,
        'filesize': filesize,
        'form': form
    })


def delete(request, document_id):
    doc = get_object_or_404(Document, id=document_id)

    if not user_can_edit_document(request.user, doc):
        raise PermissionDenied

    if request.POST:
        doc.delete()
        messages.success(request, _("Document '{0}' deleted.").format(doc.title))
        return redirect('wagtaildocs:index')

    return render(request, "wagtaildocs/documents/confirm_delete.html", {
        'document': doc,
    })


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
