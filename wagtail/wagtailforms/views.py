from __future__ import absolute_import, unicode_literals

import csv
import datetime

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.encoding import smart_str
from django.utils.translation import ungettext
from django.views.generic import ListView, TemplateView

from wagtail.wagtailadmin import messages
from wagtail.wagtailcore.models import Page
from wagtail.wagtailforms.forms import SelectDateForm
from wagtail.wagtailforms.models import get_forms_for_user


class ListFormPages(ListView):
    """ Lists the available form pages for the current user. """
    template_name = 'wagtailforms/index.html'
    context_object_name = 'form_pages'
    paginate_by = 20
    page_kwarg = 'p'

    def get_queryset(self):
        return get_forms_for_user(self.request.user)


class DeleteSubmissions(TemplateView):
    """ Delete the selected submissions """
    template_name = 'wagtailforms/confirm_delete.html'

    page = None
    submissions = None

    success_url = 'wagtailforms:list_submissions'

    def get_queryset(self):
        """ Returns a queryset for the selected submissions """
        submission_ids = self.request.GET.getlist('selected-submissions')
        return self.page.get_submission_class()._default_manager.filter(id__in=submission_ids)

    def handle_delete(self, submissions):
        """ Deletes the given queryset """
        count = submissions.count()
        submissions.delete()

        messages.success(
            self.request,
            ungettext(
                'One submission has been deleted.',
                '%(count)d submissions have been deleted.',
                count
            ) % {
                'count': count,
            }
        )

    def get_success_url(self):
        """ Returns the success URL to redirect to after a successful deletion """
        return self.success_url

    def dispatch(self, request, *args, **kwargs):
        """ Check permissions, set the page, set submissions, handle delete """
        page_id = kwargs.get('page_id')

        if not get_forms_for_user(self.request.user).filter(id=page_id).exists():
            raise PermissionDenied

        self.page = get_object_or_404(Page, id=page_id).specific

        self.submissions = self.get_queryset()

        if self.request.method == 'POST':
            self.handle_delete(self.submissions)

            return redirect(self.get_success_url(), page_id)

        return super(DeleteSubmissions, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(DeleteSubmissions, self).get_context_data(**kwargs)

        context.update({
            'page': self.page,
            'submissions': self.submissions,
        })

        return context


class ListSubmissions(ListView):
    """ Lists submissions for the provided page """
    template_name = 'wagtailforms/index_submissions.html'
    context_object_name = 'submissions'
    paginate_by = 20
    page_kwarg = 'p'

    form_page = None
    select_date_form = None

    def dispatch(self, request, *args, **kwargs):
        """ Check permissions and set the form page """
        page_id = self.kwargs.get('page_id')

        if not get_forms_for_user(self.request.user).filter(id=page_id).exists():
            raise PermissionDenied

        self.form_page = get_object_or_404(Page, id=page_id).specific

        return super(ListSubmissions, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """ Returns the form submissions queryset and applies filter_queryset() """
        form_submission_class = self.form_page.get_submission_class()

        submissions = form_submission_class.objects.filter(page=self.form_page).order_by('submit_time')

        return self.filter_queryset(submissions)

    def filter_queryset(self, submissions):
        """ Filters the given queryset using the SelectDateForm """
        self.select_date_form = SelectDateForm(self.request.GET)

        if self.select_date_form.is_valid():
            date_from = self.select_date_form.cleaned_data.get('date_from')
            date_to = self.select_date_form.cleaned_data.get('date_to')
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

        return submissions

    def get_csv_filename(self):
        """ Returns the filename for the generated CSV file """
        return 'export-{}.csv'.format(
            datetime.datetime.today().strftime('%Y-%m-%d')
        )

    def get_csv_response(self, context):
        """ Returns a CSV response """
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment;filename={}'.format(self.get_csv_filename())

        # Prevents UnicodeEncodeError for labels with non-ansi symbols
        data_headings = [smart_str(label) for label in context['data_headings']]

        writer = csv.writer(response)
        writer.writerow(data_headings)
        for s in context[self.context_object_name]:
            data_row = []
            form_data = s.get_data()
            for name, label in context['data_fields']:
                val = form_data.get(name)
                if isinstance(val, list):
                    val = ', '.join(val)
                data_row.append(smart_str(val))
            writer.writerow(data_row)
        return response

    def render_to_response(self, context, **response_kwargs):
        if self.request.GET.get('action') == 'CSV':
            return self.get_csv_response(context)
        return super(ListSubmissions, self).render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super(ListSubmissions, self).get_context_data(**kwargs)

        data_fields = self.form_page.get_data_fields()
        data_headings = [label for name, label in data_fields]

        if self.request.GET.get('action') != 'CSV':
            data_rows = []
            for s in context[self.context_object_name]:
                form_data = s.get_data()
                data_row = []
                for name, label in data_fields:
                    val = form_data.get(name)
                    if isinstance(val, list):
                        val = ', '.join(val)
                    data_row.append(val)
                data_rows.append({
                    'model_id': s.id,
                    'fields': data_row
                })
            context['data_rows'] = data_rows

        context.update({
            'form_page': self.form_page,
            'select_date_form': self.select_date_form,
            'data_headings': data_headings,
            'data_fields': data_fields
        })

        return context
