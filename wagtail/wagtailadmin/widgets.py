from __future__ import absolute_import, unicode_literals

import json

from django.core.urlresolvers import reverse
from django.forms import widgets
from django.contrib.contenttypes.models import ContentType
from django.utils.safestring import mark_safe

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


class AdminPageChooser(WidgetWithScript, widgets.Input):
    input_type = 'hidden'
    target_content_type = None

    def __init__(self, content_type=None, **kwargs):
        super(AdminPageChooser, self).__init__(**kwargs)
        self.target_content_type = content_type or ContentType.objects.get_for_model(Page)

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


class StreamWidget(widgets.Widget):
    def __init__(self, block_def, attrs=None):
        super(StreamWidget, self).__init__(attrs=attrs)
        self.block_def = block_def

    def render(self, name, value, attrs=None):
        bound_block = self.block_def.bind(json.loads(value), prefix=name)
        js_initializer = self.block_def.js_initializer()
        if js_initializer:
            js_snippet = """
                <script>
                $(function() {
                    var initializer = %s;
                    initializer('%s');
                })
                </script>
            """ % (js_initializer, name)
        else:
            js_snippet = ''
        return mark_safe(bound_block.render_form() + js_snippet)

    @property
    def media(self):
        return self.block_def.all_media()

    def value_from_datadict(self, data, files, name):
        return json.dumps(self.block_def.value_from_datadict(data, files, name))
