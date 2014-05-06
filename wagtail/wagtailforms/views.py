import datetime
import json
import unicodecsv

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import permission_required

from wagtail.wagtailcore.models import Page
from wagtail.wagtailforms.models import FormSubmission, get_form_types
from wagtail.wagtailforms.forms import SelectDateForm


@permission_required('wagtailadmin.access_admin')
def index(request):
    form_types = get_form_types()
    form_pages = Page.objects.filter(content_type__in=form_types)

    return render(request, 'wagtailforms/index.html', {
        'form_pages': form_pages,
    })


@permission_required('wagtailadmin.access_admin')
def list_submissions(request, page_id):
    form_page = get_object_or_404(Page, id=page_id).specific
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
        writer = unicodecsv.writer(response, encoding='utf-8')

        header_row = ['Submission date'] + [label for name, label in data_fields]

        writer.writerow(header_row)
        for s in submissions:
            data_row = [s.submit_time]
            form_data = json.loads(s.form_data)
            for name, label in data_fields:
                data_row.append(form_data.get(name))
            writer.writerow(data_row)
        return response

    p = request.GET.get('p', 1)
    paginator = Paginator(submissions, 20)

    try:
        submissions = paginator.page(p)
    except PageNotAnInteger:
        submissions = paginator.page(1)
    except EmptyPage:
        submissions = paginator.page(paginator.num_pages)

    return render(request, 'wagtailforms/form_index.html', {
         'form_page': form_page,
         'select_date_form': select_date_form,
         'submissions': submissions,
    })
