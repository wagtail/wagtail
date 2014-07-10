from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext as _
from django.views.decorators.vary import vary_on_headers
from django.core.urlresolvers import reverse

from wagtail.wagtailadmin.forms import SearchForm

from wagtail.wagtailimages.models import get_image_model
from wagtail.wagtailimages.forms import get_image_form


@permission_required('wagtailimages.add_image')
@vary_on_headers('X-Requested-With')
def index(request):
    Image = get_image_model()

    # Get images
    images = Image.objects.order_by('-created_at')

    # Permissions
    if not request.user.has_perm('wagtailimages.change_image'):
        # restrict to the user's own images
        images = images.filter(uploaded_by_user=request.user)

    # Search
    query_string = None
    if 'q' in request.GET:
        form = SearchForm(request.GET, placeholder=_("Search images"))
        if form.is_valid():
            query_string = form.cleaned_data['q']

            is_searching = True
            if not request.user.has_perm('wagtailimages.change_image'):
                # restrict to the user's own images
                images = Image.search(query_string, filters={'uploaded_by_user_id': request.user.id})
            else:
                images = Image.search(query_string)
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

            'search_form': form,
            'popular_tags': Image.popular_tags(),
        })


@permission_required('wagtailadmin.access_admin')  # more specific permission tests are applied within the view
def edit(request, image_id):
    Image = get_image_model()
    ImageForm = get_image_form()

    image = get_object_or_404(Image, id=image_id)

    if not image.is_editable_by_user(request.user):
        raise PermissionDenied

    usage_url = reverse('wagtailimages_image_usage',
                        args=(image.id,))

    if request.POST:
        original_file = image.file
        form = ImageForm(request.POST, request.FILES, instance=image)
        if form.is_valid():
            if 'file' in form.changed_data:
                # if providing a new image file, delete the old one and all renditions.
                # NB Doing this via original_file.delete() clears the file field,
                # which definitely isn't what we want...
                original_file.storage.delete(original_file.name)
                image.renditions.all().delete()
            form.save()
            messages.success(request, _("Image '{0}' updated.").format(image.title))
            return redirect('wagtailimages_index')
        else:
            messages.error(request, _("The image could not be saved due to errors."))
    else:
        form = ImageForm(instance=image)

    return render(request, "wagtailimages/images/edit.html", {
        'image': image,
        'form': form,
        'usage_url': usage_url
    })


@permission_required('wagtailadmin.access_admin')  # more specific permission tests are applied within the view
def delete(request, image_id):
    image = get_object_or_404(get_image_model(), id=image_id)

    if not image.is_editable_by_user(request.user):
        raise PermissionDenied

    if request.POST:
        image.delete()
        messages.success(request, _("Image '{0}' deleted.").format(image.title))
        return redirect('wagtailimages_index')

    return render(request, "wagtailimages/images/confirm_delete.html", {
        'image': image,
    })


@permission_required('wagtailimages.add_image')
def add(request):
    ImageForm = get_image_form()
    ImageModel = get_image_model()

    if request.POST:
        image = ImageModel(uploaded_by_user=request.user)
        form = ImageForm(request.POST, request.FILES, instance=image)
        if form.is_valid():
            form.save()
            messages.success(request, _("Image '{0}' added.").format(image.title))
            return redirect('wagtailimages_index')
        else:
            messages.error(request, _("The image could not be created due to errors."))
    else:
        form = ImageForm()

    return render(request, "wagtailimages/images/add.html", {
        'form': form,
    })


@permission_required('wagtailadmin.access_admin')
def usage(request, image_id):
    image = get_object_or_404(get_image_model(), id=image_id)

    return render(request, "wagtailimages/images/usage.html", {
        'image': image,
    })
