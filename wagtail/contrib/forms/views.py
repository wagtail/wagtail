import csv
import datetime

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.encoding import smart_str
from django.utils.translation import ungettext

from wagtail.utils.pagination import paginate
from wagtail.admin import messages
from wagtail.core.models import Page
from wagtail.contrib.forms.forms import SelectDateForm
from wagtail.contrib.forms.models import get_forms_for_user


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

    ordering = form_page.get_field_ordering(request.GET.getlist('order_by'))

    # convert ordering tuples to a list of strings like ['-submit_time']
    ordering_strings = [
        '%s%s' % ('-' if order_str[1] == 'descending' else '', order_str[0])
        for order_str in ordering]

    if request.GET.get('action') == 'CSV':
        #  Revert to CSV being sorted submit_time ascending for backwards compatibility
        submissions = form_submission_class.objects.filter(page=form_page).order_by('submit_time')
    else:
        submissions = form_submission_class.objects.filter(page=form_page).order_by(*ordering_strings)

    data_fields_with_ordering = []
    for name, label in data_fields:
        order = None
        for order_value in [o[1] for o in ordering if o[0] == name]:
            order = order_value
        data_fields_with_ordering.append({
            "name": name,
            "label": label,
            "order": order,
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
