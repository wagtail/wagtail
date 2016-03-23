from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext as _
from django.views.decorators.vary import vary_on_headers
from django.core.urlresolvers import reverse

from wagtail.utils.pagination import paginate
from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailadmin.utils import PermissionPolicyChecker, permission_denied
from wagtail.wagtailsearch.backends import get_search_backends
from wagtail.wagtailadmin import messages
from wagtail.wagtailcore.models import Collection

from wagtail.wagtaildocs.models import get_document_model
from wagtail.wagtaildocs.forms import get_document_form
from wagtail.wagtaildocs.permissions import permission_policy


permission_checker = PermissionPolicyChecker(permission_policy)


@permission_checker.require_any('add', 'change', 'delete')
@vary_on_headers('X-Requested-With')
def index(request):
    Document = get_document_model()

    # Get documents (filtered by user permission)
    documents = permission_policy.instances_user_has_any_permission_for(
        request.user, ['change', 'delete']
    )

    # Ordering
    if 'ordering' in request.GET and request.GET['ordering'] in ['title', '-created_at']:
        ordering = request.GET['ordering']
    else:
        ordering = '-created_at'
    documents = documents.order_by(ordering)

    # Filter by collection
    current_collection = None
    collection_id = request.GET.get('collection_id')
    if collection_id:
        try:
            current_collection = Collection.objects.get(id=collection_id)
            documents = documents.filter(collection=current_collection)
        except (ValueError, Collection.DoesNotExist):
            pass

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

    collections = permission_policy.collections_user_has_any_permission_for(
        request.user, ['add', 'change']
    )
    if len(collections) < 2:
        collections = None

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
            'user_can_add': permission_policy.user_has_permission(request.user, 'add'),
            'collections': collections,
            'current_collection': current_collection,
        })


@permission_checker.require('add')
def add(request):
    Document = get_document_model()
    DocumentForm = get_document_form(Document)

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


@permission_checker.require('change')
def edit(request, document_id):
    Document = get_document_model()
    DocumentForm = get_document_form(Document)

    doc = get_object_or_404(Document, id=document_id)

    if not permission_policy.user_has_permission_for_instance(request.user, 'change', doc):
        return permission_denied(request)

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
        messages.error(
            request,
            _("The file could not be found. Please change the source or delete the document"),
            buttons=[messages.button(reverse('wagtaildocs:delete', args=(doc.id,)), _('Delete'))]
        )

    return render(request, "wagtaildocs/documents/edit.html", {
        'document': doc,
        'filesize': filesize,
        'form': form,
        'user_can_delete': permission_policy.user_has_permission_for_instance(
            request.user, 'delete', doc
        ),
    })


@permission_checker.require('delete')
def delete(request, document_id):
    Document = get_document_model()
    doc = get_object_or_404(Document, id=document_id)

    if not permission_policy.user_has_permission_for_instance(request.user, 'delete', doc):
        return permission_denied(request)

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
