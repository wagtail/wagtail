"""
Contains application views.
"""
from django.core.exceptions import PermissionDenied
from django.core.paginator import (
    EmptyPage,
    PageNotAnInteger,
    Paginator
)
from django.core.urlresolvers import reverse
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render
)
from django.utils.translation import ugettext as _

from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.utils import send_notification
from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.models import (
    Page,
    PageRevision
)


from .diff_tools import model_to_dict
from django.db.models.fields.related import OneToOneField
from dictdiffer import diff as dict_diff



def get_revisions(page, page_num=1, paginator_number=10):
    """
    Returns paginated queryset of PageRevision instances for
    specified Page instance.

    :param page: the page instance.
    :param page_num: the pagination page number.
    :rtype: django.db.models.query.QuerySet.
    """
    revisions = page.revisions.order_by('-created_at')
    current = page.get_latest_revision()

    if current:
        revisions.exclude(id=current.id)

    paginator = Paginator(revisions, paginator_number)

    try:
        revisions = paginator.page(page_num)
    except PageNotAnInteger:
        revisions = paginator.page(1)
    except EmptyPage:
        revisions = paginator.page(paginator.num_pages)

    return revisions


def page_revisions(request, page_id, template_name='wagtailrollbacks/edit_handlers/revisions.html'):
    """
    Returns GET response for specified page revisions.

    :param request: the request instance.
    :param page_id: the page ID.
    :param template_name: the template name.
    :rtype: django.http.HttpResponse.
    """
    page = get_object_or_404(Page, pk=page_id)
    page_perms = page.permissions_for_user(request.user)

    if not page_perms.can_edit():
        raise PermissionDenied

    page_num = request.GET.get('p', 1)
    revisions = get_revisions(page, page_num)

    return render(
        request,
        template_name,
        {
            'page': page,
            'revisions': revisions,
            'p': page_num,
        }
    )


def preview_page_version(request, revision_id):
    """
    Returns GET response for specified page preview.

    :param request: the request instance.
    :param reversion_pk: the page revision ID.
    :rtype: django.http.HttpResponse.
    """
    revision = get_object_or_404(PageRevision, pk=revision_id)

    if not revision.page.permissions_for_user(request.user).can_publish():
        raise PermissionDenied

    page = revision.as_page_object()
    request.revision_id = revision_id

    return page.serve_preview(request, page.default_preview_mode)


def confirm_page_reversion(request, revision_id, template_name='wagtailrollbacks/pages/confirm_reversion.html'):
    """
    Handles page reversion process (GET and POST).

    :param request: the request instance.
    :param revision_id: the page revision ID.
    :param template_name: the template name.
    :rtype: django.http.HttpResponse.
    """
    revision = get_object_or_404(PageRevision, pk=revision_id)
    page = revision.page

    if page.locked:
        messages.error(
            request,
            _("Page '{0}' is locked.").format(page.title),
            buttons=[]
        )

        return redirect(reverse('wagtailadmin_pages:edit', args=(page.id,)))

    page_perms = page.permissions_for_user(request.user)
    if not page_perms.can_edit():
        raise PermissionDenied

    if request.POST:
        is_publishing = bool(request.POST.get('action-publish')) and page_perms.can_publish()
        is_submitting = bool(request.POST.get('action-submit'))
        new_revision = page.rollback(
            revision_id=revision_id,
            user=request.user,
            submitted_for_moderation=is_submitting
        )

        if is_publishing:
            new_revision.publish()

            messages.success(
                request,
                _("Page '{0}' published.").format(page.title),
                buttons=[
                    messages.button(page.url, _('View live')),
                    messages.button(reverse('wagtailadmin_pages:edit', args=(page.id,)), _('Edit'))
                ]
            )
        elif is_submitting:
            messages.success(
                request,
                _("Page '{0}' submitted for moderation.").format(page.title),
                buttons=[
                    messages.button(reverse('wagtailadmin_pages:view_draft', args=(page.id,)), _('View draft')),
                    messages.button(reverse('wagtailadmin_pages:edit', args=(page.id,)), _('Edit'))
                ]
            )
            send_notification(new_revision.id, 'submitted', request.user.id)
        else:
            messages.success(
                request,
                _("Page '{0}' updated.").format(page.title),
                buttons=[]
            )

        for fn in hooks.get_hooks('after_edit_page'):
            result = fn(request, page)
            if hasattr(result, 'status_code'):
                return result

        return redirect('wagtailadmin_explore', page.get_parent().id)

    return render(
        request,
        template_name,
        {
            'page': page,
            'revision': revision,
            'page_perms': page_perms
        }
    )




def get_revision_fields(page):
    """
    Filters system fields out of diffs

    TODO: Find the correct system fields
    """
    field_defs = []
    exclude = [
        'id', 'content_type',
        'path', 'depth', 'numchild',
        'url_path', 'has_unpublished_changes',
        'owner', 'first_published_at',
        'latest_revision_created_at'
    ]

    for field in page.specific._meta.fields:

        if field.name in exclude:
            continue

        if isinstance(field, OneToOneField) and '_ptr' in field.name:
            continue

        d = {
            'name': field.name,
            'type': field.__class__.__name__,
        }

        if hasattr(page, field.name):
            d['value'] = getattr(page, field.name)

        field_defs.append(d)

    related = {}

    for attrib in filter(lambda a: not a.startswith('__'), dir(page)):
        value = getattr(page, attrib, False)

        # Quack quack
        if hasattr(value, 'get_queryset') and 'DeferringRelatedManager' in value.__class__.__name__:
            related[attrib] = [x for x in value.get_queryset()]

    return field_defs, related


def get_related_serial(related):
    """
    Returns serialised representations of related items
    """
    serialised = dict()

    for key, values in related.iteritems():
        serialised[key] = []

        for value in values:
            serialised[key].append(model_to_dict(value))

    return serialised





def preview_page_diff(request, revision_id, revision_2_id=None, template_name='wagtailrollbacks/edit_handlers/diff.html'):
    """
    Provides the ability to compare simple text values of two pages, and
    highlights chnages between them using difflib

    TODO:
     - Handle relations (eg, Images, StreamFields, etc)
     - Nice messages for nodes that don't have any diffable text content.
    """
    revision_1 = get_object_or_404(PageRevision, pk=revision_id)
    page_1 = revision_1.as_page_object()
    page_perms = page_1.permissions_for_user(request.user)

    if not page_perms.can_edit():
        raise PermissionDenied

    page_num = request.GET.get('p', 1)
    revisions = get_revisions(page_1, page_num, paginator_number=20)

    if revision_2_id is not None:
        revision_2_id = int(revision_2_id)
        page_2 = get_object_or_404(PageRevision, pk=revision_2_id).as_page_object()
        revision_2 = get_object_or_404(PageRevision, pk=revision_2_id)

    # Get latest revision by default
    else:
        page_2 = get_object_or_404(Page, id=page_1.id).get_latest_revision_as_page()
        revision_2 = page_2.get_latest_revision()

    # Always compare oldest to newest
    if revision_1.pk > revision_2.pk:
        revision_1, revision_2 = [revision_2, revision_1]
        page_1, page_2 = [page_2, page_1]

    revisions = [rev for rev in revisions if rev.pk is not revision_1.pk]

    # revision_1_fields, revision_1_related = get_revision_fields(page_1)
    # revision_2_fields, revision_2_related = get_revision_fields(page_2)

    revision_1_fields = model_to_dict(page_1)
    revision_2_fields = model_to_dict(page_2)

    difference = list(dict_diff(revision_1_fields, revision_2_fields))


    formatted_difference = []

    for change in difference:
        item = change
        title = item[1]

        if isinstance(title, list):
            title = {
                'label': title[0],
                'index': title[1]
            }
        else:
            title = {
                'label': title
            }

        change = item[2]
        new_change = []

        if isinstance(change, list):
            for operation in change:
                key = operation[0]
                value = operation[1]

                new_change.append({
                    'key': key,
                    'value': value,
                    'type': str(type(value).__name__)
                })
        else:
            new_change = change

        formatted_difference.append({
            'action': item[0],
            'title': title,
            'change': new_change
        })

    # print difference
    # print formatted_difference

    # # Don't compare things to themselves.
    # text_deltas = []

    # # Diff simple text fields
    # for idx, field in enumerate(revision_1_fields):

    #     if 'value' in revision_2_fields[idx]:
    #         diff_result = diff_fields(field['value'], revision_2_fields[idx]['value'])

    #         # TODO: Find a better way to determine if there's no differences
    #         # in the diff results.
    #         if diff_result is not None and 'No Differences Found' not in diff_result:
    #             text_deltas.append({
    #                 'html': diff_result,
    #                 'field_name': field['name']
    #             })

    # # Diff related objects

    # serial_a = get_related_serial(revision_1_related)
    # serial_b = get_related_serial(revision_2_related)




    return render(
        request,
        template_name,
        {
            'page': page_1,
            'revision': revision_1,
            'fields': revision_1_fields,
            'head': revision_2_fields,
            'compare_page': page_2,
            'compare_revision': revision_2,
            'revisions': revisions,
            'diff_id': revision_2_id,
            'difference': formatted_difference
            # 'deltas': [d for d in text_deltas if d['html'] is not None]
        }
    )
