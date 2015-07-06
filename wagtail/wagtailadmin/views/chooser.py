from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, render
from django.http import Http404
from django.utils.http import urlencode

from wagtail.wagtailadmin.modal_workflow import render_modal_workflow
from wagtail.wagtailadmin.forms import SearchForm, ExternalLinkChooserForm, ExternalLinkChooserWithLinkTextForm, EmailLinkChooserForm, EmailLinkChooserWithLinkTextForm

from wagtail.wagtailcore.models import Page


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
    ITEMS_PER_PAGE = 25

    page_type = request.GET.get('page_type') or 'wagtailcore.page'
    content_type_app_name, content_type_model_name = page_type.split('.')

    try:
        content_type = ContentType.objects.get_by_natural_key(content_type_app_name, content_type_model_name)
    except ContentType.DoesNotExist:
        raise Http404
    desired_class = content_type.model_class()

    if parent_page_id:
        parent_page = get_object_or_404(Page, id=parent_page_id)
    else:
        parent_page = Page.get_first_root_node()

    parent_page.can_choose = issubclass(parent_page.specific_class, desired_class)
    search_form = SearchForm()
    pages = parent_page.get_children()

    if desired_class == Page:
        # apply pagination first, since we know that the page listing won't
        # have to be filtered, and that saves us walking the entire list
        p = request.GET.get('p', 1)
        paginator = Paginator(pages, ITEMS_PER_PAGE)
        try:
            pages = paginator.page(p)
        except PageNotAnInteger:
            pages = paginator.page(1)
        except EmptyPage:
            pages = paginator.page(paginator.num_pages)

        for page in pages:
            page.can_choose = True
            page.can_descend = page.get_children_count()

    else:
        # restrict the page listing to just those pages that:
        # - are of the given content type (taking into account class inheritance)
        # - or can be navigated into (i.e. have children)

        shown_pages = []
        for page in pages:
            page.can_choose = issubclass(page.specific_class or Page, desired_class)
            page.can_descend = page.get_children_count()

            if page.can_choose or page.can_descend:
                shown_pages.append(page)

        # Apply pagination
        p = request.GET.get('p', 1)
        paginator = Paginator(shown_pages, ITEMS_PER_PAGE)
        try:
            pages = paginator.page(p)
        except PageNotAnInteger:
            pages = paginator.page(1)
        except EmptyPage:
            pages = paginator.page(paginator.num_pages)

    return render_modal_workflow(
        request,
        'wagtailadmin/chooser/browse.html', 'wagtailadmin/chooser/browse.js',
        shared_context(request, {
            'parent_page': parent_page,
            'pages': pages,
            'search_form': search_form,
            'page_type_string': page_type,
            'page_type_name': desired_class.get_verbose_name(),
            'page_types_restricted': (page_type != 'wagtailcore.page')
        })
    )


def search(request, parent_page_id=None):
    page_type = request.GET.get('page_type') or 'wagtailcore.page'
    content_type_app_name, content_type_model_name = page_type.split('.')

    try:
        content_type = ContentType.objects.get_by_natural_key(content_type_app_name, content_type_model_name)
    except ContentType.DoesNotExist:
        raise Http404
    desired_class = content_type.model_class()

    search_form = SearchForm(request.GET)
    if search_form.is_valid() and search_form.cleaned_data['q']:
        pages = desired_class.objects.exclude(
            depth=1  # never include root
        ).search(search_form.cleaned_data['q'], fields=['title'])[:10]
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
