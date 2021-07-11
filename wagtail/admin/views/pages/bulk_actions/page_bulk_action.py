from django import forms

from wagtail.admin.views.bulk_action import BulkAction
from wagtail.core.models import Page


class DefaultForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['include_descendants'] = forms.BooleanField(
            required=False
        )


class PageBulkAction(BulkAction):
    model = Page
    object_key = 'page'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = DefaultForm()
        context['pages_with_no_access'] = [
            {'page': page, 'can_edit': page.permissions_for_user(self.request.user).can_edit()} for page in context['pages_with_no_access']
        ]
        return context
