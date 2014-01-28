from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import permission_required, login_required
from django.core.exceptions import PermissionDenied

from wagtail.wagtailimages.models import get_image_model
from wagtail.wagtailimages.forms import get_image_form
from wagtail.wagtailadmin.forms import SearchForm

@permission_required('wagtailimages.add_image')
def index(request):
    Image = get_image_model()

    q = None
    p = request.GET.get("p", 1)
    is_searching = False

    if 'q' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            q = form.cleaned_data['q']

            is_searching = True
            if not request.user.has_perm('wagtailimages.change_image'):
                # restrict to the user's own images
                images = Image.search(q, results_per_page=20, page=p, filters={'uploaded_by_user_id': request.user.id})
            else:
                images = Image.search(q, results_per_page=20, page=p)
        else:
            images = Image.objects.order_by('-created_at')
            if not request.user.has_perm('wagtailimages.change_image'):
                # restrict to the user's own images
                images = images.filter(uploaded_by_user=request.user)
    else:
        images = Image.objects.order_by('-created_at')
        if not request.user.has_perm('wagtailimages.change_image'):
            # restrict to the user's own images
            images = images.filter(uploaded_by_user=request.user)
        form = SearchForm()

    if not is_searching:
        paginator = Paginator(images, 20)

        try:
            images = paginator.page(p)
        except PageNotAnInteger:
            images = paginator.page(1)
        except EmptyPage:
            images = paginator.page(paginator.num_pages)

    if request.is_ajax():
        return render(request, "wagtailimages/images/results.html", {
            'images': images,
            'is_searching': is_searching,
            'search_query': q,
        })
    else:
        return render(request, "wagtailimages/images/index.html", {
            'form': form,
            'images': images,
            'is_searching': is_searching,
            'popular_tags': Image.popular_tags(),
            'search_query': q,
        })


@login_required  # more specific permission tests are applied within the view
def edit(request, image_id):
    Image = get_image_model()
    ImageForm = get_image_form()

    image = get_object_or_404(Image, id=image_id)

    if not image.is_editable_by_user(request.user):
        raise PermissionDenied

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
            messages.success(request, "Image '%s' updated." % image.title)
            return redirect('wagtailimages_index')
        else:
            messages.error(request, "The image could not be saved due to errors.")
    else:
        form = ImageForm(instance=image)

    return render(request, "wagtailimages/images/edit.html", {
        'image': image,
        'form': form,
    })


@login_required  # more specific permission tests are applied within the view
def delete(request, image_id):
    image = get_object_or_404(get_image_model(), id=image_id)

    if not image.is_editable_by_user(request.user):
        raise PermissionDenied

    if request.POST:
        image.delete()
        messages.success(request, "Image '%s' deleted." % image.title)
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
            messages.success(request, "Image '%s' added." % image.title)
            return redirect('wagtailimages_index')
        else:
            messages.error(request, "The image could not be created due to errors.")
    else:
        form = ImageForm()

    return render(request, "wagtailimages/images/add.html", {
        'form': form,
    })


@permission_required('wagtailimages.add_image')
def search(request):
    Image = get_image_model()
    images = []
    q = None
    is_searching = False
    
    if 'q' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            q = form.cleaned_data['q']

            # page number
            p = request.GET.get("p", 1)
            is_searching = True
            images = Image.search(q, results_per_page=20, page=p)
    else:
        form = SearchForm()

    if request.is_ajax():
        return render(request, "wagtailimages/images/results.html", {
            'images': images,
            'is_searching': is_searching,
            'search_query': q,
        })
    else:
        return render(request, "wagtailimages/images/index.html", {
            'form': form,
            'images': images,
            'is_searching': is_searching,
            'popular_tags': Image.popular_tags(),
            'search_query': q,
        })
