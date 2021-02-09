import json

from django import forms
from django.contrib.admin.utils import quote
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.widgets import AdminChooser
from wagtail.admin.widgets.button import ListingButton
from wagtail.core.telepath import register
from wagtail.core.widget_adapters import WidgetAdapter


class AdminSnippetChooser(AdminChooser):

    def __init__(self, model, **kwargs):
        self.target_model = model
        name = self.target_model._meta.verbose_name
        self.choose_one_text = _('Choose %s') % name
        self.choose_another_text = _('Choose another %s') % name
        self.link_to_chosen_text = _('Edit this %s') % name

        super().__init__(**kwargs)

    def get_value_data(self, value):
        if value is None:
            return None
        elif isinstance(value, self.target_model):
            instance = value
        else:  # assume instance ID
            instance = self.target_model.objects.get(pk=value)

        app_label = self.target_model._meta.app_label
        model_name = self.target_model._meta.model_name
        quoted_id = quote(instance.pk)
        edit_url = reverse('wagtailsnippets:edit', args=[app_label, model_name, quoted_id])

        return {
            'id': instance.pk,
            'string': str(instance),
            'edit_url': edit_url,
        }

    def render_html(self, name, value_data, attrs):
        value_data = value_data or {}

        original_field_html = super().render_html(name, value_data.get('id'), attrs)

        return render_to_string("wagtailsnippets/widgets/snippet_chooser.html", {
            'widget': self,
            'original_field_html': original_field_html,
            'attrs': attrs,
            'value': bool(value_data),  # only used by chooser.html to identify blank values
            'display_title': value_data.get('string', ''),
            'edit_url': value_data.get('edit_url', ''),
        })

    @property
    def model_string(self):
        model = self.target_model
        return '{app}/{model}'.format(app=model._meta.app_label, model=model._meta.model_name)

    def render_js_init(self, id_, name, value_data):
        return "createSnippetChooser({id}, {model});".format(
            id=json.dumps(id_),
            model=json.dumps(self.model_string)
        )

    @cached_property
    def media(self):
        return forms.Media(js=[
            versioned_static('wagtailsnippets/js/snippet-chooser-modal.js'),
            versioned_static('wagtailsnippets/js/snippet-chooser.js'),
        ])


class SnippetChooserAdapter(WidgetAdapter):
    js_constructor = 'wagtail.snippets.widgets.SnippetChooser'

    def js_args(self, widget):
        return [
            widget.render_html('__NAME__', None, attrs={'id': '__ID__'}),
            widget.id_for_label('__ID__'), widget.model_string
        ]

    @cached_property
    def media(self):
        return forms.Media(js=[
            versioned_static('wagtailsnippets/js/snippet-chooser-telepath.js'),
        ])


register(SnippetChooserAdapter(), AdminSnippetChooser)


class SnippetListingButton(ListingButton):
    pass
