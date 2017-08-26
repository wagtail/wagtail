from __future__ import absolute_import, unicode_literals

import csv
import datetime

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.encoding import smart_str
from django.utils.translation import ungettext

from wagtail.utils.pagination import paginate
from wagtail.wagtailadmin import messages
from wagtail.wagtailcore.models import Page
from wagtail.wagtailforms.forms import SelectDateForm
from wagtail.wagtailforms.models import get_forms_for_user


def index(request):
    form_pages = get_forms_for_user(request.user)

    paginator, form_pages = paginate(request, form_pages)

    return render(request, 'wagtailforms/index.html', {
        'form_pages': form_pages,
    })


def delete_submissions(request, page_id):
    if not get_forms_for_user(request.user).filter(id=page_id).exists():
        raise PermissionDenied

    page = get_object_or_404(Page, id=page_id).specific

    # Get submissions
    submission_ids = request.GET.getlist('selected-submissions')
    submissions = page.get_submission_class()._default_manager.filter(id__in=submission_ids)

    if request.method == 'POST':
        count = submissions.count()
        submissions.delete()

        messages.success(
            request,
            ungettext(
                "One submission has been deleted.",
                "%(count)d submissions have been deleted.",
                count
            ) % {
                'count': count,
            }
        )

        return redirect('wagtailforms:list_submissions', page_id)

    return render(request, 'wagtailforms/confirm_delete.html', {
        'page': page,
        'submissions': submissions,
    })


def list_submissions(request, page_id):
    if not get_forms_for_user(request.user).filter(id=page_id).exists():
        raise PermissionDenied

    form_page = get_object_or_404(Page, id=page_id).specific
    form_submission_class = form_page.get_submission_class()

    data_fields = form_page.get_data_fields()

    def validate_order_by(ordering_list):
        """
            accepts a list of strings ['-submit_time', 'id']
            checks these are valid and returns valid options
            invalid options are simply ignored - no error created
            removes duplicate field definitions
        """
        default = ('-', 'submit_time')
        valid_fields = ['id', 'submit_time']
        field_ordering = []
        if len(ordering_list) == 0:
            return [default]
        for order in ordering_list:
            try:
                none, prefix, field_name = order.rpartition('-')
                if field_name not in valid_fields:
                    continue  # Invalid field_name, skip it
                # only add to ordering if the field is not already set
                if field_name not in [o[1] for o in field_ordering]:
                    field_ordering.append((prefix, field_name))
            except (IndexError, ValueError):
                continue  # Invalid ordering specified, skip it
        return field_ordering

    field_ordering = validate_order_by(request.GET.getlist('order_by'))
    order_by = ['%s%s' % (o[0], o[1]) for o in field_ordering]

    submissions = form_submission_class.objects.filter(page=form_page).order_by(*order_by)

    data_fields_with_ordering = []
    for name, label in data_fields:
        ordering = None
        for order in [o for o in field_ordering if o[1] == name]:
            if order[0] == '-':
                ordering = 'descending'
            else:
                ordering = 'ascending'
        data_fields_with_ordering.append({
            "name": name,
            "label": label,
            "ordering": ordering,
        })

    data_headings = [label for name, label in data_fields]

    select_date_form = SelectDateForm(request.GET)
    if select_date_form.is_valid():
        date_from = select_date_form.cleaned_data.get('date_from')
        date_to = select_date_form.cleaned_data.get('date_to')
        # careful: date_to should be increased by 1 day since the submit_time
        # is a time so it will always be greater
        if date_to:
            date_to += datetime.timedelta(days=1)
        if date_from and date_to:
            submissions = submissions.filter(submit_time__range=[date_from, date_to])
        elif date_from and not date_to:
            submissions = submissions.filter(submit_time__gte=date_from)
        elif not date_from and date_to:
            submissions = submissions.filter(submit_time__lte=date_to)

    if request.GET.get('action') == 'CSV':
        # return a CSV instead
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment;filename=export.csv'

        # Prevents UnicodeEncodeError for labels with non-ansi symbols
        data_headings = [smart_str(label) for label in data_headings]

        writer = csv.writer(response)
        writer.writerow(data_headings)
        for s in submissions:
            data_row = []
            form_data = s.get_data()
            for name, label in data_fields:
                val = form_data.get(name)
                if isinstance(val, list):
                    val = ', '.join(val)
                data_row.append(smart_str(val))
            writer.writerow(data_row)
        return response

    paginator, submissions = paginate(request, submissions)

    data_rows = []
    for s in submissions:
        form_data = s.get_data()
        data_row = []
        for name, label in data_fields:
            val = form_data.get(name)
            if isinstance(val, list):
                val = ', '.join(val)
            data_row.append(val)
        data_rows.append({
            "model_id": s.id,
            "fields": data_row
        })

    return render(request, 'wagtailforms/index_submissions.html', {
        'form_page': form_page,
        'select_date_form': select_date_form,
        'submissions': submissions,
        'data_fields_with_ordering': data_fields_with_ordering,
        'data_rows': data_rows
    })
