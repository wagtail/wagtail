from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import ugettext as _

from wagtail.admin.forms.search import SearchForm
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.admin.utils import PermissionPolicyChecker, popular_tags_for_model
from wagtail.core import hooks
from wagtail.core.models import Collection
from wagtail.images import get_image_model
from wagtail.images.formats import get_image_format
from wagtail.images.forms import ImageInsertionForm, get_image_form
from wagtail.images.permissions import permission_policy
from wagtail.search import index as search_index
from wagtail.utils.pagination import paginate

permission_checker = PermissionPolicyChecker(permission_policy)


def get_chooser_js_data():
    """construct context variables needed by the chooser JS"""
    return {
        'step': 'chooser',
        'error_label': _("Server Error"),
        'error_message': _("Report this error to your webmaster with the following information:"),
        'tag_autocomplete_url': reverse('wagtailadmin_tag_autocomplete'),
    }


def get_image_result_data(image):
    """
    helper function: given an image, return the json data to pass back to the
    image chooser panel
    """
    preview_image = image.get_rendition('max-165x165')

    return {
        'id': image.id,
        'edit_link': reverse('wagtailimages:edit', args=(image.id,)),
        'title': image.title,
        'preview': {
            'url': preview_image.url,
            'width': preview_image.width,
            'height': preview_image.height,
        }
    }


def get_chooser_context(request):
    """Helper function to return common template context variables for the main chooser view"""

    collections = Collection.objects.all()
    if len(collections) < 2:
        collections = None
    else:
        collections = Collection.order_for_display(collections)

    return {
        'searchform': SearchForm(),
        'is_searching': False,
        'query_string': None,
        'will_select_format': request.GET.get('select_format'),
        'popular_tags': popular_tags_for_model(get_image_model()),
        'collections': collections,
    }


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

    if (
        'q' in request.GET or 'p' in request.GET or 'tag' in request.GET
        or 'collection_id' in request.GET
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
            q = None

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
        paginator, images = paginate(request, images, per_page=12)

        context = get_chooser_context(request)
        context.update({
            'images': images,
            'uploadform': uploadform,
        })
        return render_modal_workflow(
            request, 'wagtailimages/chooser/chooser.html', None, context,
            json_data=get_chooser_js_data()
        )


def image_chosen(request, image_id):
    image = get_object_or_404(get_image_model(), id=image_id)

    return render_modal_workflow(
        request, None, None,
        None, json_data={'step': 'image_chosen', 'result': get_image_result_data(image)}
    )


@permission_checker.require('add')
def chooser_upload(request):
    Image = get_image_model()
    ImageForm = get_image_form(Image)

    if request.method == 'POST':
        image = Image(uploaded_by_user=request.user)
        form = ImageForm(request.POST, request.FILES, instance=image, user=request.user)

        if form.is_valid():
            # Set image file size
            image.file_size = image.file.size

            # Set image file hash
            image.file.seek(0)
            image._set_file_hash(image.file.read())
            image.file.seek(0)

            form.save()

            # Reindex the image to make sure all tags are indexed
            search_index.insert_or_update_object(image)

            if request.GET.get('select_format'):
                form = ImageInsertionForm(initial={'alt_text': image.default_alt_text})
                return render_modal_workflow(
                    request, 'wagtailimages/chooser/select_format.html', None,
                    {'image': image, 'form': form}, json_data={'step': 'select_format'}
                )
            else:
                # not specifying a format; return the image details now
                return render_modal_workflow(
                    request, None, None,
                    None, json_data={'step': 'image_chosen', 'result': get_image_result_data(image)}
                )
    else:
        form = ImageForm(user=request.user)

    images = Image.objects.order_by('-created_at')

    # allow hooks to modify the queryset
    for hook in hooks.get_hooks('construct_image_chooser_queryset'):
        images = hook(images, request)

    paginator, images = paginate(request, images, per_page=12)

    context = get_chooser_context(request)
    context.update({
        'images': images,
        'uploadform': form,
    })
    return render_modal_workflow(
        request, 'wagtailimages/chooser/chooser.html', None, context,
        json_data=get_chooser_js_data()
    )


def chooser_select_format(request, image_id):
    image = get_object_or_404(get_image_model(), id=image_id)

    if request.method == 'POST':
        form = ImageInsertionForm(request.POST, initial={'alt_text': image.default_alt_text})
        if form.is_valid():

            format = get_image_format(form.cleaned_data['format'])
            preview_image = image.get_rendition(format.filter_spec)

            image_data = {
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
            }

            return render_modal_workflow(
                request, None, None,
                None, json_data={'step': 'image_chosen', 'result': image_data}
            )
    else:
        initial = {'alt_text': image.default_alt_text}
        initial.update(request.GET.dict())
        form = ImageInsertionForm(initial=initial)

    return render_modal_workflow(
        request, 'wagtailimages/chooser/select_format.html', None,
        {'image': image, 'form': form}, json_data={'step': 'select_format'}
    )
