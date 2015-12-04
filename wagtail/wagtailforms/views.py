import datetime

import csv

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.encoding import smart_str
from django.utils.translation import ugettext as _

from wagtail.utils.pagination import paginate
from wagtail.wagtailcore.models import Page
from wagtail.wagtailforms.models import FormSubmission, get_forms_for_user
from wagtail.wagtailforms.forms import SelectDateForm
from wagtail.wagtailadmin import messages


def index(request):
    form_pages = get_forms_for_user(request.user)

    paginator, form_pages = paginate(request, form_pages)

    return render(request, 'wagtailforms/index.html', {
        'form_pages': form_pages,
    })


def delete_submission(request, page_id, submission_id):
    if not get_forms_for_user(request.user).filter(id=page_id).exists():
        raise PermissionDenied

    submission = get_object_or_404(FormSubmission, id=submission_id)
    page = get_object_or_404(Page, id=page_id)

    if request.method == 'POST':
        submission.delete()

        messages.success(request, _("Submission deleted."))
        return redirect('wagtailforms:list_submissions', page_id)

    return render(request, 'wagtailforms/confirm_delete.html', {
        'page': page,
        'submission': submission
    })


def list_submissions(request, page_id):
    form_page = get_object_or_404(Page, id=page_id).specific

    if not get_forms_for_user(request.user).filter(id=page_id).exists():
        raise PermissionDenied

    data_fields = [
        (field.clean_name, field.label)
        for field in form_page.form_fields.all()
    ]

    submissions = FormSubmission.objects.filter(page=form_page)

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

        writer = csv.writer(response)

        header_row = ['Submission date'] + [label for name, label in data_fields]

        writer.writerow(header_row)
        for s in submissions:
            data_row = [s.submit_time]
            form_data = s.get_data()
            for name, label in data_fields:
                data_row.append(smart_str(form_data.get(name)))
            writer.writerow(data_row)
        return response

    paginator, submissions = paginate(request, submissions)

    data_headings = [label for name, label in data_fields]
    data_rows = []
    for s in submissions:
        form_data = s.get_data()
        data_row = [s.submit_time] + [form_data.get(name) for name, label in data_fields]
        data_rows.append({
            "model_id": s.id,
            "fields": data_row
        })

    return render(request, 'wagtailforms/index_submissions.html', {
        'form_page': form_page,
        'select_date_form': select_date_form,
        'submissions': submissions,
        'data_headings': data_headings,
        'data_rows': data_rows
    })
