import csv
import datetime

from django.core.exceptions import PermissionDenied
from django.core.paginator import InvalidPage
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.encoding import smart_str
from django.utils.translation import ungettext
from django.views.generic import ListView, TemplateView

from wagtail.admin import messages
from wagtail.contrib.forms.forms import SelectDateForm
from wagtail.contrib.forms.utils import get_forms_for_user
from wagtail.core.models import Page


def get_submissions_list_view(request, *args, **kwargs):
    """ Call the form page's list submissions view class """
    page_id = kwargs.get('page_id')
    form_page = get_object_or_404(Page, id=page_id).specific
    return form_page.serve_submissions_list_view(request, *args, **kwargs)


class SafePaginateListView(ListView):
    """ Listing view with safe pagination, allowing incorrect or out of range values """

    paginate_by = 20
    page_kwarg = 'p'

    def paginate_queryset(self, queryset, page_size):
        """Paginate the queryset if needed with nice defaults on invalid param."""
        paginator = self.get_paginator(
            queryset,
            page_size,
            orphans=self.get_paginate_orphans(),
            allow_empty_first_page=self.get_allow_empty()
        )
        page_kwarg = self.page_kwarg
        page_request = self.kwargs.get(page_kwarg) or self.request.GET.get(page_kwarg) or 0
        try:
            page_number = int(page_request)
        except ValueError:
            if page_request == 'last':
                page_number = paginator.num_pages
            else:
                page_number = 0
        try:
            if page_number > paginator.num_pages:
                page_number = paginator.num_pages  # page out of range, show last page
            page = paginator.page(page_number)
            return (paginator, page, page.object_list, page.has_other_pages())
        except InvalidPage:
            page = paginator.page(1)
            return (paginator, page, page.object_list, page.has_other_pages())
        return super().paginage_queryset(queryset, page_size)


class FormPagesListView(SafePaginateListView):
    """ Lists the available form pages for the current user """
    template_name = 'wagtailforms/index.html'
    context_object_name = 'form_pages'

    def get_queryset(self):
        """ Return the queryset of form pages for this view """
        queryset = get_forms_for_user(self.request.user)
        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)
        return queryset


class DeleteSubmissionsView(TemplateView):
    """ Delete the selected submissions """
    template_name = 'wagtailforms/confirm_delete.html'
    page = None
    submissions = None
    success_url = 'wagtailforms:list_submissions'

    def get_queryset(self):
        """ Returns a queryset for the selected submissions """
        submission_ids = self.request.GET.getlist('selected-submissions')
        submission_class = self.page.get_submission_class()
        return submission_class._default_manager.filter(id__in=submission_ids)

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
            ) % {'count': count}
        )

    def get_success_url(self):
        """ Returns the success URL to redirect to after a successful deletion """
        return self.success_url

    def dispatch(self, request, *args, **kwargs):
        """ Check permissions, set the page and submissions, handle delete """
        page_id = kwargs.get('page_id')

        if not get_forms_for_user(self.request.user).filter(id=page_id).exists():
            raise PermissionDenied

        self.page = get_object_or_404(Page, id=page_id).specific

        self.submissions = self.get_queryset()

        if self.request.method == 'POST':
            self.handle_delete(self.submissions)
            return redirect(self.get_success_url(), page_id)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """ Get the context for this view """
        context = super().get_context_data(**kwargs)

        context.update({
            'page': self.page,
            'submissions': self.submissions,
        })

        return context


class SubmissionsListView(SafePaginateListView):
    """ Lists submissions for the provided form page """
    template_name = 'wagtailforms/index_submissions.html'
    context_object_name = 'submissions'
    form_page = None
    ordering = ('-submit_time',)
    ordering_csv = ('submit_time',)  # keep legacy CSV ordering
    orderable_fields = ('id', 'submit_time',)  # used to validate ordering in URL
    select_date_form = None

    def dispatch(self, request, *args, **kwargs):
        """ Check permissions and set the form page """

        self.form_page = kwargs.get('form_page')

        if not get_forms_for_user(request.user).filter(pk=self.form_page.id).exists():
            raise PermissionDenied

        self.is_csv_export = (self.request.GET.get('action') == 'CSV')
        if self.is_csv_export:
            self.paginate_by = None

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """ Return queryset of form submissions with filter and order_by applied """
        submission_class = self.form_page.get_submission_class()
        queryset = submission_class._default_manager.filter(page=self.form_page)

        filtering = self.get_filtering()
        if filtering and isinstance(filtering, dict):
            queryset = queryset.filter(**filtering)

        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)

        return queryset

    def get_paginate_by(self, queryset):
        """ Get the number of items to paginate by, or ``None`` for no pagination """
        if self.is_csv_export:
            return None
        return self.paginate_by

    def get_validated_ordering(self):
        """ Return a dict of field names with ordering labels if ordering is valid """
        orderable_fields = self.orderable_fields or ()
        ordering = dict()
        if self.is_csv_export:
            #  Revert to CSV order_by submit_time ascending for backwards compatibility
            default_ordering = self.ordering_csv or ()
        else:
            default_ordering = self.ordering or ()
        if isinstance(default_ordering, str):
            default_ordering = (default_ordering,)
        ordering_strs = self.request.GET.getlist('order_by') or list(default_ordering)
        for order in ordering_strs:
            try:
                _, prefix, field_name = order.rpartition('-')
                if field_name in orderable_fields:
                    ordering[field_name] = (
                        prefix, 'descending' if prefix == '-' else 'ascending'
                    )
            except (IndexError, ValueError):
                continue  # invalid ordering specified, skip it
        return ordering

    def get_ordering(self):
        """ Return the field or fields to use for ordering the queryset """
        ordering = self.get_validated_ordering()
        return [values[0] + name for name, values in ordering.items()]

    def get_filtering(self):
        """ Return filering as a dict for submissions queryset """
        self.select_date_form = SelectDateForm(self.request.GET)
        result = dict()
        if self.select_date_form.is_valid():
            date_from = self.select_date_form.cleaned_data.get('date_from')
            date_to = self.select_date_form.cleaned_data.get('date_to')
            if date_to:
                # careful: date_to must be increased by 1 day
                # as submit_time is a time so will always be greater
                date_to += datetime.timedelta(days=1)
                if date_from:
                    result['submit_time__range'] = [date_from, date_to]
                else:
                    result['submit_time__lte'] = date_to
            elif date_from:
                result['submit_time__gte'] = date_from
        return result

    def get_csv_filename(self):
        """ Returns the filename for the generated CSV file """
        return 'export-{}.csv'.format(
            datetime.datetime.today().strftime('%Y-%m-%d')
        )

    def get_csv_response(self, context):
        """ Returns a CSV response """
        filename = self.get_csv_filename()
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment;filename={}'.format(filename)

        writer = csv.writer(response)
        writer.writerow(context['data_headings'])
        for data_row in context['data_rows']:
            writer.writerow(data_row)
        return response

    def render_to_response(self, context, **response_kwargs):
        if self.is_csv_export:
            return self.get_csv_response(context)
        return super().render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        """ Return context for view, handle CSV or normal output """
        context = super().get_context_data(**kwargs)
        submissions = context[self.context_object_name]
        data_fields = self.form_page.get_data_fields()
        data_rows = []

        if self.is_csv_export:
            # Build data_rows as list of lists containing formatted data values
            # Using smart_str prevents UnicodeEncodeError for values with non-ansi symbols
            for submission in submissions:
                form_data = submission.get_data()
                data_row = []
                for name, label in data_fields:
                    val = form_data.get(name)
                    if isinstance(val, list):
                        val = ', '.join(val)
                    data_row.append(smart_str(val))
                data_rows.append(data_row)
            data_headings = [smart_str(label) for name, label in data_fields]
        else:
            # Build data_rows as list of dicts containing model_id and fields
            for submission in submissions:
                form_data = submission.get_data()
                data_row = []
                for name, label in data_fields:
                    val = form_data.get(name)
                    if isinstance(val, list):
                        val = ', '.join(val)
                    data_row.append(val)
                data_rows.append({
                    'model_id': submission.id,
                    'fields': data_row
                })
            # Build data_headings as list of dicts containing model_id and fields
            ordering_by_field = self.get_validated_ordering()
            orderable_fields = self.orderable_fields
            data_headings = []
            for name, label in data_fields:
                order_label = None
                if name in orderable_fields:
                    order = ordering_by_field.get(name)
                    if order:
                        order_label = order[1]  # 'ascending' or 'descending'
                    else:
                        order_label = 'orderable'  # not ordered yet but can be
                data_headings.append({
                    'name': name,
                    'label': label,
                    'order': order_label,
                })

        context.update({
            'form_page': self.form_page,
            'select_date_form': self.select_date_form,
            'data_headings': data_headings,
            'data_rows': data_rows,
            'submissions': submissions,
        })

        return context
