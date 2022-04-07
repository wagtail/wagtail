import os

from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.http import urlencode
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from wagtail.admin import messages
from wagtail.admin.auth import PermissionPolicyChecker
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.models import popular_tags_for_model
from wagtail.admin.views.pages.utils import get_valid_next_url_from_request
from wagtail.documents import get_document_model
from wagtail.documents.forms import get_document_form
from wagtail.documents.permissions import permission_policy
from wagtail.models import Collection
from wagtail.search import index as search_index

permission_checker = PermissionPolicyChecker(permission_policy)


class BaseListingView(TemplateView):
    @method_decorator(permission_checker.require_any("add", "change", "delete"))
    def get(self, request):
        return super().get(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get documents (filtered by user permission)
        documents = permission_policy.instances_user_has_any_permission_for(
            self.request.user, ["change", "delete"]
        )

        # Ordering
        if "ordering" in self.request.GET and self.request.GET["ordering"] in [
            "title",
            "-created_at",
        ]:
            ordering = self.request.GET["ordering"]
        else:
            ordering = "-created_at"
        documents = documents.order_by(ordering)

        # Filter by collection
        self.current_collection = None
        collection_id = self.request.GET.get("collection_id")
        if collection_id:
            try:
                self.current_collection = Collection.objects.get(id=collection_id)
                documents = documents.filter(collection=self.current_collection)
            except (ValueError, Collection.DoesNotExist):
                pass

        # Search
        query_string = None
        if "q" in self.request.GET:
            self.form = SearchForm(self.request.GET, placeholder=_("Search documents"))
            if self.form.is_valid():
                query_string = self.form.cleaned_data["q"]
                documents = documents.search(query_string)
        else:
            self.form = SearchForm(placeholder=_("Search documents"))

        # Pagination
        paginator = Paginator(documents, per_page=20)
        documents = paginator.get_page(self.request.GET.get("p"))

        next_url = reverse("wagtaildocs:index")
        request_query_string = self.request.META.get("QUERY_STRING")
        if request_query_string:
            next_url += "?" + request_query_string

        context.update(
            {
                "ordering": ordering,
                "documents": documents,
                "query_string": query_string,
                "is_searching": bool(query_string),
                "next": next_url,
            }
        )
        return context


class IndexView(BaseListingView):
    template_name = "wagtaildocs/documents/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        collections = permission_policy.collections_user_has_any_permission_for(
            self.request.user, ["add", "change"]
        )
        if len(collections) < 2:
            collections = None

        Document = get_document_model()

        context.update(
            {
                "search_form": self.form,
                "popular_tags": popular_tags_for_model(get_document_model()),
                "user_can_add": permission_policy.user_has_permission(
                    self.request.user, "add"
                ),
                "collections": collections,
                "current_collection": self.current_collection,
                "app_label": Document._meta.app_label,
                "model_name": Document._meta.model_name,
            }
        )
        return context


class ListingResultsView(BaseListingView):
    template_name = "wagtaildocs/documents/results.html"


@permission_checker.require("add")
def add(request):
    Document = get_document_model()
    DocumentForm = get_document_form(Document)

    if request.method == "POST":
        doc = Document(uploaded_by_user=request.user)
        form = DocumentForm(
            request.POST, request.FILES, instance=doc, user=request.user
        )
        if form.is_valid():
            doc.file_size = doc.file.size

            # Set new document file hash
            doc.file.seek(0)
            doc._set_file_hash(doc.file.read())
            doc.file.seek(0)

            form.save()

            # Reindex the document to make sure all tags are indexed
            search_index.insert_or_update_object(doc)

            messages.success(
                request,
                _("Document '{0}' added.").format(doc.title),
                buttons=[
                    messages.button(
                        reverse("wagtaildocs:edit", args=(doc.id,)), _("Edit")
                    )
                ],
            )
            return redirect("wagtaildocs:index")
        else:
            messages.error(request, _("The document could not be saved due to errors."))
    else:
        form = DocumentForm(user=request.user)

    return TemplateResponse(
        request,
        "wagtaildocs/documents/add.html",
        {
            "form": form,
        },
    )


@permission_checker.require("change")
def edit(request, document_id):
    Document = get_document_model()
    DocumentForm = get_document_form(Document)

    doc = get_object_or_404(Document, id=document_id)

    if not permission_policy.user_has_permission_for_instance(
        request.user, "change", doc
    ):
        raise PermissionDenied

    next_url = get_valid_next_url_from_request(request)

    if request.method == "POST":
        original_file = doc.file
        form = DocumentForm(
            request.POST, request.FILES, instance=doc, user=request.user
        )
        if form.is_valid():
            if "file" in form.changed_data:
                doc = form.save(commit=False)
                doc.file_size = doc.file.size

                # Set new document file hash
                doc.file.seek(0)
                doc._set_file_hash(doc.file.read())
                doc.file.seek(0)
                doc.save()
                form.save_m2m()

                # If providing a new document file, delete the old one.
                # NB Doing this via original_file.delete() clears the file field,
                # which definitely isn't what we want...
                original_file.storage.delete(original_file.name)
            else:
                doc = form.save()

            # Reindex the document to make sure all tags are indexed
            search_index.insert_or_update_object(doc)

            edit_url = reverse("wagtaildocs:edit", args=(doc.id,))
            redirect_url = "wagtaildocs:index"
            if next_url:
                edit_url = f"{edit_url}?{urlencode({'next': next_url})}"
                redirect_url = next_url

            messages.success(
                request,
                _("Document '{0}' updated").format(doc.title),
                buttons=[messages.button(edit_url, _("Edit"))],
            )
            return redirect(redirect_url)
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
                _(
                    "The file could not be found. Please change the source or delete the document"
                ),
                buttons=[
                    messages.button(
                        reverse("wagtaildocs:delete", args=(doc.id,)), _("Delete")
                    )
                ],
            )

    return TemplateResponse(
        request,
        "wagtaildocs/documents/edit.html",
        {
            "document": doc,
            "filesize": doc.get_file_size(),
            "form": form,
            "user_can_delete": permission_policy.user_has_permission_for_instance(
                request.user, "delete", doc
            ),
            "next": next_url,
        },
    )


@permission_checker.require("delete")
def delete(request, document_id):
    Document = get_document_model()
    doc = get_object_or_404(Document, id=document_id)

    if not permission_policy.user_has_permission_for_instance(
        request.user, "delete", doc
    ):
        raise PermissionDenied

    next_url = get_valid_next_url_from_request(request)

    if request.method == "POST":
        doc.delete()
        messages.success(request, _("Document '{0}' deleted.").format(doc.title))
        return redirect(next_url) if next_url else redirect("wagtaildocs:index")

    return TemplateResponse(
        request,
        "wagtaildocs/documents/confirm_delete.html",
        {
            "document": doc,
            "next": next_url,
        },
    )


def usage(request, document_id):
    Document = get_document_model()
    doc = get_object_or_404(Document, id=document_id)

    paginator = Paginator(doc.get_usage(), per_page=20)
    used_by = paginator.get_page(request.GET.get("p"))

    return TemplateResponse(
        request,
        "wagtaildocs/documents/usage.html",
        {"document": doc, "used_by": used_by},
    )
