from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, render
from django.http import Http404
from django.utils.http import urlencode

from wagtail.wagtailadmin.modal_workflow import render_modal_workflow
from wagtail.wagtailadmin.forms import SearchForm, ExternalLinkChooserForm, ExternalLinkChooserWithLinkTextForm, EmailLinkChooserForm, EmailLinkChooserWithLinkTextForm

from wagtail.wagtailcore.models import Page
from wagtail.wagtailcore.utils import resolve_model_string


def get_querystring(request):
    return urlencode({
        'page_type': request.GET.get('page_type', ''),
        'allow_external_link': request.GET.get('allow_external_link', ''),
        'allow_email_link': request.GET.get('allow_email_link', ''),
        'prompt_for_link_text': request.GET.get('prompt_for_link_text', ''),
    })


def shared_context(request, extra_context={}):
    context = {
        'allow_external_link': request.GET.get('allow_external_link'),
        'allow_email_link': request.GET.get('allow_email_link'),
        'querystring': get_querystring(request),
    }
    context.update(extra_context)
    return context


def browse(request, parent_page_id=None):
    # Find parent page
    if parent_page_id:
        parent_page = get_object_or_404(Page, id=parent_page_id)
    else:
        parent_page = Page.get_first_root_node()

    # Get children of parent page
    pages = parent_page.get_children()

    # Filter them by page type
    page_type_string = request.GET.get('page_type', 'wagtailcore.page')
    if page_type_string != 'wagtailcore.page':
        try:
            desired_class = resolve_model_string(page_type_string)
        except (ValueError, LookupError):
            raise Http404

        if not issubclass(desired_class, Page):
            raise Http404

        # restrict the page listing to just those pages that:
        # - are of the given content type (taking into account class inheritance)
        # - or can be navigated into (i.e. have children)
        choosable_pages = pages.type(desired_class)
        descendable_pages = pages.filter(numchild__gt=0)
        pages = choosable_pages | descendable_pages
    else:
        desired_class = Page

    # Parent page can be chosen if it is a instance of desired_class
    parent_page.can_choose = issubclass(parent_page.specific_class, desired_class)

    # Pagination
    # We apply pagination first so we don't need to walk the entire list
    # in the block below
    p = request.GET.get('p', 1)
    paginator = Paginator(pages, 25)
    try:
        pages = paginator.page(p)
    except PageNotAnInteger:
        pages = paginator.page(1)
    except EmptyPage:
        pages = paginator.page(paginator.num_pages)

    # Annotate each page with can_choose/can_decend flags
    for page in pages:
        if desired_class == Page:
            page.can_choose = True
        else:
            page.can_choose = issubclass(page.specific_class, desired_class)

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
            'page_type_name': desired_class.get_verbose_name(),
            'page_types_restricted': (page_type_string != 'wagtailcore.page')
        })
    )


def search(request, parent_page_id=None):
    page_type_string = request.GET.get('page_type', 'wagtailcore.page')

    try:
        desired_class = resolve_model_string(page_type_string)
    except (ValueError, LookupError):
        raise Http404

    if not issubclass(desired_class, Page):
        raise Http404

    search_form = SearchForm(request.GET)
    if search_form.is_valid() and search_form.cleaned_data['q']:
        pages = desired_class.objects.exclude(
            depth=1  # never include root
        ).filter(title__icontains=search_form.cleaned_data['q'])[:10]
    else:
        pages = desired_class.objects.none()

    shown_pages = []
    for page in pages:
        page.can_choose = True
        shown_pages.append(page)

    return render(
        request, 'wagtailadmin/chooser/_search_results.html',
        shared_context(request, {
            'searchform': search_form,
            'pages': shown_pages,
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
                    'link_text': form.cleaned_data['link_text'] if (prompt_for_link_text and form.cleaned_data['link_text']) else form.cleaned_data['email_address']
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
