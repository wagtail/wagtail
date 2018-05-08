import os

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.decorators.vary import vary_on_headers

from wagtail.admin import messages
from wagtail.admin.forms import SearchForm
from wagtail.admin.utils import PermissionPolicyChecker, permission_denied, popular_tags_for_model
from wagtail.core.models import Collection
from wagtail.documents.forms import get_document_form
from wagtail.documents.models import get_document_model
from wagtail.documents.permissions import permission_policy
from wagtail.search import index as search_index
from wagtail.utils.pagination import paginate

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
            'popular_tags': popular_tags_for_model(Document),
            'user_can_add': permission_policy.user_has_permission(request.user, 'add'),
            'collections': collections,
            'current_collection': current_collection,
        })


@permission_checker.require('add')
def add(request):
    Document = get_document_model()
    DocumentForm = get_document_form(Document)

    if request.method == 'POST':
        doc = Document(uploaded_by_user=request.user)
        form = DocumentForm(request.POST, request.FILES, instance=doc, user=request.user)
        if form.is_valid():
            doc.file_size = doc.file.size

            form.save()

            # Reindex the document to make sure all tags are indexed
            search_index.insert_or_update_object(doc)

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

    if request.method == 'POST':
        original_file = doc.file
        form = DocumentForm(request.POST, request.FILES, instance=doc, user=request.user)
        if form.is_valid():
            doc = form.save()
            if 'file' in form.changed_data:
                doc.file_size = doc.file.size

                # if providing a new document file, delete the old one.
                # NB Doing this via original_file.delete() clears the file field,
                # which definitely isn't what we want...
                original_file.storage.delete(original_file.name)

            # Reindex the document to make sure all tags are indexed
            search_index.insert_or_update_object(doc)

            messages.success(request, _("Document '{0}' updated").format(doc.title), buttons=[
                messages.button(reverse('wagtaildocs:edit', args=(doc.id,)), _('Edit'))
            ])
            return redirect('wagtaildocs:index')
        else:
            messages.error(request, _("The document could not be saved due to errors."))
    else:
        form = DocumentForm(instance=doc, user=request.user)

    try:
        local_path = doc.file.path
    except NotImplementedError:
        # Document is hosted externally (eg, S3)
        local_path = None

    if local_path:
        # Give error if document file doesn't exist
        if not os.path.isfile(local_path):
            messages.error(
                request,
                _("The file could not be found. Please change the source or delete the document"),
                buttons=[messages.button(reverse('wagtaildocs:delete', args=(doc.id,)), _('Delete'))]
            )

    return render(request, "wagtaildocs/documents/edit.html", {
        'document': doc,
        'filesize': doc.get_file_size(),
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

    if request.method == 'POST':
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
