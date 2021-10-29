import re

from django.conf import settings
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls.base import reverse

from wagtail.admin.forms.choosers import (
    AnchorLinkChooserForm, EmailLinkChooserForm, ExternalLinkChooserForm, PhoneLinkChooserForm)
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.core import hooks
from wagtail.core.models import Page, Site, UserPagePermissionsProxy
from wagtail.core.utils import resolve_model_string


def shared_context(request, extra_context=None):
    context = {
        # parent_page ID is passed as a GET parameter on the external_link, anchor_link and mail_link views
        # so that it's remembered when browsing from 'Internal link' to another link type
        # and back again. On the 'browse' / 'internal link' view this will be overridden to be
        # sourced from the standard URL path parameter instead.
        'parent_page_id': request.GET.get('parent_page_id'),
        'allow_external_link': request.GET.get('allow_external_link'),
        'allow_email_link': request.GET.get('allow_email_link'),
        'allow_phone_link': request.GET.get('allow_phone_link'),
        'allow_anchor_link': request.GET.get('allow_anchor_link'),
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


def can_choose_page(page, permission_proxy, desired_classes, can_choose_root=True, user_perm=None, target_pages=None, match_subclass=True):
    """Returns boolean indicating of the user can choose page.
    will check if the root page can be selected and if user permissions
    should be checked.
    """

    if not target_pages:
        target_pages = []

    if not match_subclass and page.specific_class not in desired_classes:
        return False
    elif match_subclass and not issubclass(page.specific_class or Page, desired_classes) and not desired_classes == (Page, ):
        return False
    elif not can_choose_root and page.is_root():
        return False

    if user_perm == 'move_to':
        pages_to_move = target_pages

        for page_to_move in pages_to_move:
            if page == page_to_move or page.is_descendant_of(page_to_move):
                return False
    if user_perm == 'copy_to':
        return permission_proxy.for_page(page).can_add_subpage()

    return True


def browse(request, parent_page_id=None):
    # A missing or empty page_type parameter indicates 'all page types'
    # (i.e. descendants of wagtailcore.page)
    page_type_string = request.GET.get('page_type') or 'wagtailcore.page'
    user_perm = request.GET.get('user_perms', False)

    try:
        desired_classes = page_models_from_string(page_type_string)
    except (ValueError, LookupError):
        raise Http404

    # Find parent page
    if parent_page_id:
        parent_page = get_object_or_404(Page, id=parent_page_id)
    elif desired_classes == (Page,):
        # Just use the root page
        parent_page = Page.get_first_root_node()
    else:
        # Find the highest common ancestor for the specific classes passed in
        # In many cases, such as selecting an EventPage under an EventIndex,
        # this will help the administrator find their page quicker.
        all_desired_pages = Page.objects.all().type(*desired_classes)
        parent_page = all_desired_pages.first_common_ancestor()

    parent_page = parent_page.specific

    # Get children of parent page (without streamfields)
    pages = parent_page.get_children().defer_streamfields().specific()

    # allow hooks to modify the queryset
    for hook in hooks.get_hooks('construct_page_chooser_queryset'):
        pages = hook(pages, request)

    # Filter them by page type
    if desired_classes != (Page,):
        # restrict the page listing to just those pages that:
        # - are of the given content type (taking into account class inheritance)
        # - or can be navigated into (i.e. have children)
        choosable_pages = pages.type(*desired_classes)
        descendable_pages = pages.filter(numchild__gt=0)
        pages = choosable_pages | descendable_pages

    can_choose_root = request.GET.get('can_choose_root', False)
    target_pages = Page.objects.filter(pk__in=[int(pk) for pk in request.GET.get('target_pages', '').split(',') if pk])

    match_subclass = request.GET.get('match_subclass', True)

    # Do permission lookups for this user now, instead of for every page.
    permission_proxy = UserPagePermissionsProxy(request.user)

    # Parent page can be chosen if it is a instance of desired_classes
    parent_page.can_choose = can_choose_page(
        parent_page, permission_proxy, desired_classes, can_choose_root, user_perm, target_pages=target_pages, match_subclass=match_subclass)

    # Pagination
    # We apply pagination first so we don't need to walk the entire list
    # in the block below
    paginator = Paginator(pages, per_page=25)
    pages = paginator.get_page(request.GET.get('p'))

    # Annotate each page with can_choose/can_decend flags
    for page in pages:
        page.can_choose = can_choose_page(page, permission_proxy, desired_classes, can_choose_root, user_perm, target_pages=target_pages, match_subclass=match_subclass)
        page.can_descend = page.get_children_count()

    # Render
    context = shared_context(request, {
        'parent_page': parent_page,
        'parent_page_id': parent_page.pk,
        'pages': pages,
        'search_form': SearchForm(),
        'page_type_string': page_type_string,
        'page_type_names': [desired_class.get_verbose_name() for desired_class in desired_classes],
        'page_types_restricted': (page_type_string != 'wagtailcore.page')
    })

    return render_modal_workflow(
        request,
        'wagtailadmin/chooser/browse.html', None,
        context,
        json_data={'step': 'browse', 'parent_page_id': context['parent_page_id']},
    )


def search(request, parent_page_id=None):
    # A missing or empty page_type parameter indicates 'all page types' (i.e. descendants of wagtailcore.page)
    page_type_string = request.GET.get('page_type') or 'wagtailcore.page'

    try:
        desired_classes = page_models_from_string(page_type_string)
    except (ValueError, LookupError):
        raise Http404

    pages = Page.objects.all()
    # allow hooks to modify the queryset
    for hook in hooks.get_hooks('construct_page_chooser_queryset'):
        pages = hook(pages, request)

    search_form = SearchForm(request.GET)
    if search_form.is_valid() and search_form.cleaned_data['q']:
        pages = pages.exclude(
            depth=1  # never include root
        )
        pages = pages.type(*desired_classes)
        pages = pages.specific()
        pages = pages.search(search_form.cleaned_data['q'])
    else:
        pages = pages.none()

    paginator = Paginator(pages, per_page=25)
    pages = paginator.get_page(request.GET.get('p'))

    for page in pages:
        page.can_choose = True

    return TemplateResponse(
        request, 'wagtailadmin/chooser/_search_results.html',
        shared_context(request, {
            'searchform': search_form,
            'pages': pages,
            'page_type_string': page_type_string,
        })
    )


LINK_CONVERSION_ALL = 'all'
LINK_CONVERSION_EXACT = 'exact'
LINK_CONVERSION_CONFIRM = 'confirm'


def external_link(request):
    initial_data = {
        'url': request.GET.get('link_url', ''),
        'link_text': request.GET.get('link_text', ''),
    }

    if request.method == 'POST':
        form = ExternalLinkChooserForm(request.POST, initial=initial_data, prefix='external-link-chooser')

        if form.is_valid():
            submitted_url = form.cleaned_data['url']
            result = {
                'url': submitted_url,
                'title': form.cleaned_data['link_text'].strip() or form.cleaned_data['url'],
                # If the user has explicitly entered / edited something in the link_text field,
                # always use that text. If not, we should favour keeping the existing link/selection
                # text, where applicable.
                # (Normally this will match the link_text passed in the URL here anyhow,
                # but that won't account for non-text content such as images.)
                'prefer_this_title_as_link_text': ('link_text' in form.changed_data),
            }

            link_conversion = getattr(settings, 'WAGTAILADMIN_EXTERNAL_LINK_CONVERSION', LINK_CONVERSION_ALL).lower()

            if link_conversion not in [LINK_CONVERSION_ALL, LINK_CONVERSION_EXACT, LINK_CONVERSION_CONFIRM]:
                # We should not attempt to convert external urls to page links
                return render_modal_workflow(
                    request, None, None,
                    None, json_data={'step': 'external_link_chosen', 'result': result}
                )

            # Next, we should check if the url matches an internal page
            # Strip the url of its query/fragment link parameters - these won't match a page
            url_without_query = re.split(r"\?|#", submitted_url)[0]

            # Start by finding any sites the url could potentially match
            sites = getattr(request, '_wagtail_cached_site_root_paths', None)
            if sites is None:
                sites = Site.get_site_root_paths()

            match_relative_paths = submitted_url.startswith('/') and len(sites) == 1
            # We should only match relative urls if there's only a single site
            # Otherwise this could get very annoying accidentally matching coincidentally
            # named pages on different sites

            if match_relative_paths:
                possible_sites = [
                    (pk, url_without_query)
                    for pk, path, url, language_code
                    in sites
                ]
            else:
                possible_sites = [
                    (pk, url_without_query[len(url):])
                    for pk, path, url, language_code
                    in sites
                    if submitted_url.startswith(url)
                ]

            # Loop over possible sites to identify a page match
            for pk, url in possible_sites:
                try:
                    route = Site.objects.get(pk=pk).root_page.specific.route(
                        request,
                        [component for component in url.split('/') if component]
                    )

                    matched_page = route.page.specific

                    internal_data = {
                        'id': matched_page.pk,
                        'parentId': matched_page.get_parent().pk,
                        'adminTitle': matched_page.draft_title,
                        'editUrl': reverse('wagtailadmin_pages:edit', args=(matched_page.pk,)),
                        'url': matched_page.url
                    }

                    # Let's check what this page's normal url would be
                    normal_url = matched_page.get_url_parts(request=request)[-1] if match_relative_paths else matched_page.get_full_url(request=request)

                    # If that's what the user provided, great. Let's just convert the external
                    # url to an internal link automatically unless we're set up tp manually check
                    # all conversions
                    if normal_url == submitted_url and link_conversion != LINK_CONVERSION_CONFIRM:
                        return render_modal_workflow(
                            request,
                            None,
                            None,
                            None,
                            json_data={'step': 'external_link_chosen', 'result': internal_data}
                        )
                    # If not, they might lose query parameters or routable page information

                    if link_conversion == LINK_CONVERSION_EXACT:
                        # We should only convert exact matches
                        continue

                    # Let's confirm the conversion with them explicitly
                    else:
                        return render_modal_workflow(
                            request,
                            'wagtailadmin/chooser/confirm_external_to_internal.html',
                            None,
                            {
                                'submitted_url': submitted_url,
                                'internal_url': normal_url,
                                'page': matched_page.draft_title,
                            },
                            json_data={'step': 'confirm_external_to_internal', 'external': result, 'internal': internal_data}
                        )

                except Http404:
                    continue

            # Otherwise, with no internal matches, fall back to an external url
            return render_modal_workflow(
                request, None, None,
                None, json_data={'step': 'external_link_chosen', 'result': result}
            )
    else:
        form = ExternalLinkChooserForm(initial=initial_data, prefix='external-link-chooser')

    return render_modal_workflow(
        request,
        'wagtailadmin/chooser/external_link.html', None,
        shared_context(request, {
            'form': form,
        }), json_data={'step': 'external_link'}
    )


def anchor_link(request):
    initial_data = {
        'link_text': request.GET.get('link_text', ''),
        'url': request.GET.get('link_url', ''),
    }

    if request.method == 'POST':
        form = AnchorLinkChooserForm(request.POST, initial=initial_data, prefix='anchor-link-chooser')

        if form.is_valid():
            result = {
                'url': '#' + form.cleaned_data['url'],
                'title': form.cleaned_data['link_text'].strip() or form.cleaned_data['url'],
                'prefer_this_title_as_link_text': ('link_text' in form.changed_data),
            }
            return render_modal_workflow(
                request, None, None,
                None, json_data={'step': 'external_link_chosen', 'result': result}
            )
    else:
        form = AnchorLinkChooserForm(initial=initial_data, prefix='anchor-link-chooser')

    return render_modal_workflow(
        request,
        'wagtailadmin/chooser/anchor_link.html', None,
        shared_context(request, {
            'form': form,
        }), json_data={'step': 'anchor_link'}
    )


def email_link(request):
    initial_data = {
        'link_text': request.GET.get('link_text', ''),
        'email_address': request.GET.get('link_url', ''),
    }

    if request.method == 'POST':
        form = EmailLinkChooserForm(request.POST, initial=initial_data, prefix='email-link-chooser')

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
                request, None, None,
                None, json_data={'step': 'external_link_chosen', 'result': result}
            )
    else:
        form = EmailLinkChooserForm(initial=initial_data, prefix='email-link-chooser')

    return render_modal_workflow(
        request,
        'wagtailadmin/chooser/email_link.html', None,
        shared_context(request, {
            'form': form,
        }), json_data={'step': 'email_link'}
    )


def phone_link(request):
    initial_data = {
        'link_text': request.GET.get('link_text', ''),
        'phone_number': request.GET.get('link_url', ''),
    }

    if request.method == 'POST':
        form = PhoneLinkChooserForm(request.POST, initial=initial_data, prefix='phone-link-chooser')

        if form.is_valid():
            result = {
                'url': 'tel:' + form.cleaned_data['phone_number'],
                'title': form.cleaned_data['link_text'].strip() or form.cleaned_data['phone_number'],
                # If the user has explicitly entered / edited something in the link_text field,
                # always use that text. If not, we should favour keeping the existing link/selection
                # text, where applicable.
                'prefer_this_title_as_link_text': ('link_text' in form.changed_data),
            }
            return render_modal_workflow(
                request, None, None,
                None, json_data={'step': 'external_link_chosen', 'result': result}
            )
    else:
        form = PhoneLinkChooserForm(initial=initial_data, prefix='phone-link-chooser')

    return render_modal_workflow(
        request,
        'wagtailadmin/chooser/phone_link.html', None,
        shared_context(request, {
            'form': form,
        }), json_data={'step': 'phone_link'}
    )
