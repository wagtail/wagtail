import os.path

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.vary import vary_on_headers

from wagtail.admin.auth import PermissionPolicyChecker
from wagtail.images import get_image_model
from wagtail.images.fields import ALLOWED_EXTENSIONS
from wagtail.images.forms import get_image_form
from wagtail.images.models import UploadedImage
from wagtail.images.permissions import permission_policy
from wagtail.search.backends import get_search_backends


permission_checker = PermissionPolicyChecker(permission_policy)


def get_image_edit_form(ImageModel):
    ImageForm = get_image_form(ImageModel)

    # Make a new form with the file and focal point fields excluded
    class ImageEditForm(ImageForm):
        class Meta(ImageForm.Meta):
            model = ImageModel
            exclude = (
                'file',
                'focal_point_x',
                'focal_point_y',
                'focal_point_width',
                'focal_point_height',
            )

    return ImageEditForm


@permission_checker.require('add')
@vary_on_headers('X-Requested-With')
def add(request):
    Image = get_image_model()
    ImageForm = get_image_form(Image)

    collections = permission_policy.collections_user_has_permission_for(request.user, 'add')
    if len(collections) < 2:
        # no need to show a collections chooser
        collections = None

    if request.method == 'POST':
        if not request.is_ajax():
            return HttpResponseBadRequest("Cannot POST to this view without AJAX")

        if not request.FILES:
            return HttpResponseBadRequest("Must upload a file")

        # Build a form for validation
        form = ImageForm({
            'title': request.FILES['files[]'].name,
            'collection': request.POST.get('collection'),
        }, {
            'file': request.FILES['files[]'],
        }, user=request.user)

        if form.is_valid():
            # Save it
            image = form.save(commit=False)
            image.uploaded_by_user = request.user
            image.file_size = image.file.size
            image.file.seek(0)
            image._set_file_hash(image.file.read())
            image.file.seek(0)
            image.save()

            # Success! Send back an edit form for this image to the user
            return JsonResponse({
                'success': True,
                'image_id': int(image.id),
                'form': render_to_string('wagtailimages/multiple/edit_form.html', {
                    'image': image,
                    'edit_action': reverse('wagtailimages:edit_multiple', args=(image.id,)),
                    'delete_action': reverse('wagtailimages:delete_multiple', args=(image.id,)),
                    'form': get_image_edit_form(Image)(
                        instance=image, prefix='image-%d' % image.id, user=request.user
                    ),
                }, request=request),
            })
        elif 'file' in form.errors:
            # The uploaded file is invalid; reject it now
            return JsonResponse({
                'success': False,
                'error_message': '\n'.join(form.errors['file']),
            })
        else:
            # Some other field of the image form has failed validation, e.g. a required metadata field
            # on a custom image model. Store the image as an UploadedImage instead and present the
            # edit form so that it will become a proper Image when successfully filled in
            uploaded_image = UploadedImage.objects.create(
                file=request.FILES['files[]'], uploaded_by_user=request.user
            )
            image = Image(title=request.FILES['files[]'].name, collection_id=request.POST.get('collection'))

            return JsonResponse({
                'success': True,
                'uploaded_image_id': uploaded_image.id,
                'form': render_to_string('wagtailimages/multiple/edit_form.html', {
                    'uploaded_image': uploaded_image,
                    'edit_action': reverse('wagtailimages:create_multiple_from_uploaded_image', args=(uploaded_image.id,)),
                    'delete_action': reverse('wagtailimages:delete_upload_multiple', args=(uploaded_image.id,)),
                    'form': get_image_edit_form(Image)(
                        instance=image, prefix='uploaded-image-%d' % uploaded_image.id, user=request.user
                    ),
                }, request=request),
            })
    else:
        # Instantiate a dummy copy of the form that we can retrieve validation messages and media from;
        # actual rendering of forms will happen on AJAX POST rather than here
        form = ImageForm(user=request.user)

        return TemplateResponse(request, 'wagtailimages/multiple/add.html', {
            'max_filesize': form.fields['file'].max_upload_size,
            'help_text': form.fields['file'].help_text,
            'allowed_extensions': ALLOWED_EXTENSIONS,
            'error_max_file_size': form.fields['file'].error_messages['file_too_large_unknown_size'],
            'error_accepted_file_types': form.fields['file'].error_messages['invalid_image_extension'],
            'collections': collections,
            'form_media': form.media,
        })


@require_POST
def edit(request, image_id, callback=None):
    Image = get_image_model()
    ImageForm = get_image_edit_form(Image)

    image = get_object_or_404(Image, id=image_id)

    if not request.is_ajax():
        return HttpResponseBadRequest("Cannot POST to this view without AJAX")

    if not permission_policy.user_has_permission_for_instance(request.user, 'change', image):
        raise PermissionDenied

    form = ImageForm(
        request.POST, request.FILES, instance=image, prefix='image-%d' % image_id, user=request.user
    )

    if form.is_valid():
        form.save()

        # Reindex the image to make sure all tags are indexed
        for backend in get_search_backends():
            backend.add(image)

        return JsonResponse({
            'success': True,
            'image_id': int(image_id),
        })
    else:
        return JsonResponse({
            'success': False,
            'image_id': int(image_id),
            'form': render_to_string('wagtailimages/multiple/edit_form.html', {
                'image': image,
                'edit_action': reverse('wagtailimages:edit_multiple', args=(image_id,)),
                'delete_action': reverse('wagtailimages:delete_multiple', args=(image_id,)),
                'form': form,
            }, request=request),
        })


@require_POST
def delete(request, image_id):
    image = get_object_or_404(get_image_model(), id=image_id)

    if not request.is_ajax():
        return HttpResponseBadRequest("Cannot POST to this view without AJAX")

    if not permission_policy.user_has_permission_for_instance(request.user, 'delete', image):
        raise PermissionDenied

    image.delete()

    return JsonResponse({
        'success': True,
        'image_id': int(image_id),
    })


@require_POST
def create_from_uploaded_image(request, uploaded_image_id):
    Image = get_image_model()
    ImageForm = get_image_edit_form(Image)

    uploaded_image = get_object_or_404(UploadedImage, id=uploaded_image_id)

    if not request.is_ajax():
        return HttpResponseBadRequest("Cannot POST to this view without AJAX")

    if uploaded_image.uploaded_by_user != request.user:
        raise PermissionDenied

    image = Image()
    form = ImageForm(
        request.POST, request.FILES, instance=image, prefix='uploaded-image-%d' % uploaded_image_id, user=request.user
    )

    if form.is_valid():
        # assign the file content from uploaded_image to the image object, to ensure it gets saved to
        # Image's storage

        image.file.save(os.path.basename(uploaded_image.file.name), uploaded_image.file.file, save=False)
        image.uploaded_by_user = request.user
        image.file_size = image.file.size
        image.file.open()
        image.file.seek(0)
        image._set_file_hash(image.file.read())
        image.file.seek(0)
        form.save()

        uploaded_image.file.delete()
        uploaded_image.delete()

        # Reindex the image to make sure all tags are indexed
        for backend in get_search_backends():
            backend.add(image)

        return JsonResponse({
            'success': True,
            'image_id': image.id,
        })
    else:
        return JsonResponse({
            'success': False,
            'form': render_to_string('wagtailimages/multiple/edit_form.html', {
                'uploaded_image': uploaded_image,
                'edit_action': reverse('wagtailimages:create_multiple_from_uploaded_image', args=(uploaded_image.id,)),
                'delete_action': reverse('wagtailimages:delete_upload_multiple', args=(uploaded_image.id,)),
                'form': form,
            }, request=request),
        })


@require_POST
def delete_upload(request, uploaded_image_id):
    uploaded_image = get_object_or_404(UploadedImage, id=uploaded_image_id)

    if not request.is_ajax():
        return HttpResponseBadRequest("Cannot POST to this view without AJAX")

    if uploaded_image.uploaded_by_user != request.user:
        raise PermissionDenied

    uploaded_image.file.delete()
    uploaded_image.delete()

    return JsonResponse({
        'success': True,
    })
