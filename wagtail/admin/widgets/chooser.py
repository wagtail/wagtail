import json

from django import forms
from django.forms import widgets
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from wagtail.admin.staticfiles import versioned_static
from wagtail.core.models import Page
from wagtail.utils.widgets import WidgetWithScript


class AdminChooser(WidgetWithScript, widgets.Input):
    input_type = 'hidden'
    choose_one_text = _("Choose an item")
    choose_another_text = _("Choose another item")
    clear_choice_text = _("Clear choice")
    link_to_chosen_text = _("Edit this item")
    show_edit_link = True
    show_clear_link = True

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
        if 'show_clear_link' in kwargs:
            self.show_clear_link = kwargs.pop('show_clear_link')
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

    @property
    def media(self):
        return forms.Media(js=[
            versioned_static('wagtailadmin/js/page-chooser-modal.js'),
            versioned_static('wagtailadmin/js/page-chooser.js'),
        ])
