import os

from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext as _
from django.views.decorators.vary import vary_on_headers
from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import HttpResponse, JsonResponse

from wagtail.wagtailcore.models import Site
from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailadmin import messages
from wagtail.wagtailsearch.backends import get_search_backends, get_search_backend

from wagtail.wagtailimages.models import get_image_model, Filter
from wagtail.wagtailimages.forms import get_image_form, URLGeneratorForm
from wagtail.wagtailimages.permissions import \
    image_permission_required, any_image_permission_required, user_can_edit_image, user_has_image_permission, images_editable_by_user
from wagtail.wagtailimages.utils import generate_signature
from wagtail.wagtailimages.exceptions import InvalidFilterSpecError


@any_image_permission_required()
@vary_on_headers('X-Requested-With')
def index(request):
    Image = get_image_model()

    # Get images
    images = images_editable_by_user(request.user).order_by('-created_at')

    # Search
    query_string = None
    if 'q' in request.GET:
        form = SearchForm(request.GET, placeholder=_("Search images"))
        if form.is_valid():
            s = get_search_backend()
            query_string = form.cleaned_data['q']
            images = s.search(query_string, images)
    else:
        form = SearchForm(placeholder=_("Search images"))

    # Pagination
    p = request.GET.get('p', 1)
    paginator = Paginator(images, 20)

    try:
        images = paginator.page(p)
    except PageNotAnInteger:
        images = paginator.page(1)
    except EmptyPage:
        images = paginator.page(paginator.num_pages)

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

            'can_add_image': user_has_image_permission(request.user, 'wagtailimages.add_image'),
            'search_form': form,
            'popular_tags': Image.popular_tags(),
        })


def edit(request, image_id):
    Image = get_image_model()
    ImageForm = get_image_form(Image)

    image = get_object_or_404(Image, id=image_id)

    if not user_can_edit_image(request.user, image):
        raise PermissionDenied

    if request.POST:
        original_file = image.file
        form = ImageForm(request.POST, request.FILES, instance=image, user=request.user)
        if form.is_valid():
            if 'file' in form.changed_data:
                # if providing a new image file, delete the old one and all renditions.
                # NB Doing this via original_file.delete() clears the file field,
                # which definitely isn't what we want...
                original_file.storage.delete(original_file.name)
                image.renditions.all().delete()

                # Set new image file size
                image.file_size = image.file.size

            form.save()

            # Reindex the image to make sure all tags are indexed
            for backend in get_search_backends():
                backend.add(image)

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
            messages.error(request, _("The source image file could not be found. Please change the source or delete the image.").format(image.title), buttons=[
                messages.button(reverse('wagtailimages:delete', args=(image.id,)), _('Delete'))
            ])

    return render(request, "wagtailimages/images/edit.html", {
        'image': image,
        'form': form,
        'url_generator_enabled': url_generator_enabled,
        'filesize': image.get_file_size(),
    })


def url_generator(request, image_id):
    image = get_object_or_404(get_image_model(), id=image_id)

    if not user_can_edit_image(request.user, image):
        raise PermissionDenied

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
    if not user_can_edit_image(request.user, image):
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
        response, image_format = Filter(spec=filter_spec).run(image, HttpResponse())
        response['Content-Type'] = 'image/' + image_format
        return response
    except InvalidFilterSpecError:
        return HttpResponse("Invalid filter spec: " + filter_spec, content_type='text/plain', status=400)


def delete(request, image_id):
    image = get_object_or_404(get_image_model(), id=image_id)

    if not user_can_edit_image(request.user, image):
        raise PermissionDenied

    if request.POST:
        image.delete()
        messages.success(request, _("Image '{0}' deleted.").format(image.title))
        return redirect('wagtailimages:index')

    return render(request, "wagtailimages/images/confirm_delete.html", {
        'image': image,
    })


@image_permission_required('wagtailimages.add_image')
def add(request):
    ImageModel = get_image_model()
    ImageForm = get_image_form(ImageModel)

    if request.POST:
        image = ImageModel(uploaded_by_user=request.user)
        form = ImageForm(request.POST, request.FILES, instance=image, user=request.user)
        if form.is_valid():
            # Set image file size
            image.file_size = image.file.size

            form.save()

            # Reindex the image to make sure all tags are indexed
            for backend in get_search_backends():
                backend.add(image)

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

    # Pagination
    p = request.GET.get('p', 1)
    paginator = Paginator(image.get_usage(), 20)

    try:
        used_by = paginator.page(p)
    except PageNotAnInteger:
        used_by = paginator.page(1)
    except EmptyPage:
        used_by = paginator.page(paginator.num_pages)

    return render(request, "wagtailimages/images/usage.html", {
        'image': image,
        'used_by': used_by
    })
