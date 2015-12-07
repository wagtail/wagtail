from django.shortcuts import get_object_or_404, render
from django.http import Http404

from wagtail.utils.pagination import paginate
from wagtail.wagtailadmin.modal_workflow import render_modal_workflow
from wagtail.wagtailadmin.forms import (
    SearchForm, ExternalLinkChooserForm, ExternalLinkChooserWithLinkTextForm,
    EmailLinkChooserForm, EmailLinkChooserWithLinkTextForm)

from wagtail.wagtailcore.models import Page
from wagtail.wagtailcore.utils import resolve_model_string


def shared_context(request, extra_context={}):
    context = {
        'allow_external_link': request.GET.get('allow_external_link'),
        'allow_email_link': request.GET.get('allow_email_link'),
    }
    context.update(extra_context)
    return context


def page_models_from_string(string):
    page_models = []

    for sub_string in string.split(','):
        page_model = resolve_model_string(sub_string)

        if not issubclass(page_model, Page):
            raise ValueError("Model is not a page")

        page_models.append(page_model)

    return tuple(page_models)


def filter_page_type(queryset, page_models):
    qs = queryset.none()

    for model in page_models:
        qs |= queryset.type(model)

    return qs


def browse(request, parent_page_id=None):
    # Find parent page
    if parent_page_id:
        parent_page = get_object_or_404(Page, id=parent_page_id)
    else:
        parent_page = Page.get_first_root_node()

    # Get children of parent page
    pages = parent_page.get_children()

    # Filter them by page type
    # A missing or empty page_type parameter indicates 'all page types' (i.e. descendants of wagtailcore.page)
    page_type_string = request.GET.get('page_type') or 'wagtailcore.page'
    if page_type_string != 'wagtailcore.page':
        try:
            desired_classes = page_models_from_string(page_type_string)
        except (ValueError, LookupError):
            raise Http404

        # restrict the page listing to just those pages that:
        # - are of the given content type (taking into account class inheritance)
        # - or can be navigated into (i.e. have children)
        choosable_pages = filter_page_type(pages, desired_classes)
        descendable_pages = pages.filter(numchild__gt=0)
        pages = choosable_pages | descendable_pages
    else:
        desired_classes = (Page, )

    can_choose_root = request.GET.get('can_choose_root', False)

    # Parent page can be chosen if it is a instance of desired_classes
    parent_page.can_choose = (
        issubclass(parent_page.specific_class or Page, desired_classes) and
        (can_choose_root or not parent_page.is_root())
    )

    # Pagination
    # We apply pagination first so we don't need to walk the entire list
    # in the block below
    paginator, pages = paginate(request, pages, per_page=25)

    # Annotate each page with can_choose/can_decend flags
    for page in pages:
        if desired_classes == (Page, ):
            page.can_choose = True
        else:
            page.can_choose = issubclass(page.specific_class or Page, desired_classes)

        page.can_descend = page.get_children_count()

    # Render
    return render_modal_workflow(
        request,
        'wagtailadmin/chooser/browse.html', 'wagtailadmin/chooser/browse.js',
        shared_context(request, {
            'parent_page': parent_page,
            'pages': pages,
            'search_form': SearchForm(),
            'page_type_string': page_type_string,
            'page_type_names': [desired_class.get_verbose_name() for desired_class in desired_classes],
            'page_types_restricted': (page_type_string != 'wagtailcore.page')
        })
    )


def search(request, parent_page_id=None):
    # A missing or empty page_type parameter indicates 'all page types' (i.e. descendants of wagtailcore.page)
    page_type_string = request.GET.get('page_type') or 'wagtailcore.page'

    try:
        desired_classes = page_models_from_string(page_type_string)
    except (ValueError, LookupError):
        raise Http404

    search_form = SearchForm(request.GET)
    if search_form.is_valid() and search_form.cleaned_data['q']:
        pages = Page.objects.exclude(
            depth=1  # never include root
        )
        pages = filter_page_type(pages, desired_classes)
        pages = pages.search(search_form.cleaned_data['q'], fields=['title'])
    else:
        pages = Page.objects.none()

    paginator, pages = paginate(request, pages, per_page=25)

    for page in pages:
        page.can_choose = True

    return render(
        request, 'wagtailadmin/chooser/_search_results.html',
        shared_context(request, {
            'searchform': search_form,
            'pages': pages,
            'page_type_string': page_type_string,
        })
    )


def external_link(request):
    prompt_for_link_text = bool(request.GET.get('prompt_for_link_text'))

    if prompt_for_link_text:
        form_class = ExternalLinkChooserWithLinkTextForm
    else:
        form_class = ExternalLinkChooserForm

    if request.POST:
        form = form_class(request.POST)
        if form.is_valid():
            return render_modal_workflow(
                request,
                None, 'wagtailadmin/chooser/external_link_chosen.js',
                {
                    'url': form.cleaned_data['url'],
                    'link_text': form.cleaned_data['link_text'] if prompt_for_link_text else form.cleaned_data['url']
                }
            )
    else:
        form = form_class()

    return render_modal_workflow(
        request,
        'wagtailadmin/chooser/external_link.html', 'wagtailadmin/chooser/external_link.js',
        shared_context(request, {
            'form': form,
        })
    )


def email_link(request):
    prompt_for_link_text = bool(request.GET.get('prompt_for_link_text'))

    if prompt_for_link_text:
        form_class = EmailLinkChooserWithLinkTextForm
    else:
        form_class = EmailLinkChooserForm

    if request.POST:
        form = form_class(request.POST)
        if form.is_valid():
            return render_modal_workflow(
                request,
                None, 'wagtailadmin/chooser/external_link_chosen.js',
                {
                    'url': 'mailto:' + form.cleaned_data['email_address'],
                    'link_text': form.cleaned_data['link_text'] if (
                        prompt_for_link_text and form.cleaned_data['link_text']
                    ) else form.cleaned_data['email_address']
                }
            )
    else:
        form = form_class()

    return render_modal_workflow(
        request,
        'wagtailadmin/chooser/email_link.html', 'wagtailadmin/chooser/email_link.js',
        shared_context(request, {
            'form': form,
        })
    )
