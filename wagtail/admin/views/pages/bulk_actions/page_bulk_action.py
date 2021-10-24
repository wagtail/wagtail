from django import forms

from wagtail.admin.views.bulk_action import BulkAction
from wagtail.admin.views.pages.search import page_filter_search
from wagtail.core.models import Page


class DefaultPageForm(forms.Form):
    include_descendants = forms.BooleanField(required=False)


class PageBulkAction(BulkAction):
    models = [Page]
    form_class = DefaultPageForm

    def get_all_objects_in_listing_query(self, parent_id):
        listing_objects = self.model.objects.all()

        if parent_id is not None:
            listing_objects = listing_objects.get(id=parent_id).get_children()

        listing_objects = listing_objects.values_list('pk', flat=True)

        if 'q' in self.request.GET:
            q = self.request.GET.get('q', '')

            listing_objects = page_filter_search(q, listing_objects)[0].results()

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
