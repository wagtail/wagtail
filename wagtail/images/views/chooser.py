from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.translation import gettext as _
from django.views.generic.base import View

from wagtail import hooks
from wagtail.admin.auth import PermissionPolicyChecker
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.admin.models import popular_tags_for_model
from wagtail.images import get_image_model
from wagtail.images.formats import get_image_format
from wagtail.images.forms import ImageInsertionForm, get_image_form
from wagtail.images.permissions import permission_policy
from wagtail.images.utils import find_image_duplicates
from wagtail.search import index as search_index

permission_checker = PermissionPolicyChecker(permission_policy)

CHOOSER_PAGE_SIZE = getattr(settings, "WAGTAILIMAGES_CHOOSER_PAGE_SIZE", 12)


def get_image_result_data(image):
    """
    helper function: given an image, return the json data to pass back to the
    image chooser panel
    """
    preview_image = image.get_rendition("max-165x165")

    return {
        "id": image.id,
        "edit_link": reverse("wagtailimages:edit", args=(image.id,)),
        "title": image.title,
        "preview": {
            "url": preview_image.url,
            "width": preview_image.width,
            "height": preview_image.height,
        },
    }


class BaseChooseView(View):
    def get(self, request):
        self.image_model = get_image_model()

        images = permission_policy.instances_user_has_any_permission_for(
            request.user, ["choose"]
        ).order_by("-created_at")

        # allow hooks to modify the queryset
        for hook in hooks.get_hooks("construct_image_chooser_queryset"):
            images = hook(images, request)

        collection_id = request.GET.get("collection_id")
        if collection_id:
            images = images.filter(collection=collection_id)

        self.is_searching = False
        self.q = None

        if "q" in request.GET:
            self.search_form = SearchForm(request.GET)
            if self.search_form.is_valid():
                self.q = self.search_form.cleaned_data["q"]
                self.is_searching = True
                images = images.search(self.q)
        else:
            self.search_form = SearchForm()

        if not self.is_searching:
            tag_name = request.GET.get("tag")
            if tag_name:
                images = images.filter(tags__name=tag_name)

        # Pagination
        paginator = Paginator(images, per_page=CHOOSER_PAGE_SIZE)
        self.images = paginator.get_page(request.GET.get("p"))
        return self.render_to_response()

    def get_context_data(self):
        return {
            "images": self.images,
            "is_searching": self.is_searching,
            "query_string": self.q,
            "will_select_format": self.request.GET.get("select_format"),
        }

    def render_to_response(self):
        raise NotImplementedError()


class ChooseView(BaseChooseView):
    def get_context_data(self):
        context = super().get_context_data()

        if permission_policy.user_has_permission(self.request.user, "add"):
            ImageForm = get_image_form(self.image_model)
            uploadform = ImageForm(
                user=self.request.user, prefix="image-chooser-upload"
            )
        else:
            uploadform = None

        collections = permission_policy.collections_user_has_permission_for(
            self.request.user, "choose"
        )
        if len(collections) < 2:
            collections = None

        context.update(
            {
                "searchform": self.search_form,
                "popular_tags": popular_tags_for_model(self.image_model),
                "collections": collections,
                "uploadform": uploadform,
            }
        )
        return context

    def render_to_response(self):
        return render_modal_workflow(
            self.request,
            "wagtailimages/chooser/chooser.html",
            None,
            self.get_context_data(),
            json_data={
                "step": "chooser",
                "error_label": _("Server Error"),
                "error_message": _(
                    "Report this error to your website administrator with the following information:"
                ),
                "tag_autocomplete_url": reverse("wagtailadmin_tag_autocomplete"),
            },
        )


class ChooseResultsView(BaseChooseView):
    def render_to_response(self):
        return TemplateResponse(
            self.request, "wagtailimages/chooser/results.html", self.get_context_data()
        )


def image_chosen(request, image_id):
    image = get_object_or_404(get_image_model(), id=image_id)

    return render_modal_workflow(
        request,
        None,
        None,
        None,
        json_data={"step": "image_chosen", "result": get_image_result_data(image)},
    )


def duplicate_found(request, new_image, existing_image):
    next_step_url = (
        "wagtailimages:chooser_select_format"
        if request.GET.get("select_format")
        else "wagtailimages:image_chosen"
    )
    choose_new_image_url = reverse(next_step_url, args=(new_image.id,))
    choose_existing_image_url = reverse(next_step_url, args=(existing_image.id,))

    cancel_duplicate_upload_action = (
        f"{reverse('wagtailimages:delete', args=(new_image.id,))}?"
        f"{urlencode({'next': choose_existing_image_url})}"
    )

    duplicate_upload_html = render_to_string(
        "wagtailimages/chooser/confirm_duplicate_upload.html",
        {
            "new_image": new_image,
            "existing_image": existing_image,
            "confirm_duplicate_upload_action": choose_new_image_url,
            "cancel_duplicate_upload_action": cancel_duplicate_upload_action,
        },
        request,
    )
    return render_modal_workflow(
        request,
        None,
        None,
        None,
        json_data={
            "step": "duplicate_found",
            "htmlFragment": duplicate_upload_html,
        },
    )


@permission_checker.require("add")
def chooser_upload(request):
    Image = get_image_model()
    ImageForm = get_image_form(Image)

    if request.method == "POST":
        image = Image(uploaded_by_user=request.user)
        form = ImageForm(
            request.POST,
            request.FILES,
            instance=image,
            user=request.user,
            prefix="image-chooser-upload",
        )

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

            duplicates = find_image_duplicates(
                image=image,
                user=request.user,
                permission_policy=permission_policy,
            )
            existing_image = duplicates.first()
            if existing_image:
                return duplicate_found(request, image, existing_image)

            if request.GET.get("select_format"):
                form = ImageInsertionForm(
                    initial={"alt_text": image.default_alt_text},
                    prefix="image-chooser-insertion",
                )
                return render_modal_workflow(
                    request,
                    "wagtailimages/chooser/select_format.html",
                    None,
                    {"image": image, "form": form},
                    json_data={"step": "select_format"},
                )
            else:
                # not specifying a format; return the image details now
                return render_modal_workflow(
                    request,
                    None,
                    None,
                    None,
                    json_data={
                        "step": "image_chosen",
                        "result": get_image_result_data(image),
                    },
                )
    else:
        form = ImageForm(user=request.user, prefix="image-chooser-upload")

    upload_form_html = render_to_string(
        "wagtailimages/chooser/upload_form.html",
        {
            "form": form,
            "will_select_format": request.GET.get("select_format"),
        },
        request,
    )

    return render_modal_workflow(
        request,
        None,
        None,
        None,
        json_data={"step": "reshow_upload_form", "htmlFragment": upload_form_html},
    )


def chooser_select_format(request, image_id):
    image = get_object_or_404(get_image_model(), id=image_id)

    if request.method == "POST":
        form = ImageInsertionForm(
            request.POST,
            initial={"alt_text": image.default_alt_text},
            prefix="image-chooser-insertion",
        )
        if form.is_valid():

            format = get_image_format(form.cleaned_data["format"])
            preview_image = image.get_rendition(format.filter_spec)

            image_data = {
                "id": image.id,
                "title": image.title,
                "format": format.name,
                "alt": form.cleaned_data["alt_text"],
                "class": format.classnames,
                "edit_link": reverse("wagtailimages:edit", args=(image.id,)),
                "preview": {
                    "url": preview_image.url,
                    "width": preview_image.width,
                    "height": preview_image.height,
                },
                "html": format.image_to_editor_html(
                    image, form.cleaned_data["alt_text"]
                ),
            }

            return render_modal_workflow(
                request,
                None,
                None,
                None,
                json_data={"step": "image_chosen", "result": image_data},
            )
    else:
        initial = {"alt_text": image.default_alt_text}
        initial.update(request.GET.dict())
        # If you edit an existing image, and there is no alt text, ensure that
        # "image is decorative" is ticked when you open the form
        initial["image_is_decorative"] = initial["alt_text"] == ""
        form = ImageInsertionForm(initial=initial, prefix="image-chooser-insertion")

    return render_modal_workflow(
        request,
        "wagtailimages/chooser/select_format.html",
        None,
        {"image": image, "form": form},
        json_data={"step": "select_format"},
    )
