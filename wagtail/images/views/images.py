import os
from tempfile import SpooledTemporaryFile

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy, ngettext
from django.views import View

from wagtail.admin import messages
from wagtail.admin.auth import PermissionPolicyChecker
from wagtail.admin.filters import BaseMediaFilterSet
from wagtail.admin.ui.tables import (
    BaseColumn,
    BulkActionsCheckboxColumn,
    Column,
    DateColumn,
    TitleColumn,
    UsageCountColumn,
)
from wagtail.admin.utils import get_valid_next_url_from_request, set_query_params
from wagtail.admin.views import generic
from wagtail.images import get_image_model
from wagtail.images.exceptions import InvalidFilterSpecError
from wagtail.images.forms import URLGeneratorForm, get_image_form
from wagtail.images.models import Filter, SourceImageIOError
from wagtail.images.permissions import permission_policy
from wagtail.images.utils import generate_signature
from wagtail.models import ReferenceIndex, Site

permission_checker = PermissionPolicyChecker(permission_policy)

Image = get_image_model()

USAGE_PAGE_SIZE = getattr(settings, "WAGTAILIMAGES_USAGE_PAGE_SIZE", 20)


class ImagesFilterSet(BaseMediaFilterSet):
    permission_policy = permission_policy

    class Meta:
        model = Image
        fields = []


class IndexView(generic.IndexView):
    ORDERING_OPTIONS = {
        "-created_at": gettext_lazy("Newest"),
        "created_at": gettext_lazy("Oldest"),
        "title": gettext_lazy("Title: (A -> Z)"),
        "-title": gettext_lazy("Title: (Z -> A)"),
        "file_size": gettext_lazy("File size: (low to high)"),
        "-file_size": gettext_lazy("File size: (high to low)"),
        "usage_count": gettext_lazy("Usage count: (low to high)"),
        "-usage_count": gettext_lazy("Usage count: (high to low)"),
    }
    default_ordering = "-created_at"
    context_object_name = "images"
    permission_policy = permission_policy
    any_permission_required = ["add", "change", "delete"]
    model = Image
    filterset_class = ImagesFilterSet
    show_other_searches = True
    header_icon = "image"
    page_title = gettext_lazy("Images")
    add_item_label = gettext_lazy("Add an image")
    index_url_name = "wagtailimages:index"
    index_results_url_name = "wagtailimages:index_results"
    add_url_name = "wagtailimages:add_multiple"
    edit_url_name = "wagtailimages:edit"
    template_name = "wagtailimages/images/index.html"
    results_template_name = "wagtailimages/images/index_results.html"

    def get_paginate_by(self, queryset):
        return getattr(settings, "WAGTAILIMAGES_INDEX_PAGE_SIZE", 30)

    def get_valid_orderings(self):
        return self.ORDERING_OPTIONS

    def get_base_queryset(self):
        # Get images (filtered by user permission)
        images = (
            permission_policy.instances_user_has_any_permission_for(
                self.request.user, ["change", "delete"]
            )
            .select_related("collection")
            .prefetch_renditions("max-165x165")
        )

        # Annotate with usage count from the ReferenceIndex
        images = images.annotate(
            usage_count=ReferenceIndex.usage_count_subquery(self.model)
        )

        return images

    @cached_property
    def current_collection(self):
        # Upon validation, the cleaned data is a Collection instance
        return self.filters and self.filters.form.cleaned_data.get("collection_id")

    def get_add_url(self):
        # Pass the collection filter to prefill the add form's collection field
        return set_query_params(
            super().get_add_url(),
            {"collection_id": self.current_collection and self.current_collection.pk},
        )

    def get_filterset_kwargs(self):
        kwargs = super().get_filterset_kwargs()
        kwargs["is_searching"] = self.is_searching
        return kwargs

    def get_next_url(self):
        next_url = self.index_url
        request_query_string = self.request.META.get("QUERY_STRING")
        if request_query_string:
            next_url += "?" + request_query_string
        return next_url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "next": self.get_next_url(),
                "current_collection": self.current_collection,
                "current_ordering": self.ordering,
                "ORDERING_OPTIONS": self.ORDERING_OPTIONS,
                "layout": self.layout,
            }
        )

        return context

    @cached_property
    def layout(self):
        return self.request.GET.get("layout", "grid")

    @cached_property
    def columns(self):
        if self.layout == "grid":
            return []
        else:
            columns = [
                BulkActionsColumn("bulk_actions"),
                ImagePreviewColumn(
                    "preview",
                    label=_("Preview"),
                    accessor="image",
                    classname="image-preview",
                ),
                TitleColumnWithFilename(
                    "title",
                    label=_("Title"),
                    sort_key="title",
                    get_url=self.get_edit_url,
                    width="35%",
                    classname="title-with-filename",
                ),
                Column("collection", label=_("Collection"), accessor="collection.name"),
                DateColumn(
                    "created_at",
                    label=_("Created"),
                    sort_key="created_at",
                ),
                UsageCountColumn(
                    "usage_count",
                    label=_("Usage"),
                    sort_key="usage_count",
                    width="16%",
                ),
            ]

            return columns


class BulkActionsColumn(BulkActionsCheckboxColumn):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, obj_type="image", **kwargs)

    def get_header_context_data(self, parent_context):
        context = super().get_header_context_data(parent_context)
        parent = parent_context.get("current_collection")
        if parent:
            context["parent"] = parent.id
        return context


class ImagePreviewColumn(BaseColumn):
    cell_template_name = "wagtailimages/images/image_preview_column_cell.html"


class TitleColumnWithFilename(TitleColumn):
    cell_template_name = "wagtailimages/images/title_column_cell.html"


class EditView(generic.EditView):
    permission_policy = permission_policy
    pk_url_kwarg = "image_id"
    error_message = gettext_lazy("The image could not be saved due to errors.")
    template_name = "wagtailimages/images/edit.html"
    index_url_name = "wagtailimages:index"
    edit_url_name = "wagtailimages:edit"
    delete_url_name = "wagtailimages:delete"
    url_generator_url_name = "wagtailimages:url_generator"
    header_icon = "image"
    context_object_name = "image"

    @cached_property
    def model(self):
        return get_image_model()

    def get_form_class(self):
        return get_image_form(self.model)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not permission_policy.user_has_permission_for_instance(
            self.request.user, "change", obj
        ):
            raise PermissionDenied
        return obj

    def get_success_message(self):
        return _("Image '%(image_title)s' updated.") % {
            "image_title": self.object.title
        }

    @cached_property
    def next_url(self):
        return get_valid_next_url_from_request(self.request)

    def get_success_url(self):
        return self.next_url or super().get_success_url()

    def render_to_response(self, context, **response_kwargs):
        if self.object.is_stored_locally():
            # Give error if image file doesn't exist
            if not os.path.isfile(self.object.file.path):
                messages.error(
                    self.request,
                    _(
                        "The source image file could not be found. Please change the source or delete the image."
                    )
                    % {"image_title": self.object.title},
                    buttons=[messages.button(self.get_delete_url(), _("Delete"))],
                )

        return super().render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["next"] = self.next_url
        context["usage_count_val"] = self.object.get_usage().count()

        try:
            context["filesize"] = self.object.get_file_size()
        except SourceImageIOError:
            context["filesize"] = None

        try:
            reverse("wagtailimages_serve", args=("foo", "1", "bar"))
            context["url_generator_url"] = reverse(
                self.url_generator_url_name, args=(self.object.id,)
            )
        except NoReverseMatch:
            context["url_generator_url"] = None

        return context


class URLGeneratorView(generic.InspectView):
    any_permission_required = ["change"]
    model = get_image_model()
    pk_url_kwarg = "image_id"
    header_icon = "image"
    page_title = gettext_lazy("Generate URL")
    template_name = "wagtailimages/images/url_generator.html"
    index_url_name = "wagtailimages:index"
    edit_url_name = "wagtailimages:edit"

    def get_page_subtitle(self):
        return self.object.title

    def get_fields(self):
        return []

    def get(self, request, image_id, *args, **kwargs):
        self.object = get_object_or_404(self.model, id=image_id)

        if not permission_policy.user_has_permission_for_instance(
            request.user, "change", self.object
        ):
            raise PermissionDenied

        self.form = URLGeneratorForm(
            initial={
                "filter_method": "original",
                "width": self.object.width,
                "height": self.object.height,
            }
        )

        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        return context


class GenerateURLView(View):
    def get(self, request, image_id, filter_spec):
        # Get the image
        Image = get_image_model()
        try:
            image = Image.objects.get(id=image_id)
        except Image.DoesNotExist:
            return JsonResponse({"error": "Cannot find image."}, status=404)

        # Check if this user has edit permission on this image
        if not permission_policy.user_has_permission_for_instance(
            request.user, "change", image
        ):
            return JsonResponse(
                {
                    "error": "You do not have permission to generate a URL for this image."
                },
                status=403,
            )

        # Parse the filter spec to make sure it's valid
        try:
            Filter(spec=filter_spec).operations
        except InvalidFilterSpecError:
            return JsonResponse({"error": "Invalid filter spec."}, status=400)

        # Generate url
        signature = generate_signature(image_id, filter_spec)
        url = reverse("wagtailimages_serve", args=(signature, image_id, filter_spec))

        # Get site root url
        try:
            site_root_url = Site.objects.get(is_default_site=True).root_url
        except Site.DoesNotExist:
            site_root_url = Site.objects.first().root_url

        # Generate preview url
        preview_url = reverse("wagtailimages:preview", args=(image_id, filter_spec))

        return JsonResponse(
            {"url": site_root_url + url, "preview_url": preview_url}, status=200
        )


def preview(request, image_id, filter_spec):
    image = get_object_or_404(get_image_model(), id=image_id)

    try:
        # Temporary image needs to be an instance that Willow can run optimizers on
        temp_image = SpooledTemporaryFile(max_size=settings.FILE_UPLOAD_MAX_MEMORY_SIZE)
        image = Filter(spec=filter_spec).run(image, temp_image)
        temp_image.seek(0)
        response = FileResponse(temp_image)
        response["Content-Type"] = "image/" + image.format_name
        return response
    except InvalidFilterSpecError:
        return HttpResponse(
            "Invalid filter spec: " + filter_spec, content_type="text/plain", status=400
        )


class DeleteView(generic.DeleteView):
    model = get_image_model()
    pk_url_kwarg = "image_id"
    permission_policy = permission_policy
    permission_required = "delete"
    header_icon = "image"
    template_name = "wagtailimages/images/confirm_delete.html"
    usage_url_name = "wagtailimages:image_usage"
    delete_url_name = "wagtailimages:delete"
    index_url_name = "wagtailimages:index"
    page_title = gettext_lazy("Delete image")

    def user_has_permission(self, permission):
        return self.permission_policy.user_has_permission_for_instance(
            self.request.user, permission, self.object
        )

    @property
    def confirmation_message(self):
        # This message will only appear in the singular, but we specify a plural
        # so it can share the translation string with confirm_bulk_delete.html
        return ngettext(
            "Are you sure you want to delete this image?",
            "Are you sure you want to delete these images?",
            1,
        )

    def get_success_message(self):
        return _("Image '%(image_title)s' deleted.") % {
            "image_title": self.object.title
        }


class CreateView(generic.CreateView):
    permission_policy = permission_policy
    index_url_name = "wagtailimages:index"
    add_url_name = "wagtailimages:add"
    edit_url_name = "wagtailimages:edit"
    error_message = gettext_lazy("The image could not be created due to errors.")
    template_name = "wagtailimages/images/add.html"
    header_icon = "image"

    @cached_property
    def model(self):
        return get_image_model()

    def get_form_class(self):
        return get_image_form(self.model)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial_form_instance(self):
        return self.model(uploaded_by_user=self.request.user)

    def get_success_message(self, instance):
        return _("Image '%(image_title)s' added.") % {"image_title": instance.title}


class UsageView(generic.UsageView):
    model = get_image_model()
    paginate_by = USAGE_PAGE_SIZE
    pk_url_kwarg = "image_id"
    permission_policy = permission_policy
    permission_required = "change"
    header_icon = "image"
    index_url_name = "wagtailimages:index"
    edit_url_name = "wagtailimages:edit"

    def get_base_object_queryset(self):
        return super().get_base_object_queryset().select_related("uploaded_by_user")

    def user_has_permission(self, permission):
        return self.permission_policy.user_has_permission_for_instance(
            self.request.user, permission, self.object
        )

    def get_page_subtitle(self):
        return self.object.title
