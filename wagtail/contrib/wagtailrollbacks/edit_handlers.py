"""
Contains application edit handlers.
"""
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from wagtail.wagtailadmin.edit_handlers import EditHandler, ObjectList

from .views import get_revisions


def add_panel_to_edit_handler(model, panel_cls, heading, index=None):
    """
    Adds specified panel class to model class.
    :param model: the model class.
    :param panel_cls: the panel class.
    :param heading: the panel heading.
    :param index: the index position to insert at.
    """
    from wagtail.wagtailadmin.views.pages import get_page_edit_handler

    edit_handler = get_page_edit_handler(model)
    panel_instance = ObjectList(
        [panel_cls(), ],
        heading=heading
    ).bind_to_model(model)

    if index:
        edit_handler.children.insert(index, panel_instance)
    else:
        edit_handler.children.append(panel_instance)


class BaseHistoryPanel(EditHandler):
    template = 'wagtailrollbacks/edit_handlers/page_history.html'

    def __init__(self, instance=None, form=None):
        super(BaseHistoryPanel, self).__init__(instance, form)
        self.instance = instance

    def render(self):
        context = {
            'self': self,
            'revisions': get_revisions(self.instance),
        }

        return mark_safe(
            render_to_string(self.template, context)
        )


class HistoryPanel(object):

    @staticmethod
    def bind_to_model(model):
        base = {'model': model}
        return type(str('_RelatedPanel'), (BaseHistoryPanel,), base)
