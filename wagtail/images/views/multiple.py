from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils.encoding import force_text
from django.views.decorators.http import require_POST
from django.views.decorators.vary import vary_on_headers

from wagtail.admin.utils import PermissionPolicyChecker
from wagtail.core.models import Collection
from wagtail.images import get_image_model
from wagtail.images.fields import ALLOWED_EXTENSIONS
from wagtail.images.forms import get_image_form
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
    if len(collections) > 1:
        collections_to_choose = Collection.order_for_display(collections)
    else:
        # no need to show a collections chooser
        collections_to_choose = None

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
                    'form': get_image_edit_form(Image)(
                        instance=image, prefix='image-%d' % image.id, user=request.user
                    ),
                }, request=request),
            })
        else:
            # Validation error
            return JsonResponse({
                'success': False,

                # https://github.com/django/django/blob/stable/1.6.x/django/forms/util.py#L45
                'error_message': '\n'.join(['\n'.join([force_text(i) for i in v]) for k, v in form.errors.items()]),
            })
    else:
        form = ImageForm(user=request.user)

    return render(request, 'wagtailimages/multiple/add.html', {
        'max_filesize': form.fields['file'].max_upload_size,
        'help_text': form.fields['file'].help_text,
        'allowed_extensions': ALLOWED_EXTENSIONS,
        'error_max_file_size': form.fields['file'].error_messages['file_too_large_unknown_size'],
        'error_accepted_file_types': form.fields['file'].error_messages['invalid_image'],
        'collections': collections_to_choose,
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
        request.POST, request.FILES, instance=image, prefix='image-' + image_id, user=request.user
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
