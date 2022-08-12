import os.path

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.vary import vary_on_headers
from django.views.generic.base import TemplateView, View

from wagtail.admin.views.generic import PermissionCheckedMixin


class AddView(PermissionCheckedMixin, TemplateView):
    # subclasses need to provide:
    # - permission_policy
    # - template_name
    # - upload_model

    # - edit_object_url_name
    # - delete_object_url_name
    # - edit_object_form_prefix
    # - context_object_name
    # - context_object_id_name

    # - edit_upload_url_name
    # - delete_upload_url_name
    # - edit_upload_form_prefix
    # - context_upload_name
    # - context_upload_id_name

    # - get_model()
    # - get_upload_form_class()
    # - get_edit_form_class()

    permission_required = "add"
    edit_form_template_name = "wagtailadmin/generic/multiple_upload/edit_form.html"

    @method_decorator(vary_on_headers("X-Requested-With"))
    def dispatch(self, request):
        self.model = self.get_model()

        return super().dispatch(request)

    def save_object(self, form):
        return form.save()

    def get_edit_object_form_context_data(self):
        """
        Return the context data necessary for rendering the HTML form for editing
        an object that has been successfully uploaded
        """
        edit_form_class = self.get_edit_form_class()
        return {
            self.context_object_name: self.object,
            "edit_action": reverse(self.edit_object_url_name, args=(self.object.pk,)),
            "delete_action": reverse(
                self.delete_object_url_name, args=(self.object.pk,)
            ),
            "form": edit_form_class(
                instance=self.object,
                prefix="%s-%d" % (self.edit_object_form_prefix, self.object.pk),
                user=self.request.user,
            ),
        }

    def get_edit_object_response_data(self):
        """
        Return the JSON response data for an object that has been successfully uploaded
        """
        return {
            "success": True,
            self.context_object_id_name: self.object.pk,
            "form": render_to_string(
                self.edit_form_template_name,
                self.get_edit_object_form_context_data(),
                request=self.request,
            ),
        }

    def get_edit_upload_form_context_data(self):
        """
        Return the context data necessary for rendering the HTML form for supplying the
        metadata to turn an upload object into a final object
        """
        edit_form_class = self.get_edit_form_class()
        return {
            self.context_upload_name: self.upload_object,
            "edit_action": reverse(
                self.edit_upload_url_name, args=(self.upload_object.id,)
            ),
            "delete_action": reverse(
                self.delete_upload_url_name, args=(self.upload_object.id,)
            ),
            "form": edit_form_class(
                instance=self.object,
                prefix="%s-%d" % (self.edit_upload_form_prefix, self.upload_object.id),
                user=self.request.user,
            ),
        }

    def get_edit_upload_response_data(self):
        """
        Return the JSON response data for an object that has been uploaded to an
        upload object and now needs extra metadata to become a final object
        """
        return {
            "success": True,
            self.context_upload_id_name: self.upload_object.id,
            "form": render_to_string(
                self.edit_form_template_name,
                self.get_edit_upload_form_context_data(),
                request=self.request,
            ),
        }

    def get_invalid_response_data(self, form):
        """
        Return the JSON response data for an invalid form submission
        """
        return {
            "success": False,
            "error_message": "\n".join(form.errors["file"]),
        }

    def post(self, request):
        if not request.FILES:
            return HttpResponseBadRequest("Must upload a file")

        # Build a form for validation
        upload_form_class = self.get_upload_form_class()
        form = upload_form_class(
            {
                "title": request.POST.get("title", request.FILES["files[]"].name),
                "collection": request.POST.get("collection"),
            },
            {
                "file": request.FILES["files[]"],
            },
            user=request.user,
        )

        if form.is_valid():
            # Save it
            self.object = self.save_object(form)

            # Success! Send back an edit form for this object to the user
            return JsonResponse(self.get_edit_object_response_data())
        elif "file" in form.errors:
            # The uploaded file is invalid; reject it now
            return JsonResponse(self.get_invalid_response_data(form))
        else:
            # Some other field of the form has failed validation, e.g. a required metadata field
            # on a custom image model. Store the object as an upload_model instance instead and
            # present the edit form so that it will become a proper object when successfully filled in
            self.upload_object = self.upload_model.objects.create(
                file=self.request.FILES["files[]"], uploaded_by_user=self.request.user
            )
            self.object = self.model(
                title=self.request.FILES["files[]"].name,
                collection_id=self.request.POST.get("collection"),
            )

            return JsonResponse(self.get_edit_upload_response_data())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Instantiate a dummy copy of the form that we can retrieve validation messages and media from;
        # actual rendering of forms will happen on AJAX POST rather than here
        upload_form_class = self.get_upload_form_class()
        self.form = upload_form_class(user=self.request.user)

        collections = self.permission_policy.collections_user_has_permission_for(
            self.request.user, "add"
        )
        if len(collections) < 2:
            # no need to show a collections chooser
            collections = None

        context.update(
            {
                "help_text": self.form.fields["file"].help_text,
                "collections": collections,
                "form_media": self.form.media,
            }
        )

        return context


class EditView(View):
    # subclasses need to provide:
    # - permission_policy
    # - pk_url_kwarg
    # - edit_object_form_prefix
    # - context_object_name
    # - context_object_id_name
    # - edit_object_url_name
    # - delete_object_url_name
    # - get_model()
    # - get_edit_form_class()

    http_method_names = ["post"]
    edit_form_template_name = "wagtailadmin/generic/multiple_upload/edit_form.html"

    def save_object(self, form):
        form.save()

    def post(self, request, *args, **kwargs):
        object_id = kwargs[self.pk_url_kwarg]
        self.model = self.get_model()
        self.form_class = self.get_edit_form_class()

        self.object = get_object_or_404(self.model, pk=object_id)

        if not self.permission_policy.user_has_permission_for_instance(
            request.user, "change", self.object
        ):
            raise PermissionDenied

        form = self.form_class(
            request.POST,
            request.FILES,
            instance=self.object,
            prefix="%s-%d" % (self.edit_object_form_prefix, object_id),
            user=request.user,
        )

        if form.is_valid():
            self.save_object(form)

            return JsonResponse(
                {
                    "success": True,
                    self.context_object_id_name: self.object.pk,
                }
            )
        else:
            return JsonResponse(
                {
                    "success": False,
                    self.context_object_id_name: self.object.pk,
                    "form": render_to_string(
                        self.edit_form_template_name,
                        {
                            self.context_object_name: self.object,  # only used for tests
                            "edit_action": reverse(
                                self.edit_object_url_name, args=(object_id,)
                            ),
                            "delete_action": reverse(
                                self.delete_object_url_name, args=(object_id,)
                            ),
                            "form": form,
                        },
                        request=request,
                    ),
                }
            )


class DeleteView(View):
    # subclasses need to provide:
    # - permission_policy
    # - pk_url_kwarg
    # - context_object_id_name

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        object_id = kwargs[self.pk_url_kwarg]
        self.model = self.get_model()
        self.object = get_object_or_404(self.model, pk=object_id)
        object_id = (
            self.object.pk
        )  # retrieve object id cast to the appropriate type (usually int)

        if not self.permission_policy.user_has_permission_for_instance(
            request.user, "delete", self.object
        ):
            raise PermissionDenied

        self.object.delete()

        return JsonResponse(
            {
                "success": True,
                self.context_object_id_name: object_id,
            }
        )


class CreateFromUploadView(View):
    # subclasses need to provide:
    # - edit_upload_url_name
    # - delete_upload_url_name
    # - upload_model
    # - upload_pk_url_kwarg
    # - edit_upload_form_prefix
    # - context_object_id_name
    # - context_upload_name
    # - get_model()
    # - get_edit_form_class()

    http_method_names = ["post"]
    edit_form_template_name = "wagtailadmin/generic/multiple_upload/edit_form.html"

    def save_object(self, form):
        self.object.file.save(
            os.path.basename(self.upload.file.name), self.upload.file.file, save=False
        )
        self.object.uploaded_by_user = self.request.user
        form.save()

    def post(self, request, *args, **kwargs):
        upload_id = kwargs[self.upload_pk_url_kwarg]
        self.model = self.get_model()
        self.form_class = self.get_edit_form_class()

        self.upload = get_object_or_404(self.upload_model, id=upload_id)

        if self.upload.uploaded_by_user != request.user:
            raise PermissionDenied

        self.object = self.model()
        form = self.form_class(
            request.POST,
            request.FILES,
            instance=self.object,
            prefix="%s-%d" % (self.edit_upload_form_prefix, upload_id),
            user=request.user,
        )

        if form.is_valid():
            self.save_object(form)
            self.upload.file.delete()
            self.upload.delete()

            return JsonResponse(
                {
                    "success": True,
                    self.context_object_id_name: self.object.id,
                }
            )
        else:
            return JsonResponse(
                {
                    "success": False,
                    "form": render_to_string(
                        self.edit_form_template_name,
                        {
                            self.context_upload_name: self.upload,
                            "edit_action": reverse(
                                self.edit_upload_url_name, args=(self.upload.id,)
                            ),
                            "delete_action": reverse(
                                self.delete_upload_url_name, args=(self.upload.id,)
                            ),
                            "form": form,
                        },
                        request=request,
                    ),
                }
            )


class DeleteUploadView(View):
    # subclasses need to provide:
    # - upload_model
    # - upload_pk_url_kwarg

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        upload_id = kwargs[self.upload_pk_url_kwarg]
        upload = get_object_or_404(self.upload_model, id=upload_id)

        if upload.uploaded_by_user != request.user:
            raise PermissionDenied

        upload.file.delete()
        upload.delete()

        return JsonResponse(
            {
                "success": True,
            }
        )
