from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, render
from django.http import Http404
from django.utils.http import urlencode

from wagtail.wagtailadmin.modal_workflow import render_modal_workflow
from wagtail.wagtailadmin.forms import SearchForm, ExternalLinkChooserForm, ExternalLinkChooserWithLinkTextForm, EmailLinkChooserForm, EmailLinkChooserWithLinkTextForm

from wagtail.wagtailcore.utils import resolve_model_string
from wagtail.wagtailcore.models import Page


def get_querystring(request):
    return urlencode({
        'page_types': request.GET.get('page_types', ''),
        'allow_external_link': request.GET.get('allow_external_link', ''),
        'allow_email_link': request.GET.get('allow_email_link', ''),
        'prompt_for_link_text': request.GET.get('prompt_for_link_text', ''),
    })


def browse(request, parent_page_id=None):
    ITEMS_PER_PAGE = 25

    page_types = request.GET.get('page_types', 'wagtailcore.page').split(',')

    desired_classes = []
    for page_type in page_types:
        try:
            content_type = resolve_model_string(page_type)
        except LookupError:
            raise Http404

        desired_classes.append(content_type)

    if parent_page_id:
        parent_page = get_object_or_404(Page, id=parent_page_id)
    else:
        parent_page = Page.get_first_root_node()

    parent_page.can_choose = issubclass(parent_page.specific_class, tuple(desired_classes))
    search_form = SearchForm()
    pages = parent_page.get_children()

    if desired_classes == [Page]:
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
            page.can_choose = issubclass(page.specific_class or Page, tuple(desired_classes))
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

    return render_modal_workflow(request, 'wagtailadmin/chooser/browse.html', 'wagtailadmin/chooser/browse.js', {
        'allow_external_link': request.GET.get('allow_external_link'),
        'allow_email_link': request.GET.get('allow_email_link'),
        'querystring': get_querystring(request),
        'parent_page': parent_page,
        'pages': pages,
        'search_form': search_form,
        'page_type_string': ','.join(page_types),
        'page_type_names': [desired_class.get_verbose_name() for desired_class in desired_classes],
        'page_types_restricted': (page_type != 'wagtailcore.page')
    })


def search(request, parent_page_id=None):
    page_types = request.GET.get('page_types')
    content_types = []

    # Convert page_types string into list of ContentType objects
    if page_types:
        try:
            content_types = ContentType.objects.get_for_models(*[
                resolve_model_string(page_type) for page_type in page_types.split(',')])
        except LookupError:
            raise Http404

    search_form = SearchForm(request.GET)
    if search_form.is_valid() and search_form.cleaned_data['q']:
        pages = Page.objects.exclude(
            depth=1  # never include root
        )

        # Restrict content types
        if content_types:
            pages = pages.filter(content_type__in=content_types)

        # Do search
        pages = pages.filter(title__icontains=search_form.cleaned_data['q'])

        # Truncate results
        pages = pages[:10]
    else:
        pages = Page.objects.none()

    shown_pages = []
    for page in pages:
        page.can_choose = True
        shown_pages.append(page)

    return render(request, 'wagtailadmin/chooser/_search_results.html', {
        'querystring': get_querystring(request),
        'searchform': search_form,
        'pages': shown_pages,
    })


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
        {
            'querystring': get_querystring(request),
            'allow_email_link': request.GET.get('allow_email_link'),
            'form': form,
        }
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
        {
            'querystring': get_querystring(request),
            'allow_external_link': request.GET.get('allow_external_link'),
            'form': form,
        }
    )
