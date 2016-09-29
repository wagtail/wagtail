from __future__ import absolute_import, unicode_literals

import json

from django.http import Http404
from django.shortcuts import get_object_or_404, render

from wagtail.utils.pagination import paginate
from wagtail.wagtailadmin.forms import EmailLinkChooserForm, ExternalLinkChooserForm, SearchForm
from wagtail.wagtailadmin.modal_workflow import render_modal_workflow
from wagtail.wagtailcore.models import Page
from wagtail.wagtailcore.utils import resolve_model_string


def shared_context(request, extra_context=None):
    context = {
        # parent_page ID is passed as a GET parameter on the external_link and email_link views
        # so that it's remembered when browsing from 'Internal link' to another link type
        # and back again. On the 'browse' / 'internal link' view this will be overridden to be
        # sourced from the standard URL path parameter instead.
        'parent_page_id': request.GET.get('parent_page_id'),
        'allow_external_link': request.GET.get('allow_external_link'),
        'allow_email_link': request.GET.get('allow_email_link'),
    }
    if extra_context:
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
            'parent_page_id': parent_page.pk,
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
    initial_data = {
        'url': request.GET.get('link_url', ''),
        'link_text': request.GET.get('link_text', ''),
    }

    if request.method == 'POST':
        form = ExternalLinkChooserForm(request.POST, initial=initial_data)

        if form.is_valid():
            result = {
                'url': form.cleaned_data['url'],
                'title': form.cleaned_data['link_text'].strip() or form.cleaned_data['url'],
                # If the user has explicitly entered / edited something in the link_text field,
                # always use that text. If not, we should favour keeping the existing link/selection
                # text, where applicable.
                # (Normally this will match the link_text passed in the URL here anyhow,
                # but that won't account for non-text content such as images.)
                'prefer_this_title_as_link_text': ('link_text' in form.changed_data),
            }

            return render_modal_workflow(
                request,
                None, 'wagtailadmin/chooser/external_link_chosen.js',
                {
                    'result_json': json.dumps(result),
                }
            )
    else:
        form = ExternalLinkChooserForm(initial=initial_data)

    return render_modal_workflow(
        request,
        'wagtailadmin/chooser/external_link.html', 'wagtailadmin/chooser/external_link.js',
        shared_context(request, {
            'form': form,
        })
    )


def email_link(request):
    initial_data = {
        'link_text': request.GET.get('link_text', ''),
        'email_address': request.GET.get('link_url', ''),
    }

    if request.method == 'POST':
        form = EmailLinkChooserForm(request.POST, initial=initial_data)

        if form.is_valid():
            result = {
                'url': 'mailto:' + form.cleaned_data['email_address'],
                'title': form.cleaned_data['link_text'].strip() or form.cleaned_data['email_address'],
                # If the user has explicitly entered / edited something in the link_text field,
                # always use that text. If not, we should favour keeping the existing link/selection
                # text, where applicable.
                'prefer_this_title_as_link_text': ('link_text' in form.changed_data),
            }
            return render_modal_workflow(
                request,
                None, 'wagtailadmin/chooser/external_link_chosen.js',
                {
                    'result_json': json.dumps(result),
                }
            )
    else:
        form = EmailLinkChooserForm(initial=initial_data)

    return render_modal_workflow(
        request,
        'wagtailadmin/chooser/email_link.html', 'wagtailadmin/chooser/email_link.js',
        shared_context(request, {
            'form': form,
        })
    )
