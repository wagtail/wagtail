import os

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.utils.translation import ugettext as _
from django.views.decorators.vary import vary_on_headers

from wagtail.admin import messages
from wagtail.admin.forms import SearchForm
from wagtail.admin.utils import PermissionPolicyChecker, permission_denied, popular_tags_for_model
from wagtail.core.models import Collection, Site
from wagtail.images import get_image_model
from wagtail.images.exceptions import InvalidFilterSpecError
from wagtail.images.forms import URLGeneratorForm, get_image_form
from wagtail.images.models import Filter, SourceImageIOError
from wagtail.images.permissions import permission_policy
from wagtail.images.views.serve import generate_signature
from wagtail.search import index as search_index
from wagtail.utils.pagination import paginate

permission_checker = PermissionPolicyChecker(permission_policy)


@permission_checker.require_any('add', 'change', 'delete')
@vary_on_headers('X-Requested-With')
def index(request):
    Image = get_image_model()

    # Get images (filtered by user permission)
    images = permission_policy.instances_user_has_any_permission_for(
        request.user, ['change', 'delete']
    ).order_by('-created_at')

    # Search
    query_string = None
    if 'q' in request.GET:
        form = SearchForm(request.GET, placeholder=_("Search images"))
        if form.is_valid():
            query_string = form.cleaned_data['q']

            images = images.search(query_string)
    else:
        form = SearchForm(placeholder=_("Search images"))

    # Filter by collection
    current_collection = None
    collection_id = request.GET.get('collection_id')
    if collection_id:
        try:
            current_collection = Collection.objects.get(id=collection_id)
            images = images.filter(collection=current_collection)
        except (ValueError, Collection.DoesNotExist):
            pass

    paginator, images = paginate(request, images)

    collections = permission_policy.collections_user_has_any_permission_for(
        request.user, ['add', 'change']
    )
    if len(collections) < 2:
        collections = None

    # Create response
    if request.is_ajax():
        return render(request, 'wagtailimages/images/results.html', {
            'images': images,
            'query_string': query_string,
            'is_searching': bool(query_string),
        })
    else:
        return render(request, 'wagtailimages/images/index.html', {
            'images': images,
            'query_string': query_string,
            'is_searching': bool(query_string),

            'search_form': form,
            'popular_tags': popular_tags_for_model(Image),
            'collections': collections,
            'current_collection': current_collection,
            'user_can_add': permission_policy.user_has_permission(request.user, 'add'),
        })


@permission_checker.require('change')
def edit(request, image_id):
    Image = get_image_model()
    ImageForm = get_image_form(Image)

    image = get_object_or_404(Image, id=image_id)

    if not permission_policy.user_has_permission_for_instance(request.user, 'change', image):
        return permission_denied(request)

    if request.method == 'POST':
        original_file = image.file
        form = ImageForm(request.POST, request.FILES, instance=image, user=request.user)
        if form.is_valid():
            if 'file' in form.changed_data:
                # Set new image file size
                image.file_size = image.file.size

                # Set new image file hash
                image.file.seek(0)
                image._set_file_hash(image.file.read())

            form.save()

            if 'file' in form.changed_data:
                # if providing a new image file, delete the old one and all renditions.
                # NB Doing this via original_file.delete() clears the file field,
                # which definitely isn't what we want...
                original_file.storage.delete(original_file.name)
                image.renditions.all().delete()

            # Reindex the image to make sure all tags are indexed
            search_index.insert_or_update_object(image)

            messages.success(request, _("Image '{0}' updated.").format(image.title), buttons=[
                messages.button(reverse('wagtailimages:edit', args=(image.id,)), _('Edit again'))
            ])
            return redirect('wagtailimages:index')
        else:
            messages.error(request, _("The image could not be saved due to errors."))
    else:
        form = ImageForm(instance=image, user=request.user)

    # Check if we should enable the frontend url generator
    try:
        reverse('wagtailimages_serve', args=('foo', '1', 'bar'))
        url_generator_enabled = True
    except NoReverseMatch:
        url_generator_enabled = False

    if image.is_stored_locally():
        # Give error if image file doesn't exist
        if not os.path.isfile(image.file.path):
            messages.error(request, _(
                "The source image file could not be found. Please change the source or delete the image."
            ).format(image.title), buttons=[
                messages.button(reverse('wagtailimages:delete', args=(image.id,)), _('Delete'))
            ])

    try:
        filesize = image.get_file_size()
    except SourceImageIOError:
        filesize = None

    return render(request, "wagtailimages/images/edit.html", {
        'image': image,
        'form': form,
        'url_generator_enabled': url_generator_enabled,
        'filesize': filesize,
        'user_can_delete': permission_policy.user_has_permission_for_instance(
            request.user, 'delete', image
        ),
    })


def url_generator(request, image_id):
    image = get_object_or_404(get_image_model(), id=image_id)

    if not permission_policy.user_has_permission_for_instance(request.user, 'change', image):
        return permission_denied(request)

    form = URLGeneratorForm(initial={
        'filter_method': 'original',
        'width': image.width,
        'height': image.height,
    })

    return render(request, "wagtailimages/images/url_generator.html", {
        'image': image,
        'form': form,
    })


def generate_url(request, image_id, filter_spec):
    # Get the image
    Image = get_image_model()
    try:
        image = Image.objects.get(id=image_id)
    except Image.DoesNotExist:
        return JsonResponse({
            'error': "Cannot find image."
        }, status=404)

    # Check if this user has edit permission on this image
    if not permission_policy.user_has_permission_for_instance(request.user, 'change', image):
        return JsonResponse({
            'error': "You do not have permission to generate a URL for this image."
        }, status=403)

    # Parse the filter spec to make sure its valid
    try:
        Filter(spec=filter_spec).operations
    except InvalidFilterSpecError:
        return JsonResponse({
            'error': "Invalid filter spec."
        }, status=400)

    # Generate url
    signature = generate_signature(image_id, filter_spec)
    url = reverse('wagtailimages_serve', args=(signature, image_id, filter_spec))

    # Get site root url
    try:
        site_root_url = Site.objects.get(is_default_site=True).root_url
    except Site.DoesNotExist:
        site_root_url = Site.objects.first().root_url

    # Generate preview url
    preview_url = reverse('wagtailimages:preview', args=(image_id, filter_spec))

    return JsonResponse({'url': site_root_url + url, 'preview_url': preview_url}, status=200)


def preview(request, image_id, filter_spec):
    image = get_object_or_404(get_image_model(), id=image_id)

    try:
        response = HttpResponse()
        image = Filter(spec=filter_spec).run(image, response)
        response['Content-Type'] = 'image/' + image.format_name
        return response
    except InvalidFilterSpecError:
        return HttpResponse("Invalid filter spec: " + filter_spec, content_type='text/plain', status=400)


@permission_checker.require('delete')
def delete(request, image_id):
    image = get_object_or_404(get_image_model(), id=image_id)

    if not permission_policy.user_has_permission_for_instance(request.user, 'delete', image):
        return permission_denied(request)

    if request.method == 'POST':
        image.delete()
        messages.success(request, _("Image '{0}' deleted.").format(image.title))
        return redirect('wagtailimages:index')

    return render(request, "wagtailimages/images/confirm_delete.html", {
        'image': image,
    })


@permission_checker.require('add')
def add(request):
    ImageModel = get_image_model()
    ImageForm = get_image_form(ImageModel)

    if request.method == 'POST':
        image = ImageModel(uploaded_by_user=request.user)
        form = ImageForm(request.POST, request.FILES, instance=image, user=request.user)
        if form.is_valid():
            # Set image file size
            image.file_size = image.file.size

            # Set image file hash
            image.file.seek(0)
            image._set_file_hash(image.file.read())

            form.save()

            # Reindex the image to make sure all tags are indexed
            search_index.insert_or_update_object(image)

            messages.success(request, _("Image '{0}' added.").format(image.title), buttons=[
                messages.button(reverse('wagtailimages:edit', args=(image.id,)), _('Edit'))
            ])
            return redirect('wagtailimages:index')
        else:
            messages.error(request, _("The image could not be created due to errors."))
    else:
        form = ImageForm(user=request.user)

    return render(request, "wagtailimages/images/add.html", {
        'form': form,
    })


def usage(request, image_id):
    image = get_object_or_404(get_image_model(), id=image_id)

    paginator, used_by = paginate(request, image.get_usage())

    return render(request, "wagtailimages/images/usage.html", {
        'image': image,
        'used_by': used_by
    })
