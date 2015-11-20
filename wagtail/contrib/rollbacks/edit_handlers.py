"""
Contains application edit handlers.
"""
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from wagtail.wagtailadmin.edit_handlers import EditHandler

from .views import get_revisions


class BaseHistoryPanel(EditHandler):
    template = 'wagtailrollbacks/edit_handlers/page_history.html'

    def __init__(self, instance=None, form=None):
        super(BaseHistoryPanel, self).__init__(instance, form)
        self.instance = instance

    def render(self):
        context = {
            'self':         self,
            'revisions':    get_revisions(self.instance),
        }

        return mark_safe(
            render_to_string(self.template, context)
        )

class HistoryPanel(object):
    @staticmethod
    def bind_to_model(model):
        base = {'model': model}
        return type(str('_RelatedPanel'), (BaseHistoryPanel,), base)
