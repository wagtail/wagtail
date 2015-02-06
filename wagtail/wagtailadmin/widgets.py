from __future__ import absolute_import, unicode_literals

import json

from django.core.urlresolvers import reverse
from django.forms import widgets
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string

from wagtail.utils.widgets import WidgetWithScript
from wagtail.wagtailcore.models import Page

from taggit.forms import TagWidget


class AdminDateInput(WidgetWithScript, widgets.DateInput):
    def render_js_init(self, id_, name, value):
        return 'initDateChooser({0});'.format(json.dumps(id_))


class AdminTimeInput(WidgetWithScript, widgets.TimeInput):
    def render_js_init(self, id_, name, value):
        return 'initTimeChooser({0});'.format(json.dumps(id_))


class AdminDateTimeInput(WidgetWithScript, widgets.DateTimeInput):
    def render_js_init(self, id_, name, value):
        return 'initDateTimeChooser({0});'.format(json.dumps(id_))


class AdminTagWidget(WidgetWithScript, TagWidget):
    def render_js_init(self, id_, name, value):
        return "initTagField({0}, {1});".format(
            json.dumps(id_),
            json.dumps(reverse('wagtailadmin_tag_autocomplete')))


class AdminChooser(WidgetWithScript, widgets.Input):
    input_type = 'hidden'
    choose_one_text = _("Choose an item")
    choose_another_text = _("Choose another item")
    clear_choice_text = _("Clear choice")

    def __init__(self, **kwargs):
        # allow choose_one_text / choose_another_text to be overridden per-instance
        if 'choose_one_text' in kwargs:
            self.choose_one_text = kwargs.pop('choose_one_text')
        if 'choose_another_text' in kwargs:
            self.choose_another_text = kwargs.pop('choose_another_text')
        if 'clear_choice_text' in kwargs:
            self.clear_choice_text = kwargs.pop('clear_choice_text')
        super(AdminChooser, self).__init__(**kwargs)


class AdminPageChooser(AdminChooser):
    target_content_type = None
    choose_one_text = _('Choose a page')
    choose_another_text = _('Choose another page')

    def __init__(self, content_type=None, **kwargs):
        super(AdminPageChooser, self).__init__(**kwargs)
        self.target_content_type = content_type or ContentType.objects.get_for_model(Page)

    def render_html(self, name, value, attrs):
        original_field_html = super(AdminPageChooser, self).render_html(name, value, attrs)

        return render_to_string("wagtailadmin/widgets/page_chooser.html", {
            'original_field_html': original_field_html,
            'widget': self,
        })

    def render_js_init(self, id_, name, value):
        page = Page.objects.get(pk=value) if value else None
        parent = page.get_parent() if page else None
        content_type = self.target_content_type

        return "createPageChooser({id}, {content_type}, {parent});".format(
            id=json.dumps(id_),
            content_type=json.dumps('{app}.{model}'.format(
                app=content_type.app_label,
                model=content_type.model)),
            parent=json.dumps(parent.id if parent else None))
