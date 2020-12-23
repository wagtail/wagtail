from django.http import HttpResponseBadRequest, JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.vary import vary_on_headers
from django.views.generic.base import TemplateView

from wagtail.admin.views.generic import PermissionCheckedMixin


class AddView(PermissionCheckedMixin, TemplateView):
    # subclasses need to provide:
    # - permission_policy
    # - template_name
    # - edit_form_template_name
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

    permission_required = 'add'

    @method_decorator(vary_on_headers('X-Requested-With'))
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
            'edit_action': reverse(self.edit_object_url_name, args=(self.object.id,)),
            'delete_action': reverse(self.delete_object_url_name, args=(self.object.id,)),
            'form': edit_form_class(
                instance=self.object,
                prefix='%s-%d' % (self.edit_object_form_prefix, self.object.id),
                user=self.request.user
            ),
        }

    def get_edit_object_response_data(self):
        """
        Return the JSON response data for an object that has been successfully uploaded
        """
        return {
            'success': True,
            self.context_object_id_name: int(self.object.id),
            'form': render_to_string(
                self.edit_form_template_name,
                self.get_edit_object_form_context_data(),
                request=self.request
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
            'edit_action': reverse(self.edit_upload_url_name, args=(self.upload_object.id,)),
            'delete_action': reverse(self.delete_upload_url_name, args=(self.upload_object.id,)),
            'form': edit_form_class(
                instance=self.object,
                prefix='%s-%d' % (self.edit_upload_form_prefix, self.upload_object.id),
                user=self.request.user
            ),
        }

    def get_edit_upload_response_data(self):
        """
        Return the JSON response data for an object that has been uploaded to an
        upload object and now needs extra metadata to become a final object
        """
        return {
            'success': True,
            self.context_upload_id_name: self.upload_object.id,
            'form': render_to_string(
                self.edit_form_template_name,
                self.get_edit_upload_form_context_data(),
                request=self.request
            ),
        }

    def get_invalid_response_data(self, form):
        """
        Return the JSON response data for an invalid form submission
        """
        return {
            'success': False,
            'error_message': '\n'.join(form.errors['file']),
        }

    def post(self, request):
        if not request.is_ajax():
            return HttpResponseBadRequest("Cannot POST to this view without AJAX")

        if not request.FILES:
            return HttpResponseBadRequest("Must upload a file")

        # Build a form for validation
        upload_form_class = self.get_upload_form_class()
        form = upload_form_class({
            'title': request.FILES['files[]'].name,
            'collection': request.POST.get('collection'),
        }, {
            'file': request.FILES['files[]'],
        }, user=request.user)

        if form.is_valid():
            # Save it
            self.object = self.save_object(form)

            # Success! Send back an edit form for this object to the user
            return JsonResponse(self.get_edit_object_response_data())
        elif 'file' in form.errors:
            # The uploaded file is invalid; reject it now
            return JsonResponse(self.get_invalid_response_data(form))
        else:
            # Some other field of the form has failed validation, e.g. a required metadata field
            # on a custom image model. Store the object as an upload_model instance instead and
            # present the edit form so that it will become a proper object when successfully filled in
            self.upload_object = self.upload_model.objects.create(
                file=self.request.FILES['files[]'], uploaded_by_user=self.request.user
            )
            self.object = self.model(
                title=self.request.FILES['files[]'].name,
                collection_id=self.request.POST.get('collection')
            )

            return JsonResponse(self.get_edit_upload_response_data())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Instantiate a dummy copy of the form that we can retrieve validation messages and media from;
        # actual rendering of forms will happen on AJAX POST rather than here
        upload_form_class = self.get_upload_form_class()
        self.form = upload_form_class(user=self.request.user)

        collections = self.permission_policy.collections_user_has_permission_for(self.request.user, 'add')
        if len(collections) < 2:
            # no need to show a collections chooser
            collections = None

        context.update({
            'help_text': self.form.fields['file'].help_text,
            'collections': collections,
            'form_media': self.form.media,
        })

        return context
