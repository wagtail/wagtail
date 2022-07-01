from django import forms
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import View

from wagtail import hooks
from wagtail.admin.auth import PermissionPolicyChecker
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.admin.models import popular_tags_for_model
from wagtail.admin.views.generic.chooser import (
    BaseChooseView,
    ChooseResultsViewMixin,
    ChooseViewMixin,
    ChosenResponseMixin,
    ChosenViewMixin,
    CreateViewMixin,
    CreationFormMixin,
)
from wagtail.images import get_image_model
from wagtail.images.formats import get_image_format
from wagtail.images.forms import ImageInsertionForm, get_image_form
from wagtail.images.permissions import permission_policy
from wagtail.images.utils import find_image_duplicates

permission_checker = PermissionPolicyChecker(permission_policy)


class ImageChosenResponseMixin(ChosenResponseMixin):
    def get_chosen_response_data(self, image):
        """
        Given an image, return the json data to pass back to the image chooser panel
        """
        response_data = super().get_chosen_response_data(image)
        preview_image = image.get_rendition("max-165x165")
        response_data["preview"] = {
            "url": preview_image.url,
            "width": preview_image.width,
            "height": preview_image.height,
        }
        return response_data


class ImageFilterForm(forms.Form):
    q = forms.CharField(
        label=_("Search term"),
        widget=forms.TextInput(attrs={"placeholder": _("Search")}),
        required=False,
    )

    def __init__(self, *args, collections, **kwargs):
        super().__init__(*args, **kwargs)

        if collections:
            collection_choices = [
                ("", _("All collections"))
            ] + collections.get_indented_choices()
            self.fields["collection_id"] = forms.ChoiceField(
                label=_("Collection"),
                choices=collection_choices,
                required=False,
            )


class ImageCreationFormMixin(CreationFormMixin):
    creation_tab_id = "upload"
    create_url_name = "wagtailimages:chooser_upload"
    create_action_label = _("Upload")
    create_action_clicked_label = _("Uploading…")
    permission_policy = permission_policy

    def get_creation_form_class(self):
        return get_image_form(self.model)

    def get_create_url(self):
        url = super().get_create_url()
        if self.request.GET.get("select_format"):
            url += "?select_format=true"
        return url

    def get_creation_form_kwargs(self):
        kwargs = super().get_creation_form_kwargs()
        kwargs.update(
            {
                "user": self.request.user,
                "prefix": "image-chooser-upload",
            }
        )
        if self.request.method in ("POST", "PUT"):
            kwargs["instance"] = self.model(uploaded_by_user=self.request.user)

        return kwargs


class BaseImageChooseView(BaseChooseView):
    icon = "image"
    page_title = _("Choose an image")
    results_url_name = "wagtailimages:chooser_results"
    template_name = "wagtailimages/chooser/chooser.html"
    results_template_name = "wagtailimages/chooser/results.html"
    filter_form_class = ImageFilterForm
    per_page = getattr(settings, "WAGTAILIMAGES_CHOOSER_PAGE_SIZE", 12)

    def get_object_list(self):
        images = (
            permission_policy.instances_user_has_any_permission_for(
                self.request.user, ["choose"]
            )
            .order_by("-created_at")
            .select_related("collection")
            .prefetch_renditions("max-165x165")
        )

        # allow hooks to modify the queryset
        for hook in hooks.get_hooks("construct_image_chooser_queryset"):
            images = hook(images, self.request)

        tag_name = self.request.GET.get("tag")
        if tag_name:
            images = images.filter(tags__name=tag_name)

        return images

    def get_filter_form(self):
        FilterForm = self.get_filter_form_class()
        return FilterForm(self.request.GET, collections=self.collections)

    def filter_object_list(self, images, form):
        collection_id = form.cleaned_data.get("collection_id")
        if collection_id:
            images = images.filter(collection=collection_id)

        self.search_query = form.cleaned_data["q"]
        if self.search_query:
            self.is_searching = True
            images = images.search(self.search_query)

        return images

    @cached_property
    def collections(self):
        collections = self.permission_policy.collections_user_has_permission_for(
            self.request.user, "choose"
        )
        if len(collections) < 2:
            return None

        return collections

    def get(self, request):
        self.model = get_image_model()
        return super().get(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "will_select_format": self.request.GET.get("select_format"),
                "collections": self.collections,
            }
        )
        return context


class ImageChooseViewMixin(ChooseViewMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["popular_tags"] = popular_tags_for_model(self.model)
        return context

    def get_response_json_data(self):
        json_data = super().get_response_json_data()
        json_data["tag_autocomplete_url"] = reverse("wagtailadmin_tag_autocomplete")
        return json_data


class ChooseView(ImageChooseViewMixin, ImageCreationFormMixin, BaseImageChooseView):
    pass


class ChooseResultsView(
    ChooseResultsViewMixin, ImageCreationFormMixin, BaseImageChooseView
):
    pass


class ImageChosenView(ChosenViewMixin, ImageChosenResponseMixin, View):
    def get(self, request, *args, pk, **kwargs):
        self.model = get_image_model()
        return super().get(request, *args, pk, **kwargs)


class ImageUploadViewMixin(CreateViewMixin):
    def get(self, request):
        self.model = get_image_model()
        return super().get(request)

    def post(self, request):
        self.model = get_image_model()
        self.form = self.get_creation_form()

        if self.form.is_valid():
            image = self.save_form(self.form)

            duplicates = find_image_duplicates(
                image=image,
                user=request.user,
                permission_policy=permission_policy,
            )
            existing_image = duplicates.first()
            if existing_image:
                return self.render_duplicate_found_response(
                    request, image, existing_image
                )

            if request.GET.get("select_format"):
                insertion_form = ImageInsertionForm(
                    initial={"alt_text": image.default_alt_text},
                    prefix="image-chooser-insertion",
                )
                return render_modal_workflow(
                    request,
                    "wagtailimages/chooser/select_format.html",
                    None,
                    {"image": image, "form": insertion_form},
                    json_data={"step": "select_format"},
                )
            else:
                # not specifying a format; return the image details now
                return self.get_chosen_response(image)

        else:  # form is invalid
            return self.get_reshow_creation_form_response()

    def render_duplicate_found_response(self, request, new_image, existing_image):
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


class ImageUploadView(
    ImageUploadViewMixin, ImageCreationFormMixin, ImageChosenResponseMixin, View
):
    pass


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
                json_data={"step": "chosen", "result": image_data},
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
