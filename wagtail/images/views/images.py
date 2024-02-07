import os

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.utils.http import urlencode
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy, ngettext
from django.views import View

from wagtail.admin import messages
from wagtail.admin.auth import PermissionPolicyChecker
from wagtail.admin.models import popular_tags_for_model
from wagtail.admin.utils import get_valid_next_url_from_request, set_query_params
from wagtail.admin.views import generic
from wagtail.images import get_image_model
from wagtail.images.exceptions import InvalidFilterSpecError
from wagtail.images.forms import URLGeneratorForm, get_image_form
from wagtail.images.models import Filter, SourceImageIOError
from wagtail.images.permissions import permission_policy
from wagtail.images.utils import generate_signature
from wagtail.models import Collection, Site

permission_checker = PermissionPolicyChecker(permission_policy)

INDEX_PAGE_SIZE = getattr(settings, "WAGTAILIMAGES_INDEX_PAGE_SIZE", 30)
USAGE_PAGE_SIZE = getattr(settings, "WAGTAILIMAGES_USAGE_PAGE_SIZE", 20)


class IndexView(generic.IndexView):
    ENTRIES_PER_PAGE_CHOICES = sorted({10, 30, 60, 100, 250, INDEX_PAGE_SIZE})
    ORDERING_OPTIONS = {
        "-created_at": _("Newest"),
        "created_at": _("Oldest"),
        "title": _("Title: (A -> Z)"),
        "-title": _("Title: (Z -> A)"),
        "file_size": _("File size: (low to high)"),
        "-file_size": _("File size: (high to low)"),
    }
    default_ordering = "-created_at"
    context_object_name = "images"
    permission_policy = permission_policy
    any_permission_required = ["add", "change", "delete"]
    model = get_image_model()
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
        entries_per_page = self.request.GET.get("entries_per_page", INDEX_PAGE_SIZE)
        try:
            entries_per_page = int(entries_per_page)
        except ValueError:
            entries_per_page = INDEX_PAGE_SIZE
        if entries_per_page not in self.ENTRIES_PER_PAGE_CHOICES:
            entries_per_page = INDEX_PAGE_SIZE

        self.entries_per_page = entries_per_page

        return entries_per_page

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
        return images

    def filter_queryset(self, queryset):
        # Filter by collection
        self.current_collection = None
        collection_id = self.request.GET.get("collection_id")
        if collection_id:
            try:
                self.current_collection = Collection.objects.get(id=collection_id)
                queryset = queryset.filter(collection=self.current_collection)
            except (ValueError, Collection.DoesNotExist):
                pass

        # Filter by tag
        self.current_tag = self.request.GET.get("tag")
        # Combining search with tag filter is not yet supported, see
        # https://github.com/wagtail/wagtail/issues/6616
        if self.current_tag and not self.search_query:
            try:
                queryset = queryset.filter(tags__name=self.current_tag)
            except AttributeError:
                self.current_tag = None

        return queryset

    def get_add_url(self):
        # Pass the query string so that the collection filter is preserved
        return set_query_params(
            super().get_add_url(),
            self.request.GET.copy(),
        )

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
                "entries_per_page": self.entries_per_page,
                "current_tag": self.current_tag,
                "current_collection": self.current_collection,
                "ENTRIES_PER_PAGE_CHOICES": self.ENTRIES_PER_PAGE_CHOICES,
                "current_ordering": self.ordering,
                "ORDERING_OPTIONS": self.ORDERING_OPTIONS,
            }
        )

        if self.results_only:
            return context

        collections = self.permission_policy.collections_user_has_any_permission_for(
            self.request.user, ["add", "change"]
        )
        if len(collections) < 2:
            collections = None

        context.update(
            {
                "popular_tags": popular_tags_for_model(get_image_model()),
                "collections": collections,
            }
        )
        return context


@permission_checker.require("change")
def edit(request, image_id):
    Image = get_image_model()
    ImageForm = get_image_form(Image)

    image = get_object_or_404(Image, id=image_id)

    if not permission_policy.user_has_permission_for_instance(
        request.user, "change", image
    ):
        raise PermissionDenied

    next_url = get_valid_next_url_from_request(request)

    if request.method == "POST":
        form = ImageForm(request.POST, request.FILES, instance=image, user=request.user)
        if form.is_valid():
            form.save()

            edit_url = reverse("wagtailimages:edit", args=(image.id,))
            redirect_url = "wagtailimages:index"
            if next_url:
                edit_url = f"{edit_url}?{urlencode({'next': next_url})}"
                redirect_url = next_url

            messages.success(
                request,
                _("Image '%(image_title)s' updated.") % {"image_title": image.title},
                buttons=[messages.button(edit_url, _("Edit again"))],
            )
            return redirect(redirect_url)
        else:
            messages.error(request, _("The image could not be saved due to errors."))
    else:
        form = ImageForm(instance=image, user=request.user)

    # Check if we should enable the frontend url generator
    try:
        reverse("wagtailimages_serve", args=("foo", "1", "bar"))
        url_generator_enabled = True
    except NoReverseMatch:
        url_generator_enabled = False

    if image.is_stored_locally():
        # Give error if image file doesn't exist
        if not os.path.isfile(image.file.path):
            messages.error(
                request,
                _(
                    "The source image file could not be found. Please change the source or delete the image."
                )
                % {"image_title": image.title},
                buttons=[
                    messages.button(
                        reverse("wagtailimages:delete", args=(image.id,)), _("Delete")
                    )
                ],
            )

    try:
        filesize = image.get_file_size()
    except SourceImageIOError:
        filesize = None

    return TemplateResponse(
        request,
        "wagtailimages/images/edit.html",
        {
            "image": image,
            "form": form,
            "url_generator_enabled": url_generator_enabled,
            "filesize": filesize,
            "user_can_delete": permission_policy.user_has_permission_for_instance(
                request.user, "delete", image
            ),
            "next": next_url,
        },
    )


class URLGeneratorView(generic.InspectView):
    any_permission_required = ["change"]
    model = get_image_model()
    pk_url_kwarg = "image_id"
    header_icon = "image"
    page_title = "Generating URL"
    template_name = "wagtailimages/images/url_generator.html"

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
        response = HttpResponse()
        image = Filter(spec=filter_spec).run(image, response)
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


@permission_checker.require("add")
def add(request):
    ImageModel = get_image_model()
    ImageForm = get_image_form(ImageModel)

    if request.method == "POST":
        image = ImageModel(uploaded_by_user=request.user)
        form = ImageForm(request.POST, request.FILES, instance=image, user=request.user)
        if form.is_valid():
            form.save()

            messages.success(
                request,
                _("Image '%(image_title)s' added.") % {"image_title": image.title},
                buttons=[
                    messages.button(
                        reverse("wagtailimages:edit", args=(image.id,)), _("Edit")
                    )
                ],
            )
            return redirect("wagtailimages:index")
        else:
            messages.error(request, _("The image could not be created due to errors."))
    else:
        form = ImageForm(user=request.user)

    return TemplateResponse(
        request,
        "wagtailimages/images/add.html",
        {
            "form": form,
        },
    )


class UsageView(generic.UsageView):
    model = get_image_model()
    paginate_by = USAGE_PAGE_SIZE
    pk_url_kwarg = "image_id"
    permission_policy = permission_policy
    permission_required = "change"
    header_icon = "image"

    def user_has_permission(self, permission):
        return self.permission_policy.user_has_permission_for_instance(
            self.request.user, permission, self.object
        )

    def get_page_subtitle(self):
        return self.object.title
