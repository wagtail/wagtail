from __future__ import absolute_import, unicode_literals

import json

from django import forms
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.functional import cached_property

from wagtail.utils.widgets import WidgetWithScript
from wagtail.wagtailcore.blocks import FieldBlock


class TableInput(WidgetWithScript, forms.HiddenInput):

    def __init__(self, table_options=None, attrs=None):
        self.table_options = table_options
        super(TableInput, self).__init__(attrs=attrs)

    def render(self, name, value, attrs=None):
        original_field_html = super(TableInput, self).render(name, value, attrs)
        return render_to_string("table_block/widgets/table.html", {
            'original_field_html': original_field_html,
            'attrs': attrs,
            'value': value,
        })

    def render_js_init(self, id_, name, value):
        return "initTable({0}, {1});".format(json.dumps(id_), json.dumps(self.table_options))


class TableBlock(FieldBlock):
    def __init__(self, required=True, help_text=None, table_options=None, **kwargs):
        # CharField's 'label' and 'initial' parameters are not exposed, as Block handles that functionality
        # natively (via 'label' and 'default')
        # CharField's 'max_length' and 'min_length' parameters are not exposed as table data needs to
        # have arbitrary length
        # table_options can contain any valid handsontable options: http://docs.handsontable.com/0.18.0/Options.html
        self.field_options = {'required': required, 'help_text': help_text}

        language = translation.get_language()
        if language is not None and len(language) > 2:
            language = language[:2]

        default_table_options = {
            'minSpareRows': 0,
            'startRows': 3,
            'startCols': 3,
            'colHeaders': False,
            'rowHeaders': False,
            'contextMenu': True,
            'editor': 'text',
            'stretchH': 'all',
            'height': 108,
            'language': language,
            'renderer': 'text',
            'autoColumnSize': False,
        }
        if table_options is not None:
            default_table_options.update(table_options)
        self.table_options = default_table_options
        super(TableBlock, self).__init__(**kwargs)

    @cached_property
    def field(self):
        return forms.CharField(widget=TableInput(table_options=self.table_options), **self.field_options)

    def value_from_form(self, value):
        return json.loads(value)

    def value_for_form(self, value):
        return json.dumps(value)

    def is_html_renderer(self):
        return self.table_options['renderer'] == 'html'

    def render(self, value):
        template = getattr(self.meta, 'template', None)
        if template and value:
            table_header = value['data'][0] if value.get('data', None) and len(value['data']) > 0 and value.get('first_row_is_table_header', False) else None
            first_col_is_header = value.get('first_col_is_header', False)
            context = {
                'self': value,
                self.TEMPLATE_VAR: value,
                'table_header': table_header,
                'first_col_is_header': first_col_is_header,
                'html_renderer': self.is_html_renderer(),
                'data': value['data'][1:] if table_header else value.get('data', [])
            }
            return render_to_string(template, context)
        else:
            return self.render_basic(value)

    @property
    def media(self):
        return forms.Media(
            css={'all': ['table_block/css/vendor/handsontable-0.24.2.full.min.css']},
            js=['table_block/js/vendor/handsontable-0.24.2.full.min.js', 'table_block/js/table.js']
        )

    class Meta:
        default = None
        template = 'table_block/blocks/table.html'
        icon = "table"
