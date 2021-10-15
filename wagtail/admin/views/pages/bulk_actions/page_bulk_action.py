from django import forms

from wagtail.admin.views.bulk_action import BulkAction
from wagtail.core.models import Page
from wagtail.search.query import MATCH_ALL
from wagtail.search.utils import parse_query_string


class DefaultPageForm(forms.Form):
    include_descendants = forms.BooleanField(required=False)


class PageBulkAction(BulkAction):
    models = [Page]
    form_class = DefaultPageForm

    def get_all_objects_in_listing_query(self, parent_id):
        _objects = self.model.objects.all()

        if 'q' in self.request.GET:
            q = self.request.GET.get('q', '')
            filters, query = parse_query_string(q, operator='and', zero_terms=MATCH_ALL)

            live_filter = filters.get('live') or filters.get('published')
            live_filter = live_filter and live_filter.lower()
            if live_filter in ['yes', 'true']:
                _objects = _objects.filter(live=True)
            elif live_filter in ['no', 'false']:
                _objects = _objects.filter(live=False)

            _objects = _objects.search(query).results()

        listing_objects = []
        for obj in _objects:
            listing_objects.append(obj.pk)

        return listing_objects

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items_with_no_access'] = [
            {'item': page, 'can_edit': page.permissions_for_user(self.request.user).can_edit()} for page in context['items_with_no_access']
        ]
        return context

    def get_execution_context(self):
        return {
            'user': self.request.user
        }
