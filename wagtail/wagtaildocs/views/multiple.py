from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils.encoding import force_text
from django.views.decorators.http import require_POST
from django.views.decorators.vary import vary_on_headers

from wagtail.wagtailadmin.utils import PermissionPolicyChecker
from wagtail.wagtailsearch.backends import get_search_backends

from ..models import get_document_model
from ..forms import get_document_form, get_document_multi_form
from ..permissions import permission_policy


permission_checker = PermissionPolicyChecker(permission_policy)


@permission_checker.require('add')
@vary_on_headers('X-Requested-With')
def add(request):
    Document = get_document_model()
    DocumentForm = get_document_form(Document)
    DocumentMultiForm = get_document_multi_form(Document)

    collections = permission_policy.collections_user_has_permission_for(request.user, 'add')
    if len(collections) > 1:
        collections_to_choose = collections
    else:
        # no need to show a collections chooser
        collections_to_choose = None

    if request.method == 'POST':
        if not request.is_ajax():
            return HttpResponseBadRequest("Cannot POST to this view without AJAX")

        if not request.FILES:
            return HttpResponseBadRequest("Must upload a file")

        # Build a form for validation
        form = DocumentForm({
            'title': request.FILES['files[]'].name,
            'collection': request.POST.get('collection'),
        }, {
            'file': request.FILES['files[]']
        }, user=request.user)

        if form.is_valid():
            # Save it
            doc = form.save(commit=False)
            doc.uploaded_by_user = request.user
            doc.file_size = doc.file.size
            doc.save()

            # Success! Send back an edit form for this document to the user
            return JsonResponse({
                'success': True,
                'doc_id': int(doc.id),
                'form': render_to_string('wagtaildocs/multiple/edit_form.html', {
                    'doc': doc,
                    'form': DocumentMultiForm(
                        instance=doc, prefix='doc-%d' % doc.id, user=request.user
                    ),
                }, request=request),
            })
        else:
            # Validation error
            return JsonResponse({
                'success': False,

                # https://github.com/django/django/blob/stable/1.6.x/django/forms/util.py#L45
                'error_message': '\n'.join(['\n'.join([force_text(i) for i in v]) for k, v in form.errors.items()]),
            })
    else:
        form = DocumentForm(user=request.user)

    return render(request, 'wagtaildocs/multiple/add.html', {
        'help_text': form.fields['file'].help_text,
        'collections': collections_to_choose,
    })


@require_POST
def edit(request, doc_id, callback=None):
    Document = get_document_model()
    DocumentMultiForm = get_document_multi_form(Document)

    doc = get_object_or_404(Document, id=doc_id)

    if not request.is_ajax():
        return HttpResponseBadRequest("Cannot POST to this view without AJAX")

    if not permission_policy.user_has_permission_for_instance(request.user, 'change', doc):
        raise PermissionDenied

    form = DocumentMultiForm(
        request.POST, request.FILES, instance=doc, prefix='doc-' + doc_id, user=request.user
    )

    if form.is_valid():
        form.save()

        # Reindex the doc to make sure all tags are indexed
        for backend in get_search_backends():
            backend.add(doc)

        return JsonResponse({
            'success': True,
            'doc_id': int(doc_id),
        })
    else:
        return JsonResponse({
            'success': False,
            'doc_id': int(doc_id),
            'form': render_to_string('wagtaildocs/multiple/edit_form.html', {
                'doc': doc,
                'form': form,
            }, request=request),
        })


@require_POST
def delete(request, doc_id):
    Document = get_document_model()

    doc = get_object_or_404(Document, id=doc_id)

    if not request.is_ajax():
        return HttpResponseBadRequest("Cannot POST to this view without AJAX")

    if not permission_policy.user_has_permission_for_instance(request.user, 'delete', doc):
        raise PermissionDenied

    doc.delete()

    return JsonResponse({
        'success': True,
        'doc_id': int(doc_id),
    })
