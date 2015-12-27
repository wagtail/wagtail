from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext as _
from django.views.decorators.vary import vary_on_headers
from django.core.urlresolvers import reverse

from wagtail.utils.pagination import paginate
from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailadmin.utils import permission_required, any_permission_required
from wagtail.wagtailsearch.backends import get_search_backends
from wagtail.wagtailadmin import messages

from wagtail.wagtaildocs.models import get_document_model
from wagtail.wagtaildocs.forms import get_document_form


@any_permission_required('wagtaildocs.add_document', 'wagtaildocs.change_document')
@vary_on_headers('X-Requested-With')
def index(request):
    Document = get_document_model()

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
            documents = documents.search(query_string)
    else:
        form = SearchForm(placeholder=_("Search documents"))

    # Pagination
    paginator, documents = paginate(request, documents)

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
    Document = get_document_model()
    DocumentForm = get_document_form(Document)

    if request.POST:
        doc = Document(uploaded_by_user=request.user)
        form = DocumentForm(request.POST, request.FILES, instance=doc)
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
        form = DocumentForm()

    return render(request, "wagtaildocs/documents/add.html", {
        'form': form,
    })


def edit(request, document_id):
    Document = get_document_model()
    DocumentForm = get_document_form(Document)

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

            messages.success(request, _("Document '{0}' updated").format(doc.title), buttons=[
                messages.button(reverse('wagtaildocs:edit', args=(doc.id,)), _('Edit'))
            ])
            return redirect('wagtaildocs:index')
        else:
            messages.error(request, _("The document could not be saved due to errors."))
    else:
        form = DocumentForm(instance=doc)

    filesize = None

    # Get file size when there is a file associated with the Document object
    if doc.file:
        try:
            filesize = doc.file.size
        except OSError:
            # File doesn't exist
            pass

    if not filesize:
        messages.error(
            request,
            _("The file could not be found. Please change the source or delete the document"),
            buttons=[messages.button(reverse('wagtaildocs:delete', args=(doc.id,)), _('Delete'))]
        )

    return render(request, "wagtaildocs/documents/edit.html", {
        'document': doc,
        'filesize': filesize,
        'form': form
    })


def delete(request, document_id):
    Document = get_document_model()
    doc = get_object_or_404(Document, id=document_id)

    if not doc.is_editable_by_user(request.user):
        raise PermissionDenied

    if request.POST:
        doc.delete()
        messages.success(request, _("Document '{0}' deleted.").format(doc.title))
        return redirect('wagtaildocs:index')

    return render(request, "wagtaildocs/documents/confirm_delete.html", {
        'document': doc,
    })


def usage(request, document_id):
    Document = get_document_model()
    doc = get_object_or_404(Document, id=document_id)

    paginator, used_by = paginate(request, doc.get_usage())

    return render(request, "wagtaildocs/documents/usage.html", {
        'document': doc,
        'used_by': used_by
    })
