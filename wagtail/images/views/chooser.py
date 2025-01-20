from django.conf import settings
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import path, reverse
from django.utils.functional import cached_property
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import View

from wagtail.admin.auth import PermissionPolicyChecker
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.admin.models import popular_tags_for_model
from wagtail.admin.views.generic.chooser import (
    BaseChooseView,
    ChooseResultsViewMixin,
    ChooseViewMixin,
    ChosenMultipleViewMixin,
    ChosenResponseMixin,
    ChosenViewMixin,
    CreateViewMixin,
    CreationFormMixin,
    PreserveURLParametersMixin,
)
from wagtail.admin.viewsets.chooser import ChooserViewSet
from wagtail.images import get_image_model
from wagtail.images.formats import get_image_format
from wagtail.images.forms import ImageInsertionForm, get_image_form
from wagtail.images.permissions import permission_policy
from wagtail.images.utils import find_image_duplicates

permission_checker = PermissionPolicyChecker(permission_policy)


class ImageChosenResponseMixin(ChosenResponseMixin):
    def get_chosen_response_data(self, image, preview_image_filter="max-165x165"):
        """
        Given an image, return the json data to pass back to the image chooser panel
        """
        response_data = super().get_chosen_response_data(image)
        preview_image = image.get_rendition(preview_image_filter)
        response_data["preview"] = {
            "url": preview_image.url,
            "width": preview_image.width,
            "height": preview_image.height,
        }
        response_data["default_alt_text"] = image.default_alt_text
        return response_data


class ImageCreationFormMixin(CreationFormMixin):
    creation_tab_id = "upload"
    create_action_label = _("Upload")
    create_action_clicked_label = _("Uploading…")
    permission_policy = permission_policy

    def get_creation_form_class(self):
        return get_image_form(self.model)

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
    template_name = "wagtailimages/chooser/chooser.html"
    results_template_name = "wagtailimages/chooser/results.html"
    ordering = "-created_at"
    construct_queryset_hook_name = "construct_image_chooser_queryset"

    @property
    def per_page(self):
        # Make per_page into a property so that we can read back WAGTAILIMAGES_CHOOSER_PAGE_SIZE
        # at runtime.
        return getattr(settings, "WAGTAILIMAGES_CHOOSER_PAGE_SIZE", 20)

    def get_object_list(self):
        return (
            permission_policy.instances_user_has_any_permission_for(
                self.request.user, ["choose"]
            )
            .select_related("collection")
            .prefetch_renditions("max-165x165")
        )

    def filter_object_list(self, objects):
        tag_name = self.request.GET.get("tag")
        if tag_name:
            objects = objects.filter(tags__name=tag_name)

        return super().filter_object_list(objects)

    def get_filter_form(self):
        FilterForm = self.get_filter_form_class()
        return FilterForm(self.request.GET, collections=self.collections)

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
        chosen_url_name = (
            "wagtailimages_chooser:select_format"
            if self.request.GET.get("select_format")
            else "wagtailimages_chooser:chosen"
        )

        for image in context["results"]:
            image.chosen_url = self.append_preserved_url_parameters(
                reverse(chosen_url_name, args=(image.id,))
            )

        context["collections"] = self.collections
        return context


class ImageChooseViewMixin(ChooseViewMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["popular_tags"] = popular_tags_for_model(self.model)
        return context


class ImageChooseView(
    ImageChooseViewMixin, ImageCreationFormMixin, BaseImageChooseView
):
    pass


class ImageChooseResultsView(
    ChooseResultsViewMixin, ImageCreationFormMixin, BaseImageChooseView
):
    pass


class ImageChosenView(ChosenViewMixin, ImageChosenResponseMixin, View):
    def get(self, request, *args, pk, **kwargs):
        self.model = get_image_model()
        return super().get(request, *args, pk, **kwargs)


class ImageChosenMultipleView(ChosenMultipleViewMixin, ImageChosenResponseMixin, View):
    def get(self, request, *args, **kwargs):
        self.model = get_image_model()
        return super().get(request, *args, **kwargs)


class SelectFormatResponseMixin(PreserveURLParametersMixin):
    def render_select_format_response(self, image, form):
        action_url = self.append_preserved_url_parameters(
            reverse("wagtailimages_chooser:select_format", args=(image.id,))
        )
        return render_modal_workflow(
            self.request,
            "wagtailimages/chooser/select_format.html",
            None,
            {"image": image, "form": form, "select_format_action_url": action_url},
            json_data={"step": "select_format"},
        )


class ImageUploadViewMixin(SelectFormatResponseMixin, CreateViewMixin):
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
                return self.render_select_format_response(image, insertion_form)
            else:
                # not specifying a format; return the image details now
                return self.get_chosen_response(image)

        else:  # form is invalid
            return self.get_reshow_creation_form_response()

    def render_duplicate_found_response(self, request, new_image, existing_image):
        next_step_url = (
            "wagtailimages_chooser:select_format"
            if request.GET.get("select_format")
            else "wagtailimages_chooser:chosen"
        )
        choose_new_image_url = self.append_preserved_url_parameters(
            reverse(next_step_url, args=(new_image.id,))
        )
        choose_existing_image_url = self.append_preserved_url_parameters(
            reverse(next_step_url, args=(existing_image.id,))
        )

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


class ImageSelectFormatView(SelectFormatResponseMixin, ImageChosenResponseMixin, View):
    model = None

    def get(self, request, image_id):
        image = get_object_or_404(self.model, id=image_id)
        initial = {"alt_text": image.default_alt_text}
        initial.update(request.GET.dict())
        # If you edit an existing image, and there is no alt text, ensure that
        # "image is decorative" is ticked when you open the form
        initial["image_is_decorative"] = initial["alt_text"] == ""
        form = ImageInsertionForm(initial=initial, prefix="image-chooser-insertion")
        return self.render_select_format_response(image, form)

    def get_chosen_response_data(self, image):
        format = get_image_format(self.form.cleaned_data["format"])
        alt_text = self.form.cleaned_data["alt_text"]
        response_data = super().get_chosen_response_data(
            image, preview_image_filter=format.filter_spec
        )
        response_data.update(
            {
                "format": format.name,
                "alt": alt_text,
                "class": format.classname,
                "html": format.image_to_editor_html(image, alt_text),
            }
        )
        return response_data

    def post(self, request, image_id):
        image = get_object_or_404(get_image_model(), id=image_id)

        self.form = ImageInsertionForm(
            request.POST,
            initial={"alt_text": image.default_alt_text},
            prefix="image-chooser-insertion",
        )
        if self.form.is_valid():
            return self.get_chosen_response(image)
        else:
            return self.render_select_format_response(image, self.form)


class ImageChooserViewSet(ChooserViewSet):
    choose_view_class = ImageChooseView
    choose_results_view_class = ImageChooseResultsView
    chosen_view_class = ImageChosenView
    chosen_multiple_view_class = ImageChosenMultipleView
    create_view_class = ImageUploadView
    select_format_view_class = ImageSelectFormatView
    permission_policy = permission_policy
    register_widget = False
    preserve_url_parameters = ChooserViewSet.preserve_url_parameters + ["select_format"]

    icon = "image"
    choose_one_text = _("Choose an image")
    create_action_label = _("Upload")
    create_action_clicked_label = _("Uploading…")
    choose_another_text = _("Choose another image")
    edit_item_text = _("Edit this image")

    @property
    def select_format_view(self):
        return self.select_format_view_class.as_view(
            model=self.model,
            preserve_url_parameters=self.preserve_url_parameters,
        )

    def get_urlpatterns(self):
        return super().get_urlpatterns() + [
            path(
                "<int:image_id>/select_format/",
                self.select_format_view,
                name="select_format",
            ),
        ]


viewset = ImageChooserViewSet(
    "wagtailimages_chooser",
    model=get_image_model(),
    url_prefix="images/chooser",
)
