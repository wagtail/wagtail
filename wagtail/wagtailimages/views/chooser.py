from __future__ import absolute_import, unicode_literals

import json

from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render

from wagtail.utils.pagination import paginate
from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailadmin.modal_workflow import render_modal_workflow
from wagtail.wagtailadmin.utils import PermissionPolicyChecker, popular_tags_for_model
from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.models import Collection
from wagtail.wagtailimages import get_image_model
from wagtail.wagtailimages.formats import get_image_format
from wagtail.wagtailimages.forms import ImageInsertionForm, get_image_form
from wagtail.wagtailimages.permissions import permission_policy
from wagtail.wagtailsearch import index as search_index

permission_checker = PermissionPolicyChecker(permission_policy)


def get_image_json(image):
    """
    helper function: given an image, return the json to pass back to the
    image chooser panel
    """
    preview_image = image.get_rendition('max-165x165')

    return json.dumps({
        'id': image.id,
        'edit_link': reverse('wagtailimages:edit', args=(image.id,)),
        'title': image.title,
        'preview': {
            'url': preview_image.url,
            'width': preview_image.width,
            'height': preview_image.height,
        }
    })


def chooser(request):
    Image = get_image_model()

    if permission_policy.user_has_permission(request.user, 'add'):
        ImageForm = get_image_form(Image)
        uploadform = ImageForm(user=request.user)
    else:
        uploadform = None

    images = Image.objects.order_by('-created_at')

    # allow hooks to modify the queryset
    for hook in hooks.get_hooks('construct_image_chooser_queryset'):
        images = hook(images, request)

    q = None
    if (
        'q' in request.GET or 'p' in request.GET or 'tag' in request.GET or
        'collection_id' in request.GET
    ):
        # this request is triggered from search, pagination or 'popular tags';
        # we will just render the results.html fragment
        collection_id = request.GET.get('collection_id')
        if collection_id:
            images = images.filter(collection=collection_id)

        searchform = SearchForm(request.GET)
        if searchform.is_valid():
            q = searchform.cleaned_data['q']

            images = images.search(q)
            is_searching = True
        else:
            is_searching = False

            tag_name = request.GET.get('tag')
            if tag_name:
                images = images.filter(tags__name=tag_name)

        # Pagination
        paginator, images = paginate(request, images, per_page=12)

        return render(request, "wagtailimages/chooser/results.html", {
            'images': images,
            'is_searching': is_searching,
            'query_string': q,
            'will_select_format': request.GET.get('select_format')
        })
    else:
        searchform = SearchForm()

        collections = Collection.objects.all()
        if len(collections) < 2:
            collections = None

        paginator, images = paginate(request, images, per_page=12)

        return render_modal_workflow(request, 'wagtailimages/chooser/chooser.html', 'wagtailimages/chooser/chooser.js', {
            'images': images,
            'uploadform': uploadform,
            'searchform': searchform,
            'is_searching': False,
            'query_string': q,
            'will_select_format': request.GET.get('select_format'),
            'popular_tags': popular_tags_for_model(Image),
            'collections': collections,
        })


def image_chosen(request, image_id):
    image = get_object_or_404(get_image_model(), id=image_id)

    return render_modal_workflow(
        request, None, 'wagtailimages/chooser/image_chosen.js',
        {'image_json': get_image_json(image)}
    )


@permission_checker.require('add')
def chooser_upload(request):
    Image = get_image_model()
    ImageForm = get_image_form(Image)

    searchform = SearchForm()

    if request.method == 'POST':
        image = Image(uploaded_by_user=request.user)
        form = ImageForm(request.POST, request.FILES, instance=image, user=request.user)

        if form.is_valid():
            form.save()

            # Reindex the image to make sure all tags are indexed
            search_index.insert_or_update_object(image)

            if request.GET.get('select_format'):
                form = ImageInsertionForm(initial={'alt_text': image.default_alt_text})
                return render_modal_workflow(
                    request, 'wagtailimages/chooser/select_format.html', 'wagtailimages/chooser/select_format.js',
                    {'image': image, 'form': form}
                )
            else:
                # not specifying a format; return the image details now
                return render_modal_workflow(
                    request, None, 'wagtailimages/chooser/image_chosen.js',
                    {'image_json': get_image_json(image)}
                )
    else:
        form = ImageForm(user=request.user)

    images = Image.objects.order_by('-created_at')
    paginator, images = paginate(request, images, per_page=12)

    return render_modal_workflow(
        request, 'wagtailimages/chooser/chooser.html', 'wagtailimages/chooser/chooser.js',
        {'images': images, 'uploadform': form, 'searchform': searchform}
    )


def chooser_select_format(request, image_id):
    image = get_object_or_404(get_image_model(), id=image_id)

    if request.method == 'POST':
        form = ImageInsertionForm(request.POST, initial={'alt_text': image.default_alt_text})
        if form.is_valid():

            format = get_image_format(form.cleaned_data['format'])
            preview_image = image.get_rendition(format.filter_spec)

            image_json = json.dumps({
                'id': image.id,
                'title': image.title,
                'format': format.name,
                'alt': form.cleaned_data['alt_text'],
                'class': format.classnames,
                'edit_link': reverse('wagtailimages:edit', args=(image.id,)),
                'preview': {
                    'url': preview_image.url,
                    'width': preview_image.width,
                    'height': preview_image.height,
                },
                'html': format.image_to_editor_html(image, form.cleaned_data['alt_text']),
            })

            return render_modal_workflow(
                request, None, 'wagtailimages/chooser/image_chosen.js',
                {'image_json': image_json}
            )
    else:
        initial = {'alt_text': image.default_alt_text}
        initial.update(request.GET.dict())
        form = ImageInsertionForm(initial=initial)

    return render_modal_workflow(
        request, 'wagtailimages/chooser/select_format.html', 'wagtailimages/chooser/select_format.js',
        {'image': image, 'form': form}
    )
