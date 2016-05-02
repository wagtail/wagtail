from __future__ import absolute_import, unicode_literals

import itertools
import json
import warnings
from functools import total_ordering

from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.forms import widgets
from django.forms.utils import flatatt
from django.template.loader import render_to_string
from django.utils.encoding import python_2_unicode_compatible
from django.utils.formats import get_format
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from taggit.forms import TagWidget

from wagtail.utils.deprecation import RemovedInWagtail17Warning
from wagtail.utils.widgets import WidgetWithScript
from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.models import Page


class AdminAutoHeightTextInput(WidgetWithScript, widgets.Textarea):
    def __init__(self, attrs=None):
        # Use more appropriate rows default, given autoheight will alter this anyway
        default_attrs = {'rows': '1'}
        if attrs:
            default_attrs.update(attrs)

        super(AdminAutoHeightTextInput, self).__init__(default_attrs)

    def render_js_init(self, id_, name, value):
        return 'autosize($("#{0}"));'.format(id_)


class AdminDateInput(WidgetWithScript, widgets.DateInput):
    # Set a default date format to match the one that our JS date picker expects -
    # it can still be overridden explicitly, but this way it won't be affected by
    # the DATE_INPUT_FORMATS setting
    def __init__(self, attrs=None, format='%Y-%m-%d'):
        super(AdminDateInput, self).__init__(attrs=attrs, format=format)

    def render_js_init(self, id_, name, value):
        return 'initDateChooser({0}, {1});'.format(
            json.dumps(id_),
            json.dumps({'dayOfWeekStart': get_format('FIRST_DAY_OF_WEEK')})
        )


class AdminTimeInput(WidgetWithScript, widgets.TimeInput):
    def __init__(self, attrs=None, format='%H:%M'):
        super(AdminTimeInput, self).__init__(attrs=attrs, format=format)

    def render_js_init(self, id_, name, value):
        return 'initTimeChooser({0});'.format(json.dumps(id_))


class AdminDateTimeInput(WidgetWithScript, widgets.DateTimeInput):
    def __init__(self, attrs=None, format='%Y-%m-%d %H:%M'):
        super(AdminDateTimeInput, self).__init__(attrs=attrs, format=format)

    def render_js_init(self, id_, name, value):
        return 'initDateTimeChooser({0}, {1});'.format(
            json.dumps(id_),
            json.dumps({'dayOfWeekStart': get_format('FIRST_DAY_OF_WEEK')})
        )


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
    show_edit_link = True

    # when looping over form fields, this one should appear in visible_fields, not hidden_fields
    # despite the underlying input being type="hidden"
    is_hidden = False

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
        if 'show_edit_link' in kwargs:
            self.show_edit_link = kwargs.pop('show_edit_link')
        super(AdminChooser, self).__init__(**kwargs)


class AdminPageChooser(AdminChooser):
    choose_one_text = _('Choose a page')
    choose_another_text = _('Choose another page')
    link_to_chosen_text = _('Edit this page')

    def __init__(self, target_models=None, content_type=None, can_choose_root=False, **kwargs):
        super(AdminPageChooser, self).__init__(**kwargs)

        self.target_models = list(target_models or [Page])

        if content_type is not None:
            if target_models is not None:
                raise ValueError("Can not set both target_models and content_type")
            warnings.warn(
                'The content_type argument for AdminPageChooser() is deprecated. Use the target_models argument instead',
                category=RemovedInWagtail17Warning)
            if isinstance(content_type, ContentType):
                self.target_models = [content_type.model_class()]
            else:
                self.target_models = [ct.model_class() for ct in content_type]

        self.can_choose_root = can_choose_root

    @cached_property
    def target_content_types(self):
        warnings.warn(
            'AdminPageChooser.target_content_types is deprecated. Use AdminPageChooser.target_models instead',
            category=RemovedInWagtail17Warning)
        return list(ContentType.objects.get_for_models(*self.target_models).values())

    def _get_lowest_common_page_class(self):
        """
        Return a Page class that is an ancestor for all Page classes in
        ``target_models``, and is also a concrete Page class itself.
        """
        if len(self.target_models) == 1:
            # Shortcut for a single page type
            return self.target_models[0]
        else:
            return Page

    def render_html(self, name, value, attrs):
        model_class = self._get_lowest_common_page_class()

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
        if isinstance(value, Page):
            page = value
        else:
            # Value is an ID look up object
            model_class = self._get_lowest_common_page_class()
            page = self.get_instance(model_class, value)

        parent = page.get_parent() if page else None

        return "createPageChooser({id}, {model_names}, {parent}, {can_choose_root});".format(
            id=json.dumps(id_),
            model_names=json.dumps([
                '{app}.{model}'.format(
                    app=model._meta.app_label,
                    model=model._meta.model_name)
                for model in self.target_models
            ]),
            parent=json.dumps(parent.id if parent else None),
            can_choose_root=('true' if self.can_choose_root else 'false')
        )


@python_2_unicode_compatible
@total_ordering
class Button(object):
    def __init__(self, label, url, classes=set(), attrs={}, priority=1000):
        self.label = label
        self.url = url
        self.classes = classes
        self.attrs = attrs.copy()
        self.priority = priority

    def render(self):
        attrs = {'href': self.url, 'class': ' '.join(sorted(self.classes))}
        attrs.update(self.attrs)
        return format_html('<a{}>{}</a>', flatatt(attrs), self.label)

    def __str__(self):
        return self.render()

    def __repr__(self):
        return '<Button: {}>'.format(self.label)

    def __lt__(self, other):
        if not isinstance(other, Button):
            return NotImplemented
        return (self.priority, self.label) < (other.priority, other.label)

    def __eq__(self, other):
        if not isinstance(other, Button):
            return NotImplemented
        return (self.label == other.label and
                self.url == other.url and
                self.classes == other.classes and
                self.attrs == other.attrs and
                self.priority == other.priority)


class PageListingButton(Button):
    def __init__(self, label, url, classes=set(), **kwargs):
        classes = {'button', 'button-small', 'button-secondary'} | set(classes)
        super(PageListingButton, self).__init__(label, url, classes=classes, **kwargs)


class BaseDropdownMenuButton(Button):
    def __init__(self, *args, **kwargs):
        super(BaseDropdownMenuButton, self).__init__(*args, url=None, **kwargs)

    def get_buttons_in_dropdown(self):
        raise NotImplementedError

    def render(self):
        return render_to_string(self.template_name, {
            'buttons': self.get_buttons_in_dropdown(),
            'label': self.label,
            'title': self.attrs.get('title'),
            'is_parent': self.is_parent})


class ButtonWithDropdownFromHook(BaseDropdownMenuButton):
    template_name = 'wagtailadmin/pages/listing/_button_with_dropdown.html'

    def __init__(self, label, hook_name, page, page_perms, is_parent, **kwargs):
        self.hook_name = hook_name
        self.page = page
        self.page_perms = page_perms
        self.is_parent = is_parent

        super(ButtonWithDropdownFromHook, self).__init__(label, **kwargs)

    def get_buttons_in_dropdown(self):
        button_hooks = hooks.get_hooks(self.hook_name)
        return sorted(itertools.chain.from_iterable(
            hook(self.page, self.page_perms, self.is_parent)
            for hook in button_hooks))
