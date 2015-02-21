from __future__ import absolute_import, unicode_literals

import json

from django.core.urlresolvers import reverse
from django.forms import widgets
from django.contrib.contenttypes.models import ContentType
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string

from wagtail.utils.widgets import WidgetWithScript
from wagtail.wagtailcore.models import Page

from taggit.forms import TagWidget


class AdminAutoHeightTextInput(WidgetWithScript, widgets.Textarea):
    def __init__(self, attrs=None):
        # Use more appropriate rows default, given autoheight will alter this anyway
        default_attrs = {'rows': '1'}
        if attrs:
            default_attrs.update(attrs)

        super(AdminAutoHeightTextInput, self).__init__(default_attrs)

    def render_js_init(self, id_, name, value):
        return '$("#{0}").autosize();'.format(id_)

class AdminDateInput(WidgetWithScript, widgets.DateInput):
    # Set a default date format to match the one that our JS date picker expects -
    # it can still be overridden explicitly, but this way it won't be affected by
    # the DATE_INPUT_FORMATS setting
    def __init__(self, attrs=None, format='%Y-%m-%d'):
        super(AdminDateInput, self).__init__(attrs=attrs, format=format)

    def render_js_init(self, id_, name, value):
        return 'initDateChooser({0});'.format(json.dumps(id_))


class AdminTimeInput(WidgetWithScript, widgets.TimeInput):
    def __init__(self, attrs=None, format='%H:%M'):
        super(AdminTimeInput, self).__init__(attrs=attrs, format=format)

    def render_js_init(self, id_, name, value):
        return 'initTimeChooser({0});'.format(json.dumps(id_))


class AdminDateTimeInput(WidgetWithScript, widgets.DateTimeInput):
    def __init__(self, attrs=None, format='%Y-%m-%d %H:%M'):
        super(AdminDateTimeInput, self).__init__(attrs=attrs, format=format)

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
    link_to_chosen_text = _("Edit this item")

    def get_instance(self, model_class, value):
        # helper method for cleanly turning 'value' into an instance object
        if value is None:
            return None

        try:
            return model_class.objects.get(pk=value)
        except model_class.DoesNotExist:
            return None

    def get_instance_and_id(self, model_class, value):
        if value is None:
            return (None, None)
        elif isinstance(value, model_class):
            return (value, value.pk)
        else:
            try:
                return (model_class.objects.get(pk=value), value)
            except model_class.DoesNotExist:
                return (None, None)

    def value_from_datadict(self, data, files, name):
        # treat the empty string as None
        result = super(AdminChooser, self).value_from_datadict(data, files, name)
        if result == '':
            return None
        else:
            return result

    def __init__(self, **kwargs):
        # allow choose_one_text / choose_another_text to be overridden per-instance
        if 'choose_one_text' in kwargs:
            self.choose_one_text = kwargs.pop('choose_one_text')
        if 'choose_another_text' in kwargs:
            self.choose_another_text = kwargs.pop('choose_another_text')
        if 'clear_choice_text' in kwargs:
            self.clear_choice_text = kwargs.pop('clear_choice_text')
        if 'link_to_chosen_text' in kwargs:
            self.link_to_chosen_text = kwargs.pop('link_to_chosen_text')
        super(AdminChooser, self).__init__(**kwargs)


class AdminPageChooser(AdminChooser):
    target_content_type = None
    choose_one_text = _('Choose a page')
    choose_another_text = _('Choose another page')
    link_to_chosen_text = _('Edit this page')

    def __init__(self, content_type=None, **kwargs):
        super(AdminPageChooser, self).__init__(**kwargs)
        self.target_content_type = content_type or ContentType.objects.get_for_model(Page)

    def render_html(self, name, value, attrs):
        model_class = self.target_content_type.model_class()
        instance, value = self.get_instance_and_id(model_class, value)

        original_field_html = super(AdminPageChooser, self).render_html(name, value, attrs)

        return render_to_string("wagtailadmin/widgets/page_chooser.html", {
            'widget': self,
            'original_field_html': original_field_html,
            'attrs': attrs,
            'value': value,
            'page': instance,
        })

    def render_js_init(self, id_, name, value):
        model_class = self.target_content_type.model_class()
        if isinstance(value, model_class):
            page = value
        else:
            page = self.get_instance(model_class, value)
        parent = page.get_parent() if page else None
        content_type = self.target_content_type

        return "createPageChooser({id}, {content_type}, {parent});".format(
            id=json.dumps(id_),
            content_type=json.dumps('{app}.{model}'.format(
                app=content_type.app_label,
                model=content_type.model)),
            parent=json.dumps(parent.id if parent else None))
