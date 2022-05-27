import os

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.utils.decorators import method_decorator
from django.utils.http import urlencode
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from wagtail.admin import messages
from wagtail.admin.auth import PermissionPolicyChecker
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.models import popular_tags_for_model
from wagtail.admin.views.pages.utils import get_valid_next_url_from_request
from wagtail.images import get_image_model
from wagtail.images.exceptions import InvalidFilterSpecError
from wagtail.images.forms import URLGeneratorForm, get_image_form
from wagtail.images.models import Filter, SourceImageIOError
from wagtail.images.permissions import permission_policy
from wagtail.images.utils import generate_signature
from wagtail.models import Collection, Site
from wagtail.search import index as search_index

permission_checker = PermissionPolicyChecker(permission_policy)

INDEX_PAGE_SIZE = getattr(settings, "WAGTAILIMAGES_INDEX_PAGE_SIZE", 30)
USAGE_PAGE_SIZE = getattr(settings, "WAGTAILIMAGES_USAGE_PAGE_SIZE", 20)


class BaseListingView(TemplateView):
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

    @method_decorator(permission_checker.require_any("add", "change", "delete"))
    def get(self, request):
        return super().get(request)

    def get_num_entries_per_page(self):
        entries_per_page = self.request.GET.get("entries_per_page", INDEX_PAGE_SIZE)
        try:
            entries_per_page = int(entries_per_page)
        except ValueError:
            entries_per_page = INDEX_PAGE_SIZE
        if entries_per_page not in self.ENTRIES_PER_PAGE_CHOICES:
            entries_per_page = INDEX_PAGE_SIZE

        return entries_per_page

    def get_valid_orderings(self):
        return self.ORDERING_OPTIONS

    def get_ordering(self):
        # TODO: remove this method when this view will be based on the
        # generic model index view from wagtail.admin.views.generic.models.IndexView
        ordering = self.request.GET.get("ordering")
        if ordering is None or ordering not in self.get_valid_orderings():
            ordering = self.default_ordering
        return ordering

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get ordering
        ordering = self.get_ordering()

        # Get images (filtered by user permission and ordered by `ordering`)
        images = (
            permission_policy.instances_user_has_any_permission_for(
                self.request.user, ["change", "delete"]
            )
            .order_by(ordering)
            .select_related("collection")
            .prefetch_renditions("max-165x165")
        )

        # Search
        query_string = None
        if "q" in self.request.GET:
            self.form = SearchForm(self.request.GET, placeholder=_("Search images"))
            if self.form.is_valid():
                query_string = self.form.cleaned_data["q"]

                images = images.search(query_string)
        else:
            self.form = SearchForm(placeholder=_("Search images"))

        # Filter by collection
        self.current_collection = None
        collection_id = self.request.GET.get("collection_id")
        if collection_id:
            try:
                self.current_collection = Collection.objects.get(id=collection_id)
                images = images.filter(collection=self.current_collection)
            except (ValueError, Collection.DoesNotExist):
                pass

        # Filter by tag
        self.current_tag = self.request.GET.get("tag")
        if self.current_tag:
            try:
                images = images.filter(tags__name=self.current_tag)
            except (AttributeError):
                self.current_tag = None

        entries_per_page = self.get_num_entries_per_page()
        paginator = Paginator(images, per_page=entries_per_page)
        images = paginator.get_page(self.request.GET.get("p"))

        next_url = reverse("wagtailimages:index")
        request_query_string = self.request.META.get("QUERY_STRING")
        if request_query_string:
            next_url += "?" + request_query_string

        context.update(
            {
                "images": images,
                "query_string": query_string,
                "is_searching": bool(query_string),
                "next": next_url,
                "entries_per_page": entries_per_page,
                "ENTRIES_PER_PAGE_CHOICES": self.ENTRIES_PER_PAGE_CHOICES,
                "current_ordering": ordering,
                "ORDERING_OPTIONS": self.ORDERING_OPTIONS,
            }
        )

        return context


class IndexView(BaseListingView):
    template_name = "wagtailimages/images/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        collections = permission_policy.collections_user_has_any_permission_for(
            self.request.user, ["add", "change"]
        )
        if len(collections) < 2:
            collections = None

        Image = get_image_model()

        context.update(
            {
                "search_form": self.form,
                "popular_tags": popular_tags_for_model(get_image_model()),
                "current_tag": self.current_tag,
                "collections": collections,
                "current_collection": self.current_collection,
                "user_can_add": permission_policy.user_has_permission(
                    self.request.user, "add"
                ),
                "app_label": Image._meta.app_label,
                "model_name": Image._meta.model_name,
            }
        )
        return context


class ListingResultsView(BaseListingView):
    template_name = "wagtailimages/images/results.html"


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
        original_file = image.file
        form = ImageForm(request.POST, request.FILES, instance=image, user=request.user)
        if form.is_valid():
            if "file" in form.changed_data:
                # Set new image file size
                image.file_size = image.file.size

                # Set new image file hash
                image.file.seek(0)
                image._set_file_hash(image.file.read())
                image.file.seek(0)

            form.save()

            if "file" in form.changed_data:
                # if providing a new image file, delete the old one and all renditions.
                # NB Doing this via original_file.delete() clears the file field,
                # which definitely isn't what we want...
                original_file.storage.delete(original_file.name)
                image.renditions.all().delete()

            # Reindex the image to make sure all tags are indexed
            search_index.insert_or_update_object(image)

            edit_url = reverse("wagtailimages:edit", args=(image.id,))
            redirect_url = "wagtailimages:index"
            if next_url:
                edit_url = f"{edit_url}?{urlencode({'next': next_url})}"
                redirect_url = next_url

            messages.success(
                request,
                _("Image '{0}' updated.").format(image.title),
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
                ).format(image.title),
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


def url_generator(request, image_id):
    image = get_object_or_404(get_image_model(), id=image_id)

    if not permission_policy.user_has_permission_for_instance(
        request.user, "change", image
    ):
        raise PermissionDenied

    form = URLGeneratorForm(
        initial={
            "filter_method": "original",
            "width": image.width,
            "height": image.height,
        }
    )

    return TemplateResponse(
        request,
        "wagtailimages/images/url_generator.html",
        {
            "image": image,
            "form": form,
        },
    )


def generate_url(request, image_id, filter_spec):
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
            {"error": "You do not have permission to generate a URL for this image."},
            status=403,
        )

    # Parse the filter spec to make sure its valid
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


@permission_checker.require("delete")
def delete(request, image_id):
    image = get_object_or_404(get_image_model(), id=image_id)

    if not permission_policy.user_has_permission_for_instance(
        request.user, "delete", image
    ):
        raise PermissionDenied

    next_url = get_valid_next_url_from_request(request)

    if request.method == "POST":
        image.delete()
        messages.success(request, _("Image '{0}' deleted.").format(image.title))
        return redirect(next_url) if next_url else redirect("wagtailimages:index")

    return TemplateResponse(
        request,
        "wagtailimages/images/confirm_delete.html",
        {
            "image": image,
            "next": next_url,
        },
    )


@permission_checker.require("add")
def add(request):
    ImageModel = get_image_model()
    ImageForm = get_image_form(ImageModel)

    if request.method == "POST":
        image = ImageModel(uploaded_by_user=request.user)
        form = ImageForm(request.POST, request.FILES, instance=image, user=request.user)
        if form.is_valid():
            # Set image file size
            image.file_size = image.file.size

            # Set image file hash
            image.file.seek(0)
            image._set_file_hash(image.file.read())
            image.file.seek(0)

            form.save()

            # Reindex the image to make sure all tags are indexed
            search_index.insert_or_update_object(image)

            messages.success(
                request,
                _("Image '{0}' added.").format(image.title),
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


def usage(request, image_id):
    image = get_object_or_404(get_image_model(), id=image_id)

    paginator = Paginator(image.get_usage(), per_page=USAGE_PAGE_SIZE)
    used_by = paginator.get_page(request.GET.get("p"))

    return TemplateResponse(
        request, "wagtailimages/images/usage.html", {"image": image, "used_by": used_by}
    )
