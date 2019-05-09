import itertools
import json
from functools import total_ordering

from django.conf import settings
from django.forms import widgets
from django.forms.utils import flatatt
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.formats import get_format
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from taggit.forms import TagWidget

from wagtail.admin.datetimepicker import to_datetimepicker_format
from wagtail.core import hooks
from wagtail.core.models import Page
from wagtail.utils.widgets import WidgetWithScript

DEFAULT_DATE_FORMAT = '%Y-%m-%d'
DEFAULT_DATETIME_FORMAT = '%Y-%m-%d %H:%M'


class AdminAutoHeightTextInput(widgets.Textarea):
    template_name = 'wagtailadmin/widgets/auto_height_text_input.html'

    def __init__(self, attrs=None):
        # Use more appropriate rows default, given autoheight will alter this anyway
        default_attrs = {'rows': '1'}
        if attrs:
            default_attrs.update(attrs)

        super().__init__(default_attrs)


class AdminDateInput(widgets.DateInput):
    template_name = 'wagtailadmin/widgets/date_input.html'

    def __init__(self, attrs=None, format=None):
        default_attrs = {'autocomplete': 'new-date'}
        fmt = format
        if attrs:
            default_attrs.update(attrs)
        if fmt is None:
            fmt = getattr(settings, 'WAGTAIL_DATE_FORMAT', DEFAULT_DATE_FORMAT)
        self.js_format = to_datetimepicker_format(fmt)
        super().__init__(attrs=default_attrs, format=fmt)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        config = {
            'dayOfWeekStart': get_format('FIRST_DAY_OF_WEEK'),
            'format': self.js_format,
        }
        context['widget']['config_json'] = json.dumps(config)

        return context

    class Media:
        js = ['wagtailadmin/js/date-time-chooser.js']


class AdminTimeInput(widgets.TimeInput):
    template_name = 'wagtailadmin/widgets/time_input.html'

    def __init__(self, attrs=None, format='%H:%M'):
        default_attrs = {'autocomplete': 'new-time'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs, format=format)

    class Media:
        js = ['wagtailadmin/js/date-time-chooser.js']


class AdminDateTimeInput(widgets.DateTimeInput):
    template_name = 'wagtailadmin/widgets/datetime_input.html'

    def __init__(self, attrs=None, format=None):
        default_attrs = {'autocomplete': 'new-date-time'}
        fmt = format
        if attrs:
            default_attrs.update(attrs)
        if fmt is None:
            fmt = getattr(settings, 'WAGTAIL_DATETIME_FORMAT', DEFAULT_DATETIME_FORMAT)
        self.js_format = to_datetimepicker_format(fmt)
        super().__init__(attrs=default_attrs, format=fmt)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        config = {
            'dayOfWeekStart': get_format('FIRST_DAY_OF_WEEK'),
            'format': self.js_format,
        }
        context['widget']['config_json'] = json.dumps(config)

        return context

    class Media:
        js = ['wagtailadmin/js/date-time-chooser.js']


class AdminTagWidget(TagWidget):
    template_name = 'wagtailadmin/widgets/tag_widget.html'

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['autocomplete_url'] = reverse('wagtailadmin_tag_autocomplete')
        context['widget']['tag_spaces_allowed'] = getattr(settings, 'TAG_SPACES_ALLOWED', True)
        context['widget']['tag_limit'] = getattr(settings, 'TAG_LIMIT', None)

        return context


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
        result = super().value_from_datadict(data, files, name)
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
        super().__init__(**kwargs)


class AdminPageChooser(AdminChooser):
    choose_one_text = _('Choose a page')
    choose_another_text = _('Choose another page')
    link_to_chosen_text = _('Edit this page')

    def __init__(self, target_models=None, can_choose_root=False, user_perms=None, **kwargs):
        super().__init__(**kwargs)

        if target_models:
            model_names = [model._meta.verbose_name.title() for model in target_models if model is not Page]
            if len(model_names) == 1:
                self.choose_one_text += ' (' + model_names[0] + ')'

        self.user_perms = user_perms
        self.target_models = list(target_models or [Page])
        self.can_choose_root = can_choose_root

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

        original_field_html = super().render_html(name, value, attrs)

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

        return "createPageChooser({id}, {model_names}, {parent}, {can_choose_root}, {user_perms});".format(
            id=json.dumps(id_),
            model_names=json.dumps([
                '{app}.{model}'.format(
                    app=model._meta.app_label,
                    model=model._meta.model_name)
                for model in self.target_models
            ]),
            parent=json.dumps(parent.id if parent else None),
            can_choose_root=('true' if self.can_choose_root else 'false'),
            user_perms=json.dumps(self.user_perms),
        )

    class Media:
        js = [
            'wagtailadmin/js/page-chooser-modal.js',
            'wagtailadmin/js/page-chooser.js',
        ]


@total_ordering
class Button:
    show = True

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
        return (self.label == other.label
                and self.url == other.url
                and self.classes == other.classes
                and self.attrs == other.attrs
                and self.priority == other.priority)


class PageListingButton(Button):
    def __init__(self, label, url, classes=set(), **kwargs):
        classes = {'button', 'button-small', 'button-secondary'} | set(classes)
        super().__init__(label, url, classes=classes, **kwargs)


class BaseDropdownMenuButton(Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, url=None, **kwargs)

    @cached_property
    def dropdown_buttons(self):
        raise NotImplementedError

    def render(self):
        return render_to_string(self.template_name, {
            'buttons': self.dropdown_buttons,
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

        super().__init__(label, **kwargs)

    @property
    def show(self):
        return bool(self.dropdown_buttons)

    @cached_property
    def dropdown_buttons(self):
        button_hooks = hooks.get_hooks(self.hook_name)
        return sorted(itertools.chain.from_iterable(
            hook(self.page, self.page_perms, self.is_parent)
            for hook in button_hooks))
